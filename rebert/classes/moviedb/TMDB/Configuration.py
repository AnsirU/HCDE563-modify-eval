#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: Configuration.py
#   REVISION: July, 2024
#   CREATION DATE: July, 2024
#   AUTHOR: David W. McDonald
#
#   A web service class that implements the configuration request for TMDB
#   
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
#
#   Standard python modules
import json, copy
from datetime import datetime
#
#   This class is a sub-class of HTTPConnection
from rebert.classes.base.HTTPConnection import HTTPConnection

#####
#   
#   CONSTANTS
#   
#####
#
#
#####
#   
#   START class Configuration definition
#   
#####
#
class Configuration(HTTPConnection):
    def __init__(self, name="TMDB-Configuration", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #
        #   Set attributes specific to this server
        self.setHost("https://api.themoviedb.org")
        #
        #   There is only one type of configuration call
        self.setServiceEndpoint("/3/configuration")
        #
        self.setThrottleRate(rps=1.0)
        self.throttlingOn()
        #   Pick a random user agent to simulate a browser reqeust
        self.setUserAgent()
        #   Set a request header value to tell the server we accept JSON
        #   as the response data (required)
        self.setHeaderValue('accept', 'application/json')
        return
    
    
    ##
    #   A method that performs a configuration request  
    #
    def getConfiguration(self):
        '''
        Get the TMDB configuration data
        
        This method makes a configuration request and returns the result
        
        Parameters:
            None
                    
        Returns:
            A configuration dictionary 
        '''
        config = dict()
        self.log(f"entering", level="DEBUG")
        
        token = self.getHeaderValue('Authorization')
        key = self.getRequestParam('api_key')
        if not key and not token:
            self.log("Set the API Key or Bearer Token to search TMDB", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return config
        
        self.queueRequest()
        self.makeRequest()
        resp = self.nextResponse()
        config = resp.json()
        
        self.log(f"returning", level="DEBUG")
        return config
        

    ##########
    #
    #   REQUEST PARAMETER MANAGEMENT
    #
    ##########
    
    
    ##
    #   This uses the TMDB 'Access Token' as a key in the
    #   request header. This is one of the two forms of auth
    #   for TMDB
    #
    def setBearerToken(self, token=""):
        bearer_str = ""
        if token:
            bearer_str = f"Bearer {token}"
        self.setAuthorization(bearer_str)
        return
    
    
    ##
    #   This uses the "API Key" from TMDB as a key in the
    #   request parameters. This is another form of auth
    #   for TMDB
    #
    def setAPIKey(self, key=""):
        self.setRequestParam('api_key',key)
        return

#####
#   
#   END class Configuration definition
#   
#####

if __name__ == '__main__':
    print("Configuration.py is a class with no main()")


