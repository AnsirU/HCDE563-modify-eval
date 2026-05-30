#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: Transcription.py
#   REVISION: December, 2024
#   CREATION DATE: April, 2023
#   AUTHOR: David W. McDonald
#
#   A web service example that implements the 'audio/transcriptions' endpoint of OpenAI. Documentation
#   of this part of the API can be found at:
#   
#   https://platform.openai.com/docs/api-reference/audio/create
#   and
#   https://platform.openai.com/docs/guides/speech-to-text
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
OAI_API_SERVICE = "audio/transcriptions"
#
#####
#   
#   START class Transcription definition
#   
#####
class Transcription(OpenAIAPIBase):
    '''
    This class implements the OpenAI transcription request
    
    Attributes:
        There are no new attributes, all are inhereited from the super class
    
    Methods:
        No new methods, all methods are inherited from the super class
    '''
    def __init__(self, name="Transcription", *args, **kwargs):
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
        self.setRPMRateLimit(50)            # audio maxes out at 50 RPM for all account types
        self.setTPMRateLimit(1000)          # the TPM (tokens) limit isn't used for audio
        self.throttlingOn()
        #self.setContentType("application/json")
        #self.setContentType("multipart/form-data")
        self.setUserAgent()
        return    
    

#    ##
#    #   A convenience routine that makes sure that the payload corresponds to this service
#    #
#    def newRequestPayload(self):
#        payload = RequestDataFiles(self.oai_api_service)
#        # The only model right now for transcription
#        payload.setModel('whisper-1')
#        # This temperature allows the transcriber to auto adjust
#        payload.setTemperature(0.0)
#        return payload


#####
#   
#   END class Transcription definition
#   
#####

if __name__ == '__main__':
    print("Transcription.py is a class with no main()")


