#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: OpenAIAPIBase.py
#   REVISION: June, 2024
#   CREATION DATE: April, 2023
#   AUTHOR: David W. McDonald
#
#   A web service class that provides access to the OpenAI LLM service interface. This is a base 
#   class that will be subclassed for specific request types.
#
#   The OpenAI models have different rate limits. The combination of requests per minute and 
#   tokens per minute throttling make adherence a little complex. This class does the best it
#   can to adhere to the limits and prevent problems. Here is a link to the current limits:
#   https://platform.openai.com/docs/guides/rate-limits/overview
#
#   This base class rate limit will be set to 60 RPM (requests per minute). This should work for
#   the primary use cases of Text, Chat, and Embeddings. Once an account has been approved and
#   making requests - the limits can be changed
#
#   
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#

import sys, time, datetime, json, copy
#
#   This allows us to put a lock on attribute variables when we need
from threading import Semaphore
#
#   This class is a sub-class of HTTPConnection
from rebert.classes.base.HTTPConnection import HTTPConnection
#
#   Need to know something about the type of payloads that are sent in a request
from rebert.classes.OpenAI.payload.ChatRequestPayload import ChatRequestPayload
from rebert.classes.OpenAI.payload.TranscriptionPayload import TranscriptionPayload


#####
#   
#   CONSTANTS
#   
#####
#
#   This is the base number of seconds used in an exponential backoff
THROTTLE_BACKOFF_SECONDS = 0.3
#
#   The number of "clean" or non-errored responses before the backoff
#   counter is decreased.
BACKOFF_REDUCTION_THRESHOLD = 3
#
#   The default method for OpenAI API request is a POST
OAI_API_METHOD = "POST"
#
#   The current default version is 'v1' for everything
OAI_API_VERSION = "v1"
#
#   Service is defined in the specific subclasses.
OAI_API_SERVICE = ""
#
#####
#   
#   START class OpenAIAPIBase definition
#   
#####
#
#
class OpenAIAPIBase(HTTPConnection):
    '''
    The OpenAIAPIBase class implements the basics of an OpenAI API call. This class is based 
    on the HTTPConnection class and can run either threaded or non-threaded.
    
    Attributes:
        There are a small number of attributes that should probably not be accessed directly 
        because they are likely to change the behaviors of the object.
    
    Methods:
        setRPMRateLimit()       - set the Requests Per Minute (RPM) rate limit
        setThrottleRate()       - override that sets the RPM rate limit 
        setTPMRateLimit()       - set the Tokens Per Minute (TPM) rate limit 
        
        setBearerToken()        - set the authorization token, API key, for requests
        setOrganizationID()     - set the Organization ID for requests
        
        getUsageStatus()        - produces a summary of usage for the last one minute window
        
        queueRequest()          - override of queueRequest() method to set the HTTP request
                                  method when the queue is called
        _throttleRequests_()    - override of base _throttleRequests_() to account for both
                                  TMP and RPM usage and backoff conditions
        _backoff_()             - implements a backoff counter that waits extra time when
                                  the API stars reporting errors
        _checkResponseValue_()  - checks for error conditions for potential _backoff_()
                                  call, and tracks API token usage
        makeRequest()           - an override of the base makeRequest() method to ensure
                                  that responses are checked with _checkResponseValue_()
    '''
    def __init__(self, name="OpenAIAPIBase", *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, *args, **kwargs)

        self.setHost("https://api.openai.com")
        self.oai_api_method = OAI_API_METHOD
        self.oai_api_version = OAI_API_VERSION
        self.oai_api_service = OAI_API_SERVICE
        
        self.oai_requests_per_minute = 60    # default RPM
        self.oai_tokens_per_minute = 250000  # default TPM
        
        self.oai_api_request_throttle = (60.0/float(self.oai_requests_per_minute))
        self.oai_api_token_throttle = (60.0/float(self.oai_tokens_per_minute))
        
        self.oai_api_throttle_backoff = 0    # number of backoffs
        self.oai_api_throttle_clean = 0      # counts the number of clean requests
        
        self.oai_last_request_at = None      # timestamp of last request
        self.oai_usage_list = list()         # list of usage data
        self.sem_usage_status = Semaphore(1) # semaphore to control access to usage
        
        #
        #   Something like this belongs in every service subclass of this base object
        #
        #self.oai_api_method = OAI_API_METHOD
        #self.oai_api_version = OAI_API_VERSION
        #self.oai_api_service = OAI_API_SERVICE
        # create the service endpoint part of the URL
        #endpoint = "/"+self.oai_api_version+"/"+self.oai_api_service
        #self.setServiceEndpoint(endpoint)
        #self.setRPMRateLimit()
        #self.setTPMRateLimit()
        #self.throttlingOn()
        #self.setContentType("application/json")
        #self.setUserAgent()
        return
    
    
    
    ##
    #   Allows changing the default RPM (Requests Per Minute). This value depends
    #   on your account with OpenAI. Default values are for a 'pay-as-you-go' account
    #   account in it's first 48 hours of existence. Once your account is established
    #   there are higher rate limits. 
    #
    def setRPMRateLimit(self, rpm=60.0):
        '''
        Set the requests per minute rate and throttle values.
        
        This method sets the number of requests that can be made per minute. The
        default is the base level for an initial account opening and can be increased
        as the account passes the OpenAI usage thresholds.
        
        Parameters:
        rpm         : number of requests per minute (float) (optional)
        '''
        self.log(f"entering rpm={rpm:4.1f}", level="DEBUG")
        if rpm <= 0: rpm = 60
        self.oai_requests_per_minute = rpm
        self.oai_api_request_throttle = (60.0/float(self.oai_requests_per_minute))
        mesg = f"set oai_api_request_throttle={self.oai_api_request_throttle:4.1f}"
        self.log(f"returning {mesg}", level="DEBUG")
        return


    ###
    #   This method overrides the default throttle setting to work with the
    #   throttling approach the OpenAI API.
    #
    def setThrottleRate(self, rpm=60.0, rps=1.0):
        '''
        Set the throttling rate either with requests per second or requests per minute.
        
        This method override calls self.setRPMRateLimit() to set the requests per
        minute value for the OpenAI API.
        
        Parameters:
        rpm         : number of requests per minute (float) (optional)
        rps         : number of requests per second (float) (optional)
        '''
        self.log(f"entering", level="DEBUG")
        if rpm > 0.0:
            self.setRPMRateLimit(rpm)
        elif rps >= 0.0:
            rpm = 60.0 * rps
            self.setRPMRateLimit(rpm)
        else:
            self.log(f"rps and rpm were out of bounds, setting base rate limit.", 
                     level="DEBUG")
            self.setRPMRateLimit(rpm)
        self.log(f"returning", level="DEBUG")
        return


    ##
    #   Allows changing the default TPM (Tokens Per Minute). This value is different depending
    #   on your account with OpenAI. The basic values defined above are for a 'pay-as-you-go' account
    #   in it's first 48 hours of existence. Once you have your account longer there are higher
    #   rate limits that you can set. 
    #
    def setTPMRateLimit(self, tpm=250000.0):
        '''
        Set the tokens per minute rate and throttle values.
        
        This method sets the number of tokens per minute that can be consumed/used
        by API requests. 
        
        Parameters:
        tpm         : number of tokens per minute (float) (optional)
        '''
        self.log(f"entering tmp={tpm:7.1f}", level="DEBUG")
        if tpm <= 0: tpm = 250000.0
        self.oai_tokens_per_minute = tpm
        self.oai_api_token_throttle = (60.0/float(self.oai_tokens_per_minute))
        mesg = f"set oai_api_token_throttle={self.oai_api_token_throttle:4.1f}"
        self.log(f"returning {mesg}", level="DEBUG")
        return
        
    
    ##
    #   The OpenAI documentation sometimes calls the token an API Key, but the
    #   API actually usees bearer token authentication. This method reflects 
    #   their authentication approach.
    #
    def setBearerToken(self, token=""):
        '''
        Set bearer token for the API
        
        OpenAI uses a bearer token authorization model. The token should be the
        one you were assigned when you set up your OpenAI account.
        
        Parameters:
        token         : the API token issued to your account
        '''
        bearer_str = ""
        if token:
            bearer_str = f"Bearer {token}"
        self.setAuthorization(bearer_str)
        return
    
    
    ##
    #   This allows the setting of the organization ID for a request. Everyone should have
    #   an organization ID that was created when they created their account with OpenAi.
    #
    #   The OpenAI standard is that organization ID is sent in the header of a request as:
    #   'OpenAI-Organization: <Organization_ID>' string
    #
    def setOrganizationID(self, oid=None):
        '''
        Set the Organization ID for the request.
        
        The Organization ID can be used to help track different projects
        
        Parameters:
        oid         : the Organization ID associated with the authentication token.
        '''
        if oid:
            self.setHeaderValue("OpenAI-Organization",oid)
        else:
            # an empty value removes the param
            self.setHeaderValue("OpenAI-Organization")
        return
    
    
    ##
    #   Retrieve the 'usage' records - a way of checking the status of the request object
    #
    def getUsageStatus(self):
        '''
        Retrieves a list of records containing the usage statistics for the API
        
        This method can tell you something about how much the API has been used
        based on the 1 minute windows of usage. This usage data is the basis for
        how throttling works. This is an approximation based on what is coming back
        from the API.
        
        Returns:
        A dictionary structure summarizing usage, with a short list of info about
        recent requests
        '''
        self.log(f"entering", level="DEBUG")
        usage = dict()
        with self.sem_usage_status:
            current = datetime.datetime.now()
            usage['current_time'] = str(current).partition('.')[0]
            if not self.oai_last_request_at:
                self.oai_last_request_at = current
            usage['last_request_at'] = str(self.oai_last_request_at).partition('.')[0]
            diff = current - self.oai_last_request_at
            # number of seconds remaining to the next one minute window
            remaining = 60.0
            if diff.total_seconds() > 0.0:
                remaining = 60.0 - diff.total_seconds()
            if remaining < 0.0:
                remaining = 0.0
            usage['seconds_since_last_request'] = diff.total_seconds()
            usage['seconds_to_reset'] = remaining
            #
            # First clean up an calculate the usage rate in the last minute. This is on the
            # careful side when estimating the 'last minute'
            oai_usage = list()
            total_requests = 0
            total_tokens = 0
            for use in self.oai_usage_list:
                use['age'] = current - use['timestamp']
                clean_use = use.copy()
                clean_use['age'] = use['age'].total_seconds()
                clean_use['timestamp'] = str(use['timestamp']).partition('.')[0]
                oai_usage.append(clean_use)
                if use['age'].total_seconds() > 60.0:
                    continue
                total_requests += 1
                if 'total_tokens' in use:
                    total_tokens = total_tokens + use['total_tokens']
            # show totals for the last one minute window
            usage['total_requests'] = total_requests
            usage['total_tokens'] = total_tokens
            if total_requests > 0:
                avg_tokens_per_request = total_tokens / total_requests
                usage['avg_tokens_per_request'] = avg_tokens_per_request
            else:
                avg_tokens_per_request = 1.0
                usage['avg_tokens_per_request'] = "undefined"
            usage['oai_rpm_limit'] = self.oai_requests_per_minute
            usage['oai_tpm_limit'] = self.oai_tokens_per_minute
            reqs_rem = self.oai_requests_per_minute - total_requests
            if reqs_rem > 0:
                # got to wait a few seconds to space out the remaining requests
                usage['rpm_throttle_wait'] = remaining/reqs_rem
            else:
                usage['rpm_throttle_wait'] = 60.0
    
            toks_rem = self.oai_tokens_per_minute - total_tokens
            if toks_rem > 0:
                usage['tpm_throttle_wait'] = remaining/toks_rem
            else:
                usage['tpm_throttle_wait'] = 60.0
            usage['usage_list'] = oai_usage
        self.log(f"returning", level="DEBUG")
        return usage
    
    
    ##
    #   Override - Sets a payload body for a request
    #
    def setRequestPayload(self, *args, **kwargs):        
        '''
        Sets a request payload or request body for the next request.
        
        A parameter argument without a key is accepted as a just generic data, and the parameter 
        type (ptype) is set to the default 'data'.
        
        Optional arguments
        payload:    accepts the parameter as generic data and sets the payload type as 'data'
        data:       accepts the parameter as generic data and sets the payload type as 'data'
        json:       accepts the parameter as a json thing and sets the payload type as 'json'
        '''
        #
        #   If any of these valid parameters are a ChatRequestPayload, or TranscriptionPayload
        #   then we try to convert it to something usable by the lower level
        if args:
            if isinstance(args[0],ChatRequestPayload):
                self.log(f"Moving ChatRequestPayload() from generic arg to 'data' param", level="DEBUG")
                chat = str(args[0])
                super().setRequestPayload(data=chat)
                return
            elif isinstance(args[0],TranscriptionPayload):
                self.log(f"Moving TranscriptionPayload() from generic arg to 'data' param", level="DEBUG")
                form = args[0].getFormMultiPartEncoded()
                super().setRequestPayload(data=form, nocopy=True)
                self.setContentType(form.content_type)
                return
        
        elif 'payload' in kwargs:
            if isinstance(kwargs['payload'],ChatRequestPayload):
                self.log(f"Moving ChatRequestPayload() from 'payload' param to 'data' param", level="DEBUG")
                chat = str(kwargs['payload'])
                super().setRequestPayload(data=chat)
                return
            elif isinstance(kwargs['payload'],TranscriptionPayload):
                self.log(f"Moving TranscriptionPayload() from 'payload' param to 'data' param", level="DEBUG")
                form = kwargs['payload'].getFormMultiPartEncoded()
                super().setRequestPayload(data=form, nocopy=True)
                self.setContentType(form.content_type)
                return
        
        elif 'data' in kwargs:
            if isinstance(kwargs['data'],ChatRequestPayload):
                self.log(f"Handling ChatRequestPayload() 'data' param", level="DEBUG")
                chat = str(kwargs['data'])
                super().setRequestPayload(data=chat)
                return
            elif isinstance(kwargs['data'],TranscriptionPayload):
                self.log(f"Handling TranscriptionPayload() 'data' param", level="DEBUG")
                form = kwargs['data'].getFormMultiPartEncoded()
                super().setRequestPayload(data=form, nocopy=True)
                self.setContentType(form.content_type)
                return
        
        elif 'json' in kwargs:
            if isinstance(kwargs['json'],ChatRequestPayload):
                self.log(f"Moving ChatRequestPayload() from 'json' param to 'data' param", level="DEBUG")
                chat = str(kwargs['json'])
                super().setRequestPayload(data=chat)
                return
            elif isinstance(kwargs['json'],TranscriptionPayload):
                self.log(f"Moving TranscriptionPayload() from 'json' param to 'data' param", level="DEBUG")
                form = kwargs['json'].getFormMultiPartEncoded()
                super().setRequestPayload(data=form, nocopy=True)
                self.setContentType(form.content_type)
                return        
        
        #   Otherwise, just pass it to our parent and hope it can do the right thing
        super().setRequestPayload(*args, **kwargs)    
        return



    ###
    #   This fixes a request that has been configured through the given accessor methods
    #   above. Once this is done the request can be considered to have been made and the
    #   request data is effectively immutable.
    #
    #   This creates a copy of the current request data and adds that to a request
    #   queue that is actually used to make the request when in a threaded mode
    #   This helps prevent the data from being accidentially changed by other threads
    #
    def queueRequest(self, method="GET", url=None, params=None, header=None, payload=None, ptype=None):
        '''
        Override of queueRequest method in HTTPConnection.
        
        This override will use the method assigned to the self.oai_api_method, which
        should be POST for basically every type of request. This code also checks that
        a payload has been set - because a payload is needed for just about everything.
        It then calls the super.queueRequest() version 
        
        Parameters:
        method:     the http method - should be GET or POST
        url:        the URL to use for this request - the host and any service endpoint
        params:     a dictionary of URL query string parameters and values
        header:     a dictionary of HTTP request header key:value pairs
        payload:    a payload (probably used when making POST requests)
        ptype:      a string 'type' for the payload "JSON" or "DATA" - used differently when POST-ing
        '''
        p = self.getRequestPayload()
        if not (payload or p['payload']):
            self.log(f"there is no payload for the request!", level="WARNING")
        super().queueRequest(method=self.oai_api_method, 
                             url=url, 
                             params=params, 
                             header=header, 
                             payload=payload, 
                             ptype=ptype)
        return
    
    
    ##
    #   This implements the throttling for the OpenAI requests. 
    #
    #   This counts the number of requests made in the last minute to track the RPM (requests per minute)
    #   usage rate-limits
    #
    #   As well, it considers the response usage and counts the tokens used in the last minute
    #
    #   This method cleans the oai_usage_list of everything that is older than 1 minute
    #
    def _throttleRequests_(self):
        '''
        Performs the throttling. That is, this sleeps the thread an amount to try to make sure
        that each request is spaced out to meet the rate limits..
        '''
        self.log(f"entering", level="DEBUG")
        self.log(f"throttling: {str(self.throttling)}", level="INFO")
        waits = 0.0
        current = datetime.datetime.now()
        if not self.oai_last_request_at:
            self.oai_last_request_at = current
        diff = current - self.oai_last_request_at
        # number of seconds remaining to the next one minute window
        remaining = 60.0
        if diff.total_seconds() > 0.0:
            remaining = 60.0 - diff.total_seconds()
        #
        # First clean up an calculate the usage rate in the last minute. This is on the
        # careful side when estimating the 'last minute'
        oai_usages = list()
        total_requests = 0
        total_tokens = 0
        with self.sem_usage_status: 
            for use in self.oai_usage_list:
                # if it's more than a minute old - ignore it
                if use['age'].total_seconds() > 60.0:
                    continue
                total_requests += 1
                if 'total_tokens' in use and (use['total_tokens'] > 0):
                    total_tokens = total_tokens + use['total_tokens']
                oai_usages.append(use)
            self.oai_usage_list = oai_usages
        #
        # if we are into the next window, don't bother to calculate a throttle
        if remaining <= 0.0:
            waits = 0.0
            self.log(f"wait: {waits}", level="INFO")
            self.log(f"returning", level="DEBUG")
            return
            
        if self.throttling:
            rpm_wait = 60.0 # worst case wait a minute
            tpm_wait = 60.0
            reqs_rem = self.oai_requests_per_minute - total_requests
            # no requests remaining, got to wait a whole minute
            if reqs_rem > 0:
                # got to wait a few seconds to space out the remaining requests
                rpm_wait = remaining/reqs_rem
            toks_rem = self.oai_tokens_per_minute - total_tokens
            if toks_rem > 0:
                tpm_wait = remaining/toks_rem
            #
            #   The backoff seconds
            bos = (2**self.oai_api_throttle_backoff)*THROTTLE_BACKOFF_SECONDS            
            if tpm_wait > rpm_wait:
                waits = tpm_wait + bos + 0.001  # add a small fudge factor
            else:
                waits = rpm_wait + bos + 0.001  # add a small fudge factor
            self.log(f"wait: {waits}", level="INFO")
            time.sleep(waits)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ##
    #   This _backoff_() method is called inside a makeRequest() to implement an exponential
    #   backoff on the request timing. That is, everytime an error happens, we assume it is
    #   rate limit related and increase the time we wait between requests.
    #
    def _backoff_(self, b=1):
        '''
        Increment/decrement a backoff counter when an API error happens.
        
        This method will increase or decrease a counter that is used to compute an
        additional amount of time to wait when API errors are happening. This backoff
        works to space out the requests over the one minute time windows.

        Parameters:
        b:     an integer backoff amount 1 to backoff, -1 to
        '''
        self.log(f"entering, {b:d}", level="DEBUG")
        self.oai_api_throttle_backoff = self.oai_api_throttle_backoff + b
        if self.oai_api_throttle_backoff < 0:
            self.oai_api_throttle_backoff = 0
        #print("_backoff_(%s)"%str(self.oai_api_throttle_backoff))
        self.log(f"returning, self.oai_api_throttle_backoff={self.oai_api_throttle_backoff} ",
                 level="DEBUG")
        return
    
    
    ##
    #   This method is called by the overridden makeRequest
    #
    def _checkResponseValue_(self, response=None):
        '''
        Check the response for an error.
        
        This method checks for an error condition and performs a backoff if there was an
        error in the response. This method also updates the usage information to track
        the total number of tokens being consumed.

        Parameters:
        response:     a response from a request that should be checked
        '''
        self.log(f"entering", level="DEBUG")
        resp_j = None
        resp_t = ""
        try:
            resp_j = response.json()
            self.log(f"json response", level="INFO")
        except Exception as e:
            resp_t = response.text
            self.log(f"handling response as text", level="INFO")
        
        if resp_j:
            if( 'error' in resp_j ):
                self.log(f"error condition in response", level="WARN")
                self.oai_api_throttle_clean = 0
                self._backoff_()    # Error condition, so increment the backoff
            else:
                #   No errors, so if we made more than BACKOFF_REDUCTION_THRESHOLD
                #   requests that had no errors, then we backoff and start a new
                #   count of clean/error free requests
                if self.oai_api_throttle_clean > BACKOFF_REDUCTION_THRESHOLD:
                    self._backoff_(b=-1)    # Reduce the backoff amount
                    self.oai_api_throttle_clean = 0
                else:
                    self.oai_api_throttle_clean += 1
            #
            #   We've got a dictionary response, now extract the usage and
            #   update the usage records to track our consumption/usage
            #
            #   Run through all of the usage records update their age
            with self.sem_usage_status:
                for use in self.oai_usage_list:
                    use['age'] = self.oai_last_request_at - use['timestamp']
            #   
            #   Create a new usage record to reflect usage for this response
            new_use = dict()
            new_use['age'] = datetime.datetime.now() - self.oai_last_request_at
            new_use['timestamp'] = self.oai_last_request_at
            if 'usage' in resp_j:
                if 'total_tokens' in resp_j['usage']:
                    new_use['total_tokens'] = resp_j['usage']['total_tokens']
                else:
                    new_use['total_tokens'] = -1
                if 'prompt_tokens' in resp_j['usage']:
                    new_use['prompt_tokens'] = resp_j['usage']['prompt_tokens']
                else:
                    new_use['prompt_tokens'] = -1
                if 'completion_tokens' in resp_j['usage']:
                    new_use['completion_tokens'] = resp_j['usage']['completion_tokens']
                else:
                    new_use['completion_tokens'] = -1
            else:
                self.log(f"the response is missing 'usage' informaiton", level="WARN")
            #
            #   Grab the semaphore and update the usage list
            with self.sem_usage_status:
                self.oai_usage_list.append(new_use)
        
        elif resp_t:
            #   Check for error conditions
            if( ("\"error\":" in resp_t) or ("'error':" in resp_t) ):
                self.log(f"error condition in response", level="INFO")
                self.oai_api_throttle_clean = 0
                self._backoff_()    # Error, so increment the backoff
            else:
                # clean - no errors
                if self.oai_api_throttle_clean > BACKOFF_REDUCTION_THRESHOLD:
                    self._backoff_(b=-1)    # Reduce the backoff amount
                    self.oai_api_throttle_clean = 0
                else:
                    self.oai_api_throttle_clean += 1
        else:
            pass
        self.log(f"returning", level="DEBUG")
        return
    
    
    ##
    #   This is an override of the default makeRequest() method. This can be called 
    #   once a request has been queued.
    #
    def makeRequest(self):
        '''
        This makes the OpenAI API request. This should work for all subclasses that
        make OpenAI API requests. 
        
        This is an override of the default makeRequest() method. This version helps
        manage the different forms of throttling.
        '''
        if self.isRequesting(): return
        try:
            self.setRequestingStatus(True)
            #   The local override of queueRequest() should ensure the 
            #   consistency of the request parameters before calling super()
            #
            #   THIS CAUSES DUPLICATE ENTRIES - USER MUST queueRequest() ITEM
            #   AFTER SETTING THE PAYLOAD
            #self.queueRequest()
            
            #   Note the time, we're going to make a request and we need to know
            #   so that we can track the time between each request
            self.oai_last_request_at = datetime.datetime.now()
            
            self.log("making a request", level="INFO")
            response = self._makeRequest_()
            if response:
                #   Put the response in the queue
                self.queueResponse(response)
                self._checkResponseValue_(response)
                 
            self.setRequestingStatus(False)
        except Exception as ex:
            self.setRequestingStatus(False)
            raise ex
        return 
        
#####
#   
#   END class OpenAIAPIBase definition
#   
#####

if __name__ == '__main__':
    print("OpenAIAPIBase.py is a class with no main()")
