#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: Chat.py
#   REVISION: June, 2024
#   CREATION DATE: April, 2023
#   AUTHOR: David W. McDonald
#
#   A web service example that implements the 'chat/completions' endpoint of OpenAI. Documentation
#   for this API can be found at:
#   
#   https://platform.openai.com/docs/api-reference/chat
#   and
#   https://platform.openai.com/docs/guides/chat
#
#   
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#

import sys, datetime, json, copy
#
#   This Chat class is based on the OpenAIAPIBase class
from rebert.classes.OpenAI.OpenAIAPIBase import OpenAIAPIBase
#
#####
#   
#   CONSTANTS
#   
#####
#
#   This is the part of the URL (service endpoint) that is not part of the super class.
#   In the subclass we set this as the oai_api_service and then use that to construct
#   the full service endpoint - with the version number.
#
OAI_API_SERVICE = "chat/completions"
#
#####
#   
#   START class Chat definition
#   
#####
#
#   Chat is a very simple subclass of the OpenAI API base class. That class contains
#   the essential methods for interacting with the API and handling the responses.
#   This class just needs to make a very small specialization so that it all works
#   correctly.
#
class Chat(OpenAIAPIBase):
    '''
    This class implements the OpenAI chat completions request
    
    Attributes:
        There are no new attributes, all are inhereited from the super class
    
    Methods:
        No new methods, all methods are inherited from the super class
    '''
    def __init__(self, name="Chat", *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, *args, **kwargs)
        #   These two are set at the OpenAIAPIBase() class level and do not need overriding
        #self.oai_api_method = OAI_API_METHOD
        #self.oai_api_version = OAI_API_VERSION
        self.oai_api_service = OAI_API_SERVICE      # only one that needs override right now
        #   Create the service endpoint part of the URL
        endpoint = "/"+self.oai_api_version+"/"+self.oai_api_service
        self.setServiceEndpoint(endpoint)
        self.setRPMRateLimit()
        self.setTPMRateLimit()
        self.throttlingOn()
        self.setContentType("application/json")
        self.setUserAgent()
        return 

#####
#   
#   END class Chat definition
#   
#####

if __name__ == '__main__':
    print("Chat.py is a class with no main()")



