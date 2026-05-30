#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: Object.py
#   REVISION: March, 2024
#   CREATION DATE: June, 2017
#   Author: David W. McDonald
#
#   A base class for the objects in project rebert. This largely the same as the base class
#   used for most of my instructional projects.
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
import logging

#####
#   
#   CONSTANTS
#   
#####

#
#   Dictionary that links string logging levels to their numeric constants
#
LOGGER_LOG_LEVELS = {
    "DEBUG"     : logging.DEBUG,  
    "INFO"      : logging.INFO,
    "WARN"      : logging.WARNING,
    "WARNING"   : logging.WARNING,
    "ERROR"     : logging.ERROR,
    "CRITICAL"  : logging.CRITICAL
}


#####
#   
#   START class Object definition
#   
#####

class Object(object):
    '''
    A base Object class that provides configurable debugging and logging.
    
    Attributes:
        disable_debug   : whether debug output should be enabled or disabled
        daemon          : whether or not to consider this object as a daemon (server) object
        name            : a string name or descriptor for this object
        logger          : a logger object to be used when logging output to a file
    
    Methods:
        debugOn()           - enables debugging
        debugOff()          - disables debugging
        debug()             - outputs to the logger and/or to the screen depending on settings
        setLogger()         - set a logger on the current object
        getLogger()         - get the logger on this object
        log()               - write to the associated logger
        __className__()     - returns a simplified name of this class(object_name)
    
    '''

    ###
    #   Object constructor/initializer
    #
    def __init__(self, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__()
        self.disable_debug = True          # by default objects start with output suppressed
        self.daemon = False
        self.name = "Object"
        self.logger = None
        
        if 'name' in kwargs:
            self.name = kwargs['name']
        if 'logger' in kwargs:
            self.logger = kwargs['logger']
        return
    
    #####
    #   
    #   PUBLIC METHODS
    #   
    #####
    
    ###
    #   Turn on the debugging output  
    #
    def debugOn(self):
        '''Enables debugging output.'''
        self.disable_debug = False
        return
    
    ###
    #   Turn off the debugging output  
    #
    def debugOff(self):
        '''Disables debugging output.'''
        self.disable_debug = True
        return
    
    ###
    #   Write some debug output to the screen and optionally to a logger object  
    #
    def debug(self, *args, **kwargs):
        '''
        Prints output to the screen and optionally to an attached logger object (file). By using this
        method in your code:
            self.debug("Some message you want to see", level="DEBUG")
        you can simulate print line debugging - and turn that on or off on an object by object basis.
        
        If debugging has been disabled then there is no output.
        If a logger has been provided then the output is provided to the logger.
        If this object is a daemon object and there is a logger then output will go to the logger
        but not be sent to the screen.
        If debugging is enabled and this is not a daemon then ouptut is sent to stdout with a print().
        '''
        if self.disable_debug : return
        if self.logger:
            self.logger.log(*args, **kwargs)
        if self.daemon: return
        if 'level' in kwargs:
            del kwargs['level']
        print(*args, **kwargs)
        return
    
    
    
    ###
    #   Set a logger object for this object to use  
    #
    def setLogger(self, logger=None):
        '''Sets a logger object for use by this object.'''
        self.logger = logger
        return
    
    ###
    #   Get the logger object this object is currently using  
    #
    def getLogger(self):
        '''Gets the logger object used by this object.'''
        return self.logger
    
    ###
    #   Write output to a log file - if a logger object has been set on this object
    #   The optional parameter 'level' can either be the numeric level or an all caps
    #   string
    #
    def log(self, *args, **kwargs):
        '''
        Writes output to a logger object, if this object has a logger object associated with it.
        
        The log() method accepts a log string and an optional parameter 'level'. Without the optional
        parameter the log() method will force output by setting the message to the current log level
        of the associated logger.
        
        If the optional parameter 'level' is provided it will log the message at that level. The levels 
        are the same as for the python logging package and are also provided in the LOGGER_LOG_LEVELS
        constant.
        '''
        if self.logger:
            if 'level' in kwargs:
                level = kwargs['level']
                if str(kwargs['level']).upper() in LOGGER_LOG_LEVELS:
                    level = LOGGER_LOG_LEVELS[str(kwargs['level']).upper()]
                del kwargs['level']
                
                if level == logging.DEBUG:
                    self.logger.debug(*args, **kwargs)
                elif level == logging.INFO:
                    self.logger.info(*args, **kwargs)
                elif level == logging.WARNING:
                    self.logger.warning(*args, **kwargs)
                elif level == logging.ERROR:
                    self.logger.error(*args, **kwargs)
                elif level == logging.CRITICAL:
                    self.logger.critical(*args, **kwargs)
                else:
                    self.logger.log(f"Unrecognized log level: '{level}'")
            else:
                self.logger.log(*args, **kwargs)
        else:
            if 'level' in kwargs:
                del kwargs['level']
            self.debug(*args, **kwargs)
        return
    
    
    #####
    #   
    #   PRIVATE METHODS
    #   
    #####
    
    ###
    #   Get a 'pretty' version of a name for this object  
    #
    def __className__(self):
        '''Returns a string of this object class and the specified object name'''
        name = str(self.__class__).split("'")[1].strip()
        if self.name:
            name = name+f"(name={self.name})"
        return name
    
#####
#   
#   END class Object definition
#   
#####

if __name__ == '__main__':
    print("Object.py has no main()")

