#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: KeyManager.py
#   REVISION: May, 2024
#   CREATION DATE: August, 2023
#   Author: David W. McDonald
#
#   A simple class to manage API keys - without having to embed them in code
#   or add them to environment variables.
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
#
import os, sys, json, datetime

#   The key manager will inherit from our base Object class
from rebert.classes.base.Object import Object

# 
#   This dictionary structure is the default data stored for each key. Not all
#   fields are required. Required fields are the 'key' and either 'domain' or
#   'username'. Otherwise there is no way to find the actual key.
#
API_KEY_DICT_TEMPLATE = {
        'key'           : "",   #   the api key
        'domain'        : "",   #   the domain/host for api access
        'username'      : "",   #   the username/account associated with the key
        'organization'  : "",   #   the user's organization, some APIs require this
        'mnemonic'      : "",   #   a memorable term to help remember the key
        'description'   : "",   #   a string description of the api/key/domain
        'created_ts'    : "",   #   a timestamp for the creation of this record
        'updated_ts'    : "",   #   a timestamp of the last update to this record
        'expired'       : False #   whether or not the key has been expired
}
#
#   The actual key file is stored in a local file on disk. The file is
#   in JSON format. A 'hidden' directory is used to make the key file
#   less obvious. 
#
KM_KEY_FILE_DEFAULT = "access_keys.json"
KM_KEY_HIDDEN_DIR_DEFAULT = ".apikey_manager"
#
#   Simple status strings
KM_STATUS_OPEN = "open and loaded"
KM_STATUS_CLOSED = "still closed"


#####
#   
#   START class KeyManager definition
#   
#####

class KeyManager(Object):
    '''
    This class implements an API key manager. The basic idea is to store keys 
    locally on your disk to avoid embedding them into code. One common technique 
    that programmers often use is to create environment variables for each of 
    the different keys they use and then use some code to get those keys.

    This key manager has the same benefits and drawbacks as that approach. However,
    it also has some additional benefits. For example, this organizes keys by domain
    and user account. That is you can access different keys for the same API resource
    as a function of the user account. You can even store multiple keys if you like.
    
    The KeyManager class provides the following public methods:
        newRecord()     - to create a blank dictionary - key record
        submitRecord()  - takes key record and saves it
        createRecord()  - simplified creation of a key record
        findRecord()    - searches the keys using the username and/or domain
        updateRecord()  - given a key record makes updates to the exising record
        expireRecord()  - given a key record will mark that key record as expired
        listRecords()   - generates a descriptive list of existing keys
    
    Private methods perform low-level modifications of the key record and maintain
    data consistency between memory and keys on disk.
    '''
    def __init__(self, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        key_fname       :   str, the name of the key file on disk
        key_dir         :   str, directory path to the key file 
        '''
        super().__init__(*args, **kwargs)
        #
        #   Could use a different file name (optional parameter)
        if 'key_fname' in kwargs:
            self.key_fname = kwargs['key_fname']
        else:
            self.key_fname = KM_KEY_FILE_DEFAULT
        #   Could be in a different directory (optional parameter)
        if 'key_dir' in kwargs:
            self.key_dir = kwargs['key_dir']
        else:
            self.key_dir = ""
        #
        #   Initalize the key management dictionary
        self.__key_dict__ = dict()
        self.__key_dict__['dirty'] = False
        self.__key_dict__['by_user'] = dict()
        self.__key_dict__['by_domain'] = dict()
        
        self.status = KM_STATUS_CLOSED
        try:
            self.__read_key_file__()
            self.status = KM_STATUS_OPEN
        except Exception as ex:
            self.status = "Exception: "+str(ex)
        return        
    
    
    ###
    #   Create a new, blank, API key record
    #    
    def newRecord(self):
        '''
        This method creates a new, empty API key record - a python dictionary. 
        
        Returns:
        a new key dictionary with timestamp
        '''
        key = API_KEY_DICT_TEMPLATE.copy()
        key['created_ts'] = str(datetime.datetime.now()).partition('.')[0]
        return key
    
    
    ###
    #   Submit, that is save, a key record
    #    
    def submitRecord(self, record=None):
        '''
        This method will take a key record and incorporate it into the existing key datastructure. Once the key
        is incorporated it will write/update the key file on the disk.

        This method takes one parameter, a record that is a key record like that provided by the newRecord() method.

        The method performs some basic validation of the record, checking the 'username', 'domain' and 'key' fields
        to make sure that the API key record has something reasonable to store.

        '''
        if not record['username']:
            raise Exception("The 'username' field was empty. Must have a username.")

        if not record['domain']:
            raise Exception("The 'domain' field was empty. Must have a domain name.")

        if not record['key']:
            raise Exception("The 'key' field was empty. Must have a key.")

        ruser = record['username']
        rdomain = self.__regularize_domain__(record['domain'])
        record['domain'] = rdomain
        try:
            #
            # first 'by_user'
            if ruser not in self.__key_dict__['by_user']:
                self.__key_dict__['by_user'][ruser] = dict()
            if rdomain not in self.__key_dict__['by_user'][ruser]:
                self.__key_dict__['by_user'][ruser][rdomain] = list()
            self.__key_dict__['by_user'][ruser][rdomain].append(record)
            #
            # then 'by_domain'
            if rdomain not in self.__key_dict__['by_domain']:
                self.__key_dict__['by_domain'][rdomain] = dict()
            if ruser not in self.__key_dict__['by_domain'][rdomain]:
                self.__key_dict__['by_domain'][rdomain][ruser] = list()
            self.__key_dict__['by_domain'][rdomain][ruser].append(record)
        except Exception as ex:
            raise
        #
        # If we make it here, then we're dirty, try to save it
        self.__key_dict__['dirty'] = True
        record['updated_ts'] = str(datetime.datetime.now()).partition('.')[0]
        self.__write_key_file__()
        return
    
    
    ###
    #   Create a key based on the provided parameters
    #    
    def createRecord(self, username=None, domain=None, key=None, description=None):
        '''
        A simple, shortcut method for creating a key record.
        
        The method takes the parameter supplied and creates a record. Parameters
        must include username, domain, and key as a minimum. Method calls 
        newRecord() to create the record, fills out the record with the
        parameters supplied, and then calls submitRecord() to attempt the save.
        
        Parameters:
        username        : a string username associated with the key
        domain          : the API domain name
        key             : the key
        description     : a text description for this key (optional)
        '''
        if not username:
            raise Exception("The 'username' field was empty. Must have a username.")

        if not domain:
            raise Exception("The 'domain' field was empty. Must have a domain name.")

        if not key:
            raise Exception("The 'key' field was empty. Must have a key.")

        record = self.newRecord()
        record['username'] = username
        record['key'] = key
        record['domain'] = self.__regularize_domain__(domain)
        if not description:
            record['description'] = f"A key for the {domain} API"
        else:
            record['description'] = description
        self.submitRecord(record)
        return
    
    
    ###
    #   Search for a key in the set of keys that were loaded - return 
    #   copies of the key data. This relies on the private method that
    #   accepts the same parameters, but returns the actual records.
    #    
    def findRecord(self, username=None, domain=None, all=False):
        '''
        Find a record matching the parameters.
        
        This uses the parameters and attemps to find the record(s). The return 
        value is either an empty list, or a list of matching key records. This 
        technically returns copies of the key records so that if records are 
        changed during runtime there won't be accidental changes in the official
        key record that is saved to disk.
        
        Parameters:
        username        : a string username to search for
        domain          : the API domain name to search for
        all             : a flag, defaults to False. Setting this value to True
                          allows finding of expired keys
        
        Returns:
        a list of copies of key records that meet the search params
        '''
        result = list()
        findings = self.__find_record__(username,domain,all)
        for r in findings:
            result.append(r.copy())
                            
        return result
    
    
    ###
    #   Update a key, add/remove additional fields, update description
    #    
    def updateRecord(self, record=None):
        '''
        Updates information in a key record.

        The username, domain, and key cannot be updated. One should instead expire 
        an old key and create a new key record. This is useful for updating a description, 
        or adding/removing existing fields that are stored with the API key record.
        
        Parameters:
        record          : a dictionary, with username or domain and key
        
        Returns:
        True when expire is successful, False otherwise
        '''
        if not record:
            raise Exception("Cannot update a key without a key record.")
        ruser = record['username']
        rdomain = self.__regularize_domain__(record['domain'])

        if not ruser and not rdomain:
            raise Exception("Cannot update a key without either a username or a domain.")
        
        if not record['key']:
            raise Exception("The 'key' field was empty. Cannot update a record without the key.")
        
        found_records = self.__find_record__(ruser,rdomain,False)
        
        for r in found_records:
            if record['key']==r['key']:
                #   First, for any dictionary keys in 'r' but not in 
                #   parameter 'record' - delete those
                removals = list(r.keys())
                for field in removals:
                    if field in record: continue
                    del r[field]
                # create a list of fields that cannot be updated
                restricted = list(API_KEY_DICT_TEMPLATE.keys())
                restricted.remove('description')
                restricted.remove('organization')
                restricted.remove('mnemonic')
                updates = list(record.keys())
                #   Second update all of the fields that are in 'record' 
                #   but which are not restricted fields
                for field in updates:
                    if field in restricted: continue
                    r[field] = record[field]
                # lasly, save the record
                r['updated_ts'] = str(datetime.datetime.now()).partition('.')[0]
                self.__key_dict__['dirty'] = True
                self.__write_key_file__()
                return True
        
        return False
    
    
    ###
    #   Expire a key, mark it as expired
    #    
    def expireRecord(self, record=None):
        '''
        Expire a key.
        
        This method takes a key record, finds the corresponding record in the 
        set of keys and then marks it as expired.
        
        Parameters:
        record          : a dictionary, with username or domain and key
        
        Returns:
        True when expire is successful, False otherwise
        '''
        if not record:
            raise Exception("Cannot expire a key without a key record.")
        ruser = record['username']
        rdomain = self.__regularize_domain__(record['domain'])

        if not ruser and not rdomain:
            raise Exception("Cannot expire a key without either a username or a domain.")
        
        if not record['key']:
            raise Exception("The 'key' field was empty. Cannot expire a key without the key.")
        
        found_records = self.__find_record__(ruser,rdomain,False)
        for r in found_records:
            if record['key']==r['key']:
                r['expired'] = True
                r['updated_ts'] = str(datetime.datetime.now()).partition('.')[0]
                self.__key_dict__['dirty'] = True
                self.__write_key_file__()
                return True
        
        return False
    
    
    ###
    #   Provide a descriptive list of the keys
    #    
    def listRecords(self, username=None, domain=None):
        '''
        Generate a descriptive list of the keys.
        
        This method produces a descriptive list of all known key records. If 
        a username is provided then it filters by that. Alternatively, if a 
        domain name is given it filters by that.
        
        Parameters:
        username        : a string username to search for
        domain          : the API domain name to search for
        
        Returns:
        A list of records, containing descriptive data about the keys.
        '''
        result = list()
        #
        #   If we don't have data, return an empty list
        if not self.__key_dict__: return result
        #
        #   Got a username then filter by that
        if username:
            if username in self.__key_dict__['by_user']:
                user_domains = self.__key_dict__['by_user'][username]
                for d in user_domains.keys():
                    key_list = user_domains[d]
                    for key in key_list:
                        k = dict()
                        k['username'] = key['username']
                        k['domain'] = key['domain']
                        k['description'] = key['description']
                        k['expired'] = key['expired']
                        result.append(k)
                return result
        #
        #   Got a domain, then filter by that
        if domain:
            domain = self.__regularize_domain__(domain)
            if domain in self.__key_dict__['by_domain']:
                domain_users = self.__key_dict__['by_domain'][domain]
                for u in domain_users.keys():
                    key_list = domain_users[u]
                    for key in key_list:
                        k = dict()
                        k['username'] = key['username']
                        k['domain'] = key['domain']
                        k['description'] = key['description']
                        k['expired'] = key['expired']
                        result.append(k)
                    return result
        #
        #   Last case, return all of the data
        for uk in self.__key_dict__['by_user']:
            user_domains = self.__key_dict__['by_user'][uk]
            for d in user_domains.keys():
                key_list = user_domains[d]
                for key in key_list:
                    k = dict()
                    k['username'] = key['username']
                    k['domain'] = key['domain']
                    k['description'] = key['description']
                    k['expired'] = key['expired']
                    result.append(k)
                
        return result
    
    
    ###
    #   Private method version - does a little more work
    #   Search for a key in the set of keys that were loaded - return
    #   actual records
    #    
    def __find_record__(self, username=None, domain=None, all=False):
        '''
        This method attempts to find a key that meets the conditions of the 
        supplied parameters. 
        
        Parameters:
        username        : a string username to search for
        domain          : the API domain name to search for
        all             : a flag, defaults to False. Setting this value to True
                          allows finding of expired keys
        
        Returns:
        This private version returns the actual list of records for potential
        modification
        '''
        result = list()

        # if we didn't get the keys loaded return nothing
        if not self.__key_dict__: return result
        
        if username:
            if username in self.__key_dict__['by_user']:
                user_domains = self.__key_dict__['by_user'][username]
                if domain:
                    domain = self.__regularize_domain__(domain)
                    if domain in user_domains:
                        key_list = user_domains[domain]
                        for key in key_list:
                            if all: 
                                result.append(key)
                            elif not key['expired']:
                                result.append(key)
                        return result
                    else:
                        # domain supplied, but not in dict
                        return result
                else:
                    # no domain supplied - list keys for all domains
                    for d in user_domains.keys():
                        key_list = user_domains[d]
                        for key in key_list:
                            if all: 
                                result.append(key)
                            elif not key['expired']:
                                result.append(key)
                    return result
        
        # we're here because no user was supplied or user was not found
        if domain:
            domain = self.__regularize_domain__(domain)
            if domain in self.__key_dict__['by_domain']:
                domain_users = self.__key_dict__['by_domain'][domain]
                for u in domain_users.keys():
                    key_list = domain_users[u]
                    for key in key_list:
                        if all: 
                            result.append(key)
                        elif not key['expired']:
                            result.append(key)
                    return result
                
        return result
    
    
    ###
    #   Read the JSON key file and create two different ways to access
    #   the data: by username and by domain name. 
    #   
    def __read_key_file__(self):
        '''Reads and loads the key file.'''
        if self.__key_dict__ and self.__key_dict__['dirty']:
            raise Exception("Looks like there are new keys that have not be written.")
        self.__key_directory_path__()
        fullname = os.path.join(self.key_dir,self.key_fname)
        fp = open(fullname,"r")
        key_list = json.load(fp)
        fp.close()
        
        # first set up 'by_user'
        for record in key_list:
            ruser = record['username']
            rdomain = record['domain']
            #
            # first set up 'by_user'
            if ruser:
                if ruser not in self.__key_dict__['by_user']:
                    self.__key_dict__['by_user'][ruser] = dict()
                if rdomain not in self.__key_dict__['by_user'][ruser]:
                    self.__key_dict__['by_user'][ruser][rdomain] = list()
                self.__key_dict__['by_user'][ruser][rdomain].append(record)
            #
            # now set up 'by_domain'
            if rdomain:
                if rdomain not in self.__key_dict__['by_domain']:
                    self.__key_dict__['by_domain'][rdomain] = dict()
                if ruser not in self.__key_dict__['by_domain'][rdomain]:
                    self.__key_dict__['by_domain'][rdomain][ruser] = list()
                self.__key_dict__['by_domain'][rdomain][ruser].append(record)
        return
    
    
    ###
    #   Write the key file in JSON.
    #   
    def __write_key_file__(self):
        '''
        Write the key file as JSON.
        
        Makes sure that there is a data structure to write and that there is
        new data in the data structure.
        '''
        if self.__key_dict__ and self.__key_dict__['dirty']:
            # first set up the list of data to save
            key_list = list()
            dkeys = self.__key_dict__['by_domain'].keys()
            for dkey in dkeys:
                d = self.__key_dict__['by_domain'][dkey]
                ukeys = d.keys()
                for ukey in ukeys:
                    u = d[ukey]
                    for rec in u:
                        key_list.append(rec)
            # now make sure we have access
            self.__key_directory_path__()
            fullname = os.path.join(self.key_dir,self.key_fname)
            fp = open(fullname,"w")
            json.dump(key_list,fp,indent=4)
            fp.close()
            self.__key_dict__['dirty'] = False
        return
    
    
    ###
    #   Create the directory for the key file
    #   
    def __create_key_directory__(self, path=None):
        '''
        Creates the directory path to where the key file is stored.
        
        Parameters:
        path            : str, the directory path to be created
        '''
        # avoid clobbering an existing file
        if( not os.path.isfile(path) ):
            # not a file, maybe an existing dir
            if( not os.path.isdir(path) ):
                # not a file, not an existing dir, create
                os.mkdir(path)
        return
    
        
    ###
    #   Create/define the path to the key file.
    #   
    def __key_directory_path__(self):
        '''Create a directory path name in the user home directory.'''
        td = ""
        if( self.key_dir ):
            self.__create_key_directory__(self.key_dir)
            return self.key_dir
        else:
            #   First, try someing for MacOS and Linux
            try:
                td = os.path.join(os.environ['HOME'],KM_KEY_HIDDEN_DIR_DEFAULT)
            except:
                #   Next, try Window OS environment variable
                try:
                    td = os.path.join(os.environ['HOMEPATH'],KM_KEY_HIDDEN_DIR_DEFAULT)
                except:
                    #   Neither, then throw the exception
                    raise
            self.__create_key_directory__(td)
            self.key_dir = td
        return
    
    
    ###
    #   Regularize the domain names. Try to make them all look the same with
    #   a standard format
    #   
    def __regularize_domain__(self, domain=None):
        '''
        Returns a domain/host in a standardized format.
        
        Parameters:
        domain          : str, the host/domain name provided
        
        Returns:
        A regularized version of the domain/host name
        '''
        if not domain: return ""
        #   Assume we don't get a clean domain name,
        #   that we get a URL looking string
        d = domain.lower()
        #   Remove any HTTP or internet protocols
        parts = d.partition("://")
        d = parts[2]
        if not d:
            d = parts[0]
        #   Clean any preceeding / chars
        while d.startswith("/"):
            d = d[1:]
        #   Split any URL paths
        dlist = d.split("/")
        #   Take the first part of a path
        d = dlist[0]
        #   Now remove any port specifiers
        d = d.partition(":")[0]
        return d
    
    
#####
#   
#   END class KeyManager definition
#   
#####


#####
#   
#   Below is code that implements a simple interactive shell to
#   view, add or expire API keys.
#   
#   This interactive shell can be launched at the terminal
#   command line with something like:
#
#   > python KeyManager.py
#
#   The main() function, below, will attempt to show info on 
#   what keys are available and then wait for your command
#


###
#   Print some help information for the interactive shell
#
def print_help_info():
    print()
    print("This interactive key manager provides rudimentary access to the")
    print("KeyManager functionality. All commands should be lowercase.")
    print()
    print("?, h, help")
    print("\tGet this help message.")
    print("l, list")
    print("\tList or print a brief version of key information.")
    print("n, new")
    print("\tInteractive creation of a new key.")
    print("find d = <domain_name> u = <username>")
    print("\tFind a specific key record. This will print the full record.")
    print("a, active")
    print("\tShow the *full* information of the active record.")
    print("s, set <field> = <value>")
    print("\tCreate and/or set the value of an arbitrary field in the record.")
    print("expire")
    print("\tExpire the active record. Expire the key of the active record.")
    print("q, quit")
    print("\tQuit this interactive shell.")
    print()
    return
    
    
###
#   Print basic key information - without exposing the key value
#
def print_key_info(key_info=None):
    if not key_info:
        print("Looks like there are no keys to list.")
        return
    print()
    print("Here are the keys in the key file:")
    print()
    print("ACTIVE | USERNAME                  | DOMAIN")
    print("------------------------------------------------------------")
    for item in key_info:
        if not item['expired']:
            print(f"True   | {item['username']:25} | {item['domain']}")
        else:
            print(f"False  | {item['username']:25} | {item['domain']}")
    return
    
    
###
#   Interactive key creation, to add a new key to the key manager
#
def create_key(key_manager=None):
    if not key_manager: return
    print("To create a new key you need to enter three pieces of")
    print("information: domain name for the API, username, and key.")
    print("You can also add an optional description.")
    print()
    domain = input("KeyManager      ['domain']> ").strip()
    if not domain:
        print("The 'domain' cannot be empty. Creation aborted.")
        return
    uname = input("KeyManager    ['username']> ").strip()
    if not uname:
        print("The 'username' cannot be empty. Creation aborted.")
        return
    key = input("KeyManager         ['key']> ").strip()
    if not key:
        print("The 'key' cannot be empty. Creation aborted.")
        return
    description = input("KeyManager ['description']> ").strip()
    #
    #   Only attempt to add the record if we have the minimum
    #   three pieces of information, username, domain, & key
    key_manager.createRecord(uname, domain, key, description)
    print("Creation was attempted. Check by listing key records.")
    print("Use the 'set' command to set additional or other optional fields.")
    return


###
#   Set or create a field - but not some protected fields
#
def set_field_value(params=None, active_record=None, key_manager=None):
    if not key_manager: return
    #   The value of params should just be <field>=<value>
    parts = params.partition("=")
    field = parts[0].strip()
    value = parts[2].strip()
    #   Make sure there is a key and a value
    if not field:
        print("The 'set' command should only have one <field>=<value> pair.")
        print(f"The parameters '{params}' could not be parsed properly.")
        return
    #   Make sure we're not overwriting protected keys
    if field in ['expired','username','domain','key','created_ts','updated_ts']:
        print(f"The field '{field}' is a protected field with a value managed by the code.")
        return
    #   This can remove the value in a field for some fields or completely delete
    #   a field if it isn't part of the standard fields
    if not value:
        if field in ['organization','mnemonic','description']:
            active_record[field] = ""
        else:
            del active_record[field]
    else:
        #   Set the value in the active record
        active_record[field] = value
    #   Then attempt to update the record
    key_manager.updateRecord(active_record)
    print("Update to the record was attempted. Check by listing key records.")
    return
    
    
    
###
#   Find a key based on command line parameters. The format for
#   the command is specified in the help information
#
def find_key(params=None, key_manager=None):
    #
    #   Yes, parsing these parameters is a one liner regex
    #   Here we'll loop to break this up and pick out the
    #   parts we need
    param_list = list()
    #   Split the command up by white space
    plist = params.split()
    for p in plist:
        #   Then split up by the equal sign
        param_list.extend(p.split('='))
    #
    #   Initialize some status variables
    d = ""
    u = ""
    set_d = False
    set_u = False
    #   Run through the terms, collect values depending
    #   upon which terms come first
    for term in param_list:
        if set_d:
            if term and (term not in ['=', ' ']):
                d = term
                set_d = False
                continue
        if set_u:
            if term and (term not in ['=', ' ']):
                u = term
                set_u = False
                continue
        if term.startswith('d'): set_d = True
        if term.startswith('u'): set_u = True
    #
    #   Just output the terms if we don't have the key manager
    if not key_manager:
        print(f"Parsed out the domain '{d}' and username '{u}'")
        return None
    #
    #   Find the records that match
    record_list = key_manager.findRecord(u,d)
    if record_list:
        print(f"Found {len(record_list):d} record that met the conditions.")
        print(f"Working with the active record:")
        print(json.dumps(record_list[0],indent=4))
        return record_list[0]
    else:
        print(f"No records were found for domain '{d}' and username '{u}'")
        return None
    return None
    
    
#
#   Don't set these values unless you just want to test
#   and explore how the key manager works.
#
#   The rebert code is designed to work with the default
#   key manager file locations. If you want to use a different
#   *default* key location, then you'll need to update much of
#   the code that accesses the key manager.
#
#   The example program shows a way to pass a directory name
#   and/or a file name to change which key files are used
#
#ALTERNATE_KEY_DIR = "/Users/dwmc/Development/working3/rebert/classes/files"
#ALTERNATE_KEY_FNAME = "keys.json"
#ALTERNATE_KEY_FNAME = "newkeys.json"
ALTERNATE_KEY_DIR = ""
ALTERNATE_KEY_FNAME = ""


###
#   A small interactive command shell to view, create and expire keys
#   in this key manager.
#
def main():
    #   You can use an alternate directory to test this out
    #   Read the comments above before trying to set alternates
    if ALTERNATE_KEY_DIR and ALTERNATE_KEY_FNAME:
        key_manager = KeyManager(key_dir=ALTERNATE_KEY_DIR,
                                 key_fname=ALTERNATE_KEY_FNAME)
    else:
        key_manager = KeyManager()
    
    #   Do we have an open, existing key file or a new one
    if key_manager.status.startswith('open'):
        key_info = key_manager.listRecords()
        if key_info:
            print_key_info(key_info)
        else:
            print()
            print("Looks like there are no keys in the key file!")
    else:
        print()
        print("The key file was missing.")
        print("Are you initializing a new key file?")
    
    #   Initialize an active record, set after a 'find'    
    active_record = None
    
    #   Get a command
    print()
    command = input("KeyManager > ").strip()
    #   While the user enters some text - not 'quit'
    while len(command)>0 and (command.lower() not in ['q', 'quit']):
        #   Simple command dispatch
        #   Help requests
        if command in ['?','h','help']:
            print_help_info()
        #   List off the keys request
        elif command in ['l','list']:
            key_info = key_manager.listRecords()
            print_key_info(key_info)
        #   Create, add, a new key
        elif command in ['n', 'new']:
            create_key(key_manager)
        #   Show the active key record
        elif command in ['a', 'active']:
            if active_record:
                print("The current active record is:")
                print(json.dumps(active_record,indent=4))
            else:
                print("There is no currently active key record.")
                print("Use the 'find' command to find and set an active record.")
        elif command in ['expire']:
            if active_record:
                if key_manager:
                    key_manager.expireRecord(active_record)
                    print("Expiration was attempted. Check by listing key records.")
            else:
                print("There is no currently active key record.")
                print("Use the 'find' command to find and set an active record.")
        #   Create and/or set the value of an arbitrary field
        elif command.startswith('s ') or command.startswith('set '):
            if active_record:
                set_field_value(command.partition(' ')[2],
                                active_record,
                                key_manager)
            else:
                print("There is no currently active key record.")
                print("Use the 'find' command to find and set an active record.")
        #   Find a key, print details
        elif command.startswith('f ') or command.startswith('find '):
            active_record = find_key(command.partition(' ')[2],
                                     key_manager)
        else:
            print("Huh? ... try ? or help to get some help.")
        
        #   Get the next command
        print()
        command = input("KeyManager > ").strip()
    
    return


if __name__ == '__main__':
    main()

