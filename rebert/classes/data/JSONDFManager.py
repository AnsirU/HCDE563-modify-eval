#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: JSONDFManager.py
#   REVISION: December, 2024
#   CREATION DATE: December, 2024
#   AUTHOR: David W. McDonald
#
#   A class that manages a set of JSONDataFolders
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
#
import sys, os, json, datetime, hashlib
#
#   Inherits from the standard object
from rebert.classes.base.Object import Object
from rebert.classes.data.JSONDataFolder import JSONDataFolder
from rebert.classes.data.JSONDFIndex import JSONDFIndex
#
#

DATA_FOLDER_MANAGER_TEMPLATE = {
    'folder'        :   "",
    'short_name'    :   "",
    'data'          : None
}

#####
#   
#   START class JSONDFManager definition
#   
#####
#
#
###
#   A class/object that manages a JSONDataFolder collection
#
class JSONDFManager(Object):    
    '''
    This class is a manager of a JSONDataFolder. Most of the work is performed by 
    JSONDataFolder and JSONDFIndex classes/objects that the manager instantiates.
    
    Attributes:
        self.__by_folder__      : the set of JSONDataFolders organized by folder
        self.__by_name__        : the set of JSONDataFolders organized by short name
        
    Methods:
        load()                  - load a named JSON data folder
        search()                - perform a search based on one index/field
        multiFieldSearch()      - perform a search across multiple indexes/fields
        
        
    '''
    def __init__(self, name="JSONDFManager", *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name            : An optional description or name for the object
        logger          : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, *args, **kwargs)
        #
        self.__by_folder__ = dict()
        self.__by_name__ = dict()
        return    
    
    
    
    def load(self, folder="", short_name=""):
        '''
        Loads a JSONDataFolder and starts managing it.
        
        Parameters:
        folder          : The folder name for the data
        short_name      : The short name for this data
        '''
        #
        if not folder:
            raise Exception(f"Need to supply a data folder to be loaded.")
        if not short_name:
            raise Exception(f"Need to supply a short_name to describe the data.")
        self.log(f"entering", level="DEBUG")

        item = DATA_FOLDER_MANAGER_TEMPLATE.copy()
        item['folder'] = folder
        item['short_name'] = short_name
        self.log(f"Loading '{item['short_name']}' from '{item['folder']}'", level="DEBUG")
        item['data'] = JSONDataFolder(name=item['short_name'],logger=self.getLogger())
        item['data'].load(item['folder'])
        
        self.__by_folder__[item['folder']] = item
        self.__by_name__[item['short_name']] = item
        self.log(f"returning", level="DEBUG")
        return    
    
    

    def search(self, field="", *args, **kwargs):
        '''
        This searches the index for the search string, tokenized. This does an 'and' search
        by default, but can do a disjunctive, 'or' search.
        
        Parameters
        field               - The name of the index/field being searched
        function_name       - A string descriptor of a computed field
        short_name          - The name/short_name of the folder, to search just one
        
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
        #
        self.log(f"entering", level="DEBUG")
        results = list()
        flist = list()
        #   
        #   Set up the list of JSONDataFolders we are gonna search
        if 'short_name' in kwargs:
            short = kwargs['short_name']
            if short in self.__by_name__:
                flist.append(short)
            else:
                self.log(f"The short_name '{short}' is not one of the JSONDataFolders", level="DEBUG")
        else:
            flist = list(self.__by_name__.keys())

        results = list()
        for name in flist:
            self.log(f"Starting search of dataset '{name}'", level="DEBUG")
            items = self.__by_name__[name]['data'].search(field,*args,**kwargs)
            self.log(f"Found {len(items)} additional items.", level="DEBUG")
            results.extend(items)
            
        self.log(f"returning", level="DEBUG")
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
        results = list()
        flist = list()
        #   
        #   Set up the list of JSONDataFolders we are gonna search
        if 'short_name' in kwargs:
            short = kwargs['short_name']
            if short in self.__by_name__:
                flist.append(short)
            else:
                self.log(f"The short_name '{short}' is not one of the JSONDataFolders", level="DEBUG")
        else:
            flist = list(self.__by_name__.keys())

        results = list()
        for name in flist:
            self.log(f"Starting search of dataset '{name}'", level="DEBUG")
            items = self.__by_name__[name]['data'].multiFieldSearch(field,*args,**kwargs)
            self.log(f"Found {len(items)} additional items.", level="DEBUG")
            results.extend(items)
            
        self.log(f"returning", level="DEBUG")
        return results

#####
#   
#   END class JSONDFManager definition
#   
#####

if __name__ == '__main__':
    print("JSONDFManager.py is a class with no main()")
