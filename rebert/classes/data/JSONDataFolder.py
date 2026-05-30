#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: JSONDataFolder.py
#   REVISION: October, 2024
#   CREATION DATE: May, 2023
#   AUTHOR: David W. McDonald
#
#   A class that manages a directory of files, where each file contains a list of items
#   that can be serialized as standard JSON. A __context__.json file stores the state
#   information for the set of files. Each file is conceptualized as a 'chunk' and
#   each chunk is defined to have a fixed number of items.
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
#
import sys, os, json, datetime, hashlib
#
#   Inherits from the standard object
from rebert.classes.base.Object import Object
from rebert.classes.data.JSONDFIndex import JSONDFIndex
#
#   Defaut max number of items in a given file
DF_DEFAULT_MAX_ITEMS = 5000
#
#   The name of the file that stores the context for the object
DF_CONTEXT_FILENAME = "__context__.json"
#
#   Context contains the information to create new chunks and
#   specifies how many items are to be in each chunk.
DF_CONTEXT_TEMPLATE = {
    'base_name':        "data",     #   The name of a chunk
    'extension':        ".json",    #   The chunk suffix
    'max_items':        DF_DEFAULT_MAX_ITEMS,       #   Total number of items in a chunk
    'hashseed':         "",         #   A string to use when creating object IDs
    'indexes':          None,       #   A list of the field names that have been indexed
    'chunk_count':      0,          #   The index of the last chunk, total chunks
    'locked_context':   False,      #   Do we allow changes to the context
    'locked_data':      False       #   Do we allow adding data to this dataset
}
#
#   Each chunk has just a little tracking info and a list of data 
#   This is only used for internal management of a chunk. When a chunk is
#   saved/stored it is just the list of 'data' and nothing else.
DF_CHUNK_TEMPLATE = {
    'filename':     "",     #   The filename used for this chunk
    'dirty':        True,   #   If we've added and need to save
    'data':         None    #   A list of items that can be JSON-ified
}
#
#
#
DF_CHUNK_NAME_EXCEPTIONS = ["__context", "index_"]
#
#
#####
#   
#   START class JSONDataFolder definition
#   
#####
#
#
###
#   A class/object that manages a large-ish number of JSON serializable data items
#
class JSONDataFolder(Object):    
    '''
    This class implements a list of data items that are serialized as JSON data files
    collected into one folder. The list can be arbitarily long, as the number of items
    in the list are split across as many data files as needed. Naturally, if the
    number of data items is super large, this might not be the best approach because
    an actual database might be a better way to do this.
    
    This class implements an iterator so that the iteration can be handled naturally
    through the use of a for-loop or other iteration approaches.
    
    This class implements an indexing strategy through the use of JSONDFIndex class.
    The JSONDFIndex class currently supports indexing string, numeric, and datetime
    data in a specified field.
    
    Attributes:
        self.__path_prefix__    : a directory prefix or path to this folder
        self.__folder__         : the name of the folder containing the data
        self.__context__        : a dictionary containing state metadata
        self.__chunks__         : the complete set of all data chunks
        self.__new_data__       : a list of where new data is inserted
        self.__indexes__        : a list of index objects, JSONDFIndex types
        self.__objects__        : a dictionary of items with object IDs as keys
        self.__objects_dirty__  : a flag to indicate when the object ID dict is invalid
        self.__multi_search__   : a list of intermediate results for multi field search
        
    Methods:
        append()                - add a data item to the JSON data folder
        __append__()            - a low-level insertion, marks chunk as dirty
        setFolder()             - set the name of this data folder
        setBaseName()           - set the name of each 'chunk' - defaults to 'data'
        setMaxItems()           - set the maximum number of items in each chunk
        
        createIndex()           - create an index for a given field of data
        dropIndex()             - drop a named index
        search()                - search using an index
        
        lock()                  - lock the data folder to prevent changes
        unlock()                - unlock the data folder to allow changes
        
        save()                  - save the data 
        flush()                 - force a save of everything
        load()                  - load a data folder
        
        __next_chunk_filename__()       - next file/data chunk name
        __filenames_from_folder__()     - get the names of the files/data chunks
        __new_object_id__()             - generate an ID
            
    '''
    def __init__(self, name="JSONDataFolder", *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, *args, **kwargs)
        #
        self.__path_prefix__ = None
        self.__folder__ = None
        self.__context__ = DF_CONTEXT_TEMPLATE.copy()
        self.__context__['hashseed'] = self.__new_object_id__()
        self.__chunks__ = dict()
        self.__new_data__ = None
        self.__indexes__ = dict()
        self.__objects__ = dict()
        self.__objects_dirty__ = True
        self.__multi_search__ = None    # None, when no search in progress
        return    
    
    
    def append(self, data=None):
        '''
        Add a data item.
        
        This makes sure that we have an initialized folder and adds the data item or
        a list of data items.
        
        Parameters:
        data       : JSON serializable thing, or list of things that should
                     be added to the dataset
        '''
        #   Is this dataset locked?
        if self.__context__['locked_data']: 
            raise Exception(f"{self.__folder__} is locked and should not be modified.")
        #
        self.log(f"entering", level="DEBUG")
        #
        #   Make sure we have set up the chunk where the new data will go
        if not self.__new_data__:
            self.__new_data__ = DF_CHUNK_TEMPLATE.copy()
            fname = self.__next_chunk_filename__()
            self.__new_data__['fname'] = fname
            self.__new_data__['data'] = list()
            self.__chunks__[fname] = self.__new_data__
            self.log(f"created __new_data__ chunk: '{fname}'", level="DEBUG")
        #
        #   If it is some kind of dictionary, just insert it
        if isinstance(data, dict):
            self.__append__(data)
            self.log(f"inserted one dict item", level="DEBUG")
        #
        #   If it is a list, maybe a lot of data, break it into individual
        #   items and insert those. A nested list that is inside a list will
        #   not be broken - this is not recursive
        elif isinstance(data,list):
            #   We want to make sure that we do not insert an excessive number
            #   of items, that goes beyond the chunk size
            #   Figure out how much space is remaining in this chunk
            items_allowed = self.__context__['max_items'] - len(self.__new_data__['data'])
            #   Break the dat item into two lists, one that fits and the remainder
            data_to_insert = data[:items_allowed]
            data_remaining = data[items_allowed:]
            #
            #   Insert the items that will fit
            for item in data_to_insert:
                self.__append__(item)
            self.log(f"inserted {len(data_to_insert)} items from list", level="DEBUG")
            #
            #   With the new_data chunk filled, we call this recursively to
            #   insert the remaining items
            if data_remaining:
                #   Make sure that we create a new_data chunk on recurse
                self.__new_data__ = None
                self.log(f"recursing for remaining data", level="DEBUG")
                self.append(data_remaining)
        else:
            self.__append__(data)
            self.log(f"inserted one {str(type(data))} item", level="DEBUG")

        #
        #   Once the data is added, check to see if we will need
        #   to start a new chunk on the next call
        if len(self.__new_data__['data']) >= self.__context__['max_items']:
            self.__new_data__ = None
        self.log(f"returning", level="DEBUG")
        return
    
    
    ###
    #
    #   Add a data item and mark that new_data is dirty
    def __append__(self, data=None):
        '''
        A low-level insertion
        
        A low-level insertion, that also marks the appropriate chunk as dirty. Which
        allows the save() method to just save the dirty chunks.
        
        Parameters:
        data       : JSON serializable thing that should be added to the dataset
        '''
        if self.__context__['locked_data']: 
            raise Exception(f"{self.__folder__} is locked and should not be modified.")
        oid = self.__new_object_id__()
        wrapper = dict()
        wrapper[oid] = data
        self.__new_data__['data'].append(wrapper)
        self.__new_data__['dirty'] = True
        #   add this one item to the object ID index (dictionary)
        self.__build_access_dict__(wrapper)
        return
    
    
    ###
    #
    #   Set the name (folder) for this JSONDataFolder object
    def setFolder(self, folder=None):
        '''
        Set the name of the JSONDataFolder.
        
        Allows the setting of the folder name. This should be a directory or a
        folder, not a file.
        
        Parameters:
        fname       : A string directory or folder name
        '''
        if self.__context__['locked_context']: return
        if self.__folder__:
            raise Exception(f"The data folder for this object is already set.")
        #
        #   Looks like we can set this, then create the folder path
        #   Strip off a trailing separator - to find the folder to use
        if folder.endswith(os.path.sep): folder = folder[0:-1]
        path, fname = os.path.split(folder)
        self.__folder__ = fname
        self.__path_prefix__ = path
        #   Want it to be a folder or directory - not just a path that exists
        if not os.path.isdir(folder):
            #   Create the whole path hierarchy, ending in the named folder
            os.makedirs(folder)
            self.log(f"created folder '{folder}'", level="DEBUG")

        self.log(f"set self.__path_prefix__ = {self.__path_prefix__}", level="DEBUG")
        self.log(f"set self.__folder__ = {self.__folder__}", level="DEBUG")
        return


    ###
    #
    #   Set the base name of the data files
    def setBaseName(self, fname=None):
        '''
        Change the default name of the data files.
        
        This allows the base filename to be different from the default. It does not
        change the name of existing files. It should probably be set when first
        creating the object, and not changed after that.
        
        Parameters:
        fname       : A string filename, base name, for the files that store JSON
        '''
        if self.__context__['locked_context']: return
        if fname.endswith(".json"):
            base = fname.rpartition(".")[0]
        else:
            base = fname
        self.__context__['base_name'] = base
        self.log(f"set context 'base_name' = {base}", level="DEBUG")
        return
    
    
    ###
    #
    #   Change the maximum number of items stored in each JSON data file
    def setMaxItems(self, max_items=DF_DEFAULT_MAX_ITEMS):
        '''
        Change the maximum number of items stored in each JSON data file.
        
        This sets the number of items in each chunk or JSON file. The item sizes
        can be arbitrary, so this number could be set higher if the items are small
        and might need to be set lower if each item was large.
        
        This will default to the DF_DEFAULT_MAX_ITEMS if the value is negative.
        
        Parameters:
        max_items       : An integer number of items
        '''
        if self.__context__['locked_context']: return
        if max_items <= 0:
            self.__context__['max_items'] = DF_DEFAULT_MAX_ITEMS
        else:
            self.__context__['max_items'] = max_items
        self.log(f"set context 'max_items' = {self.__context__['max_items']}", level="DEBUG")
        return
    
    
    ###
    #
    #   Create a new index for this JSONDataFolder
    def createIndex(self, field="", index_type=None, func=None, function_name="", stops=None):
        '''
        Creates and installs a new index of the field and type specified
        
        Parameters
        field               - The name of the field in a dict to index
        index_type          - A string, type of the index to create
        func                - The function to use for computed indexes
        function_name       - A string name describing the function
        stops               - A StopWords object to use if stops are to be removed
        '''
        self.log(f"entering", level="DEBUG")
        if field in self.__indexes__:
            raise Exception(f"The field '{field}' has an existing index.")
        if not self.__context__['indexes']:
            self.__context__['indexes'] = list()
        if field in self.__context__['indexes']:
            raise Exception(f"The field '{field}' has an existing index.")
        #
        #   Create the index object and index the field
        #index = JSONDFIndex(jdf=self, logger=self.getLogger())
        index = JSONDFIndex(jdf=self, objects=self.__objects__, logger=self.getLogger())
        index.createIndex(field=field, index_type=index_type, 
                          func=func, function_name=function_name, stops=stops)
        index.save()        
        self.log(f"created and saved index on '{field}'", level="DEBUG")        

        #
        #   Now, need to use the computed index name
        self.__context__['indexes'].append(index.__context__['field'])
        self.__indexes__[index.__context__['field']] = index
        #
        #   Save this updated context information
        self.log(f"saving updated context information", level="DEBUG")
        self.save()
        #
        self.log(f"returning", level="DEBUG")
        return
    
    
    ###
    #
    #   Drop the named index from the JSONDataFolder
    def dropIndex(self, field="", function_name=""):
        '''
        Drops or deletes the index on the indicated field.
        
        Parameters
        field               - The field/index name to be dropped
        function_name       - An optional function name applied to the field
        '''
        self.log(f"entering", level="DEBUG")
        #
        #   Add the function name to the field
        if function_name:
            function_name = function_name.replace('(','').replace(')','')
            #   This mirrors functional application to a field - as field name
            function_name = function_name+"("
            field = function_name+field+")"
            self.log(f"Attempting to drop field with function: '{field}'.", level="WARN")
        #
        #   If the index does not exist, then there is nothing to do
        if (not self.__context__['indexes']) or (field not in self.__context__['indexes']):
            self.log(f"The field '{field}' is not indexed.", level="WARN")
            self.log(f"returning", level="DEBUG")
            return
        #
        #   Save the index - will use it later
        index = self.__indexes__[field]
        #   Delete the index from the active set of indexes
        del self.__indexes__[field]
        #
        if not self.__context__['indexes']:
            self.__context__['indexes'] = list()
        #
        #   Update the set of indexes
        indexes = list()
        for item in self.__context__['indexes']:
            if item == field: continue
            indexes.append(item)
        self.__context__['indexes'] = indexes
        #
        #   Save this updated context information
        self.log(f"saving updated context information", level="DEBUG")
        self.save()
        #
        #   Now, drop and remove the actual index file
        index.dropIndex()
        #
        self.log(f"returning", level="DEBUG")
        return
    
    
    ###
    #
    #   Search for this token or string, using the specified field/index
    def search(self, field="", *args, **kwargs):
        '''
        This searches the index for the search string, tokenized. This does an 'and' search
        by default, but can do a disjunctive, 'or' search.
        
        Parameters
        field               - The name of the index/field being searched
        function_name       - A string descriptor of a computed field
        
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
        
        Returns
        a list of data items from the data folder that match the search
        '''
        self.log(f"entering", level="DEBUG")
        results = list()
        #
        #   Add the function name to the field
        if 'function_name' in kwargs:
            function_name = kwargs['function_name'].replace('(','').replace(')','')
            #   This mirrors functional application to a field - as field name
            function_name = function_name+"("
            field = function_name+field+")"

        if not field:
            self.log(f"Must supply a field/index name to be searched.", level="CRITICAL")
            raise Exception(f"Must supply a field/index name to be searched.")
        
        if not field in self.__indexes__:
            self.log(f"The field '{field}' does not have an index.", level="CRITICAL")
            raise Exception(f"The field '{field}' does not have an index.")
        #
        #   Extract the specified index and conduct the search on that index
        index = self.__indexes__[field]
        self.log(f"searching index '{field}'", level="DEBUG")
        results = index.search(*args,**kwargs)
        self.log(f"returning, found {len(results)} items", level="DEBUG")
        return results
    
    
    ###
    #
    #   This allows a search across several different fields, by searching one field at a
    #   time.
    def multiFieldSearch(self, field="", *args, **kwargs):
        '''
        This makes a search of the given field and merges the results with the existing
        set of search results. That is, this assumes an "AND" boolean operation across the
        successive fields.
        
        Parameters
        field               - The name of the index/field being searched
        function_name       - A string descriptor of a computed field
        
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
        
        Returns
        a list of data items from the data folder that match the search
        '''
        self.log(f"entering", level="DEBUG")
        #
        #   Add the function name to the field
        if 'function_name' in kwargs:
            function_name = kwargs['function_name'].replace('(','').replace(')','')
            #   This mirrors functional application to a field - as field name
            function_name = function_name+"("
            field = function_name+field+")"
        #
        #   When no field name is supplied then the multi field search results
        #   are returned
        if not field:
            results = list()
            if self.__objects__:
                #
                #   Run through the list of object IDs and get their data items
                for c in self.__multi_search__:
                    try:
                        results.append(self.__objects__[c])
                    except Exception as ex:
                        self.log(f"exception when accessing object ID '{c}'", level="WARN")
                        self.log(f"the item associated with '{c}' appears to be missing", level="WARN")
                        self.log(f"{ex}", level="WARN")
                self.__multi_search__ = None
            else:
                self.log(f"the master object index, self.__objects__, is empty", level="DEBUG")
            self.log(f"returning, found {len(results)} items", level="DEBUG")
            return results
        #
        #
        #
        if not field in self.__indexes__:
            self.log(f"The field '{field}' does not have an index.", level="CRITICAL")
            raise Exception(f"The field '{field}' does not have an index.")
        #
        #   Extract the specified index and conduct the search on that index
        #   Make sure we are collecting raw object IDs
        index = self.__indexes__[field]
        self.log(f"searching index '{field}'", level="DEBUG")
        kwargs['raw'] = True
        results = index.search(*args,**kwargs)
        #
        #   Merge these results with existing results, if it is already in the
        #   existing results. This is an 'AND' across the several searches
        #
        #   First, if not a list then start with the first results
        if not isinstance(self.__multi_search__,list):
            self.__multi_search__ = results
        else:
            merged = list()
            for item in results:
                if item in self.__multi_search__:
                    merged.append(item)
            self.__multi_search__ = merged
        #
        #
        self.log(f"returning, merged, {len(self.__multi_search__)} items remaining", level="DEBUG")
        return []
    
    
    ###
    #
    #   Lock or unlock the addition of new data
    def lock(self):
        '''
        Lock the data folder, prevent additions to the dataset.
        '''
        self.__context__['locked_data'] = True
        self.log(f"JSON data folder has been LOCKED", level="DEBUG")
        return
    
    def unlock(self):
        '''
        Unlock the data folder, allow new aditions to the dataset.
        '''
        self.__context__['locked_data'] = False
        self.log(f"JSON data folder has been UNLOCKED", level="DEBUG")
        return
    
    
    ###
    #
    #   Save this object into the folder of data. If this is a new folder then
    #   the folder name needs to be specified. If this is an existing folder then
    #   the class should save the data into that existing data folder.
    def save(self, folder=None, compact=True, with_lock=False, force_save=False):
        '''
        Save a folder of data.
        
        The folder parameter is the folder where all of the JSON data files 
        should be saved. 
        
        Parameters:
        folder          : a directory or path that ends in a directory
        compact         : when writing JSON remove all whitespace, compact
        with_lock       : if the folder is locked, indicate that you have that lock
        force_save      : save everything, in case there were data updates
        
        '''
        self.log(f"entering", level="DEBUG")
        new_folder = False
        #   If we used the load() method then self.__folder__ has been set, otherwise
        if not self.__folder__:
            #   Otherwise, we would need to know where to save - we need a folder
            if not folder:
                raise Exception("A folder name is required to save the data.")
            new_folder = True
            #            
            #   Strip off a trailing separator - to find the folder to use
            if folder.endswith(os.path.sep): folder = folder[0:-1]
            path, fname = os.path.split(folder)
            self.__folder__ = fname
            self.__path_prefix__ = path
        
        #   Is this dataset locked?
        if self.__context__['locked_data'] and not with_lock: 
            raise Exception(f"{self.__folder__} is locked and should not be modified.")

        #
        #   This is the root of the data folder
        folder_path = os.path.join(self.__path_prefix__, self.__folder__)

        #
        #   If it is a new folder, we should make sure that it exists or things
        #   might go wrong
        if new_folder:
            #   Want it to be a folder or directory - not just a path that exists
            if not os.path.isdir(folder):
                #   Create the whole path hierarchy, ending in the named folder
                os.makedirs(folder)
                self.log(f"created folder '{folder}'", level="DEBUG")
#            #
#            #   Since this is a 'new' data set, new data folder, we need to rename 
#            #   all of the chunks that were created prior to this save happening.
#            new_chunks = dict()
#            file_list = list(self.__chunks__.keys())
#            for fname in file_list:
#                fullname = os.path.join(folder_path, fname)
#                new_chunks[fullname] = self.__chunks__[fname]
#                self.__chunks__[fname]['filename'] = fullname
#            #   The reset the chunks to reflect the new names
#            self.__chunks__ = new_chunks 
        
        #   Create the context filename
        context_fname = os.path.join(folder_path,DF_CONTEXT_FILENAME)
        #
        #   On the first save, we lock the context so that it won't change again
        #   over the lifetime of the data. We want to keep the context stable as
        #   we work with the data.
        self.__context__['locked_context'] = True
        cf = open(context_fname,"w")
        json.dump(self.__context__,cf,indent=4)
        cf.close()
        self.log(f"saving '{context_fname}'", level="DEBUG")
        
        file_list = list(self.__chunks__.keys())
        for fname in file_list:
            #   Run through all of the chunks, looking for any 'dirty' chunks
            #   Skip past chunks that are not dirty
            if not force_save and not self.__chunks__[fname]['dirty']: 
                continue
            #   Open the file
            fullname = os.path.join(folder_path, fname)
            f = open(fullname,"w")
            mesg = f"save chunk: '{fname}'"
            #
            #   This option makes the resulting JSON text files 
            #   harder/easier to read, compact has no spaces
            if compact:
                json.dump(self.__chunks__[fname]['data'],f)
                self.log(f"{mesg} compact: True", level="DEBUG")
            else:
                json.dump(self.__chunks__[fname]['data'],f, indent=4)
                self.log(f"{mesg} compact: False", level="DEBUG")
            f.close()
            #   Mark this chunk as clean
            self.__chunks__[fname]['dirty'] = False
        
        self.log(f"returning", level="DEBUG")
        return
    
    
    ###
    #
    #   Save this object into the folder of data
    def flush(self, compact=True, with_lock=False):
        '''
        Flush the data folder. Save the whole thing to make sure any updates are
        recorded to disk. This relies on a save() using the force_save=True to
        make sure that the whole thing is written.
        
        '''
        self.log(f"entering", level="DEBUG")
        self.save(compact=compact, with_lock=with_lock, force_save=True)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ###
    #
    #   Load a folder of data. This will load all of the data.
    def load(self, folder=None):
        '''
        Load a folder of data.
        
        The folder parameter is the folder containing the JSON data folder with a
        __context__.json file and a bunch of *.json data files
        
        Parameters:
        folder      : a directory or path that ends in a directory
        '''
        #   If self.__folder__ is set, then this is 'open' and managing a set of chunks
        if self.__folder__:
            raise Exception("Already managing a data folder.")
        #   If we got here and we didn't get a folder name, then this object would
        #   not know what to work with - need a folder name
        if not folder:
            raise Exception("Missing data folder name.")
        #
        self.log(f"entering", level="DEBUG")
        #   Strip off a trailing separator - to find the folder to use
        if folder.endswith(os.path.sep): folder = folder[0:-1]
        path, fname = os.path.split(folder)
        self.__folder__ = fname
        self.__path_prefix__ = path
        #
        #   This is the root of the data folder
        folder_path = os.path.join(self.__path_prefix__, self.__folder__)
        #
        #   Validate that the folder exists before trying load
        if not os.path.exists(folder_path):
            #   If the folder check fails then this isn't an existing data folder
            #   invalidate the folder and path prefix to make it look like this
            #   isn't an actual data folder
            self.__folder__ = ""
            self.__path_prefix__ = ""
            raise Exception(f"The data folder '{folder_path}' does not exist.")
        #
        #   Looks like we can see the folder, now try to load the context file
        context_fname = os.path.join(folder_path,DF_CONTEXT_FILENAME)
        try:
            cf = open(context_fname,"r")
            self.__context__ = json.load(cf)
            self.log(f"loaded context file", level="DEBUG")
            cf.close()
        except:
            #   If the load fails then we will invalidate the folder and path prefix
            #   to make it still look like there isn't a data folder
            self.__folder__ = ""
            self.__path_prefix__ = ""
            raise Exception(f"Could not load the context file '{context_fname}'.")
        #
        #   Start the load of the actual data - the data needs to be loaded before any
        #   indexes are loaded and initialized
        file_list = self.__filenames_from_folder__(folder_path)
        #file_list.sort()
        #
        #   Now we try and load all of the chunks        
        for fname in file_list:
            #   Skip trying to load the context file as data
            if fname.endswith(DF_CONTEXT_FILENAME): continue
            f = open(fname,"r")
            data = json.load(f)
            f.close()
            #
            chunk = DF_CHUNK_TEMPLATE.copy()
            path, fname = os.path.split(fname)
            chunk['filename'] = fname
            chunk['data'] = data
            chunk['dirty'] = False
            self.__chunks__[fname] = chunk
            self.__new_data__ = chunk
            self.log(f"loaded chunk '{fname}' with {len(data)} records", level="DEBUG")
        #
        #   Once the data is loaded, check to see if we need to start a new chunk
        if self.__new_data__ and (len(self.__new_data__['data']) >= self.__context__['max_items']):
            self.__new_data__ = None
        
        #
        #   With the data loaded we can create the access dictionary. This
        #   is used by the indexes that we might have
        self.__build_access_dict__()
        self.__objects_dirty__ = False
        
        #
        #   Now, load any indexes indexes
        if self.__context__['indexes']:
            for field in self.__context__['indexes']:
                self.log(f"attempting to load index: '{field}'", level="DEBUG")
                index = JSONDFIndex(jdf=self, objects=self.__objects__, field=field, logger=self.getLogger())
                self.__indexes__[field] = index
        else:
            #   Simplifies the 'dropIndex' when there are no indexes
            self.__context__['indexes'] = list()
        
        self.log(f"returning", level="DEBUG")
        return    
    
    
    ###
    #
    #   Using the context, get the next filename
    def __next_chunk_filename__(self):
        '''
        Using the information from the context, return the next 'chunk' filename.
        
        Returns:
        filename, string of the filename or path
        '''
        self.__context__['chunk_count'] = self.__context__['chunk_count'] + 1
        fname = self.__context__['base_name']+f"_{self.__context__['chunk_count']:03}"+self.__context__['extension']
        #if self.__folder__:
        #    path = os.path.join(self.__folder__,fname)
        #else:
        #    path = fname
        #self.log(f"next chunk filename: '{path}'", level="DEBUG")
        #return path
        self.log(f"next chunk filename: '{fname}'", level="DEBUG")
        return fname
    
    
    
    ###
    #
    #   Get a sorted list of file names - inside a folder - with .json extension
    def __filenames_from_folder__(self, folder=None, ext=".json"):
        '''
        Scan a folder to collect all of the files that have the given extension.
        
        Parameters:
        folder      : a directory or path that ends in a directory
        ext         : a file extension, or suffix 
        '''
        self.log(f"entering", level="DEBUG")
        file_list = list()
        candidates = list()
        skipped = list()
        skip = False
        flist = os.listdir(folder)
        #
        #   Figure out if any of the filenames have a prefix that we skip
        for f in flist:
            skip = False
            for prefix in DF_CHUNK_NAME_EXCEPTIONS:
                if str(f).startswith(prefix): skip = True
            if skip:
                skipped.append(f)
            else:
                candidates.append(f)
        self.log(f"skipped {len(skipped)} files with suppressed prefixes", level="DEBUG")
        #
        #   Candidates are all of the non-skipped prefixes
        for f in candidates:
            fname = os.path.join(folder,f)
            if os.path.isfile(fname):
                if ext:
                    if str(fname).endswith(ext):
                        file_list.append(str(fname))
                else:
                    file_list.append(str(fname))
        self.log(f"folder contains {len(file_list)} files", level="DEBUG")
        if file_list:
            file_list.sort()
        self.log(f"returning", level="DEBUG")
        return file_list
    
    
    ###
    #
    #   Every item in the data set gets a hashed object ID - this is useful for
    #   creating indexes and sorting. This generates a new object ID
    def __new_object_id__(self):
        '''
        Create a new object ID.
        
        Returns 
        a string, object ID
        '''
        #   An object id is a function of the data folder name and the current timestamp
        #   Using time as a unique string to be hashed
        current_time = str(datetime.datetime.now())
        #   Now add the folder name
        if self.__context__['hashseed']:
            id_bytes = bytes(self.__context__['hashseed']+"/"+current_time,'utf-8')
        else:
            id_bytes = bytes(current_time,'utf-8')
        #   Hash the id_bytes
        #   This defaults to 32 characters
        h = hashlib.blake2s(digest_size=16)
        h.update(id_bytes)
        oid = h.hexdigest()
        return str(oid)




    ###
    #
    #   This builds an access dictionary based on the object IDs. This is really
    #   useful for any indexes that are created by this. If this is not present
    #   then each index has to build its own. If this is created by the JSONDataFolder
    #   then it can be shared by all of the indexes.
    def __build_access_dict__(self, new_item=None):
        '''
        Build the underlying dictionary object that stores data with the object IDs. This
        structure is used to return the items that are found during a search with an index.
        
        Optional Parameter:
        new_item                : An new item to be added to the __objects__ dictionary
        '''
        self.log(f"entering", level="DEBUG")
        if not self.__chunks__:
            raise Exception(f"This JSONDataFolder appears to be empty.")
        
        if not new_item and not self.__objects__:
            self.log(f"initializing __objects__ dictionary", level="DEBUG")
            # if self.__objects__ does not exist then we build that firste
            chunk_names = list(self.__chunks__.keys())
            for cname in chunk_names:
                chunk = self.__chunks__[cname]
                for wrappered in chunk['data']:
                    oid_key = list(wrappered.keys())[0]
                    data = list(wrappered.values())[0]
                    self.__objects__[oid_key] = data
            self.__objects_dirty__ = False
            self.log(f"created __objects__ dictionary with {len(self.__objects__)} items", level="DEBUG")
        elif new_item:
            #   This just adds one new item - like during an append operation
            #   This new_item should be a wrappered item with it's object ID
            oid_key = list(new_item.keys())[0]
            data = list(new_item.values())[0]
            self.__objects__[oid_key] = data
            self.__objects_dirty__ = False
            self.log(f"added item to __objects__ dictionary now has {len(self.__objects__)} items", level="DEBUG")
        else:
            #   Nothing to do in this case
            pass

        self.log(f"returning", level="DEBUG")
        return

    ###
    #
    #   This will get an item by using the object ID (oid). This can be used after
    #   the __build_access_dict__() method has been called. Before that, it will
    #   cause an exception.
    def __get_oid__(self, oid=""):
        '''
        Build the underlying dictionary object that stores data with the object IDs. This
        structure is used to return the items that are found during a search with an index.
        
        Optional Parameter:
        oid                 : an object ID for an item to fetch
        '''
        self.log(f"entering", level="DEBUG")
        if not self.__objects__:
            raise Exception(f"This JSONDataFolder needs to __build_access_dict__() before accessing objects.")
        
        try:
            data = self.__objects__[oid]
        except Exception as ex:
            self.log(f"exception when accessing object ID '{oid}'", level="DEBUG")
            self.log(f"{ex}", level="DEBUG")

        self.log(f"returning", level="DEBUG")
        return




    ###
    #
    #   Making an iterator work correctly, we need a special nested class that can
    #   manage the state of the iterator. The class must implement the __next__()
    #   method to be compliant as an iterator.
    class JSONDataFolderIterator(Object):
        def __init__(self, name="JSONDataFolderIterator", logger=None, *args, **kwargs):
            super().__init__(name=name, logger=logger, *args, **kwargs)
            #
            self.chunks_ref = None      #   A referece to all the chunks
            self.chunks_keys = None     #   The list keys (chunk keys) when created
            self.chunk = None           #   The current chunk, just the 'data' field
            self.index = -1             #   Position in the current chunk
            return
        
        def __next__(self):
            '''
            Get the next item when iterating
            
            All iterators must implement the __next__() method. This manages moving
            through each of the data items in a given chunk, and moving through
            all of the chunks of a JSONDataFolder.
            
            Returns:
            A data item, the next item from a JSONDataFolder
            '''
            self.index += 1
            #   After the increment, are we past the last item
            if self.index >= len(self.chunk):
                #   Set to index the first item
                self.index = 0
                #   If we have some chunks left (still have keys)
                if self.chunks_keys:
                    #   Get the first key
                    key = self.chunks_keys[0]
                    #   Remove that key from the list of keys
                    self.chunks_keys = self.chunks_keys[1:]
                    #   Use that key to set chunk to the data
                    self.chunk = self.chunks_ref[key]['data']
                else:
                    #   This is an attempt to remove all references to the
                    #   original object - to facilitate clean up once the
                    #   iteration has come to an end
                    #
                    #   No more items, set the chunk to an empty list
                    self.chunk = list()
                    #   Well, the list of keys should already be empty
                    self.chunks_keys = list()
                    #   Remove the referece to the JSONDataFolder chunks
                    self.chunks_ref = None
                    #   Raise the StopIteration exception
                    raise StopIteration
            #   Get the wrappered data item at the current index
            wrappered = self.chunk[self.index]
            #   Remove the object ID wrapper
            item = list(wrappered.values())[0]
            #   Return the data item
            return item
        
    ###
    #
    #   Return an iterator that works with the JSONDataFolder
    def __iter__(self):
        '''
        Creates and returns an iterator object for use with a JSONDataFolder.
        
        Returns:
        A JSONDataFolderIterator object that iterates through the data in a
        JSONDataFolder object.
        '''
        #   Create an iterator object
        it = self.JSONDataFolderIterator()
        #   Initialize it's reference to the current set of chunks
        it.chunks_ref = self.__chunks__
        keys = list(self.__chunks__.keys())
        if keys:
            keys.sort()
            #   Set the reference to the first chunk based on the ordered keys
            it.chunk = self.__chunks__[keys[0]]['data']
            #   Set the remaining keys
            it.chunks_keys = keys[1:]
        else:
            it.chunk = list()
            it.chunks_keys = list()
        return it


    ###
    #
    #   Return the length len() - this is the number of data items
    def __len__(self):
        count = 0
        chunks_names = list(self.__chunks__.keys())
        for name in chunks_names:
            c = self.__chunks__[name]
            count = count+len(c['data'])
        return count

    ###
    #
    #   Two methods that make this object behave a bit like a list or array
    #   This is not really random access - it still has to compute where in
    #   the object the thing sits - and an assignment might not work the way
    #   you expect.
    #
    
    ###
    #
    #   Get the value at a given position - reports out of bounds conditions
    def __getitem__(self, i):
        item = None
        #   Check index value is integer
        if not isinstance(i,int):
            raise Exception(f"Access with integer indexes. Got: '{i}' {str(type(i))}")
        last = len(self)-1
        #   Check out of bounds range
        if (i < -2) or (i > last):      
            raise Exception(f"Index out of bounds. Position {i} is not in range [0..{last}]")
        #   Special case access the last item
        if (i==-1) or (i==last):
            wrappered = self.__new_data__['data'][-1]
            #   Remove the object ID wrapper
            item = list(wrappered.values())[0]
            #   Return the data item
            return item
        #
        #   Access any general item
        chunk_index = i // self.__context__['max_items']       # which chunk
        offset = i-(chunk_index*self.__context__['max_items']) # where in that chunk
        #   Need to get the right chunk
        chunk_keys = list(self.__chunks__.keys())
        chunk_keys.sort()
        key = chunk_keys[chunk_index]
        chunk = self.__chunks__[key]
        wrappered = chunk['data'][offset]
        item = list(wrappered.values())[0]
        return item
    ###
    #
    #   Set a value associated with an index position
    def __setitem__(self, i, v):
        #   Is this dataset locked?
        if self.__context__['locked_data']: 
            raise Exception(f"{self.__folder__} is locked and should not be modified.")
        #   Check index value is integer
        if not isinstance(i,int):
            raise Exception(f"Access with integer indexes. Got: '{i}' {str(type(i))}")
        last = len(self)-1
        #   Check out of bounds range
        if (i < -2) or (i > last):      
            raise Exception(f"Index out of bounds. Got: '{i}', range is [0..{last}]")
        #   Special case set value of the last item
        if (i==-1) or (i==last):
            oid = self.__new_object_id__()
            wrapper = dict()
            wrapper[oid] = v
            self.__new_data__['data'][-1] = wrapper
            self.__new_data__['dirty'] = True
            return
        #   Set value for a general item
        chunk_index = i // self.__context__['max_items']       # which chunk
        offset = i-(chunk_index*self.__context__['max_items']) # where in that chunk
        #   Need to get the right chunk
        chunk_keys = list(self.__chunks__.keys())
        chunk_keys.sort()
        key = chunk_keys[chunk_index]
        chunk = self.__chunks__[key]
        oid = self.__new_object_id__()
        wrapper = dict()
        wrapper[oid] = v
        chunk['data'][offset] = wrapper
        chunk['dirty'] = True
        return

#####
#   
#   END class JSONDataFolder definition
#   
#####

if __name__ == '__main__':
    print("JSONDataFolder.py is a class with no main()")
