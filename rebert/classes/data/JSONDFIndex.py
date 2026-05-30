#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: JSONDFIndex.py
#   REVISION: October, 2024
#   CREATION DATE: October, 2024
#   AUTHOR: David W. McDonald
#
#   A class that will index a specified field of a JSONDataFolder item. The class is focused on
#   indexing fields in a dictionary. Right now, there is no specific way to create a general index
#   of the items in the JSONDataFolder. This index class currently indexes NUMERIC data (FLOAT and 
#   INTEGER), STRING data and DATETIME data. They data type must be specified when the index is 
#   created - because the underlying index is a function of the data type. An index can also
#   be a computed value. When creating an index the function and a name for the function must
#   be supplied, along with the function. The combination of the function name and field are then
#   used when accessing the computed field index. Computed field indexes still need to be a
#   recognized type.
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
#
import sys, os, json, datetime, hashlib
#
#   Inherits from the standard object
from rebert.classes.base.Object import Object
#   This is a tree structure for data types other than strings
from rebert.classes.data.AVLTree import AVLTree

#
#   The name of the index file
DFI_INDEX_FILENAME = "index_{field}.json"
#
#   The name of the AVL Tree index file when it is pickled
DFI_INDEX_AVL_FILENAME = "index_{field}.avl"
#
#   Context contains basic information about the index. This should allow
#   loading of the index, creation of an index or reindexing
DFI_CONTEXT_TEMPLATE = {
    'folder_name':      "",             #   The name of the JSONDataFolder
    'index_file':       "",             #   The name of this index file
    'field':            "",             #   The field name to be indexed
    'data_type':        "",             #   The data type of data being indexed
    'index_type':       None,           #   The type of the index data structure
    'function':         None,           #   A reference to a function for computed fields
    'function_name':    "",             #   A descriptive name for the function
    'timestamp':        "",             #   The creation timestamp
    'secret':           "",             #   A 'secret' string for signing AVLTree write
    'signature':        "",             #   The write() signature response used in read
    'date_format':      "%m-%d-%Y",     #   An strf/strp date format used
                                        #   to interpret string dates
    'time_format':      "%H:%M:%S",     #   An strf/strp time format used 
                                        #   to interpret string times
    'datetime_format':  "%Y-%m-%d %H:%M:%S", 
                                        #   An strf/strp datetime format used
                                        #   to interpret datetime strings
    'data':             None            #   The index either as AVLTree() or dict()
}
#
#
#   This is a set of constants that name the types of indexes this
#   object can handle. These are added to the DFI_INDEX_TYPES list
#   for an easy check when creating a new index
DFI_STRING_INDEX = 'string'
DFI_INTEGER_INDEX = 'integer'
DFI_FLOAT_INDEX = 'float'
DFI_NUMERIC_INDEX = 'numeric'
DFI_DATE_INDEX = 'date'
DFI_TIME_INDEX = 'time'
DFI_DATETIME_INDEX = 'datetime'
#
#   A list that stores the types of indexes that we know
DFI_INDEX_TYPES = [DFI_STRING_INDEX, DFI_INTEGER_INDEX, DFI_FLOAT_INDEX, 
                   DFI_NUMERIC_INDEX, DFI_TIME_INDEX, DFI_TIME_INDEX, 
                   DFI_DATETIME_INDEX]
#
#   This is the punctuation that is stripped from tokens before they
#   are indexed
DFI_PUNCTUATION = ".,:;?!\"'&()$#~^*%=+[]{}|\\/<>"
#
#   This is the format of the datetime key strings. A datetime index
#   tries to convert all datetime objects to a string representation
#   so that the keys are standardized. 
DFI_DATETIME_KEY_FORMAT = '%Y%m%d%H%M%S'
#
#####
#   
#   START class JSONDFIndex definition
#   
#####
#
#
###
#   A class/object that can create and search and index of a JSONDataFolder object
#
class JSONDFIndex(Object):    
    '''
    This class implements an index
    
    Attributes:
        self.__jdf__        : The JSONDataFolder object that this is indexing
        self.__objects__    : A dictionary that relies on object IDs for access
        self.__context__    :
        self.__stops__      :
        self.__dirty__      :
        
    Methods:
        createIndex()       - create a new
        dropIndex()         - returns a list of recent movie releases
        search()            - requests the HTML page for the year supplied
        __numeric_search__()
        __datetime_search__()
        __string_search__()
        save()
        load()    
        __build_access_dict__()
        __build_string_index__()
        __tokenize_and_index__()
        __recurse_on_field__()
        __build_numeric_index__()
        __build_datetime_index__()
        __make_datetime_key__()

    '''
    def __init__(self, jdf=None, field="", function_name="", objects=None, stops=None, name="JSONDFIndex", *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        jdf         : A JSONDataFolder object that this index indexes
        objects     : an object access dictionary, provided by the JSONDataFolder
        stops       : An optional stopwords object, used with string indexing
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, *args, **kwargs)
        #
        self.__context__ = DFI_CONTEXT_TEMPLATE.copy()
        self.__jdf__ = jdf
        self.__objects__ = objects
        self.__stops__ = stops
        self.__dirty__ = False
        self.__path_prefix__ = None
        #
        #   If we were initialized with an underlying JSONDataFolder
        if self.__jdf__:
            #path, folder = os.path.split(self.__jdf__.__folder__)
            #self.__context__['folder_name'] = folder
            self.__path_prefix__ = self.__jdf__.__path_prefix__
            self.__context__['folder_name'] = self.__jdf__.__folder__
        #   If we were not supplied with a pre-built object access dictionary
        #   then build one for this index's individual use
        if not self.__objects__:
            self.log(f"not initialized with an 'objects' dictionary, building one", level="DEBUG")
            self.__build_access_dict__()
        else:
            self.log(f"initialized with 'objects' dictionary, having {len(self.__objects__)} keys", level="DEBUG")
        #   If we got the field - save that
        if field:
            self.__context__['field'] = field
            #   If the function name was also supplied, then we need to modify the field
            if function_name:
                function_name = function_name.replace('(','').replace(')','')
                #   This mirrors functional application to a field - as field name
                self.__context__['function_name'] = function_name+"("
                self.__context__['field'] = self.__context__['function_name']+field+")"
            else:
                self.__context__['function_name'] = str()
        #   With both the underlying JSONDataFolder and field, we can load
        if self.__jdf__ and field:
            self.load()
        return    
    
    
    
    
    
    ###
    #
    #   Create an index on a given field with a given type
    def createIndex(self, field="", index_type=None, func=None, function_name="", stops=None, secret="", pick=False):
        '''
        Performs the indexing operation and stores the data
        
        Parameters
        field               - The name of the field in a dict to index
        index_type          - A string, type of the index to create
        func                - The function to use for computed indexes
        function_name       - A string name describing the function
        stops               - A StopWords object to use if stops are to be removed
        secret              - A string 'secret' that is used when signing a pickled AVLTree
        pick                - If True, and this is an index based on an AVLTree
                                then the created index will be pickled when it is saved
        '''
        self.log(f"entering", level="DEBUG")
        if not self.__jdf__:
            raise Exception(f"Need a JSONDataFolder (jdf) before initializing an index.")
        if self.__context__['field']:
            raise Exception(f"The 'field' was previously set to '{self.__context__['field']}'.")
        if self.__context__['data_type']:
            raise Exception(f"The 'data_type' was previously set to '{str(self.__context__['data_type'])}'.")
        if not field:
            raise Exception(f"Must indicate a 'field' to index.")
        if not index_type:
            raise Exception(f"Must specify the 'type' of index.")
        if index_type not in DFI_INDEX_TYPES:
            raise Exception(f"The index type must be one of: {str(DFI_INDEX_TYPES)}")
        
        #   Build or rebuild the reference to all of the objects
        if not self.__objects__:
            self.log(f"did not have an 'objects' dictionary, building one", level="DEBUG")
            self.__build_access_dict__()
        else:
            self.log(f"existing 'objects' dictionary with {len(self.__objects__)} keys", level="DEBUG")

        #   Set up stop words if we got one
        self.__stops__ = stops
        
        #   Set the value for a secret - in case we need this
        if secret:
            self.__context__['secret'] = secret
        else:
            current_time = str(datetime.datetime.now())
            id_bytes = bytes(current_time,'utf-8')
            h = hashlib.blake2s(digest_size=16)
            h.update(id_bytes)
            self.__context__['secret'] = str(h.hexdigest())
        
        #   Initialize the field data for this
        if not func:
            self.__context__['field'] = field
        else:
            #   We'll indicate a computed field by adding a 'function' set of
            #   parentheses to the field name that is being computed over and the
            #   supplied function name, (function_name)
            self.__context__['function'] = func
            if function_name:
                function_name = function_name.replace('(','').replace(')','')
                #   This mirrors functional application to a field - as field name
                self.__context__['function_name'] = function_name+"("
                self.__context__['field'] = self.__context__['function_name']+field+")"
            else:
                self.__context__['function_name'] = str()
        self.__context__['data_type'] = index_type
        self.__context__['index_file'] = DFI_INDEX_FILENAME.format(field=self.__context__['field'])
        
        #   Now, index the data - only know how to do three kinds for now
        if index_type == DFI_STRING_INDEX:
            self.__context__['index_type'] = "dict"
            self.__build_string_index__()
        elif index_type == DFI_NUMERIC_INDEX:
            self.__context__['index_type'] = "AVLTree"
            self.__build_numeric_index__()
        elif index_type == DFI_INTEGER_INDEX:
            self.__context__['index_type'] = "AVLTree"
            self.__build_numeric_index__()
        elif index_type == DFI_FLOAT_INDEX:
            self.__context__['index_type'] = "AVLTree"
            self.__build_numeric_index__()
        elif index_type == DFI_DATETIME_INDEX:
            self.__context__['index_type'] = "AVLTree"
            self.__build_datetime_index__()
        elif index_type == DFI_DATE_INDEX:
            raise Exception(f"Cannot index {DFI_DATE_INDEX} yet")
        elif index_type == DFI_TIME_INDEX:
            raise Exception(f"Cannot index {DFI_TIME_INDEX} yet")
        else:
            raise Exception(f"The index type must be one of: {str(DFI_INDEX_TYPES)}")
        
        #
        #   Set a value that will make the save() method pickle
        #   the index file when saving. It turns out that if there
        #   is a 'signature' in the __context__ then the save() method
        #   will assume that the data was previously pickled and
        #   pickle the initial save of an AVLTree. This only matters
        #   for an AVLTree type index
        if pick and (self.__context__['index_type'] == "AVLTree"):
            self.__context__['signature'] = "pickle on save"
        
        #
        #   Mark the completion time, this should be saved
        create_time = datetime.datetime.now()
        timestamp = str(create_time).partition('.')[0]
        self.__context__['timestamp'] = timestamp
        self.__dirty__ = True
        self.log(f"returning", level="DEBUG")
        return
    
    
    ###
    #
    #   Basically, delete the data file associated with this index
    def dropIndex(self):
        self.log(f"entering", level="DEBUG")
        if not self.__context__['index_file']:
            raise Exception(f"The index file has not been created or saved.")
        #
        #   This is the root of the data folder
        folder_path = os.path.join(self.__path_prefix__, self.__context__['folder_name'])
        #   Create the context filename path
        context_path = os.path.join(folder_path, self.__context__['index_file'])
        #
        #   Try to remove the file, protect in case of a fault
        try:
            os.remove(context_path)
        except:
            self.log(f"could not delete file: '{context_path}'", level="WARN")
            self.log(f"JSONDataFolder possibly moved or renamed", level="WARN")
            raise
        self.__objects__ = None
        self.__context__ = DFI_CONTEXT_TEMPLATE.copy()
        self.__dirty__ = False
        self.log(f"returning", level="DEBUG")
        return


    ###
    #
    #   Conduct a search of this index. This checks the **kwargs 
    #   dictionary for the parameters associated with a given search 
    #   type and then passes those terms into the lower level search 
    #   method
    def search(self, *args, **kwargs):
        '''
        This searches the index for the search string, tokenized. This does an 'and' search
        by default, but can do a disjunctive, 'or' search.
        
        Parameters
        query               - A string of search terms, no specific order
        and                 - Boolean flag, assumed True by default, specifies
                              that all terms of the query must be present.
                              Indicates an 'and' search for query terms.
        or                  - Boolean flag, assumed False by default, specifies
                              that any term of the can be present for a match.
                              Indicates an 'or' search for query terms.
        
        value               - A value, numeric, to search
        lower               - The lower bound for a numeric range search
        upper               - The upper bound for a numeric range search
        
        datetime            - A datetime to use for a datetime search
        start               - The starting datetime of a range search
        stop                - The ending datetime of a range search

        raw                 - Boolean flag, assumed False, specifies that results
                              should be returned as 'raw' object IDs
        
        Returns
        a list of data items from the data folder, that satisfy the search
        criteria in the given indexed field
        
        '''
        self.log(f"entering", level="DEBUG")
        results = None
        #
        #   Set flag that applies to all searches
        raw = False
        if 'raw' in kwargs:
            if kwargs['raw']: 
                raw = True
                self.log(f"search results will be returned as 'raw' object IDs", level="DEBUG")
        #
        #   Figure out what kind of search to perform
        #
        #   This is a string index
        if self.__context__['data_type'] == DFI_STRING_INDEX:
            #   Search a string/term based dictionary
            if 'query' in kwargs:
                query = str(kwargs['query'])
                conjunction = True
                if 'and' in kwargs:
                    if not kwargs['and']:
                        conjunction = False
                elif 'or' in kwargs:
                    if kwargs['or']:
                        conjunction = False
                if not conjunction:
                    self.log(f"string 'or' search for: '{query}'", level="DEBUG")
                else:
                    self.log(f"string 'and' search for: '{query}'", level="DEBUG")
                results = self.__string_search__(query,conjunction,raw)
            else:
                raise Exception("Missing 'query' parameter for search")
        #
        #   This is a numeric index, integer or floate
        elif ((self.__context__['data_type'] == DFI_INTEGER_INDEX) or
              (self.__context__['data_type'] == DFI_FLOAT_INDEX) ):
            #   Extract the needed parameters for this type of search
            if 'value' in kwargs:
                #   The single value search take precedence over range search
                value = kwargs['value']
                results = self.__numeric_search__(self.__context__['data'],value,None,None,raw)
            elif 'lower' in kwargs and 'upper' in kwargs:
                lower = kwargs['lower']
                upper = kwargs['upper']
                results = self.__numeric_search__(self.__context__['data'],None,lower,upper,raw)
            else:
                self.log(f"Missing 'value' or missing 'lower' and 'upper' parameters")
                raise Exception("Missing 'value' or missing 'lower' and 'upper' parameters")
        #
        #   This is a datetime index
        elif self.__context__['data_type'] == DFI_DATETIME_INDEX:
            #   Extract the datetime related parameters 
            if 'datetime' in kwargs:
                #   The single value search take precedence over range search
                dt_key = self.__make_datetime_key__(kwargs['datetime'])
                results = self.__datetime_search__(self.__context__['data'],dt_key,None,None,raw)
            elif 'start' in kwargs and 'stop' in kwargs:
                dt_start = self.__make_datetime_key__(kwargs['start'])
                dt_stop = self.__make_datetime_key__(kwargs['stop'])
                results = self.__datetime_search__(self.__context__['data'],None,dt_start,dt_stop,raw)
            else:
                self.log(f"Missing 'datetime' or missing 'start' and 'stop' parameters")
                raise Exception("Missing 'datetime' or missing 'start' and 'stop' parameters")
        else:
            #   In this case we don't know what kind of index to search
            self.log(f"Could not resolve a search for index type '{self.__context__['data_type']}'")
            raise Exception(f"Could not resolve what type of search to perform")
        #
        #   Always want to return a list from this:
        if not results:
            results = list()
        self.log(f"returning, found {len(results)} items", level="DEBUG")
        return results




    ###
    #
    #   Search an AVLTree for a value or for a range lower..upper
    #
    def __numeric_search__(self, tree=None, value=None, lower=None, upper=None, raw=False):
        '''
        This performs a search of an AVLTree object
        
        Parameters
        tree                - The AVLTree to be searching
        value               - A specific numeric value
        lower               - A lower bound of a range search
        upper               - A upper bound of a range search
        raw             - Return result as a list of object IDs
        
        Returns
        a list of data items from the data folder
        '''
        #   No tree, no search
        if not tree: 
            self.log(f"need an AVLTree to search", level="DEBUG")
            return None
        self.log(f"entering", level="DEBUG")
        results = list()
        #
        #   If there is a single value, then search for that
        if not isinstance(value,bool) and (isinstance(value,int) or isinstance(value,float)):
            self.log(f"numeric search: {value}", level="DEBUG")
            candidates = tree.find(value)
            #
            #   We might want the raw list of object IDs
            if raw:
                self.log(f"returning raw object IDs - found {len(candidates)}", level="DEBUG")
                return candidates
            #
            #   Convert the candidates to the actual data items
            results = list()
            if candidates:
                for c in candidates:
                    results.append(self.__objects__[c])
        #
        #   Otherwise, look to see if we have a range search
        elif( not isinstance(lower,bool) and not isinstance(lower,bool) and
              (isinstance(lower,int) or isinstance(lower,float)) and
              (isinstance(upper,int) or isinstance(upper,float)) and 
              (lower < upper) ):
            results = list()
            self.log(f"numeric range: {lower}..{upper}", level="DEBUG")
            candidates = tree.findRange(tree,lower,upper)
            if candidates:
                #   candidates should be a dictionary where the keys
                #   are the matching indexed keys, and the values are
                #   lists of the object ids
                ckeys = list(candidates.keys())
                unique = list()
                #   First we'll make sure we have only one copy of a
                #   data folder object by adding all of the object ids 
                #   to a list, only if it is not in the list already
                for ck in ckeys:
                    oids = candidates[ck]
                    for oid in oids:
                        if oid not in unique: unique.append(oid)
                #
                #   We might want the raw list of object IDs
                if raw:
                    self.log(f"returning raw object IDs - found {len(unique)}", level="DEBUG")
                    return unique
                
                #   Then run through all of the unique object ids and add
                #   the data folder item to the results
                for oid in unique:
                    results.append(self.__objects__[oid])
        #
        #   Not a single value, not a range, don't know what to do with
        #   This is not a numeric type, that we can use, give up
        else:
            results = None
        self.log(f"returning - found {len(results)} items", level="DEBUG")
        return results




    ###
    #
    #   Search an AVLTree for a specific datetime or for a range 
    #   dt_start..dt_stop range of datetimes
    #
    def __datetime_search__(self, tree=None, dt_key=None, dt_start=None, dt_stop=None, raw=False):
        '''
        This performs a search of an AVLTree object
        
        Parameters
        tree                - The AVLTree to be searching
        dt_key              - A specific datetime
        dt_start            - The start of datetime range
        dt_stop             - The end of the datetime range
        raw             - Return result as a list of object IDs
        
        Returns
        a list of data items from the data folder
        '''
        #   No tree, no search
        if not tree: 
            self.log(f"need an AVLTree to search", level="DEBUG")
            return None
        self.log(f"entering", level="DEBUG")
        results = list()
        #
        #   If there is a single value, then search for that
        if isinstance(dt_key,str):
            self.log(f"datetime search: '{dt_key}'", level="DEBUG")
            candidates = tree.find(dt_key)
            #
            #   We might want the raw list of object IDs
            if raw:
                self.log(f"returning raw object IDs - found {len(candidates)}", level="DEBUG")
                return candidates
            #
            #   Convert the candidates to the actual data items
            results = list()
            if candidates:
                for c in candidates:
                    results.append(self.__objects__[c])
        #
        #   Otherwise, look to see if we have a range search
        elif isinstance(dt_start,str) and isinstance(dt_stop,str):
            results = list()
            self.log(f"datetime range: '{dt_start}'..'{dt_stop}'", level="DEBUG")
            candidates = tree.findRange(tree,dt_start,dt_stop)
            if candidates:
                #   candidates should be a dictionary where the keys
                #   are the matching indexed keys, and the values are
                #   lists of the object ids
                ckeys = list(candidates.keys())
                unique = list()
                #   First we'll make sure we have only one copy of a
                #   data folder object by adding all of the object ids 
                #   to a list, only if it is not in the list already
                for ck in ckeys:
                    oids = candidates[ck]
                    for oid in oids:
                        if oid not in unique: unique.append(oid)
                #
                #   We might want the raw list of object IDs
                if raw:
                    self.log(f"returning raw object IDs - found {len(unique)}", level="DEBUG")
                    return unique
                
                #   Then run through all of the unique object ids and add
                #   the data folder item to the results
                for oid in unique:
                    results.append(self.__objects__[oid])
        #
        #   Not a single value, not a range, don't know what to do with
        #   This is not a numeric type, that we can use, give up
        else:
            results = list()
        self.log(f"returning - found {len(results)} items", level="DEBUG")
        return results




    ###
    #
    #   Search a dictionary for the set of tokens in the query string.
    #   this defaults to a conjunction search - all terms must be present
    def __string_search__(self, query_string="", conjunction=True, raw=False):
        '''
        This searches the index for the search string, tokenized. This does an 'and' 
        search by default, but can do a disjunctive, 'or' search.
        
        Parameters
        query_string        - A string of search terms in no particular order
        conjunction         - Boolean flag, True by default
        raw             - Return result as a list of object IDs
        
        Returns
        a list of data items from the data folder
        '''
        self.log(f"entering", level="DEBUG")
        results = list()
        tokens = query_string.split()
        first_pass = True
        candidates = list()
        if conjunction:
            self.log(f"AND: {str(tokens)}", level="DEBUG")
        else:
            self.log(f"OR: {str(tokens)}", level="DEBUG")
        for t in tokens:
            token = t.lower()
            for p in DFI_PUNCTUATION:
                token = token.replace(p,'')
            #
            #   Remove whitespace before checking
            token = token.strip()
            #
            #   If the token is consumed by punctuation, skip it
            if not token: continue
            #
            #   If we're using a stop list, then check and possibly skip
            if self.__stops__ and token in self.__stops__:
                continue
            #
            #   If the token is not in the dict, don't have it
            if token not in self.__context__['data']: 
                #   For a conjunction, anytime a term does not exist, empty result
                if conjunction: return list()
                #   Otherwise go to the next term
                continue
            #
            if conjunction:
                #   This is an 'and' search, all terms must be present
                if first_pass:
                    candidates = self.__context__['data'][token]
                    first_pass = False
                else:
                    new_candidates = list()
                    for oid in self.__context__['data'][token]:
                        if oid in candidates: new_candidates.append(oid)
                    candidates = new_candidates
            else:
                #   This is an 'or' search, any term present
                for oid in self.__context__['data'][token]:
                    if oid not in candidates: candidates.append(oid)
        #
        #   We might want the raw list of object IDs
        if raw:
            self.log(f"returning raw object IDs - found {len(candidates)}", level="DEBUG")
            return candidates
        
        #
        #   Convert the list of 'found' object IDs to the actual data items
        if candidates:
            if self.__objects__:
                for c in candidates:
                    try:
                        results.append(self.__objects__[c])
                    except Exception as ex:
                        self.log(f"exception when accessing object ID '{c}'", level="WARN")
                        self.log(f"the item associated with '{c}' appears to be missing", level="WARN")
                        self.log(f"{ex}", level="WARN")
            else:
                self.log(f"the master object index, self.__objects__, is empty", level="DEBUG")
        else:
            self.log(f"no 'candidates' were found", level="DEBUG")
        #
        self.log(f"returning - found {len(results)} items", level="DEBUG")
        return results


    ###
    #
    #   Save this object into the folder associated with the 
    #   JSONDataFolder that this index is indexing
    def save(self, compact=True, pick=False):
        '''
        Save the index
        
        Parameters:
        compact         : boolean, whether to save in a more compressed form
        pick            : boolean, whether to pickle an AVLTree index
        '''
        #   
        self.log(f"entering", level="DEBUG")
        if not self.__dirty__:
            self.log(f"index has not been changed, not saving", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return
        
        if not self.__context__['folder_name']:
            raise Exception(f"This index is not yet associated with a JSONDataFolder.")
        if not self.__context__['index_file']:
            raise Exception(f"Must 'createIndex()' before saving the index.")
        #
        #   This is the root of the data folder
        folder_path = os.path.join(self.__path_prefix__, self.__context__['folder_name'])

        #
        #   Create the context filename path
        context_path = os.path.join(folder_path, self.__context__['index_file'])
        
        #
        #   Handle the case of a computed field - we need to keep the function
        #   as long as we will continue to index new items
        func = None
        #   Mirrors a functional application to the field as the field name
        if self.__context__['field'].startswith(self.__context__['function_name']):
            func = self.__context__['function']
            self.__context__['function'] = None
        
        #
        #   Handle the case of an AVLTree
        tree = None
        if self.__context__['index_type'] == "AVLTree":
            #   With an AVLTree, extract the tree from the data slot because
            #   we're going to use the data slot for either a list of the
            #   tree nodes (to store as JSON) or the name of a binary data
            #   file that contains the tree data. The tree is put back in the
            #   data slot after the __context__ has been written.
            tree = self.__context__['data']
            fname = DFI_INDEX_AVL_FILENAME.format(field=self.__context__['field'])
            #   Either specify it's to be pickled - or it was previously pickled
            if pick or self.__context__['signature']:
                #tree_path = os.path.join(self.__context__['folder_name'],fname)
                tree_path = os.path.join(folder_path, fname)
                #   Note, a secret is created or intitalized when the index is created
                signature = tree.write(fname=tree_path, secret=self.__context__['secret'])
                #   When pickled, the name of the pickle file is in data slot
                self.__context__['data'] = fname
                self.__context__['signature'] = signature
                self.log(f"saving AVLTree as signed pickle file", level="DEBUG")
            else:
                #   In the JSON version a list of nodes is in data slot
                self.__context__['data'] = tree.__get_raw_nodes__()
                self.log(f"saving AVLTree as list of dictionary nodes", level="DEBUG")

        #   Open the file and get ready to save it
        f = open(context_path,"w")
        mesg = f"saving index '{context_path}'"
        #
        #   This option makes the resulting JSON text files 
        #   harder/easier to read, compact has no spaces
        if compact:
            json.dump(self.__context__,f)
            self.log(f"{mesg} compact: True", level="DEBUG")
        else:
            json.dump(self.__context__,f,indent=4)
            self.log(f"{mesg} compact: False", level="DEBUG")
        f.close()
        #
        #   With an AVLTree, after everything is saved, then we need to
        #   put the actual tree back in the data slot so it can be used
        if self.__context__['index_type'] == "AVLTree":
            self.__context__['data'] = tree
        #
        #   With a computed field we need to keep the function while we continue
        #   to index new items
        if func:
            self.__context__['function'] = func
        
        self.__dirty__ = False
        self.log(f"returning", level="DEBUG")
        return



    def load(self, jdf=None, field=None):
        self.log(f"entering", level="DEBUG")
        if not self.__jdf__:
            if not jdf:
                raise Exception(f"This index is not yet associated with a JSONDataFolder.")
            self.__jdf__ = jdf
            self.__path_prefix__ = self.__jdf__.__path_prefix__
            self.__context__['folder_name'] = self.__jdf__.__folder__
        if not self.__context__['field']:
            if not field:
                raise Exception(f"Must have an index 'field' to load an index.")
            self.__context__['field'] = field

        #
        #   This is the root of the data folder
        folder_path = os.path.join(self.__path_prefix__, self.__context__['folder_name'])

        #
        #   Load the context file for the index
        index_file = DFI_INDEX_FILENAME.format(field=self.__context__['field'])
       
        #context_path = os.path.join(self.__context__['folder_name'],index_file)
        context_path = os.path.join(folder_path,index_file)
        f = open(context_path,"r")
        context = json.load(f)
        self.__context__ = context
        f.close()
        #   If this were a string type index, then we're done.
        #
        #   However, in the case that this is an AVLTree - then we might need to
        #   do more work to rebuild the AVLTree
        if self.__context__['index_type'] == "AVLTree":
            #   If the 'data' field is a string then it should be a filename
            if isinstance(self.__context__['data'],str):
                self.log(f"loading an AVLTree from file: '{self.__context__['data']}'", level="DEBUG")
                tree_path = os.path.join(self.__context__['folder_name'],self.__context__['data'])
                tree = AVLTree()
                #   Note, the read() method returns a NEW, different AVLTree object
                #   so we need to save *that* tree in the data field
                self.__context__['data'] = tree.read(fname = tree_path,
                                                    secret = self.__context__['secret'],
                                                    signature = self.__context__['signature'])
                self.__context__['data'].setLogger(logger=self.getLogger())
            #   If the 'data' field is a list, then it's a list of nodes
            elif isinstance(self.__context__['data'],list):
                self.log(f"rebuilding AVLTree from 'data' nodes", level="DEBUG")
                node_list = self.__context__['data']
                self.__context__['data'] = AVLTree(logger=self.getLogger())
                for node in node_list:
                    self.__context__['data'].insert(node=node)
            else:
                self.log(f"context 'data' field is not a recognized AVLTree type", level="DEBUG")
                
        self.__dirty__ = False
        self.log(f"returning", level="DEBUG")
        return



    def __build_access_dict__(self, jdf=None):
        '''
        Build the underlying dictionary object that stores data with the object IDs. This
        structure is used to return the items that are found during a search.
        
        Optional Parameter:
        jdf                 : An JSONDataFolder object that holds the data for this index
        '''
        self.log(f"entering", level="DEBUG")
        if jdf:
            self.__jdf__ = jdf
            self.__path_prefix__ = self.__jdf__.__path_prefix__
            self.__context__['folder_name'] = self.__jdf__.__folder__
        if not self.__jdf__:
            raise Exception(f"Need a JSONDataFolder to build the access dictionary.")
        
        chunk_names = list(self.__jdf__.__chunks__.keys())
        for cname in chunk_names:
            chunk = self.__jdf__.__chunks__[cname]
            for wrappered in chunk['data']:
                oid_key = list(wrappered.keys())[0]
                data = list(wrappered.values())[0]
                self.__objects__[oid_key] = data
        self.log(f"built new access dictionary with {len(self.__objects__)} keys", level="DEBUG")        
        self.log(f"returning", level="DEBUG")
        return



    def __build_string_index__(self):
        '''
        Build an index based on a field containing string data. 
        '''
        self.log(f"entering", level="DEBUG")
        self.__context__['data'] = dict()
        oid_list = list(self.__objects__.keys())
        for oid in oid_list:
            #   Get the data item
            item = self.__objects__[oid]
            #   Mirrors the functional application to the field as the field name
            field = self.__context__['field'].replace(self.__context__['function_name'],'').replace(')','')
            if isinstance(item,dict):
                field_value = self.__recurse_on_field__(item,field.split('.'))
            else:
                field_value = item
            #
            #   Now for a computed field, we apply the function and then index the result
            if self.__context__['function']:
                try:
                    self.log(f"Applying function to field_value: {str(type(field_value))}", level="DEBUG")
                    field_value = self.__context__['function'](field_value)
                except Exception as ex:
                    self.log(f"Exception when applying function to field '{self.__context__['field']}'", level="CRITICAL")
                    self.log(f"{str(ex)}", level="CRITICAL")
            #
            #   Make sure this is not an empty value
            if field_value:
                #   If this is a string, then just index it
                if isinstance(field_value,str):
                    self.__tokenize_and_index__(field_value,oid)
                elif isinstance(field_value,list):
                    #   If we have a list then, run through each item, and
                    #   index it - if it is a string
                    for item in field_value:
                        if isinstance(item,str):
                            self.__tokenize_and_index__(item,oid)
                else:
                    self.log(f"Trying to index strings but got: '{str(type(field_value))}'", level="WARN")


        self.log(f"returning", level="DEBUG")
        return



    def __tokenize_and_index__(self, field_value="", oid=""):
        self.log(f"entering", level="DEBUG")
        tokens = field_value.split()
        for t in tokens:
            token = t.lower()
            for p in DFI_PUNCTUATION:
                token = token.replace(p,'')
            #
            #   If the token is consumed by punctuation, skip it
            if not token: continue
            #
            #   If we're using a stop list, then check and possibly skip
            if self.__stops__ and token in self.__stops__:
                continue
            #
            #   If the token is not in the dict, then add a list
            if token not in self.__context__['data']:
                self.__context__['data'][token] = list()
            #
            #   Now add the oid - to indicate that this object has
            #   this token in this field
            self.__context__['data'][token].append(oid)
        self.log(f"returning", level="DEBUG")
        return


    def __recurse_on_field__(self, item=None, field_keys=[]):
        '''
        If the index field is in a nested dictionary, then this will recurse to find the
        specified field - and return the data 
        '''
        self.log(f"entering", level="DEBUG")
        value = None
        if len(field_keys) > 1:
            try:
                value = self.__recurse_on_field__(item[field_keys[0]],field_keys[1:])
            except:
                value = None
        else:
            try:
                value = item[field_keys[0]]
            except:
                value = None
        self.log(f"returning", level="DEBUG")
        return value


    def __build_numeric_index__(self):
        '''
        Build a numeric index using an AVLTree data structure 
        '''
        self.log(f"entering", level="DEBUG")
        #   Create an instance of the AVLTree
        self.__context__['data'] = AVLTree(logger=self.getLogger())
        oid_list = list(self.__objects__.keys())
        for oid in oid_list:
            #   Get the data item
            item = self.__objects__[oid]
            #   Mirrors the functional application to the field as the field name
            field = self.__context__['field'].replace(self.__context__['function_name'],'').replace(')','')
            if isinstance(item,dict):
                field_value = self.__recurse_on_field__(item,field.split('.'))
                #
                #   For a computed field, we apply the function and then index the result
                if self.__context__['function']:
                    try:
                        self.log(f"Applying function to field_value: {str(type(field_value))}", level="DEBUG")
                        field_value = self.__context__['function'](field_value)
                        #self.log(f"Computed result: {str(type(field_value))}: {str(field_value)}", level="DEBUG")
                    except Exception as ex:
                        self.log(f"Exception when applying function to field '{self.__context__['field']}'", level="CRITICAL")
                        self.log(f"{str(ex)}", level="CRITICAL")
                #
                #   Index the result
                if (field_value and not isinstance(field_value,bool) and
                    (isinstance(field_value,int) or isinstance(field_value,float)) ):
                    self.log(f"inserting with key: {type(field_value)}:{field_value}", level="DEBUG")
                    self.__context__['data'].insert(key=field_value, value=oid)
                elif isinstance(field_value,list):
                    #   Run through the items in the list, if any are numeric
                    #   then insert that key to represent that this field of the
                    #   dictionary has numeric values in it
                    self.log(f"indexing a list, nested in a dictionary", level="DEBUG")
                    for key in field_value:
                        if isinstance(key,int) or isinstance(key,float):
                            self.__context__['data'].insert(key=key, value=oid)
                else:
                    #   A type, nested in a dictionary that we know how to index
                    pass
                #   Make sure that data field is empty
                field_value = None
            elif not isinstance(item,bool) and (isinstance(item,int) or isinstance(item,float)):
                #
                #   Now for a computed field, we apply the function and then index the result
                if self.__context__['function']:
                    try:
                        self.log(f"Applying function to item", level="DEBUG")
                        item = self.__context__['function'](item)
                        #self.log(f"Computed result: {str(type(item))}: {str(item)}", level="DEBUG")
                    except Exception as ex:
                        self.log(f"Exception when applying function to field '{self.__context__['field']}'", level="CRITICAL")
                        self.log(f"{str(ex)}", level="CRITICAL")
                #
                #   We do a quick check on the type to make sure the insert will be valid
                if not isinstance(item,bool) and (isinstance(item,int) or isinstance(item,float)):
                    self.log(f"inserting with key: {type(item)}:{item}", level="DEBUG")
                    self.__context__['data'].insert(key=item, value=oid)
            elif isinstance(item,list):
                #
                #   Now for a computed field, we apply the function and then index the result
                if self.__context__['function']:
                    try:
                        self.log(f"Applying function to item", level="DEBUG")
                        item = self.__context__['function'](item)
                        #self.log(f"Computed result: {str(type(item))}: {str(item)}", level="DEBUG")
                    except Exception as ex:
                        self.log(f"Exception when applying function to field '{self.__context__['field']}'", level="CRITICAL")
                        self.log(f"{str(ex)}", level="CRITICAL")
                #
                #   Result was just an int or float
                if not isinstance(item,bool) and (isinstance(item,int) or isinstance(item,float)):
                    self.log(f"inserting with key: {type(item)}:{item}", level="DEBUG")
                    self.__context__['data'].insert(key=item, value=oid)
                #
                #   Result is still a list
                elif isinstance(item,list):
                    #   Run through the items in the list, if any are numeric
                    #   then insert that key to represent that the list has
                    #   possibly many ways to get to that object in the data folder
                    for key in item:
                        if not isinstance(key,bool) and (isinstance(key,int) or isinstance(key,float)):
                            self.log(f"inserting list item with key: {type(key)}:{key}", level="DEBUG")
                            self.__context__['data'].insert(key=key, value=oid)
            else:
                #   Not something we know how to index
                pass
        self.log(f"returning", level="DEBUG")
        return



    def __build_datetime_index__(self):
        '''
        Build a datetime index using an AVLTree data structure
        The keys will be strings in a YYYYMMDDHHMMSS format this will
        facilitate individual datetime and range searching
        '''
        self.log(f"entering", level="DEBUG")
        #   Create an instance of the AVLTree
        self.__context__['data'] = AVLTree(logger=self.getLogger())
        oid_list = list(self.__objects__.keys())
        for oid in oid_list:
            #   Get the data item
            item = self.__objects__[oid]
            #   Mirrors the functional application to the field as the field name
            field = self.__context__['field'].replace(self.__context__['function_name'],'').replace(')','')
            #
            #   Resolve the field value, if this is a dict type thing
            if isinstance(item,dict):
                field_value = self.__recurse_on_field__(item,field.split('.'))
            else:
                field_value = item
            #
            #   For a computed field, we apply the function and then index the result
            if self.__context__['function']:
                try:
                    self.log(f"Applying function to field_value: {str(type(field_value))}", level="DEBUG")
                    field_value = self.__context__['function'](field_value)
                    #self.log(f"Computed result: {str(type(field_value))}: {str(field_value)}", level="DEBUG")
                except Exception as ex:
                    self.log(f"Exception when applying function to field '{self.__context__['field']}'", level="CRITICAL")
                    self.log(f"{str(ex)}", level="CRITICAL")
            #
            dt_key = self.__make_datetime_key__(field_value)
            if dt_key:
                self.__context__['data'].insert(key=dt_key, value=oid)
        self.log(f"returning", level="DEBUG")
        return



    def __make_datetime_key__(self, field_value=None):
        '''
        Take a data item and try to make a YYYYMMDDHHMMSS key string
        '''
        dt_key = str()
        if not field_value: return dt_key
        self.log(f"entering", level="DEBUG")
        #
        #   If the format field is set to an empty string then the
        #   value in the resolved field *is* the key
        if not self.__context__['datetime_format']:
            self.log(f"No 'datetime_format', field value is datetime key", level="DEBUG")
            if isinstance(field_value, str):
                self.log(f"returning", level="DEBUG")
                return field_value
            else:
                self.log(f"field value should be string type, but have {type(field_value)}", 
                         level="WARN")
                self.log(f"returning", level="DEBUG")
                return field_value
        #
        #   Have a format string - try to make a standardized key string
        if isinstance(field_value, datetime.datetime):
            #   The field_value is a datetime - create a string that meets the key format
            dt_key = item.strftime(DFI_DATETIME_KEY_FORMAT)
        elif isinstance(field_value, str):
            #   Try to standardize by converting to a datetime object and then
            #   converting back to a datetime key string
            try:
                #   Try conversion with date and time
                dt_obj = datetime.datetime.strptime(field_value, 
                                                    self.__context__['datetime_format'])
                dt_key = dt_obj.strftime(DFI_DATETIME_KEY_FORMAT)
                self.log(f"parsed field value as datetime", level="DEBUG")
            except:
                try:
                    #   Try conversion just the date, only if the format is there
                    if self.__context__['date_format']:
                        dt_obj = datetime.datetime.strptime(field_value, 
                                                            self.__context__['date_format'])
                        dt_key = dt_obj.strftime(DFI_DATETIME_KEY_FORMAT)
                        self.log(f"parsed field value as date", level="DEBUG")
                except:
                    self.log(f"could not parse field value '{field_value}' as datetime or date", 
                             level="DEBUG")
                    dt_key = str()
        else:
            #   Do not know how to convert this to a thing we can use
            self.log(f"can't convert type {type(field_value)} to datetime str", level="DEBUG")
            dt_key = str()
        if dt_key:
            self.log(f"returning, '{dt_key}'", level="DEBUG")
        else:
            self.log(f"returning, an empty string", level="DEBUG")
        return dt_key



if __name__ == '__main__':
    print("JSONDFIndex.py is a class with no main()")
