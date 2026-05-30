#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: DictionaryValidatorFromTemplate.py
#   REVISION: June, 2024
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   This is a data structure that allows the specification of a dictionary by providing
#   a template dictionary. The structure attempts to maintain some data consistency by
#   validating the use of fields according to the specifications in the template.
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#

import sys, copy, collections, json
#
#   
from rebert.classes.base.Object import Object
#
#
#####
#
#   DICTIONARY VALIDATION TEMPLATES EXPLAINED
#
#   A supplied template is a dictionary where the structure of the dictionary and any
#   sub dictionaries will specify how the data will be validated
#
#   First, providing an empty template will allow any/all fields to be set or retrieved
#   and should behave much like a basic dictionary, no validation, create any keys,
#   insert any values
#
#   The simplest dictionary can just provide a key and either a boolean, True, False
#   or None values. All of the keys are then acceptable keys. Keys that are not in
#   the template will not be allowed to be set. A True value specifies that the given
#   key is a required key. The values of None or False for a key mean that the key
#   is optional.
#
#   A more complex specification requires a sub-dictionary. That is, in the template
#   a key is associated with a dictionary where that dictionary specifies aspects of 
#   the key and the values that can be associated with that key.
#
#   Below is a small example that shows an example template:
#
#        DATA_TEMPLATE = {
#            'this'     : None,
#            'that'     : True,
#            'thus'     : { 'required'  : True },
#            'the'      : { 'required'  : True,
#                           'type'      : int },
#            'there'    : { 'required'  : False,
#                           'type'      : str,
#                           'options'   : ['one', 'two', 'three'] },
#            'thunk'    : { 'required'  : True,
#                           'type'      : float,
#                           'range'     : [-1.0, 1.0],
#                           'default'   : 0.5 },
#            'think'    : None    
#        }
#
#
#   In the example above, all of the keys, 'this', 'that', 'thus', 'the', 'there', 'thunk',
#   and 'think' should be considered acceptable keys for use in the resulting dictionary.
#   The key 'this' has the value None, meaning it would be an optional field. The key
#   'that' is associated with the value True, meaning it is a required field. Required
#   means it should have a value of some kind that is not None. A boolean value of False
#   should still count as a value. The key 'thus' is associated with a sub-dictionary, 
#   but the behavior of 'thus' should be the same as 'that' - required with some 
#   value other than None.
#
#   The keys 'the', 'there' and 'thunk' are a bit more complex and show a number of the
#   value specifications. The key 'the' is required and must be an int type. Pretty much
#   any python type should work; bool, int, float, str, list, dict, ... etc. The key
#   'there' is not required, but if it is present it should be a str and further should
#   be one of the specified 'options'. The options is to be a list of acceptable values
#   of the specified 'type'. The key 'thunk' is required, should be a float, with a
#   value in the specified 'range', inclusive of the values. Further, when a new
#   dictionary is created, the value for 'thunk' should be the 'default' value.
#
#


#####
#   
#   START class DictionaryValidatorFromTemplate definition
#   
#####
#
#
class DictionaryValidatorFromTemplate(Object):
    '''
    This class implements an object that behaves much like a basic dictionary, but with
    the ability to specify fields (keys) that are required, and to specify type data for
    the values associated with the various keys
    
    Attributes:
        None of the object attributes should be accessed directly
    
    Methods:
        validate()          - a 'user' check of the data structure
        json()              - return this dictionary as a JSON string

        __validate__()      - a validator method - will throw exceptions 
        __new_dict__()      - returns a new dictionary with all fields 
        __clean_dict__()    - returns a validated and cleaned copy of the dictionary
        __getitem__()       - dictionary accessor
        __setitem__()       - dictionary settor
        __delitem__()       - dictionary delete item
        __iter__()          - returns dictionary iterator
        __len__()           - returns dictionary length
        __repr__()          - returns a compact string representation
        
    '''
    def __init__(self, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        template    : A template dictionary for the data structure
        '''
        super().__init__(*args, **kwargs)
       
        self.__template__ = None
        if "template" in kwargs:
            self.__template__ = kwargs["template"].copy()
        else:
            self.__template__ = dict()
        
        self.__acceptable_keys__ = list()
        self.__required_keys__ = list()
        
        #   Any/all keys in the template are acceptable
        template_keys = list(self.__template__.keys())
        if template_keys:
            self.__acceptable_keys__ = template_keys
        
        #   Now, which keys are required
        for k in template_keys:
            info = self.__template__[k]
            if not info: continue
            #   It's just a key and True (bool) - it's required
            if isinstance(info,bool) and info:
                self.__required_keys__.append(k)
                continue
            #   If it's a dictionary - it might be more complex
            if isinstance(info,dict):
                #   Check whether it's required or not
                if ('required' in info) and info['required']:
                    self.__required_keys__.append(k)
        #
        self.__data__ = self.__new_dict__()
        return
    
    
    #
    #   A method that relies on the hidden validation method to perform a basic 
    #   validity check. A response of empty string or None indicates that the 
    #   validity check was successful.
    #   
    def validate(self):
        '''
        Perform a validation of this object and return the first error that is found.
        
        Returns:
        A string of the first error condition found for the data
        '''
        self.log(f"entering", level="DEBUG")
        response = None
        try:
            self.__validate__()
        except Exception as e:
            response = str(e)
        self.log(f"returning", level="DEBUG")
        return response
    
    
    #
    #   Making JSON work with an object like this requires specifying how to
    #   encode the object as JSON. In this case, we just need to return the
    #   data member - it's just a regular dictionary. This nested encoder should
    #   be able to handle all of the subclasses of this type
    class DVFTJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj,DictionaryValidatorFromTemplate):
                return obj.__data__ 
            return obj
    
    #
    # A method to return a string JSON representation of the object
    #
    def json(self, r=None, clean=False, indent=0, sort_keys=False):
        '''
        Produce a JSON version of the underlying dictionary.
        
        The method provides a number of options to produce JSON. It relies on the use of a
        simple helper function so that nested DictionaryValidatorFromTemplate derivatives 
        would be appropriately serialized as JSON.
        
        Optional Parameters:
        r           : A dictionary to work with
        clean       : Perform a cleaning, to remove unused fields
        indent      : Create a formatted version of the JSON output
        sort_keys   : Sort the keys when producing the JSON
        
        Returns:
        A string of the dictionary in JSON format
        '''
        self.log(f"entering", level="DEBUG")
        if not r:
            if clean:
                try:
                    r = self.__clean_dict__()
                except Exception as e:
                    m = f'while cleaning JSON caught "{str(e)}"'
                    raise Exception(m) 
            else:
                r = self.__data__
        self.log(f"returning", level="DEBUG")
        return json.dumps(r, cls=self.DVFTJSONEncoder, indent=indent, sort_keys=sort_keys)
    
    
    #
    # A method that performs a very trivial validation of the fields in the request
    #
    def __validate__(self):
        '''
        Perform a validation of this object and throw an exception when a validation
        error is found.
        
        This low-level method is called by other methods in the class. If you want to
        check, or validate, the data structure prior to other operations on it, then
        you should use the validate() method instead and do something when an error
        string is returned.
        '''
        self.log(f"entering", level="DEBUG")
        #
        #   First make certain we have the required keys
        if self.__required_keys__:
            self.log(f"validating required fields", level="DEBUG")
            for k in self.__required_keys__:
                if k not in self.__data__ :
                    self.log(f"required field '{str(k)}' is missing", level="CRITICAL")
                    raise Exception(f"Invalid structure: required field '{str(k)}' is missing.")
                elif self.__data__[k] is None:
                    self.log(f"required field '{str(k)}' is empty, missing a value", level="CRITICAL")
                    raise Exception(f"Invalid structure: required field '{str(k)}' is empty, missing a value.")
        #
        #   Then make certain all the keys are acceptable keys
        if self.__acceptable_keys__:
            self.log(f"validating extra fields", level="DEBUG")
            for k in self.__data__:
                if str(k) not in self.__acceptable_keys__ :
                    self.log(f"extra field '{str(k)}' not allowed", level="CRITICAL")
                    raise Exception(f"Invalid structure: extra field '{str(k)}' not allowed.")
        #
        #   Run through the keys making sure the type is valid and the value
        #   fits if a value constraint was specified.
        t_keys = list(self.__template__.keys())
        for tk in t_keys:
            #   Is the field is in our data
            if tk in self.__data__: 
                #   Check to see if it is a more complex data specification
                info = self.__template__[tk]
                #   Only do type checking when a dict is used to specify type info
                if not isinstance(info, dict): continue
                #   A None value for fields that are not required should just be skipped
                #   They will be cleaned before the record is probably used
                if ((self.__data__[tk] is None) and ('required' in info) and 
                    (not info['required'])): continue               
                #
                #   Now work through each of the different specification fields
                #   checking that the data meets the stated requirements
                if 'type' in info:
                    #   Validate that we have that type of thing in the field
                    self.log(f"validating field '{tk}' data type", level="DEBUG")
                    if not isinstance(self.__data__[tk],info['type']):
                        et = str(info['type']).partition(' ')[2].replace('>','')
                        ft = str(type(self.__data__[tk])).partition(' ')[2].replace('>','')
                        self.log(f"field '{tk}', expected type {et} but found type {ft}.", level="CRITICAL")
                        raise Exception(f"In field '{tk}', expected type {et} but found type {ft}.")
                #
                #   Value was an options constraint
                if 'options' in info:
                    self.log(f"validating that '{self.__data__[tk]}' is in options set", level="DEBUG")
                    if self.__data__[tk] not in info['options']:
                        ol = str(info['options'])
                        opt = str(self.__data__[tk])
                        self.log(f"field '{tk}', option '{opt}' is not one of {ol}.", level="CRITICAL")
                        raise Exception(f"In field '{tk}', option '{opt}' is not one of {ol}.")
                #
                #   Value was a range constraint
                if 'range' in info:
                    self.log(f"validating value data type in field '{tk}' is in acceptable range", level="DEBUG")
                    if self.__data__[tk] < info['range'][0]:
                        m = str(info['range'][0])
                        v = str(self.__data__[tk])
                        self.log(f"field '{tk}', value '{v}' is less than {m}, range minimum.", level="CRITICAL")
                        raise Exception(f"In field '{tk}', value '{v}' is less than {m}, range minimum.")
                    if self.__data__[tk] > info['range'][1]:
                        m = str(info['range'][0])
                        v = str(self.__data__[tk])
                        self.log(f"field '{tk}', value '{v}' is greater than {m}, range maximum.", level="CRITICAL")
                        raise Exception(f"In field '{tk}', value '{v}' is greater than {m}, range maximum.")
        self.log(f"returning", level="DEBUG")
        return
    
    
    #
    #   A method that generates an empty version of the underlying dictionary based on
    #   the list of acceptable keys
    def __new_dict__(self):
        req_data = dict()
        for key in self.__acceptable_keys__:
            if (self.__template__ and isinstance(self.__template__[key], dict) and
                'default' in self.__template__[key]):
                req_data[key] = self.__template__[key]['default']
            else:
                req_data[key] = None
        return req_data
    
    
    #
    #   A method that returns a "cleaned" version of this object's data
    #   In this case cleaned means that the unused fields are removed, but those
    #   fields will stay in the underlying data structure
    def __clean_dict__(self):
        self.__validate__()
        req_data = copy.deepcopy(self.__data__)
        clean_k = list()
        for k in req_data:
            # skip required keys, they have to stay in the data structure
            if( str(k) in self.__required_keys__ ):
                continue
            else:
                # track the non-required
                clean_k.append(str(k))
        
        # Now, remove the non-required keys if they are empty
        for k in clean_k:
            #print(f"Cleaning optional field '{k}'")
            # delete any extra, spurious key:value pairs
            if k not in self.__acceptable_keys__:
                del req_data[k]
                continue
            # special case - keep things that might be 'False' or 0 or 0.0
            if isinstance(req_data[k],bool) or isinstance(req_data[k],int) or isinstance(req_data[k],float):
                continue
            # now delete anything that has an empty value, empty string, empty dict, empty list
            if not req_data[k]:
                del req_data[k]
        self.log(f"cleaning ", level="DEBUG")
        return req_data
    

    #
    #   Three methods that enable standard dictionary access methods work
    #
    #   Get the value given a key - reports key failure
    def __getitem__(self, k):
        if self.__acceptable_keys__ and (k not in self.__acceptable_keys__):
            self.log(f"error trying to get value of an unrecognized field: '{k}'", level="CRITICAL")
            raise Exception(f"Unrecognized field: '{k}'")
        return self.__data__[str(k)]
    #
    #   Set the value associated with a key
    def __setitem__(self, k, v):
        if self.__acceptable_keys__ and (k not in self.__acceptable_keys__):
            self.log(f"error trying to set value of an unrecognized field: '{k}'", level="CRITICAL")
            raise Exception(f"Unrecognized field: '{k}'")
        self.__data__[k]=v
        return
    #
    #   Delete a key, but not a required key
    def __delitem__(self, k):
        if self.__acceptable_keys__ and (k not in self.__acceptable_keys__):
            self.log(f"error trying to remove an unrecognized field: '{k}'", level="CRITICAL")
            raise Exception(f"Unrecognized field: '{k}'")
        if self.__required_keys__ and (k in self.__required_keys__):
            self.log(f"error trying to remove a required field: '{k}'", level="CRITICAL")
            raise Exception(f"Field '{k}' is required.")
        del self.__data__[k]
        return
    
    #
    #   Three methods that make iteration, length, and string stuff work
    #
    #   Get the value given a key - reports key failure
    def __iter__(self):
        return iter(self.__data__)
    #
    #   Return the length of the nested dictionary
    def __len__(self):
        return len(self.__data__)
    #
    #   Generates a string representation, minimized as much as possible
    #   If you want something more friendly, then use the json() method
    def __repr__(self):
        self.__validate__()
        req = self.__clean_dict__()
        rtxt = self.json(r=req).replace('\n',' ').replace('\t',' ')
        return rtxt


#
#   Making JSON work with an object like this requires specifying how to
#   encode the object as JSON. In this case, we just need to return the
#   data member - it's just a regular dictionary. This nested encoder should
#   be able to handle all of the subclasses of this type
class DVFTJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj,DictionaryValidatorFromTemplate):
            return obj.__data__ 
        return obj
    
#####
#   
#   END class DictionaryValidatorFromTemplate definition
#   
#####


if __name__ == '__main__':
    print("DictionaryValidatorFromTemplate.py is a class with no main()")



