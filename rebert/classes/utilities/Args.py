#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: Args.py
#   REVISION: July, 2024
#   CREATION DATE: November, 2019
#   AUTHOR: David W. McDonald
#
#   A simple object that handles command line parsing. This is a simplified alternative to
#   argparse, which provides a more powerful version of argument parsing.
#
#   Args is based on a direct representation model for the specification of command line
#   parameters. That means, a dictionary template is used to specify the command line flags,
#   or keys, and what the associated values might be.
#   
#   Once the command line has been parsed the Args object can be used like a dictionary
#   with the keys being the command line flags/keys as the keys to the values that were
#   found. The dictionary is friendly - it will accept keys without hyphen specifiers.
#   
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
import sys, json
from datetime import datetime
from rebert.classes.base.Object import Object
#
#
#####
#
#   COMMAND LINE PARAMETER TEMPLATES EXPLAINED
#   
#   A supplied template is a dictionary where the structure of the dictionary and any
#   sub dictionaries will specify how to parse the command line and how to access the
#   values collected from the commandline.
#   
#   The top level keys of the template dictionary specify the parameter flags or
#   keys that the parser is to look for. That key can be associated with a dictionary
#   that specifies how the value of a parameter flag should be understood.
#   
#   The simplest specification can just provide the command line flags with no
#   additional specification. In that case, every parameter is optional and all 
#   parameters will be considered strings. An example could be something like:
#   
#   ARGS_PARAM_TEMPLATE = {
#       '-infile'   : None,
#       '-outfile'  : None,
#       '-debug'    : None
#   }
#   
#   In this simple example, the Args command like parser would be looking to collect
#   three named parameters '-infile', '-outfile', and '-debug'. Any values that came
#   with these command line flags would just be strings.
#   
#   On a command line this might look something like:
#   
#   python3 <program>.py -infile data_file.txt -outfile output.csv -debug
#   
#   In that example we'll assume that <program>.py is the name of a program file that
#   you are writing and that is using the Args() class. 
#   
#   The code that would create the Args() object and parse the command line might
#   look something like:
#   
#   p = Args(template=ARGS_PARAM_TEMPLATE)
#   p.parse(sys.argv)
#   
#   Once the argument vector had been parsed then 'p' (the Args() object) could be
#   used like a dictionary to get the values of the parsed out parameter values.
#
#   input_filname = p['-infile']
#
#   That should put the value of the '-infile' flag into the variable input_filename,
#   which should be "data_file.txt" based on the command line used to launch the
#   program.
#
#   The command line parameter template has a number of different ways to specify
#   how the values of a parameter should be handled. A slightly more elaborate version
#   of the template above might look like:
#
#   ARGS_PARAM_TEMPLATE = {
#       '-infile'   : {
#               'required'  : True,
#               'type'      : str,
#               'default'   : "input.txt"
#           },
#       '-outfile'  : {
#               'type'      : str,
#               'default'   : "output.txt"
#           },
#       '-debug'    : {
#               'type'      : bool
#           }
#   }
#
#   Each of the sub-dictionaries specify something about how to handle the data
#   coming from the command line. The '-infile' parameter is a required string 
#   parameter and if no parameter is supplied, the 'default' value "input.txt" 
#   should be used. The '-outfile' parameter is also a string, but is not required.
#   If no '-outfile' parameter is given the value "output.txt" should be used.
#   Lastly, the parameter '-debug' is an optional boolean parameter. Parameters
#   like '-debug' are False if they are not present on the command line and are
#   True if they appear on the command line; it's just a boolean flag
#
#   The 'type' specifier indicates how the parser should try to treat the
#   values on the command line. It specifies how the parser will attempt to
#   convert the data. The values for 'type' are many of the basic python data
#   types: bool, str, int, float, and list. There are three types that will
#   attempt to convert a value to a time or date: "time", "date", datetime.
#   The "time" and "date" are specified as the strings in the type field
#   (rather than an actual type). The datetime is a type, but one needs to
#   import the datetime object or your template won't work correctly.
#
#   The specifiers 'range' and 'options' allow the specification of an
#   inclusive value range, and a list of stated values that are valid.
#   This might look something like:
#
#   ARGS_PARAM_TEMPLATE = {
#       '-infile'   : {
#               'required'  : True,
#               'type'      : str,
#               'default'   : "input.txt"
#           },
#       '-outfile'  : {
#               'type'      : str,
#               'default'   : "output.txt"
#           },
#       '-count'    : {
#               'required'  : True,
#               'type'      : int,
#               'range'     : [0, 100],
#               'default'   : 5
#           },
#       '-direction': {
#               'type'      : str,
#               'options'   : ['north', 'south', 'east', 'west'],
#           },
#       '-debug'    : {
#               'type'      : bool
#           }
#   }
#
#   In this example, a new parameter '-count' has been added. It is
#   specified as a require parameter, and should be an integer. If it is
#   not provided, it should be given the value 5. The 'range' specifier
#   indicates that the value for '-count' can be between 0 and 100,
#   inclusive. That is, both 0 and 100 are valid values for '-count'.
#
#   Also, in the example above is the use of the 'options' specifier
#   for the '-direction' parameter. The parameter is not required, and
#   if provided, should be a string value. The 'options' specifier also
#   indicates that the string should be one of the four provided strings
#   'north', 'south', 'east', or 'west' (case sensitive).
#
#
#####
#   
#   CONSTANTS
#   
#####
#
#   This dictionary is a template used to validate and create the structure
#   used when parsing parameters. The provided template is lightly validated
#   and converted to this structure when the Args object is initialized or
#   when the setParamTemplate() method is called.
#
ARGS_PARAM_SPECIFICATION_TEMPLATE = {
    'required'  : None,     #   Boolean, whether or not a value is required 
    'type'      : None,     #   The type to which to convert the value
    'notes'     : "",       #   Notes to show for a usage() call
    'default'   : None,     #   A default value, if no value is parsed
    'range'     : None,     #   A numeric range, list of lowest and highest
    'options'   : None,     #   A list of acceptable values
    'value'     : None      #   The value after completing a parse
}
#
#
#
#####
#   
#   START class Args definition
#   
#####
#
#
###
#   A class/object that will parse command line parameters and make them available
#   as a dictionary type thing
#
class Args(Object):
    '''
    The Args class implements a basic command line argument parser. The model is based
    on creating a template dictionary, where the keys to the dictionary are the
    command line parameters that are to be extracted from the command line. How to
    treat the values extracted is specified by an optional dictionary associated with
    each template key.
    
    Attributes:
        __argv__                - a local copy of the command line arguments
        __template__            - a local copy of the specification template
        __params__              - the validated parameters that were parsed out
        __param_errors__        - errors found when attempting to validate parameters
        __unbound__             - parameter or parts that were not matched or not used
        __unrecognized__        - 
    
    Methods:
        setParamTemplate()      - set the parameters template for this class
        usage()                 - the expected usage
        parse()                 - parse a sys.argv - argument vector from the command line
        json()                  - get a JSON string of the parameters
        keys()                  - get a list of the parameter keys
        getErrors()             - get the errors found when validating/parsing
        __addSpecification__()  - examine and validate, the parameter specification for
                                  one key in the template
        __extractFlagStringPairs__()    - find parameter flag and the string values with it
        __validate__()          - validate the values of the parse
        __parseDate__()         - parse a date or datetime string
        __parseTime__()         - parse a time
        
    '''
    def __init__(self, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        template    : A template dictionary describing the command line params
        '''
        super().__init__(*args, **kwargs)       
        self.__argv__ = None            #   a copy of the argument vector (list)
        self.__template__ = None        #   a copy of the template given
        self.__params__ = dict()        #   a validated version of the template
        self.__param_errors__ = dict()  #   errors found on validating parsed params
        self.__unbound__ = list()       #   params, parts of params, that were not used
        self.__unrecognized__ = dict()  #   flag:value pairs that were not recognized
        #
        #   If there was a template, parse that out and use it
        if "template" in kwargs:
            self.setParamTemplate(kwargs["template"])
        return
    
    
    ###
    #
    #   Use the supplied parameter specification template to initialize the Args
    #   parser.
    def setParamTemplate(self, template={}):
        '''
        Accepts a template of the parameters, validates and sets up things for parsing.
        
        Parameters:
        template        - A parameter specification dictionary as described by the
                          documentation
        '''
        if not template: 
            self.log(f"the 'template' was missing or empty", level="DEBUG")
            self.log(f"the Args parser cannot be initialzed", level="DEBUG")
            return
        self.log(f"entering", level="DEBUG")
        self.__params__ = dict()
        self.__template__ = template.copy()
        # process a template dictionary
        tkeys = list(self.__template__.keys())
        for key in tkeys:
            #   Parameter keys, or flags will start with either a single or a
            #   double hyphen. If the key in the template does not have a hypen
            #   then this adds a hyphen as a standardization.
            if (not key.startswith('--')) and (not key.startswith('-')):
                flag = '-'+key
            else:
                flag = key
            #
            #   Get the options from the template
            options = self.__template__[key]
            #   Add these options, validated, to the params
            self.__addSpecification__(flag,options)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ###
    #
    #   Prints a usage message to the screen. Trying to give some help   
    def usage(self, argv=[], param_errors={}):
        '''
        Prints some usage information for using the command on the command line
        
        Parameters:
        argv            - an argument vector like that provided by sys.argv
        param_errors    - a dictionary of parameter errors produced by the
                          validate() method
        '''
        pref = "USAGE:"
        if argv:
            pref = f"\nUSAGE: python {argv[0]}\n"
        elif self.__argv__:
            pref = f"\nUSAGE: python {self.__argv__[0]}\n"
        reqf = ""
        optf = ""
        keys = list(self.__params__.keys())
        for k in keys:
            if self.__params__[k]['required']:
                if self.__params__[k]['notes']:
                    reqf = reqf+f"\t{k} {self.__params__[k]['notes']}\n"
                else:
                    reqf = reqf+f"\t{k}\n"
            else:
                if( self.__params__[k]['notes'] ):
                    optf = optf+f"\t{k} {self.__params__[k]['notes']}\n"
                else:
                    optf = optf+f"\t{k}\n"
        
        #print(f"{pref}{reqf}{optf}")
        flag_str = f"{pref}"
        if reqf:
            flag_str = flag_str + f"    Required parameters:\n{reqf}" 
        if optf:
            flag_str = flag_str + f"    Optional parameters:\n{optf}" 
        print(flag_str)
        #
        #   If parameter errors are supplied, then exit the running program
        if param_errors:
            print("Encountered the following parameter errors:")
            print(json.dumps(param_errors,indent=4))
            sys.exit(0)
        return


    def parse(self, argv=[], validate=True):
        '''
        Parses the provided sys.argv, argument vector to collect the parameter values
        
        Parameters:
        argv            - an argument vector like that provided by sys.argv
        validate        - if true, will attempt to validate the parameters collected 
                          from the command line, as specified by the template
        '''
        if not argv: 
            self.log(f"No argv argument list was provided, returning", 
                    level="WARN")
            return
        self.log(f"entering", level="DEBUG")
        #
        #   Save a copy of the argv
        self.__argv__ = argv.copy()
        if not self.__params__:
            self.log(f"Looks like the Args parser has not been initialzed", level="DEBUG")
            self.log(f"cannot parse the command line parameters", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return
        #
        #   See if we can create pairs of flag (or key) and it's value string
        pairs = self.__extractFlagStringPairs__(argv)
        if not pairs:
            self.log(f"failure when parsing parameters, could not find any key value pairs", 
                    level="DEBUG")
            self.__param_errors__ = self.__validate__()
            if validate and self.__param_errors__:
                self.usage(argv, self.__param_errors__)
            self.log(f"returning", level="DEBUG")
            return
        #
        #   Looks like we have what we need to start associating parameters
        #   with their values. The pairs dictionary should just be parameter
        #   flags (as a key) and the following string as a value.
        pkeys = list(pairs.keys())
        for flag in pkeys:
            val_str = pairs[flag]
            #   If it's not recognized store the flag and the value
            if not flag in self.__params__:
                self.__unrecognized__[flag] = val_str
                continue
            #
            #   This will be good, it's one of the recognized flags
            #   Get the options associated with this flag (or key)
            options = self.__params__[flag]
            #
            #   Depending upon the *type* conversion specifier, try to
            #   convert the associated value string to the value
            if options['type'] == bool:
                #   Boolean 'flags' are always True when present otherwise
                #   they are False by default, using a None value
                options['value'] = True
            #
            #   Try to convert to an int value
            elif options['type'] == int:
                #   If this is some string with spaces, just get the first term
                val_str = val_str.split()[0]
                try:
                    options['value'] = int(val_str)
                except:
                    self.__unrecognized__[flag] = val_str
                    self.log(f"For parameter '{flag}' could not make int() from '{val_str}'", 
                            level="DEBUG")
            #
            #   Try to convert to a float value
            elif options['type'] == float:
                #   If this is some string with spaces, just get the first term
                val_str = val_str.split()[0]
                try:
                    options['value'] = float(val_str)
                except:
                    self.__unrecognized__[flag] = val_str
                    self.log(f"For parameter '{flag}' could not make float() from '{val_str}'", 
                            level="DEBUG")
            #
            #   It's just a string, no conversion, just save it
            elif options['type'] == str:
                #   If this is a string - then we just keep the string
                options['value'] = val_str
            #
            #   Try to convert to a list of stuff
            elif options['type'] == list:
                #   Try to convert the string to a list of things
                #   Either a comma separated string of things or a space
                #   separated list
                if ',' in val_str:
                    # commas as the sep char
                    val_str = val_str.replace(" ","")
                    val_str = val_str.split(',')
                else:
                    # no commas, so space is sep
                    val_str = val_str.split()
                #   Now that the list is broken into parts, see if we can
                #   convert any of the things to useful values, say intgers
                #   floats, or just strings
                value_list = list()
                for v in val_str:
                    try:
                        i = int(v)
                        value_list.append(i)
                    except:
                        try:
                            f = float(v)
                            value_list.append(f)
                        except:
                            value_list.append(v)
                options['value'] = value_list
            #
            #   Look for a time type thing
            elif options['type'] == "time":
                result = self.__parseTime__(val_str)
                if not result[0]:
                    #   Did not get a conversion result
                    self.log(f"For parameter '{flag}' could not make time out of '{result[1]}'", 
                            level="DEBUG")
                    options['value'] = None
                    self.__unrecognized__[flag] = result[1]
                    if result[2]:
                        self.__unbound__.append(result[2])
                else:
                    #   Conversion worked, save it
                    options['value'] = result[0]
                    if result[2]:
                        self.__unbound__.append(result[2])
            #
            #   Look for a datetime type thing
            elif options['type'] == "date" or options['type'] == datetime:
                result = self.__parseDate__(val_str)
                if not result[0]:
                    #   Did not get a conversion result
                    self.log(f"For parameter '{flag}' could not make datetime out of '{result[1]}'", 
                            level="DEBUG")
                    options['value'] = None
                    self.__unrecognized__[flag] = result[1]
                    if result[2]:
                        self.__unbound__.append(result[2])
                else:
                    #   Conversion worked, save it
                    options['value'] = result[0]
                    if result[2]:
                        self.__unbound__.append(result[2])
            else:
                #   This is some unrecognized option type
                #   Collect just the string of the type name for this
                t = type(options['type']).rpartition(' ')[2]
                t = t.replace('<','').replace('>','')
                self.log(f"For parameter '{flag}' do not recognize the type {t}", 
                        level="DEBUG")
        #
        #   Need to validate the the parameters
        self.__param_errors__ = self.__validate__()
        #
        #   Once we've collected the validation information, then possibly act on it
        if validate and self.__param_errors__:
            self.usage(argv, self.__param_errors__)
        self.log(f"returning", level="DEBUG")
        return
    
    
    
    #
    #   Making JSON work with an object like this requires specifying how to
    #   encode the object as JSON. This encoder is just needs to handle a few
    #   different types of data.
    class DefaultArgsJSONEncoder(json.JSONEncoder):
        #
        #   This encoder needs to represent the conversion types as strings
        #   or the JSON conversion will fail. This creates a JSON that might
        #   look similar to the TEMPLATE, but it is not the same becaus the
        #   types are not actual types - like they are in a dictionary
        def default(self, obj):
            if isinstance(obj,Args):
                return obj.__params__
            if isinstance(obj,datetime):
                return str(obj)
            if obj is bool:
                return "bool"
            if obj is str:
                return "str"
            if obj is int:
                return "int"
            if obj is float:
                return "float"
            if obj is list:
                return "list"
            if obj is datetime:
                return "datetime"
            if isinstance(obj,type):
                return "<unrecognized type>"
            return obj
    
    
    def json(self, indent=None, sort_keys=None):
        '''
        Produce a JSON version of the underlying dictionary.
        
        The method provides two options that are standard to the json.dumps()
        method of the standard json package. 
        
        Optional Parameters:
        indent      : Create a formatted version of the JSON output
        sort_keys   : Sort the keys when producing the JSON
        
        Returns:
        A string of the dictionary in JSON format
        '''
        return json.dumps(self.__params__, cls=self.DefaultArgsJSONEncoder, 
                          indent=indent, sort_keys=sort_keys)
    
    
    def getErrors(self):
        '''
        Produce a list of keys for accessing the parameters
        
        Returns:
        A dictionary consisting of keys and a text message of the error, an
        empty dictionary means there were no errors
        '''
        self.__param_errors__ = self.__validate__()
        return self.__param_errors__
    
    
    def keys(self):
        '''
        Produce a list of keys for accessing the parameters
        
        Returns:
        A list of keys for accessing the parameters
        '''
        return list(self.__params__.keys())
    
    
    def __addSpecification__(self, flag=None, specs={}):
        '''
        Validates (lightly) and adds a specification to the parameter dictionary
        for the given flag.
        
        Parameters:
        flag            - the parameter flag
        specs           - a dictionary specifying how to treat the parameter when parsing
        '''
        self.log(f"entering", level="DEBUG")
        validated_specs = ARGS_PARAM_SPECIFICATION_TEMPLATE.copy()
        try:
            #   Check to see whether this is required or not
            validated_specs['required'] = specs['required']
        except:
            #   If it's not specifieid, then it is not requried
            validated_specs['required'] = False
        try:
            #   Check to see if there is a type conversion specifier
            if specs['type'] in [bool, int, float, str, list, "time", "date", datetime]:
                validated_specs['type'] = specs['type']
                #   If the conversion specifier is boolean, then we make the
                #   flag optional boolean flags are either present for 'True'
                #   or absent for the default "False"
                if specs['type'] is bool:
                    #   Make booleans - not required
                    validated_specs['required'] = False
                    #   Make booleans default to False
                    specs['default'] = False
        except:
            #   If no type is specified, then it's going to be a string
            #   because that's what command line arguments are without a
            #   type conversion specifier.
            validated_specs['type'] = str
        try:
            validated_specs['notes'] = specs['notes']
        except:
            validated_specs['notes'] = ""
        #
        #   Check for a default value, if there is one then set the
        #   value to that default
        try:
            validated_specs['default'] = specs['default']
            validated_specs['value'] = specs['default']
            if specs['default']:
                if validated_specs['type'] in ["date", datetime]:
                    result = self.__parseDate__(specs['default'])
                    validated_specs['value'] = result[0]
                    if not result[0]:
                        #   Did not get a conversion result
                        self.log(f"{flag} could convert '{specs['default']}' to a date/datetime",
                                level="WARN")
                elif validated_specs['type'] in ["time"]:
                    result = self.__parseTime__(specs['default'])
                    validated_specs['value'] = result[0]
                    if not result[0]:
                        #   Did not get a conversion result
                        self.log(f"{flag} could convert '{specs['default']}' to a time",
                                level="WARN")
        except:
            validated_specs['default'] = None
            validated_specs['value'] = None
        #
        #   Check the range option - if it exists
        try:
            #
            #   Low end of range has to be less than high end
            if specs['range'][0] < specs['range'][1]:
                #
                #   Make sure it is an int or float type thing
                if validated_specs['type'] in [int, float]:
                    validated_specs['range'] = specs['range']
                    #
                    #   Check that any default value is in the specified range
                    if validated_specs['value']:
                        if ((validated_specs['value'] < validated_specs['range'][0]) or
                            (validated_specs['value'] > validated_specs['range'][1])):
                            self.log(f"{flag} 'default' value is outside of specified 'range'", 
                                    level="WARN")
                else:
                    self.log(f"{flag} must be int or float to use 'range' specification", 
                            level="WARN")
                    validated_specs['range'] = list()
            else:
                self.log(f"{flag} 'range' specification must be [low value, high value]", 
                        level="WARN")
                validated_specs['range'] = list()
        except:
            validated_specs['range'] = list()
        #
        #   Now look at whether a set of options have been defined
        try:
            if validated_specs['range']:
                validated_specs['options'] = list()
                self.log(f"{flag} has defined a 'range' so 'options' have been ignored", 
                        level="WARN")
            else:
                validated_specs['options'] = specs['options']
                #
                #   Check that any default value is in the options
                if validated_specs['value']:
                    if validated_specs['value'] not in validated_specs['options']:
                        self.log(f"{flag} 'default' value is not one of the specified 'options'", 
                                level="WARN")
        except:
            validated_specs['options'] = list()
        #
        #   Now, save the validated specifications with the params
        self.__params__[flag] = validated_specs
        self.log(f"returning", level="DEBUG")
        return
    
    
    
    #
    #   Take the argument vector, check each item to see if it is a key
    #   if it is not a key assume it is a piece of a string that is associated
    #   with the previous flag
    #
    def __extractFlagStringPairs__(self, argv=None):
        self.log(f"entering", level="DEBUG")
        result = dict()
        i = 1
        arg_key = ""
        length = len(argv)
        while( i<length ):
            #   If this is a parameter 'flag' or key, then we add that key
            #   to the result dictionary, and start adding the other params
            #   as a string
            if argv[i].startswith('--') or argv[i].startswith('-'):
                arg_key = argv[i]
                result[arg_key] = ""
                i+=1
                continue
            #   If we got here, then this thing is not a key, it's just a
            #   string that follows a key we'll add that up until we find
            #   another flag, then start again
            if result[arg_key]:
                result[arg_key] = result[arg_key]+" "+argv[i]
            else:
                result[arg_key] = argv[i]
            i+=1
        self.log(f"returning", level="DEBUG")
        return result
    
    
    
    def __validate__(self):
        #   Check that all of the 'required' params have a value
        self.log(f"entering", level="DEBUG")
        param_errors = dict()
        fk = self.__params__.keys()
        for k in fk:
            if self.__params__[k]['required']:
                if not self.__params__[k]['value']:
                    param_errors[k] = "Missing, required parameter"
                    continue
            #   If we got here it's not a required parameter, we'll first check that
            #   there is some value, then possibly check the range or check options
            if not self.__params__[k]['value']: continue
            #
            #   If we got here we have a value, check that we have an int
            if self.__params__[k]['range'] and self.__params__[k]['type'] in [int, float]:
                if ((self.__params__[k]['value'] < self.__params__[k]['range'][0]) or
                    (self.__params__[k]['value'] > self.__params__[k]['range'][1])):
                    param_errors[k] = f"value '{self.__params__[k]['value']}' out of range"
                continue
            #
            #   If we got here, then we have something, and it might be a set of options
            if self.__params__[k]['options']:
                if self.__params__[k]['value'] not in self.__params__[k]['options']:
                    param_errors[k] = f"value '{self.__params__[k]['value']}' not in specified options"
        #   Note that the validation failed
        if param_errors:
            self.log(f"validation FAILED, missing {len(param_errors)} required parameters", 
                     level="CRITICAL")
        #   Return the list of keys with missing values
        self.log(f"returning", level="DEBUG")
        return param_errors
    
    
    
    ###
    #   
    #   This date parser recognizes only one style of date or datetime
    #   The dates must be in a YYYYMMDD format:
    #       YYYY is a four digit year
    #       MM is a two digit month
    #       DD is a two digit day
    #
    #   The date can optionally be followed by HH:MM:SS time
    #       HH is a two digit 24 hour of the day
    #       MM is a two digit minutes
    #       SS is a two digit seconds
    #
    #   This should be recursive. First try as two, then try as one
    def __parseDate__(self, dstr=None):
        self.log(f"entering", level="DEBUG")
        unbound = None
        date = None
        dstr_parts = dstr.split()
        #   If this is a long string, we only want the first two parts
        if len(dstr_parts) >= 2:
            dstr_try = dstr_parts[0]+" "+dstr_parts[1]
            unbound = " ".join(dstr_parts[2:])
        else:
            dstr_try = dstr
        #
        #   First, we'll try the date and time format
        try:
            #   One long datetime string YYYYMMDDHHMMSS
            #   This should fail if it is just YYYYMMDD
            date = datetime.strptime(dstr_try, "%Y%m%d%H%M%S")
        except Exception as e1:
            try:
                #   Now, the main specified datetime format
                date = datetime.strptime(dstr_try, "%Y%m%d %H:%M:%S")
            except Exception as e2:
                try:
                    #   Lastly, just try it as a YYYYMMDD format
                    date = datetime.strptime(dstr_try,"%Y%m%d")
                except Exception as e3:
                    #   First time through should always try the first two pieces
                    #   this recursion will only use the first piece
                    if len(dstr_parts) > 1:
                        result = self.__parseDate__(dstr_parts[0])
                        if not result[0]:
                            #   Did not get a conversion result
                            self.log(f"Could not parse '{dstr}' as a datetime", level="DEBUG")
                            date = None
                        else:
                            #   Could only convert the first value
                            unbound = " ".join(dstr_parts[1:])
                            date = result[0]
        self.log(f"returning", level="DEBUG")
        return [date, dstr, unbound]
    
    
    
    ###
    #   
    #   This time parser recognizes only one style of time format
    #   The time should be formatted as HH:MM:SS where:
    #       HH is a two digit 24 hour of the day
    #       MM is a two digit minutes
    #       SS is a two digit seconds
    #
    def __parseTime__(self, tstr=None):
        self.log(f"entering", level="DEBUG")
        unbound = None
        tobj = None
        tstr_parts = tstr.split()
        #   If this is a long string, we only want the first part
        if len(tstr_parts) > 1:
            tstr = tstr_parts[0]
            unbound = " ".join(tstr_parts[1:])
        #   
        try:
            #   One long time string HHMMSS
            tobj = datetime.strptime(tstr, "%H%M%S")
        except Exception as e1:
            #print(e1)
            try:
                #   Now, the specified time format
                tobj = datetime.strptime(tstr, "%H:%M:%S")
            except Exception as e2:
                #print(e2)
                self.log(f"Could not parse '{tstr}' as a time", level="DEBUG")
                tobj = None
        self.log(f"returning", level="DEBUG")
        return [tobj, tstr, unbound]

    
    def __getitem__(self, key):
        #
        #   First try to standarize the key
        if not key.startswith('-'):
            k2 = "--"+key
            k1 = "-"+key
            if k2 in self.__params__:
                key = k2
            if k1 in self.__params__:
                key = k1
        #
        #   Then, try to access the options and
        #   return the value of that option
        try:
            options = self.__params__[key]
        except KeyError as ke:
            raise ke
        return options['value']
    
    
    def __setitem__(self, key, value):
        #
        #   First try to standarize the key
        if not key.startswith('-'):
            k2 = "--"+key
            k1 = "-"+key
            if k2 in self.__params__:
                key = k2
            if k1 in self.__params__:
                key = k1
        #
        #   Now, try to access the options and
        #   set the value field of that option
        try:
            options = self.__params__[key]
        except KeyError as ke:
            raise ke
        options['value'] = value
        return
    
    
    def __delitem__(self, key):
        #
        #   First try to standarize the key
        if not key.startswith('-'):
            k2 = "--"+key
            k1 = "-"+key
            if k2 in self.__params__:
                key = k2
            if k1 in self.__params__:
                key = k1
        #
        #   Now, try to access the options 
        #   No access to options, then the key
        #   is not legitimate and a KeyError is
        #   raised
        try:
            options = self.__params__[key]
        except KeyError as ke:
            raise ke
        del self.__params__[key]
        return
        
    
    def __iter__(self):
        return iter(self.__params__)
    
    
    def __len__(self):
        return len(self.__params__)
    
    
    def __repr__(self):
        return self.json()

#####
#   
#   END class Args definition
#   
#####

    
if __name__ == '__main__':
    print("Args.py is a class with no main()")

    





