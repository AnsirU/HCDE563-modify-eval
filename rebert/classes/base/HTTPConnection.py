#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: HTTPConnection.py
#   REVISION: March, 2024
#   CREATION DATE: March, 2012
#   Author: David W. McDonald
#
#   A base class for making web service requests. This class works to abstract away some of
#   the complexity of managing web services. The main idea is to subclass this to create a
#   class that is specialized for a specific web service or for working with a specific web
#   site. This class is designed to facilitate threading and attempts to manage the data for
#   each request to minimize possible race conditions on parameters of a request.
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
#
#   imports part of python
import sys, json, time, random, copy, logging, datetime
from threading import Semaphore
#
#   a module/package that needs to be installed
import requests
#
#
#   This HTTP connection object will allow threading, so we'll base it off our threading object
from rebert.classes.base.ThreadedObject import Object


#####
#   
#   CONSTANTS
#   
#####

#
#   A small list of 'user agent' strings. These are the strings set by a web browser to identify
#   itself to a web server. These are used to help ensure that the web server responds with an
#   a response. Some web servers are configured to ignore web requests from bots or code.
#
USER_AGENT_STRINGS = {
    "opera_2023"    : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 OPR/97.0.4719.17",
    "safari_2023"   : "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "edge_2023"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62",
    "firefox_2025"  : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "chrome_2023"   : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "arc_2025"      : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    # duplicates of the most recent - with simplified keys
    "opera"    : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 OPR/97.0.4719.17",
    "safari"   : "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "edge"     : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62",
    "firefox"  : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "chrome"   : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "arc"      : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
}
#
#   This structure stores the information necessary to make a request. This is used by the
#   queueRequestData() to collect and store queued data. The information in this record
#   is a copy of the information - to try and prevent any changes once the item has been
#   added to the queue
#
REQUEST_DATA_TEMPLATE = {
    'url'       : '',       # an associated host + service endpoint
    'params'    : None,     # a dictionary of key:value pairs that represent the parameters of the request, the query string
    'method'    : "GET",    # an HTTP method, for now either GET or POST
    'header'    : None,     # the HTTP request headers - as a dictionary of key:value pairs
    'payload'   : None,     # the payload some chunk of text
    'ptype'     : None      # the payload type, for now either 'JSON' or 'DATA'
}
#
#   This structure is used by the checkStatusCode() when some type of error condition is found in the
#   error watch dictionary. When a status code is found in error watch then the value associated with that
#   status code will be assigned to 'error_message'. There are some cases where an exception is set as the 
#   error condition.
#
ERROR_DATA_TEMPLATE = {
    'status_code'   : 0,    # http error code
    'exception'     : None, # maybe an exception
    'error_message' : ""    # any text of an error message
}
#
#   A template for the information that will be stored in the request status queue
#
STATUS_INFO_TEMPLATE = {
    'request'   : None,     # the request record
    'response'  : None,     # the response record
    'timestamp' : None,     # timestamp
    'error'     : None      # the error record
}
#
#   This is a generic error watch dictionary. The method checkStatusCode() will return one of these
#   for anything in a 400 or 500 range. A subclass should probably override and do something more
#   specific. As well, this does nothing for a range of status codes - some of which might (or might not)
#   be an error depending on the application
#
ERROR_WATCH_STATUS_CODES = {
    '4XX':  {
                'error': {
                    'message'   : 'A client error occurred - check the status code',
                    'code'      : 0
                }
            },
    '5XX':  {
                'error': {
                    'message'   : 'A server error occurred - check the status code',
                    'code'      : 0
                }
            }
}

#####
#   
#   START class HTTPConnection definition
#   
#####

class HTTPConnection(Object):
    '''
    The HTTPConnection class implements a threaded web connection. This allows potentially multiple requests
    to be performed at the same time - or to have other actions happen during a slow web request.
    
    Attributes:
        There are many attributes in this class. The important attributes should be accessed through the
        provided accessor methods to prevent race conditions on the values in the attribute variables
    
    Methods:
        setHost()                   - set the host (domain name) for the web service
        getHost()                   - get the host
        setServiceEndpoint()        - set an API service endpoint
        getServiceEndpoint()        - get the API service endpoint
        setRequestPath()            - friendly name for setting a service endpoint
        getRequestPath()            - friendly name for getting the endpoint
        
        setUserAgent()              - set the User-Agent header
        setContentType()            - set the Content-Type header
        setAuthorization()          - set the Authorization header - for key authentication
        setHeaderValue()            - set a header key:value pair
        getHeaderValue()            - get the current value for a header key
        getHeader()                 - get the current header dictionary
        clearHeader()               - reset/clear the header dictionary

        setRequestPayload()         - sets a request payload (request body) for the request
        getRequestPayload()         - returns the current request payload (request body)
        
        setRequestParam()           - set a request parameter, key:value pair
        getRequestParam()           - get the value of a parameter given a key
        deleteRequestParam()        - delete a parameter key:value pair
        getRequestParams()          - get a dictionary of the request parameters
        clearRequestParams()        - clear/reset the dictionary of request parameters
        
        queueRequest()              - append a copy of all the request values to the request queue
        queuedRequests()            - return the number of requests in the queue
        queueResponse()             - append a response to the current response queue
        
        responses()                 - return the count of the number of items in the response queue
        nextResponse()              - get the next response from the response queue
        
        _pushPriorRequest_()        - push info about a request/response onto a stack
        getPriorRequests()          - get the whole stack - a reverse chronological list
        priorRequestString()        - get a string the reflects the status of some recent requests
        
        parseResponseContinuation() - parse a response for request continuation information
        continuation()              - return the continuation information or None
        
        throttlingOn()              - turn on throttling for this object
        throttlingOff()             - turn off throttling for this object
        setThrottleRate()           - set the rate as either requests per second (rps) or requests per minute (rpm)
        _throttleRequests_()        - perform the throttling with a sleep
        
        setRequestingStatus()       - set the status to requesting (True) or not requesting (False)
        isRequesting()              - status of an on-going web request
        isRunning()                 - status of the object thread
        
        startThread()               - start this web request thread
        terminateThread()           - the method to cleanly exit/kill the thread
        startRequest()              - the way to activate a waiting/sleeping thread - will call makeRequest()
        run()                       - the run loop of the thread - what it does repeatedly
        waitRequest()               - allows another thread to wait/sleep while this one is making the request
        
        setErrorWatch()             - sets a dictionary of http status/error codes to watch for
        clearErrorWatch()           - clear/reset the error watch dictionary
        checkStatusCode()           - check an HTTP status code and note a possible error condition
        
        _makeRequest_()             - low-level requesting method - should be called from makeRequest()
        makeRequest()               - makes a web request is in the queue
    '''
    def __init__(self, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(*args, **kwargs)
        #
        #   If we set our own logger on this object, then we want to make sure that one gets used, so here 
        #   we disable the rather chatty "requests" logger - actually we just set it to the highest loglevel
        requests_logger = logging.getLogger("requests")
        requests_logger.setLevel(logging.CRITICAL)
        #
        #   Semaphores to control access by multiple threads to various data structures
        self.sem_resp_queue = Semaphore(1)      # semaphore for the response message queue
        self.sem_request_data = Semaphore(1)    # semaphore to prevent changes to the request_data
        self.sem_status_stack = Semaphore(1)    # semaphore for the status info stack
        self.sem_querying_status = Semaphore(1) # semaphore to control access to querying flag
        #
        self.running = False                        # when in threaded mode - is the thread running
        self.sem_running = Semaphore(1)             # semaphore for requesting activity - in thread mode
        self._request_queueing_releases_ = False    # this allows a thread to request when a request is queued
        #
        self.requesting_status = False      # whether or not a web request is currently being made 
        #
        self._request_host_ = ""            # the host/domain name
        self._service_endpoint_ = ""        # portion of a URL that says where on the host we find the service
        #
        self._request_header_ = dict()          # the headers - being prepared for a request
        self._request_params_ = dict()          # the request parameters - being prepared
        self._request_payload_ = None           # the request body or payload
        self._request_payload_ptype_ = None     # the type of thing that the payload is
        self._request_make_copy_ = True         # make a copy of the payload when queuing
        #
        self._request_queue_ = list()       # used when the request is set - ready to be made
        self._response_queue_ = list()
        self.max_request_queue = 25
        #
        self._prior_reqs_stack_ = list()    # keeps the status of prior reuqests/responses
        self.max_prior_reqs = 25
        #
        self.continuation = None            # if there is a recognized continuation in the response
        self._continuation_count_ = 0       # the number of continuation requests that have been queued
        self.max_continuations = 10         # the maximum number of continuations for any one initial request
        #
        self.last_error = None
        self.error_watch = dict()
        #
        self.throttling = False             # throttling on = True, throttling off = False
        self.last_throttle_check = None     # time of the last request/throttle check
        self.throttle_rps = 0.5             # 1/2 request per second (rps), 30 requests per minute
        self.throttle_wait = 2.0            # wait in seconds 
        #
        self.setErrorWatch(ERROR_WATCH_STATUS_CODES)
        return


    ##########
    #
    #   HOST/DOMAIN MANAGEMENT
    #
    ##########
    
    ###
    #   Sets the host for an http request
    #
    def setHost(self, host=None):
        '''
        Set the host for this web service or url request.
        
        Parameters:
        host:       a string hostname for the server
        '''
        if not host: 
            with self.sem_request_data:
                self._request_host_ = ""
            return
        #   throw away anything that looks like a query string - that's not part of a
        #   host/domain - That should be set as a param for the request
        host = host.partition('?')[0]
        hl = host.lower()
        #   make sure that this looks like a URL
        with self.sem_request_data:
            if hl.startswith("http://") or hl.startswith("https://"):
                self._request_host_ = host
            else:
                self._request_host_ = "https://"+host
        return
    
    ###
    #   Returns the current host for this http request
    #
    def getHost(self):
        '''Returns the web host.'''
        host = ""
        with self.sem_request_data:
            host = self._request_host_
        return host
    
    ###
    #   Sets the API service endpoint - this is the last part of a URL
    #
    def setServiceEndpoint(self, endpoint=None):
        '''
        Set an API service endpoint. This is the part of a URL string that shows the URL
        path to the place on the server where the request is to be made. Should not have the
        domain name (host) in it - and it should not include any query string portions
        
        Parameters:
        endpoint:   a string pointing to the server API endpoint
        '''
        if not endpoint: 
            with self.sem_request_data:
                self._service_endpoint_ = ""
            return
        #   remove any query string ending - that's not part of a service endpoint
        #   can't really clean the front without some more sophisticated URL hacking
        endpoint = endpoint.partition('?')[0]
        with self.sem_request_data:
            self._service_endpoint_ = endpoint
        return
    
    ###
    #   Returns the current service endpoint
    #
    def getServiceEndpoint(self):
        '''Returns the service endpoint - a URL string after the host name.'''
        endpoint = ""
        with self.sem_request_data:
            endpoint = self._service_endpoint_
        return endpoint
    
    
    ###
    #   Sets a request path - like just requesting a page from the server
    #
    def setRequestPath(self, path=None):
        '''
        Set the path to the page to request. 
        
        In the most simple case this is the web page path from the host to the
        web page. This is a convenience - it simply calls self.setServiceEndpoint()
        to set the path as the endpoint.
        
        Parameters:
        path:       a string of the web page to collect
        '''
        self.setServiceEndpoint(path)
        return
    
    ###
    #   Gets the request path
    #
    def getRequestPath(self):
        '''Returns the service endpoint - a URL string after the host name.'''
        return self.getServiceEndpoint()
        
    
    
    ##########
    #
    #   HEADER MANAGEMENT
    #
    ##########
    
    ###
    #   Set a user agent for the requests. The default used by requests is a robot/code
    #   user agent. That can result in some servers refusing to serve a request.
    #
    def setUserAgent(self, agent="random"):
        '''
        Set the 'User-Agent' header value.
        
        This sets a user agent to simulate a browser making a request - rather than the default
        requests user agent - which looks like a bot. Some web servers refuse to serve anything
        that might be a bot. This allows code to look something like a browser and at least get
        some response.
        
        Parameters:
        agent:      either 'random' or a key from the USER_AGENT_STRINGS dictionary
        '''
        if agent:
            # pick a random user agent from our list of agent strings
            if agent=="random":
                agent_list = list(USER_AGENT_STRINGS.keys())
                agent = agent_list[random.randrange(0,len(agent_list))]
            #
            # if the agent is not a key we know - remove this key:value from the headers
            if agent not in USER_AGENT_STRINGS:
                self.setHeaderValue(key="User-Agent", val=None)
                self.log(f"Removed 'User-Agent' field from header", level="DEBUG")
                return
            #
            # everything looks good - set the agent as something we know
            self.setHeaderValue(key="User-Agent", val=USER_AGENT_STRINGS[agent])
            self.log(f"Set 'User-Agent' field to '{agent}'", level="DEBUG")
        else:
            # no agent supplied - delete the key from our headers
            self.setHeaderValue(key="User-Agent", val=None)
            self.log(f"Removed 'User-Agent' field from header", level="DEBUG")
        return
    
    ###
    #   Sets the header value of the content type. The default is "text/html".
    #   Generally, the value for content type tells a server how to structure or format
    #   the response.
    #
    def setContentType(self, ctype="text/html"):
        '''Set the 'Content-Type' request header value. Default is 'text/html'. '''
        self.setHeaderValue(key="Content-Type",val=ctype)
        return
    
    ###
    #   Sets the 'Authorization' header value. This is one of the ways that an API Key
    #   is sent to a server. You still have to format the auth with "Bearer <key>"
    #   to make this work.
    #
    def setAuthorization(self, auth=""):
        '''Set the 'Authorization' request header value. '''
        self.setHeaderValue(key="Authorization",val=auth)
        return
    
    ###
    #   Sets an arbitrary header keyword or key:value pair
    #
    def setHeaderValue(self, key=None, val=None):
        '''
        Set a URL request header key:value.
        
        Parameters:
        key:        the header key (str)
        val:        the value to associate with the header key
        '''
        if not key: return
        with self.sem_request_data:
            if val:
                self._request_header_[key] = val
            else:
                if key in self._request_header_:
                    del self._request_header_[key]
        return

    ###
    #   Returns the value currently set for a parameter
    #
    def getHeaderValue(self, key=None):
        '''
        Get the value currently associated with the header key (or None).
        
        Parameters:
        key:        the header key for which you want to see the value

        returns:    the value or None
        '''
        if not key: return None
        val = None
        with self.sem_request_data:
            if key in self._request_header_ :
                val = self._request_header_[key]
        return val

    ###
    # Returns a copy of the complete header information
    #
    def getHeader(self):
        '''Returns the complete dictionary of header key:value pairs.'''
        header = dict()
        with self.sem_request_data:
            header = self._request_header_.copy()
        return header

    ###
    #   Clears all request header data - reset
    #
    def clearHeader(self):
        '''Clears and resets the header dictionary to an empty dictionary.'''
        with self.sem_request_data:
            self._request_header_ = dict()
        return
    
    
    
    
    ##########
    #
    #   REQUEST BODY (PAYLOAD) MANAGEMENT
    #
    ##########
    
    ##
    #   Sets a payload body for a request
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
        # if they pass one thing and don't specify then take it as is
        if args and len(args) <= 2:
            with self.sem_request_data:
                self._request_payload_ = args[0]
                self._request_payload_ptype_ = "DATA"
                #   Only look at the second param if it exists
                #   It should be the 'copy' or 'nocopy' param
                if (len(args) == 2) and args[1]:
                    self._request_make_copy_ = True
                else:
                    self._request_make_copy_ = False
            return
        
        if 'copy' in kwargs:
            if kwargs['copy']:
                self._request_make_copy_ = True
            else:
                self._request_make_copy_ = False
        
        if 'nocopy' in kwargs:
            if kwargs['nocopy']:
                self._request_make_copy_ = False
            else:
                self._request_make_copy_ = True
        
        if 'payload' in kwargs:
            with self.sem_request_data:
                self._request_payload_ = kwargs['payload']
                self._request_payload_ptype_ = "DATA"
            return
        
        if 'data' in kwargs:
            with self.sem_request_data:
                self._request_payload_ = kwargs['data']
                self._request_payload_ptype_ = "DATA"
            return
              
        if 'json' in kwargs:
            with self.sem_request_data:
                self._request_payload_ = kwargs['json']
                self._request_payload_ptype_ = "JSON"
            return
        
        # none of the conditions are met - remove the payload
        with self.sem_request_data:
            self._request_payload_ = None
            self._request_payload_ptype_ = None
        return
    
    ##
    #   Returns the current payload as a dict with payload and ptype
    #
    def getRequestPayload(self):
        '''
        Returns a dictionary consisting of the request payload (request body) and the associated ptype.
        '''
        result = dict()
        with self.sem_request_data:
            result['payload'] = self._request_payload_
            result['ptype'] = self._request_payload_ptype_
        return result
    
    
    
    
    ##########
    #
    #   REQUEST PARAMETER MANAGEMENT
    #
    ##########
    
    ###
    #   Sets the value for a service request parameter - these are the key:value pairs
    #   that are part of the URL when making a service rquest
    #
    #   Interesting quirk about this setter method - if 'val' is any of the python empty
    #   values - 0, False, "", etc - then the parameter key will be removed - the general
    #   idea is that if a value is an empty value then we probably don't need that parameter
    #   There are some APIs for which this might not work - that would be a later fix
    #
    def setRequestParam(self, key=None, val=None):
        '''
        Set a URL query/request parameter.
        
        Parameters:
        key:        the parameter key (str)
        val:        the value to associate with the key
        '''
        if not key: return
        with self.sem_request_data:
            if val:
                self._request_params_[key] = val
                #   Try not to put api keys into a log file
                if 'key' in key.lower():
                    self.log(f"set param: {key} = <value_hidden>", level="DEBUG")
                else:
                    self.log(f"set param: {key} = {str(val)}", level="DEBUG")
            else:
                if key in self._request_params_ :
                    del self._request_params_[key]
                    self.log(f"deleted param key: {key}", level="DEBUG")
        return
    
    ###
    #   Returns the value currently set for a parameter
    #
    def getRequestParam(self, key=None):
        '''
        Get the value currently associated with the parameter key (or None).
        
        Parameters:
        key:        the parameter key for which you want to see the value

        returns:    the value or None
        '''
        if not key: return None
        val = None
        with self.sem_request_data:
            if key in self._request_params_ :
                val = self._request_params_[key]
        return val
    
    ###
    #   Removes the key from the set of parameters
    #
    def deleteRequestParam(self, key=None):
        '''
        Delete a parameter key and any associated value.
        
        Parameters:
        key:        the parameter key for which you want to see the value        
        '''
        if not key: return
        self.setRequestParam(key=key,val=None)
        return
    
    ###
    #   Returns a copy of the http request parameters, keys and values
    #
    def getRequestParams(self):
        '''Returns the complete dictionary of request parameter key:value pairs.'''
        params = dict()
        with self.sem_request_data:
            params = copy.deepcopy(self._request_params_)
        return params
    
    ###
    #   Clears all request parameters - reset
    #
    def clearRequestParams(self):
        '''Clears and resets the parameter dictionary to an empty dictionary.'''
        with self.sem_request_data:
            self._request_params_ = dict()
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
        Collect all of the url, method, header, parameter and payload information into a dictionary
        and push that information into a request queue.
        
        This code is used to 'fix' a request. The basic idea is to prevent accidental changes to the
        request information when the code is running in a threaded mode. This code attempts to make
        copies of everything before pushing it into the queue. It looks for the parameters and will use
        those if they are included - but is meant to be based on the information set on the current
        object.
        
        Parameters:
        method:     the http method - should be GET or POST
        url:        the URL to use for this request - the host and any service endpoint
        params:     a dictionary of URL query string parameters and values
        header:     a dictionary of HTTP request header key:value pairs
        payload:    a payload (probably used when making POST requests)
        ptype:      a string 'type' for the payload "JSON" or "DATA" - used differently when POST-ing
        '''
        self.log("entering", level="DEBUG")
        if len(self._request_queue_) >= self.max_request_queue:
            self.log(f"the request queue has exceeded the limit of {self.max_request_queue} items, not adding request item")
            raise Exception(f"The request queue has exceeded the limit of {self.max_request_queue} items")
            return
        
        self.sem_request_data.acquire()
        request_data = REQUEST_DATA_TEMPLATE.copy()
        #
        #   Check the method first
        if method:
            mu = method.upper()
            if mu in ['GET', 'POST']:
                request_data['method'] = mu
            else:
                self.sem_request_data.release()
                raise Exception("queueRequest() must have a 'GET' or 'POST' method").with_traceback()
                return
        else:
            self.sem_request_data.release()
            raise Exception("queueRequest() must have a 'GET' or 'POST' method").with_traceback()
            return
        #
        #   Now, consider the URL 
        if url:
            # the URL is a call parameter
            request_data['url'] = copy.copy(url)
        else:
            # set the URL based on the values for the host and any service endpoint
            url = copy.copy(self._request_host_)
            if self._service_endpoint_:
                url = url + copy.copy(self._service_endpoint_)
            request_data['url'] = url

        #
        #   Set the request header
        if header:
            request_data['header'] = copy.copy(header)
        else:
            request_data['header'] = copy.copy(self._request_header_)


        #
        #   Next, set the params
        if params:
            if isinstance(params, str):
                if params.startswith('?') or request_data['url'].endswith('?'):
                    request_data['url'] = request_data['url'] + copy.copy(params)
                else:
                    request_data['url'] = request_data['url']+"?"+copy.copy(params)                
            else:
                request_data['params'] = copy.copy(params)
        else:
            request_data['params'] = copy.deepcopy(self._request_params_)
        
        #
        #   Handle any request body - or payload
        if payload:
            request_data['payload'] = payload
            request_data['ptype'] = "DATA"
            if ptype and (ptype.upper() == "JSON"):
                request_data['ptype'] = "JSON"
        else:
            if self._request_make_copy_:
                request_data['payload'] = copy.deepcopy(self._request_payload_)
                request_data['ptype'] = copy.copy(self._request_payload_ptype_)
            else:
                request_data['payload'] = self._request_payload_
                request_data['ptype'] = self._request_payload_ptype_
        
        #
        #   Lastly, add this request data to the end of the request queue
        self._request_queue_.append(request_data)
        self.log(f"request queue has {len(self._request_queue_)} items.",level="DEBUG")
        self.sem_request_data.release()
        #
        #   If this is running in the threading mode - and we've set the auto release
        #   flag, then release the thread and allow it to make the next request
        if self.running and self._request_queueing_releases_:
            self.log("releasing requesting thread", level="DEBUG")
            self.sem_running.release()
        self.log("returning", level="DEBUG")
        return
    
    
    ###
    #   Return the number of items in the request queue. This could be good for automating
    #   sequential requests in makeRequest()
    #
    def queuedRequests(self):
        '''Returns the number of items in the waiting request queue.'''
        count = 0
        with self.sem_request_data:
            count = len(self._request_queue_)
        return count
    
    
    
    
    ##########
    #
    #   RESPONSE QUEUE/LIST MANAGEMENT
    #
    ##########
    
    ###
    #   Just add a response to the response queue
    #
    def queueResponse(self, resp=None):
        '''
        Appends one item to the response queue.
        
        The object maintains a response/message queue that is used to decouple a requesting thread from
        any other code that might want the results of an http request. This method adds (appends) one 
        new item to the end of the queue.
        
        Parameters:
        resp        : the item to append to the end of the queue
        '''
        if not resp: return
        with self.sem_resp_queue:
            self._response_queue_.append(resp)
        self.log(f"added one item (remaining: {len(self._response_queue_)})",
                level="DEBUG")
        return

    ###
    #   Return the number of items in the response queue
    #
    def responses(self):
        '''Returns the count of the number of responses waiting in the queue.'''
        count = 0
        with self.sem_resp_queue:
            count = len(self._response_queue_)
        return count

    ###
    #   Return the next item in the response queue
    #
    def nextResponse(self, flush=False):
        '''
        Returns one item from the response queue.
        
        The object maintains a response/message queue that is used to decouple a requesting thread from
        any other code that might want the results of an http request. This method returns one item from
        the message queue.
        
        Parameters:
        flush       : when flush is True, the response queue is emptied

        returns     : a list of STATUS_INFO_TEMPLATE dictionary items
        '''
        data = None
        with self.sem_resp_queue:
            if len(self._response_queue_) > 0 :
                data = self._response_queue_[0]
                self._response_queue_ = self._response_queue_[1:]
                self.log(f"returning one item (remaining: {len(self._response_queue_)})",
                         level="DEBUG")
                if flush:
                    self._response_queue_ = list()
                    self.log(f"flushing the response queue (remaining: 0)",
                             level="DEBUG")
            else:
                self.log(f"no items in queue, returning None",
                         level="DEBUG")
        return data
    
    
    
    
    ##########
    #
    #   STATUS INFORMATION STACK
    #
    ##########
    
    ##
    #   push a prior request status item onto the status stack
    #
    def _pushPriorRequest_(self, req=None, resp=None, error=None):
        '''
        Push (completed) request information onto a status stack.
        
        This method will push status information onto a stack with a limited depth. The request status 
        includes the request information, the response, and any error detected.
                
        Parameters:
        req         : the HTTP request information as a REQUEST_DATA_TEMPLATE type dictionary
        resp        : the response returned from the request
        error       : any error as an ERROR_DATA_TEMPLATE dictionary, or None 
        '''
        self.log("entering", level="DEBUG")
        r = STATUS_INFO_TEMPLATE.copy()
        r['request'] = req
        r['response'] = resp
        r['error'] = error
        r['timestamp'] = str(datetime.datetime.now()).partition('.')[0]
        prior = list()
        prior.append(r)
        with self.sem_status_stack:
            prior.extend(self._prior_reqs_stack_)
            if len(prior) > self.max_prior_reqs:
                self._prior_reqs_stack_ = prior[:self.max_prior_reqs]
                self.log(f"max stack depth exceeded, trimmed stack", level="DEBUG")
            else:
                self._prior_reqs_stack_ = prior
        self.log(f"returning (depth: {len(self._prior_reqs_stack_)}/{self.max_prior_reqs})", 
                 level="DEBUG")
        return

    ##
    #   This returns the list of prior request status information
    #
    def getPriorRequests(self, flush=False):
        '''
        Returns the complete set of status info in reverse chronological order (most recent first).
        
        Parameters:
        flush       : when flush is True, the stack is empied

        returns     : a list of STATUS_INFO_TEMPLATE dictionary items
        '''
        data = list()
        with self.sem_status_stack:
            if len(self._prior_reqs_stack_) > 0:
                data = self._prior_reqs_stack_
                if flush:
                    self._prior_reqs_stack_ = list()
        return data
    
    
    ##
    #   Generates a printable string summary of the prior request info stack
    #
    def priorRequestString(self, depth=10):
        '''
        Returns a string that shows basic information of the prior request stack.
        
        Parameters:
        depth       : indicates how far down to go in the stack
        '''
        status_str = str()
        if len(self._prior_reqs_stack_) > 0:
            with self.sem_status_stack:
                prior = 0
                if depth < len(self._prior_reqs_stack_):
                    status_str = status_str + f"Showing {depth} of {len(self._prior_reqs_stack_)} prior requests ({self.max_prior_reqs})\n"
                else:
                    status_str = status_str + f"Showing {len(self._prior_reqs_stack_)} of {len(self._prior_reqs_stack_)} prior requests (max:{self.max_prior_reqs})\n"
                status_str = status_str + f"     TIMESTAMP             CODE  METHOD URL\n"
                for rec in self._prior_reqs_stack_:
                    try:
                        status_str = status_str + f"{prior:3}: [{rec['timestamp']}] {rec['response'].status_code:<5} {rec['request']['method']:<6} {rec['request']['url']}\n"
                    except:
                        status_str = status_str + f"{prior:3}: [{rec['timestamp']}] {rec['response'].status_code:<5} {rec['request']['method']:<6} <HOST/URL NOT FOUND>\n"
                    prior -= 1
                    depth -= 1
                    if not depth: break
        return status_str
    
    
    
    
    ##########
    #
    #   CONTINUATION MANAGEMENT
    #
    ##########
    
    
    ##
    #   This method takes a response and performs a check to see if there is any continuation data in the
    #   response. If there is continuation data then "self.continuation" should be set to an appropriate value
    #
    #   If a check of the response shows that there is no continuation data then the value of self.continuation
    #   should be set to None - so that a check of hasContinuation() returns a None/False value when there is
    #   no continuation data
    #
    def parseResponseContinuation(self, response=None):
        '''
        Processes a response to look for continuation information.
        
        When an API has responses that are paged and parameters for the 'next' page is part of each response, this 
        method should parse a response, extract the parameters, or a continuation string and save that in the
        self.coninuation attribute of the object.
        
        This method should be overridden by subclasses that need this behavior. The default behavior is to reset
        the self.continuation attribute to None.
        
        Parameters:
        response    : an http response that should be parsed for possible continuation info
        '''
        self.continuation = None
        return

    ##
    #   This returns the value of "self.continuation" variable. Should be something useful if there is continuation
    #   data in the response. Should be None/False otherwise
    #
    def continuation(self):
        '''Returns the set of continuation parameters or a continuation string.'''
        return self.continuation
    
    
    
    
    ##########
    #
    #   REQUEST THROTTLE MANAGEMENT
    #
    ##########
    
    ###
    #   Turn on throttling for the requests
    #
    def throttlingOn(self):
        '''Turn ON http request throttling.'''
        self.throttling = True
        return

    ###
    #   Turn on throttling for the requests
    #
    def throttlingOff(self):
        '''Turn OFF http request throttling.'''
        self.throttling = False
        return

    ###
    #   Set a throttling rate as either requests per minute or requests per second
    #
    def setThrottleRate(self, rpm=0.0, rps=0.0):
        '''
        Set the throttling rate either with requests per second or requests per minute.
        
        While both parameters are technically optional - you probably want to use one of them when
        setting the throttling rate. If neither rps or rpm is a value greater than zero then the
        default is 1/2 request per second (or 30 requests per minute)
        
        Parameters:
        rpm         : number of requests per minute (float) (optional)
        rps         : number of requests per second (float) (optional)
        '''
        self.log(f"entering", level="DEBUG")
        self.log(f"rpm={rpm:4.1f} rps={rps:4.1f}", level="DEBUG")
        if rps <= 0:
            if rpm > 0:
                rps = float(rpm)/60.0
            else:
                # defaults to 1/2 request per second, 2 second wait
                rps = 0.5
        
        # now, how long to wait, 1.0/rps == seconds per request
        self.throttle_rps = rps
        self.throttle_wait = 1.0/rps + 0.001    # add a small fudge factor
        mesg = f"setting: throttle_rps={self.throttle_rps:4.1f} "
        mesg = mesg + f"throttle_wait={self.throttle_wait:1.4f}"
        self.log(mesg, level="DEBUG")
        self.log(f"returning", level="DEBUG")
        return
    
    ###
    #   Possibly force the thread to sleep based on the amount of time since last request
    #
    def _throttleRequests_(self):
        '''
        Performs the throttling. That is, this sleeps the thread an amount to ensure the time between
        each request is the minimum specified.
        '''
        self.log(f"entering", level="DEBUG")
        self.log(f"throttling: {str(self.throttling)}", level="DEBUG")
        throttle_check = datetime.datetime.now()
        wait = 0.0
        if self.throttling:
            #   A one-off query will not get stopped here
            if self.last_throttle_check:
                diff = throttle_check - self.last_throttle_check
                diff_secs = diff.total_seconds()
                #   Has not been enough time between last query and this one
                if diff_secs < self.throttle_wait:
                    #   Wait the amount of time to make up for the difference
                    wait = self.throttle_wait - diff_secs
                    self.log(f"slept {wait:1.4f} seconds", level="DEBUG")
                    time.sleep(wait)
        #   Update to the new time, reflect the time after waiting
        #   or not waiting if we didn't need to wait
        self.last_throttle_check = datetime.datetime.now()
        self.log(f"returning", level="DEBUG")
        return
    
    
    
    
    ##########
    #
    #   ACTIVITY STATUS
    #
    ##########
    
    
    ##
    #   Sets the requesting status - default is to set it to True
    #
    def setRequestingStatus(self, status=True):
        '''
        Set the requesting status. This indicates whether this object is in the process of making an http request.
        
        Parameters:
        status      : boolean True should be set just before starting a request, set to False once completed
        '''
        with self.sem_querying_status:
            self.requesting_status = status
        return
    
    ##
    #   If an object is in the process of making a request - this flag should be used to keep
    #   a thread from launching a new request - until this on finishes - overrides of makeRequest()
    #   should always check this before actually starting a new request
    #
    def isRequesting(self):
        '''Returns True if this object is in the process of making an http request.'''
        with self.sem_querying_status:
            status = self.requesting_status
        return status
    
    ##
    #   Status of the request thread, if this is running as a thread then this is True
    #
    def isRunning(self):
        '''Returns True if this object is operating as a thread - and running.'''
        return self.running
    
    
    
    
    ##########
    #
    #   THREADING CONTROL
    #
    ##########
    
    
    ##
    #   This start method is an override to make sure that our own self.running variable is set to True before the
    #   run() method is called by the start() method in multiprocessing.Process
    #
    def startThread(self, d=True):
        '''Initializes the threading to the running state and grabs a semaphore to protect the run() loop.'''
        # already running - then return
        if self.running: return
        self.sem_running.acquire()
        # the default is to put the thread into daemon mode, which suppresses output other than logging
        self.daemon = d
        self.running = True         # this makes sure the run() loop keeps looping, until set to False
        self.start()                # this launches the (new) thread and calls the run() method
        return

    ##
    #   This terminate is just a simple override to make sure that our own self.running variable is set to False before 
    #   the thread is terminated.
    #
    def terminateThread(self):
        '''Cleans up a running thread and allows everything to stop - potentially exit cleanly.'''
        # if we're not running - then we're done
        if not self.running: return
        # while we're still making a request - sleep and check back
        while self.isRequesting():
            time.sleep(1.0)
        # setting the self.running flag to False will terminate the thread
        self.running = False
        self.sem_running.release()
        return

    ##
    #   This releases a semaphore lock to allow the waiting thread to make the actual request. When this is being run as
    #   a thread - this is the way to have the thread issue requests.
    #
    def startRequest(self):
        '''This allows a running thread to acquire the semaphore - and call makeRequest().'''
        self.sem_running.release()
        return

    ##
    #   This run method simply waits for the blocking semaphore to be released - and then it issues the request. This is
    #   a required override for an object that implements threadeing
    #
    def run(self):
        '''Initializes the threading to the running state and grabs a semaphore to protect the run() loop.'''
        try:
            # setting the self.running flag to False will terminate the thread
            while( self.running ):
                # this thread will wait here until 
                self.sem_running.acquire()
                self.makeRequest()
        except:
            self.running = False
            raise
        return
    
    ##
    #   This idiom is used frequently for asynchronous requests. The thread calling this wait, should *NOT* be called by 
    #   *THIS* thread or the web request will end up in deadlock!
    #
    def waitRequest(self,wait=5.0):
        '''
        This method sleeps a thread for a short time - waiting for a request to complete.
        
        Parameters:
        wait        : number of seconds to wait betweed checks on the response queue
        '''
        time.sleep(1.0)
        while( (self.responses()<1) and self.isRequesting() ):
            time.sleep(wait)
        return



    ##########
    #
    #   ERROR HANDLING
    #
    ##########
    
    
    ##
    #   This method sets an error watch dictionary - a set of http status codes that indicate
    #   specific status codes and the error messages that should be associated with them. The
    #   default is to add new codes
    #
    def setErrorWatch(self, error_watch=None, update=True):
        '''
        Sets or updates the error watch dictionary.
        
        Parameters:
        error_watch     : a dictionary of status code strings and a message that should be returned
        update          : if True the update the current dictionary - when False replace old with new
        '''
        if not error_watch: return
        if update:
            self.error_watch.update(error_watch)
        else:
            self.error_watch = error_watch.copy()
        return 
    
    ##
    #   Clear out the error watch dictionary
    #
    def clearErrorWatch(self):
        '''Reset or clear the error watch dictionary.'''
        self.error_watch = dict()
        return 
    
    ##
    #   This checks for status code error condition - returns None if there was no error
    #   If there was an error then it returs a dictionary with some error information
    #
    def checkStatusCode(self, status_code=None):
        '''
        Consider an HTTP status code and if it is an error status that is being watched create an error record.
        
        Parameters:
        status_code     : the HTTP response code/status code

        returns         : None when no error - or a error dictionary with some information from the error watch
        '''
        self.log(f"entering, status code {str(status_code)}", level="DEBUG")
        if not status_code: return None
        if self.error_watch:
            #
            #   Consider specific status_codes - likely set by a subclass
            if str(status_code) in self.error_watch:
                condition = ERROR_DATA_TEMPLATE.copy()
                condition['status_code'] = status_code
                condition['error_message'] = self.error_watch[str(status_code)]
                self.log(f"returning, found an error with status code {str(status_code)}",
                         level="INFO")
                return condition
            #
            #   Consider the 4XX range of client errors
            elif (status_code >= 400) and (status_code <= 499):
                if "4XX" in self.error_watch:
                    condition = ERROR_DATA_TEMPLATE.copy()
                    condition['status_code'] = status_code
                    message = self.error_watch["4XX"]
                    try:
                        message['error']['code'] = status_code
                    except:
                        pass
                    condition['error_message'] = message
                    self.log(f"returning, found an error with status code {str(status_code)}",
                             level="INFO")
                    return condition
            #
            #   Consider the 5XX range of server errors
            elif (status_code >= 500) and (status_code <= 599):
                if "5XX" in self.error_watch:
                    condition = ERROR_DATA_TEMPLATE.copy()
                    condition['status_code'] = status_code
                    message = self.error_watch["5XX"]
                    try:
                        message['error']['code'] = status_code
                    except:
                        pass
                    condition['error_message'] = message
                    self.log(f"returning, found an error with status code {str(status_code)}",
                             level="INFO")
                    return condition
        #   Check for a status code outside of 200-299 range - all 200 codes are considered good
        if (status_code < 200) or (status_code >= 300):
            condition = ERROR_DATA_TEMPLATE.copy()
            condition['status_code'] = status_code
            condition['error_message'] = "Check the response, an error was detected, but not trapped."
            self.log(f"returning, found an error with status code {str(status_code)}",
                     level="INFO")
            return condition
        self.log(f"returning, no error", level="DEBUG")
        return None        
    
    

    ##########
    #
    #   REQUEST MAKING
    #
    ##########
    
    
    ##
    #   The low-level call to actually make the request. Will handle some errors. Calls the handleError() method in
    #   for HTTPErrors and a few other conditions.
    #
    def _makeRequest_(self, request=None, calls=2):
        '''
        A low-level method that actually makes a request.
        
        This method makes the requests - either a GET or a POST. If the 'request' parameter is not None, then the
        data in the request parameter is used. Otherwise, the method considers the request queue and uses the first
        item in the request queue. The method will attempt to handle some exceptions by making a recursive call. If
        attempts to handle the exception fail, that is, if there are repeated exceptions, then the call will fail
        by raising the exception.
        
        Parameters:
        request     : a REQUEST_DATA_TEMPLATE type thing with the request information or None
        calls       : a potential recursion level to try and handle some errors
        '''
        self.log(f"entering [max_depth: 2, depth: {(2-calls):d}]", level="DEBUG")
        response = None
        
        
        if not request:
            self.sem_request_data.acquire()
            if len(self._request_queue_)>0:
                request = self._request_queue_[0]
                self.log(f"removing one item from request queue, {len(self._request_queue_)}", 
                         level="DEBUG")
                self._request_queue_ = self._request_queue_[1:]
                self.log(f"request queue has {len(self._request_queue_)} items.", 
                         level="DEBUG")
                self.sem_request_data.release()
            else:
                self.sem_request_data.release()
                self.log(f"no request data supplied, request queue is empty",
                         level="INFO")
                self.log("returning (calls: {calls:d}}", level="DEBUG")
                return response
        
        try:
            if request['method'] == "POST":
                if request['ptype']=="json" or request['ptype']=="JSON":
                    self.log("making POST request with 'json'", level="DEBUG")
                    response = requests.post(request['url'],
                                             params=request['params'],
                                             headers=request['header'],
                                             json=request['payload'])
                else:
                    self.log("making POST request with 'data'", level="DEBUG")
                    response = requests.post(request['url'],
                                             params=request['params'],
                                             headers=request['header'],
                                             data=request['payload'])
            
            elif request['method'] == "GET":
                self.log("making GET request", level="DEBUG")
                response = requests.get(request['url'],
                                        params=request['params'],
                                        headers=request['header'])
            else:
                mesg = f"_makeRequest_():'{request['method']}' HTTP method is not currently supported."
                self.log(mesg)
                raise Exception(f"Exception: {mesg}")
            
            #   Try to get a status_code and check what may have happened
            try:
                sc = response.status_code
            except:
                sc = None
            self.last_error = self.checkStatusCode(sc)
            
            #   Check and throttle, if throttling is on
            self._throttleRequests_()
        
        except requests.exceptions.HTTPError as http_ex: 
            mesg = f"HTTP error (exception): {calls}"
            self.log(mesg, level="WARNING")
            if calls<1:
                self.last_error = ERROR_DATA_TEMPLATE.copy()
                self.last_error['exception'] = http_ex
                raise
            else:
                time.sleep((3.0-calls))
                response = self._makeRequest_(request,(calls-1))
            
        except requests.exceptions.ReadTimeout as to_ex: 
            mesg = f"timeout error (exception): {calls}"
            self.log(mesg, level="WARNING")
            if calls<1:
                self.last_error = ERROR_DATA_TEMPLATE.copy()
                self.last_error['exception'] = to_ex
                raise
            else:
                time.sleep((3.0-calls))
                response = self._makeRequest_(request,(calls-1))
            
        except requests.exceptions.ConnectionError as conn_ex: 
            mesg = f"connection error (exception): {calls}"
            self.log(mesg, level="WARNING")
            if calls<1:
                self.last_error = ERROR_DATA_TEMPLATE.copy()
                self.last_error['exception'] = conn_ex
                raise
            else:
                time.sleep((3.0-calls))
                response = self._makeRequest_(request,(calls-1))
            
        except requests.exceptions.RequestException as gen_ex: 
            mesg = f"generic requests exception: {str(gen_ex)}"
            self.log(mesg, level="WARNING")
            self.last_error = ERROR_DATA_TEMPLATE.copy()
            self.last_error['exception'] = gen_ex
            raise
        
        #   Only push the prior request status once we know we're going to
        #   exit this procedure successfully - for the last time
        self._pushPriorRequest_(request,response,self.last_error)
        self.log(f"returning  [max_depth: 2, depth: {(2-calls):d}]", level="DEBUG")
        return response
    
    
    
    ##
    #   The request making method. This can be called once a request has been queued.
    #   When subclassing this object - the makeRequest() method should be overridden to make
    #   sure that
    #
    def makeRequest(self):
        '''
        This is what is called to make the request in the case where the object is 
        not in a threaded mode. This should work for the majority of cases that
        just want to request a URL. This will need to be overridden for some APIs to
        handle any special cases of a request or response processing.
        '''
        if self.isRequesting(): return
        try:
            self.setRequestingStatus(True)
            self.log("making a request", level="INFO")
            response = self._makeRequest_()
            if response:
                self.queueResponse(response)
            self.setRequestingStatus(False)
        except Exception as ex:
            self.setRequestingStatus(False)
            raise ex
        return 
    
    
#####
#   
#   END class HTTPConnection definition
#   
#####

if __name__ == '__main__':
    print("HTTPConnection.py is a class with no main()")
