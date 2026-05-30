#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: Logger.py
#   REVISION: March, 2024
#   CREATION DATE: November, 2019
#   Author: David W. McDonald
#
#   A class that wrappers a python logger object. This will set up generic logging to a file.
#   Log levels are the same as those for the python logger. The method log() can be used to
#   dump output regardless of the current logging level. This makes log() behave a bit like 
#   a print line debugger.
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
import logging, inspect, copy, os
from rebert.classes.base.Object import Object

#####
#   
#   CONSTANTS
#   
#####

#
#   Styles are assumed to be the % format. See https://docs.python.org/3/howto/logging.html#formatters
#
LOGGER_LOG_FORMAT_TINY ='%(message)s'
LOGGER_LOG_FORMAT_SHORT ='[%(asctime)s]: %(message)s'
LOGGER_LOG_FORMAT_WHERE ='[%(module)s %(funcName)s():%(lineno)d]: %(message)s'
LOGGER_LOG_FORMAT_MEDIUM ='[%(asctime)s] [%(module)s %(funcName)s():%(lineno)d]: %(message)s'
LOGGER_LOG_FORMAT_LONG ='[%(asctime)s] %(levelname)s [%(module)s %(funcName)s():%(lineno)d]: %(message)s'

#
#   These pre-defined log formats can be used by name - all caps
#
LOGGER_LOG_FORMAT_STYLES = {
    "NONE"          : LOGGER_LOG_FORMAT_TINY,
    "TINY"          : LOGGER_LOG_FORMAT_TINY,
    "WHERE"         : LOGGER_LOG_FORMAT_WHERE,
    "WHEN"          : LOGGER_LOG_FORMAT_SHORT,
    "SHORT"         : LOGGER_LOG_FORMAT_SHORT,
    "WHEN_WHERE"    : LOGGER_LOG_FORMAT_MEDIUM,
    "MEDIUM"        : LOGGER_LOG_FORMAT_MEDIUM,
    "LONG"          : LOGGER_LOG_FORMAT_LONG
}

#
#   Log levels are the standard levels. This dictionary creates a text mapping in case a
#   caller uses a string version of the level rather than the numeric constant
#
LOGGER_LOG_LEVELS = {
    "DEBUG"     : logging.DEBUG,  
    "INFO"      : logging.INFO,
    "WARN"      : logging.WARNING,
    "WARNING"   : logging.WARNING,
    "ERROR"     : logging.ERROR,
    "CRITICAL"  : logging.CRITICAL
}

#
#   A list of method names. These method names are skipped (ignored) when we are trying
#   to figure out where the logging call was made. Generally when making a log entry we
#   want to know who (what function/method, what file, what line) called so we can add
#   that information if it is request by the log format
#
LOGGER_METHOD_SKIPS = ['debug', 'log', 'info', 'warning', 'error', 'critical']

#
#   This is a dictionary template that is used to collect the information about the
#   likely caller. It turns out the most important thing is 'stacklevel' but its all
#   collected for now, even though stacklevel is the only thing currently used.
#
LOGGER_FRAME_INFO_TEMPLATE = {
    "stacklevel"    : 1,
    "filename"      : "",
    "module"        : "",
    "lineno"        : "",
    "function"      : "",
    "context"       : None,
    "index"         : -1
}

#####
#   
#   START class Logger definition
#   
#####

class Logger(Object):
    '''
    A base class that provides configurable debugging and logging.
    
    This provide simplified, unified, logging. That is all of the logging output
    goes into the specified file using the same output. This object uses the Python
    inspect module to try and identify where in the call chain the actual logging
    request happened. That level is then sent to the python logger.
    
    Attributes:
        logger          : the logger that is being used by this object
        file_handler    : the file handler associated with the logger
        log_filename    : the string filename where output will be written
        log_format      : a format string describing the logger output
        log_level       : the logging level
    
    Methods:
        getLevel()                  - returns the logging level of this logger
        log()                       - output to the log - regardless of the log level
        debug()                     - writes output to the file if the level is DEBUG (highest detail)
        info()                      - writes output to the file if the level is INFO or lower
        warning()                   - writes output to the file if the level is WARNING or lower
        error()                     - writes output to the file if the level is ERROR or lower
        critical()                  - writes output to the file if the level is CRITICAL or lower (lowest detail)
        __getCallerContextInfo__()  - returns record of the calling context of the most likely caller
        __close__()                 - closes the file associated with this logger
    
    '''
    
    ###
    #   Object constructor/initializer
    #
    def __init__(self, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
            filename    :   str, the file to use for logging
            format      :   str, the name of a format, or a format string
            level       :   int/str, the loglevel as an it or string name
            overwrite   :   bool, whether or not to overwrite an existing logfile
        '''
        super().__init__(*args, **kwargs)
        self.logger = None
        self.file_handler = None
        self.log_filename = 'runtime_logfile.txt'
        self.log_format = LOGGER_LOG_FORMAT_WHERE
        self.log_level = logging.WARNING
        #
        #   Check for the optional arguments
        if 'filename' in kwargs:
            self.log_filename = kwargs['filename']
        #
        if 'format' in kwargs:
            uformat = str(kwargs['format']).upper()
            if uformat in LOGGER_LOG_FORMAT_STYLES:
                self.log_format = LOGGER_LOG_FORMAT_STYLES[uformat]
            else:
                #   Not a recognized style key, then assume the coder
                #   knows what they are doing with a format string
                self.log_format = kwargs['format']
        #
        if 'level' in kwargs:
            #   Hard coded the python logging level numeric values
            if kwargs['level'] in [10, 20, 30, 40, 50]:
                self.log_level = kwargs['level']
            elif kwargs['level'] in LOGGER_LOG_LEVELS:
                self.log_level = LOGGER_LOG_LEVELS[kwargs['level']]
        #
        overwrite = False
        if 'overwrite' in kwargs:
            if kwargs['overwrite']:
                overwrite = True
        #
        #   Initialze the logging file with our parameters
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(self.log_level)
        if overwrite:
            #   Overwrite the old log file with a new one
            self.file_handler = logging.FileHandler(self.log_filename, mode='w')
        else:
            self.file_handler = logging.FileHandler(self.log_filename)
        self.file_handler.setLevel(self.log_level)
        formatter = logging.Formatter(self.log_format)
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)
        return    
    
    ###
    #   Return a list of the logging level of this logger. The list contains
    #   the integer loglevel and a string version of that level
    #
    def getLevel(self):
        '''Returns a list of the loglevel as an integer value and a descripive string.'''
        if self.log_level == logging.DEBUG:
            return [self.log_level, "DEBUG"]
        elif self.log_level == logging.INFO:
            return [self.log_level, "INFO"]
        elif self.log_level == logging.WARNING:
            return [self.log_level, "WARNING"]
        elif self.log_level == logging.ERROR:
            return [self.log_level, "ERROR"]
        elif self.log_level == logging.CRITICAL:
            return [self.log_level, "CRITICAL"]
        return [self.log_level, "UNKNOWN"]
    
    ###
    #   Write something to the log, no matter what level is selected - this should
    #   always write/log a message.
    #
    def log(self, *args, **kwargs):
        '''Writes the message to the log, regardless of the level.'''
        if not self.logger: return
        if self.log_level == logging.DEBUG:
            self.debug(*args, **kwargs)
        elif self.log_level == logging.INFO:
            self.info(*args, **kwargs)
        elif self.log_level == logging.WARNING:
            self.warning(*args, **kwargs)
        elif self.log_level == logging.ERROR:
            self.error(*args, **kwargs)
        elif self.log_level == logging.CRITICAL:
            self.critical(*args, **kwargs)
        return

    ###
    #   Write a message to the log if the log level is DEBUG
    #   Generally, debug is the most verbose level and provides the most detail
    #
    def debug(self, *args, **kwargs):
        '''Writes the message to the log if the log level is DEBUG.'''
        if not self.logger: return
        stackinfo = self.__getCallerContextInfo__()
        kwargs['stacklevel'] = stackinfo['stacklevel']
        self.logger.debug(*args, **kwargs)
        return
        
    ###
    #   Write a message to the log if the log level is INFO or lower
    #
    def info(self, *args, **kwargs):
        '''Writes the message to the log if the log level is INFO.'''
        if not self.logger: return
        stackinfo = self.__getCallerContextInfo__()
        kwargs['stacklevel'] = stackinfo['stacklevel']
        self.logger.info(*args, **kwargs)
        return
        
    ###
    #   Write a message to the log if the log level is WARNING or lower
    #
    def warning(self, *args, **kwargs):
        '''Writes the message to the log if the log level is WARNING.'''
        if not self.logger: return
        stackinfo = self.__getCallerContextInfo__()
        kwargs['stacklevel'] = stackinfo['stacklevel']
        self.logger.warning(*args, **kwargs)
        return
        
    ###
    #   Write a message to the log if the log level is ERROR or lower
    #
    def error(self, *args, **kwargs):
        '''Writes the message to the log if the log level is ERROR.'''
        if not self.logger: return
        stackinfo = self.__getCallerContextInfo__()
        kwargs['stacklevel'] = stackinfo['stacklevel']
        self.logger.error(*args, **kwargs)
        return
        
    ###
    #   Write a message to the log if the log level is CRITICAL or lower
    #
    def critical(self, *args, **kwargs):
        '''Writes the message to the log if the log level is CRITICAL.'''
        if not self.logger: return
        stackinfo = self.__getCallerContextInfo__()
        kwargs['stacklevel'] = stackinfo['stacklevel']
        self.logger.critical(*args, **kwargs)
        return

    #####
    #   
    #   PRIVATE METHODS
    #   
    #####
    
    ###
    #   This attempts to solve a sticky problem when generating logged output. Helpful
    #   logging will tell you where - in the code - the logging happened. Python's
    #   default logger does this for us - but if we use that by default - then we'll
    #   *always* get information that relates to the calls to logger in *this* file and
    #   this object.
    #
    #   What this does is look back in the execution stack to find the first calling
    #   context in the stack that is not part of this object and not one of our 
    #   well-known logging methods in our base class Object or the threaded Object.  
    #
    def __getCallerContextInfo__(self):
        '''Returns a dictionary of the first calling context that is not our own.'''
        stacklevel = 0
        try:
            cf = inspect.stack()[stacklevel]
            #   Skip all of the stack frames related 
            #   to this object
            while cf.filename.endswith("Logger.py"):
                stacklevel += 1
                cf = inspect.stack()[stacklevel]
            #   Skip all frames that contain any of the named 
            #   methods/functions that log
            while cf.function in LOGGER_METHOD_SKIPS:
                stacklevel += 1
                cf = inspect.stack()[stacklevel]
        except Exception as e:
            return LOGGER_FRAME_INFO_TEMPLATE.copy()
        #
        #   Copy everything to make sure all of the data is 
        #   'disconnected' from the actual stack frame
        frame_info = LOGGER_FRAME_INFO_TEMPLATE.copy()
        frame_info['stacklevel'] = copy.copy(stacklevel)
        frame_info['filename'] = copy.copy(cf.filename)
        frame_info['module'] = os.path.split(frame_info['filename'])[1]
        frame_info['lineno'] = copy.copy(cf.lineno)
        frame_info['function'] = copy.copy(cf.function)
        frame_info['context'] = copy.deepcopy(cf.code_context)
        frame_info['index'] = copy.copy(cf.index)
        return frame_info


    ###
    #   The only real reason to use this is when performing the testing of the logger.
    #   This is private because it really shouldn't be used - if you don't want logging
    #   don't set up a logger
    #   
    def __close__(self):
        '''Closes the file associated with this logger.'''
        stacklevel = 0
        try:
            self.logger.removeHandler(self.file_handler)
            self.file_handler.close()
            self.file_handler = None
            self.logger.addHandler(logging.NullHandler())
        except Exception as e:
            print(f"__close__(): Caught {str(e)}")
            raise
        return


#####
#   
#   END class Logger definition
#   
#####

if __name__ == '__main__':
    print("Logger.py is a class with no main()")

