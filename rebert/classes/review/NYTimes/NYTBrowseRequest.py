#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: NYTBrowseRequest.py
#   REVISION: August, 2025
#   CREATION DATE: July, 2025
#   AUTHOR: David W. McDonald
#
#   A web service object to collect movie review text. This object starts by
#   collecting a review browse page - a web page that lists the reviews that are
#   available roughly by date. The page is parsed to collect the individual URLs
#   for the reviews listed on the browse page. This class then uses a
#   ReviewArticleRequest class to collect the text of the individual reviews.
#
#   The New York Times makes some efforts to limit how much content is collected.
#   They have an API that can be hard to use. This implements a screen scrape
#   approach that extracts an API token and uses that token to make 'paged'
#   browse requests.
#
#   Generally, the NY Times states that the API limits are 5 requests per minute
#   (RPM) and a maximum of 500 pages per day. The 'max' limits in the code are
#   set to respect the site guidelines.
#
#   The main page requested is a browse for current reviews
#   https://www.nytimes.com/reviews/movies
#   
#   
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
###
#
#   Standard python modules
import json, copy, time, re, hashlib
from datetime import datetime, timedelta
#
#   BeautifulSoup is a module that specializes in parsing
#   text documents - mostly HTML. This module has to be
#   installed before it can be used. It has very good
#   documentation:
#   https://beautiful-soup-4.readthedocs.io/en/latest/
#
from bs4 import BeautifulSoup
#
#   Using a low level HTTPConnection for paged requests
from rebert.classes.base.HTTPConnection import HTTPConnection
#
from rebert.classes.review.base.ReviewBrowseBase import ReviewBrowseBase
from rebert.classes.review.NYTimes.NYTArticleRequest import NYTArticleRequest
from rebert.classes.review.base.constants import *
#
#
#####
#   
#   CONSTANTS
#   
#####
#
#   This string is at the start of a data <script> block. This is page content
#   data that is loaded when the page is sent to the browser. 
#
#   We look for that script and then parse the data to extract specific
#   chunks that can then be converted from JSON to a python dictionary
NYT_DATA_SCRIPT_START = "window.__preloadedData ="
#
#   The full set of header fields that is in the pageInfo dictionary
#NYT_KEY_HEADER_FIELDS = ["Nyt-App-Type", "Nyt-App-Version", "Nyt-Token", "X-Nyt-Internal-Meter-Override"]
#
#   Looks like we can omit the "X-Nyt-Internal-Meter-Override" header.
#   Here our key header fields list is just the headers that are currently
#   required to make a valid API browse nextReviews() request.
NYT_KEY_HEADER_FIELDS = ["Nyt-App-Type", "Nyt-App-Version", "Nyt-Token"]
#
#   This template is used to set the 'variables' part of a browse query
#   The 'cursor' field has to be updated to reflect the next offset
#   using the pageInfo of the prior response.
NYT_REQUEST_VARS_TEMPLATE = {
    "first":        30,
    "sortOrder":    "newest",
    "cursor":       ""
}
#
#   This template is used to set the 'extension' part of the browse
#   query. The 'sha256Hash' is a unique token that allows a query to
#   persist between queries. It appears that this has to be constant
#   for the API call to work.
NYT_REQUEST_EXT_TEMPLATE = {
    "persistedQuery": {
        "version": 1,
        "sha256Hash": ""
    }
}
#
#   This constant was pulled from a browse query string by observing a
#   request for additional 'browse' pages of movie reviews. This is the
#   'sha256Hash' that is used for 'persistedQuery' API requests - the
#   'extensions' part of the query string. 
#
#   Experimenting with other 'sha256Hash' values it appears that this
#   actually needs to be treated as a constant. Other values generate
#   errors. However, this value might change. If it does, then the
#   browse request should note an error and a new value would need to
#   be found for this to work.
NYT_PERSISTED_QUERY_HASH_CONST = "01cc23ab7df18d924f28da523768f46bedfb202f4dc2ca085f23b748f598ad2c"
#
#   This sets a fixed 'max' for the nextReviews() operation to make sure
#   we don't have some run-away operations. It will just stop once it
#   gets to the max number of pages.
#
#   There are about 30 movie reviews per browse page. Collecting 4 or 5 
#   pages would get a little over 120 movie reviews. That is probably
#   enough to collect the 'recent' movie reviews. We'll be a little
#   generous with our count limit.
NYT_MAX_NEXT_PAGE_COUNT = 10
#
#   After a bunch of testing, it looks like browse page 34 is where the
#   persistent browse page query starts to fail. Sometimes it stops at
#   page 33, returning an "Internal server error" and then stops 
#   responding to all other requests - potentially IP ADDR based?
#NYT_MAX_NEXT_PAGE_COUNT = 34
#
#   For testing/finding the max browse page that can be returned
NYT_MAX_NEXT_PAGE_COUNT = 120
#
#   The implementation of 'paged' requests relies on an undocumented API call
#   that is used in the NY Times "browse" web page. The NY Times API is rate
#   limited to 5 per minute (RPM). While the API token we extract from the 
#   first browse page might allow a faster request rate, we'll adhere to 
#   their standards for our API requests.
NYT_API_RATE_LIMIT_RPM = 5.0
#
#####
#   
#   START class NYTBrowseRequest definition
#   
#####
#
###
#   A class/object that interacts with The Guardian website to collect 
#   movie reviews.
#
class NYTBrowseRequest(ReviewBrowseBase):
    '''
    The NYTBrowseRequest connectes to The New York Times movie review site and requests  
    'browse' page that lists a set of recent reviews for cultural events. The class will  
    parse the requested browse page to identify links to review articles, and then uses a 
    NYTArticleRequest instance to get data from those reviews.
    
    Attributes:
        browse_service_endpoint     - a string service endpoint for a basic browse
    
    Methods:
        getReviewsByBrowse()        - parses the browse page, returns review article data
        _parseHTMLPage_()           - parse the browse page HTML
        _extractArticleLinks_()     - extract URL, article links, for the review articles
        _filterReview_()            - filter review articles based on features
        _extractMovieTitleFromArticleTitle_()  - extract the movie title from article title

    '''
    def __init__(self, name="NYTBrowseRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   The NY Times approach - does not support random access.
        #   We should use the 'nextReviews()' method to get articles
        self._supports_random_access_ = False
        #   
        #   This is our collector class
        self.__article_collector_class__ = NYTArticleRequest
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "nytimes.com"
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://www.nytimes.com")
        #   This is the service endpoint for the current reviews
        self.browse_service_endpoint = "/reviews/movies"
        self.setServiceEndpoint(self.browse_service_endpoint)
        #
        #   Some of the user agent strings are denied access to
        #   content. The 'opera' user agent seems to work most often.
        self.setUserAgent("opera_2023")
        #
        #   The NY Times implmenets rate limiting for API requests.
        #   Here we'll set a throttle rate that is designed to respect
        #   their rate limits.
        self.setThrottleRate(rpm=NYT_API_RATE_LIMIT_RPM)
        #
        #   Data needed for making nextReviews() requests 
        #
        #   First we need to extract and parse the preloaded data. This is
        #   in a <script> block with no attributes and with text that
        #   starts with the text in constant NYT_DATA_SCRIPT_START
        #
        self.__preloaded_text_data__ = ""   #   The script, from the initial request
        self.__root_query__ = dict()        #   The inital query response
        self.__page_info__ = list()         #   A list of page info
        self.__config__ = dict()            #   Configuration to make a next page
                                            #   request, request headers, URL
        #
        #   Looks like the API expects this same value for the persistent
        #   query token. We'll set it here and it will get loaded into the
        #   'extensions' part of the query.
        self.__persist_hash__ = NYT_PERSISTED_QUERY_HASH_CONST
        #self.__persist_hash__ = ""
        #
        #   A persistent HTTPConnection object that is used to make the
        #   API requests - this way we don't have to create it every time
        self.__connect__ = None
        return


    ###
    #   This method collects the browse page and then all of the articles
    #   associated with the page.
    #
    def getReviewsByBrowse(self, page=0, browse_only=False):
        '''
        This requests review browse page. If the page request is succesful this
        calls method _parseHTMLPage_() to extract review article links. It then
        uses the resulting review_list and calls 
        
        Parameters:
        page:           the index of the browse page to request, parse and collect
        browse_only:    a boolean, if True returns just the results of the browse
                        parse, False by default, returns the full article
        
        Returns
            a list of review dictionary items, or an empty list
        '''
        self.log(f"entering", level="DEBUG")
        #   Initialize the list of the review
        review_list = list()
        #
        mesg = f"{self.browse_service_endpoint}"
        if page > 1:
            #   Pages past page 1, need to use the nextReviews() method
            self.log(f"page {page}, is not a valid page, no results returned", level="WARNING")
            self.log(f"use 'nextReviews()' method to get additional pages.", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review_list
        #
        #   Then NY Times is just one page with this approach, then we need
        #   to use 'nextReviews()' approach - We always need to collect 
        #   page #1 this way - to make sure we parse the HTML
        page = 1
        #
        #   Clear out any prior list of review items that were filtered out
        #   If you want them, get them before starting a new request!
        self._removed_reviews_ = list()        
        
        #   Try to get the main browse page
        text = ""
        self.queueRequest()
        self.log(f"requesting '{mesg}'", level="DEBUG")
        self.makeRequest()
        if self.responses():
            resp = self.nextResponse()
            text = resp.text
        else:
            self.log(f"request did not return a page", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review_list
        
        #   Parse out the basic information from the 
        review_list = self._parseHTMLPage_(text)        
        #   
        if browse_only:
            #   Set the current page to make the nextReviews() work correctly
            self._current_page_ = page
            #
            self.log(f"returning, browse_only=True", level="DEBUG")
            return review_list
        #
        #   Now, get the individual article text - and filter the list so that
        #   it hopefully only contains movies/films
        review_list = self._getReviewContents_(review_list)
        #   Set the current page to make the nextReviews() work correctly
        self._current_page_ = page
        #
        self.log(f"returning", level="DEBUG")
        return review_list



    def nextBrowsePage(self, browse_only=False, start_at=0):
        '''
        This method will request the 'next' browse page and
        
        Parameters:
        browse_only:    a boolean, if True returns just the results of the
                        browse parse. By default it returns the full article.
        start_at:       an integer page number, index, where the code should
                        start returning data.
        
        Returns
            a list of review dictionary items, or an empty list
        '''
        self.log(f"entering", level="DEBUG")
        #
        #   Initialize the list of the review
        review_list = list()
        #
        #   This checks that the start_at value is something that will work
        if start_at < 0:
            self.log(f"The 'start_at' page ({start_at}), should be greater than zero.",
                    level="DEBUG")
            self.log(f"The 'start_at' page will be ignored.",
                    level="DEBUG")
            start_at = 0
        #
        #   If we're going to start at a some page, make sure we're not past 
        #   that max page
        if start_at > NYT_MAX_NEXT_PAGE_COUNT:
            self.log(f"The 'start_at' page ({start_at}), is greater than the maximum allowed page [{NYT_MAX_NEXT_PAGE_COUNT}]",
                    level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return review_list
        #
        #   Check that we already got the first browse page, if not
        #   then get that page first
        if not self.__preloaded_text_data__ or (self._current_page_ < 1):
            #   In the case we're starting with the first page
            if ((start_at == 0) or (start_at == 1)):
                #   If we're starting at the first page then, get and return that first page
                review_list = self.getReviewsByBrowse(page=1, browse_only=browse_only)
                self.log(f"returning", level="DEBUG")
                return review_list
            else:
                #   Ultimately, we're 'skipping' this page, so just get the
                #   mimimal data and toss it. This will set up the __page_info__
                rl = self.getReviewsByBrowse(page=1, browse_only=True)
        #
        #   Make sure we don't go past the max next page
        if self._current_page_ >= NYT_MAX_NEXT_PAGE_COUNT:
            self.log(f"Current page, {self._current_page_}, is at the maximum allowed pages [{NYT_MAX_NEXT_PAGE_COUNT}]",
                    level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return review_list
        #
        #   Make an API based browse request. It requests the 'next' chunk based
        #   on the extracted pageInfo in slot self.__page_info__[-1]
        data = self.__requestNextPage__()
        #
        #   This iterates over API browse requests, until it gets to the page
        #   index where it is to start returning pages - then goes on
        if data and start_at and (self._current_page_ < start_at):
            self._current_page_ = len(self.__page_info__)
            while data and (self._current_page_ < start_at):
                #print(f"Skipping browse page {self._current_page_}, getting next page")
                self.log(f"Skipping browse page {self._current_page_}, getting next page",
                        level="DEBUG")
                data = self.__requestNextPage__()
                self._current_page_ = len(self.__page_info__)
        #
        #   Perform some data checking
        if not data or ('hits' not in data):
            self.log(f"Browse query had no response, or no 'hits' in the data response.",
                    level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return review_list
        #
        #   Check that we have some hits in the query response
        if 'edges' not in data['hits']:
            self.log(f"Browse query did not have any 'edges' in the response 'hits'",
                    level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return review_list
        #
        #   Use the data from the API request, a JSON structure that is now a
        #   python dictionary, to create a list of review records
        for item in data['hits']['edges']:
            if "__typename" in item and item["__typename"]=="ContentSearchHitsEdge":
                #   If access to a field fails - it probably means we don't have a the
                #   information that we need to get the article, so skip it
                try:
                    record = self.__review_template__.copy()
                    record['title'] = item['node']['reviewItems'][0]['subject']['title']
                    record['review_url'] = item['node']['url']
                    record['review_title'] = item['node']['promotionalHeadline']
                    record['author'] = item['node']['bylines'][0]['creators'][0]['displayName']
                    try:
                        post_date_ts = item['node']['firstPublished'].partition(".")[0]
                        post_date_ts = post_date_ts.replace("T"," ")
                        record['review_date_ts'] = post_date_ts
                        pd = datetime.strptime(post_date_ts,"%Y-%m-%d %H:%M:%S")
                        review['review_date_str'] = pd.strftime("%B %d, %Y")
                    except:
                        pass
                    #print(f"Review Title: {record['review_title']}")
                    #print(f"By: {record['author']} @ {record['review_date_ts']}")
                    #print(f"Title: {record['title']}")
                    #print(f"URL: {record['review_url']}") 
                    #print()
                    review_list.append(record)
                except:
                    #print(json.dumps(item,indent=4))
                    pass
        #
        #   Set the current page - we just keep appending to the
        #   __page_info__ list (for now). The length is the number
        #   of pages we've returned successfully
        if review_list:
            self._current_page_ = len(self.__page_info__)
        #
        #   If we're not collecting the article data then, just return the list
        if browse_only:
            self.log(f"returning, browse_only=True", level="DEBUG")
            return review_list
        #
        #   Now, get the individual article text - and filter the list so that
        #   it hopefully only contains movies/films
        review_list = self._getReviewContents_(review_list)
        #
        self.log(f"returning", level="DEBUG")
        return review_list


    ###
    #   This parses the browse page to collect links to the actual review
    #   articles. This also gets the review title and movie title.
    #
    def _parseHTMLPage_(self, text=None):
        '''
        Parse the browse page to extract title and links.
        
        Parameters:
        text:       the HTML text of the browse page
        
        Returns
            a list of review dictionary items, or an empty list
        '''
        review_list = list()
        #   No HTML text, return empty list
        if not text: 
            self.log(f"HTML text was empty!", level="WARNING")
            return review_list
        self.log(f"entering", level="DEBUG")
        
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(text,'html.parser')
        #
        #   We're looking for a particular <script> with page preloaded data
        scripts = html_parse.find_all('script')
        #   Sometimes we don't actually get a page with content, Booo
        if not scripts:
            self.log(f"NO <script> tags in page",level="DEBUG")
        #   Run through all of the scripts - looking for specific data
        for s in scripts:
            #   The script we're looking for currently has no attributes
            if not s.attrs:
                #print(s.text[0:125])
                script_contents = s.text
                #   First, we need to make sure we have the correct script
                #   block, the one with the data in it
                if script_contents.startswith(NYT_DATA_SCRIPT_START):
                    script_contents = script_contents.partition("=")[2].strip()
                    if script_contents.endswith(";"):
                        #   Save that extracted script data
                        self.__preloaded_text_data__ = script_contents[:-1]
                        #print(self.__preloaded_text_data__)
                        #   Now parse that text - once parsed, then we can
                        #   mostly extract the components that we need from
                        #   dictionaries that are already parsed out
                        self.__parsePreloadedData__()       
        #
        #   The page is composed of sections - each section reflects the
        #   dated that the review article was published or posted
        sections = html_parse.find_all('section')
        #   Run through all of the sections looking for the sections that
        #   have dates in the id attribute
        for s in sections:
            if 'id' in s.attrs and 'reviews' in s['id']:
                #   The 'reviews' section contains a set of list items
                list_elts = s.find_all('li')
                #   Each list item is a potential movie review article
                for l in list_elts:
                    record = self._extractArticleLinks_(l)
                    if record: 
                        review_list.append(record)
        
        self.log(f"returning {len(review_list)} items", level="DEBUG")
        return review_list


    ###
    #   A low-level method to make the next page request, and extract
    #   the information, pageInfo, to set up for the next browse page 
    #   request
    #
    def __requestNextPage__(self):
        '''
        Assuming that the script data was successfully parsed and that we
        found a 'config' and 'root_query' - this method attempts to
        construct a query string based on the extracted data
        
        '''
        variables = None
        extensions = None
        base_url = None
        header_data = None
        self.log(f"entering", level="DEBUG")
        #
        #   __config__ contains fields that tell us where to make the request.
        #   This includes fields that need to be part of the request header
        #   in order for the request to be a valid request.
        if self.__config__:
            if 'gqlUrlClient' in self.__config__:
                base_url = self.__config__['gqlUrlClient']
            if 'gqlRequestHeaders' in self.__config__:
                header_data = self.__config__['gqlRequestHeaders']
        #
        #   __page_info__ is a list of the pageInfo dictionaries extracted from
        #   the prior responses. The last item in the list is always the "page" we 
        #   currently HAVE - and has the cursor information to get the NEXT page.
        if self.__page_info__:
            pi = self.__page_info__[-1]
            if pi['hasNextPage']:
                variables = NYT_REQUEST_VARS_TEMPLATE.copy()
                variables['cursor'] = pi['endCursor']
        
        if not (header_data and base_url and variables): 
            #   Need error logging here
            self.log(f"Could not access data in the __config__ and __page_info__ dictionaries.",
                    level="WARNING")
            self.log(f"returning", level="DEBUG")
            return
        #
        #   A unique sha256 hash token is used to persist the query data across 
        #   different requests. Create and save one for our future browse requests
        #
        #   It currently looks like the API expects the exact same token for the
        #   sha256Hash value. It should be set above
        if not self.__persist_hash__:
            #   Get a string of the current time - with microseconds
            ts = str(datetime.now())
            #   Time and a constant - give us a relatively unique set of bytes
            hash_bytes = bytes("rebert_browse_request_+"+ts,'utf-8')
            #   Create the hash object - and then convert to hash string
            h = hashlib.sha256(hash_bytes)
            self.__persist_hash__ = str(h.hexdigest())
            #print(f"sha256Hash {self.__persist_hash__=}")
        #
        #   Now set the persist hash value - nested dictionary
        extensions = NYT_REQUEST_EXT_TEMPLATE.copy()
        extensions['persistedQuery']["sha256Hash"] = self.__persist_hash__        
        #
        #   A browse request is an HTTP GET with two dictionary
        #   structures in the query string.
        #
        #   Construct the query string
        qs = "operationName=MovieReviewsQuery"
        qs = qs+"&variables="+json.dumps(variables)
        #   Currently using the extension template as a constant
        #qs = qs+"&extensions="+json.dumps(NYT_REQUEST_EXT_TEMPLATE)
        qs = qs+"&extensions="+json.dumps(extensions)
        #   Construct the URL to make the request
        url = base_url+"?"+qs
        #print(url)
        #
        #   Create a connection object and itialize it with the persistent
        #   request information
        if not self.__connect__:
            #   Create a connection object that will make the request
            self.__connect__ = HTTPConnection(name="Browse_NextPage_Request_Managed",
                                     logger=self.getLogger())
            #   Set the rate of collection, slow, but not crazy slow
            self.__connect__.setThrottleRate(rpm=NYT_API_RATE_LIMIT_RPM)
            self.__connect__.throttlingOn()
            #
            #   The NYT web server is sometimes picky about the User-Agent 
            #   The opera_2023 string appears to work most of the time
            self.__connect__.setUserAgent("opera_2023")
            #
            #   Need to set a number of additional header values
            self.__connect__.setContentType("application/json")
            #self.__connect__.setHeaderValue("key","value")
            for k in NYT_KEY_HEADER_FIELDS:
                kl = k.lower()
                if kl in header_data:
                    self.__connect__.setHeaderValue(k,header_data[kl])
            #
            #   A fix for one of the fields. The API seems to use "undefined"
            #   instead of the JSON null or python None
            #   
            #   For now - this header field can be omitted 
            #self.__connect__.setHeaderValue("X-Nyt-Internal-Meter-Override","undefined")
            #
            #   Set additional headers - for testing - can be omitted
            #self.__connect__.setHeaderValue("Accept","*/*")
            #self.__connect__.setHeaderValue("Accept-Encoding","gzip, deflate, br, zstd")
            #self.__connect__.setHeaderValue("Accept-Lanugage","en-US,en;q=0.9")
            self.__connect__.setHeaderValue("Origin","https://www.nytimes.com/")
            #self.__connect__.setHeaderValue("Priority","u=1, i")
            self.__connect__.setHeaderValue("Referer","https://www.nytimes.com/")
            #
            self.log(f"Initialized self.__connect__ for API.", level="DEBUG")
            #print("Initialized an API connect object")
            #
        #
        #   Might want to see what the headers look like on each request
        #print(json.dumps(self.__connect__.getHeader(),indent=4))
        #self.log(f"Requesting next browse pages with self.__connect__.", level="DEBUG")
        #print("Making browse API request.")
        self.__connect__.queueRequest(url=url)
        self.__connect__.makeRequest()
        response = self.__connect__.nextResponse()
        data = list()
        if not response:
            error_data = self.__connect__.getPriorRequests()
            #print(f"{error_data[0]['timestamp']=}")
            #print(f"{error_data[0]['response'].status_code=}")
            #print(f"{error_data[0]['request']['url']=}")
            err_resp = json.dumps(error_data)
            self.log(f"Error with the paged request: {err_resp}", level="DEBUG")
        else:
            #   Looks like when we get here we need to do some response
            #   checking to make sure we get something we expect.
            response = response.json()
            #
            #   If we got a response - check for an error message
            if 'errors' in response:
                #   If there were errors log them and return and empty result
                self.log(f"The API request generated the following error:", level="WARN")
                self.log(f"{json.dumps(response,indent=4)}", level="WARN")
                self.log(f"returning", level="DEBUG")
                return dict()
            #
            #   Now, check that we have a data field for the response
            if ('data' not in response) or (not response['data']):
                self.log(f"Response JSON has no 'data' field or an empty 'data' field.", level="DEBUG")
                self.log(f"{json.dumps(response,indent=4)}", level="DEBUG")
                self.log(f"returning", level="DEBUG")
                return dict()
            #
            #   Check that the data field has the search result
            if not 'contentSearch' in response['data']:
                self.log(f"Response JSON has no 'data' field.", level="DEBUG")
                self.log(f"{json.dumps(response,indent=4)}", level="DEBUG")
                self.log(f"returning", level="DEBUG")
                return dict()
            #
            #   Extract the search results - decrease some of the dict
            #   key depth - making access to the important information easier            
            data = response['data']['contentSearch']
            #print(json.dumps(data,indent=4))
            #
            #   Now set the page info - so we can get the next page if we need it
            self.__page_info__.append(data['hits']['pageInfo'])
            #print(json.dumps(data['hits']['pageInfo'],indent=4))
        self.log(f"returning", level="DEBUG")
        return data


    def __parsePreloadedData__(self):
        '''
        This is only called when we are able to find the data script that
        is loaded with the page - the 'preloaded' data.
        
        This pulls components from the script and converts them to dictionary
        items that can be used by the 'parsing' code. In the case of the 
        New York Times site - this is just extracting fields once they
        have been parsed by this method.
        
        '''
        self.log(f"entering", level="DEBUG")
        #
        #   Extract the "config" - this is a JSON structure that is 
        #   delimited with the "config" key, ending with "ssrQuery" key
        #
        #   The config data has fields that we need to make paged requests
        #   including an important request token
        try:
            config = self.__preloaded_text_data__.partition('"config"')[2][1:]
            config = config.partition('"ssrQuery"')[0].strip()[:-1]
            #
            #   With the config extracted, there are some problem fields
            #   that have to be fixed.
            #
            #   First we remove some JavaScript code in the statsig field
            statsig = config.partition('"statsig"')[2]
            statsig = statsig.partition('"fastlyEntitlements"')[0]
            statsig = '"statsig"'+statsig
            config = config.replace(statsig,"")
            #   With the code removed we change undefined to null so that
            #   the JSON parser will do the right thing
            config = config.replace("undefined","null")
            #   What remains should convert to a python dictionary
            config = json.loads(config)
            self.__config__ = config
            #print(json.dumps(self.__config__,indent=4))
        except:
            self.log(f"Could not extract the __config__ from the data <script>.",
                    level="WARNING")
            self.__config__ = dict()
        #
        #   Extract the "ROOT_QUERY" - this is a JSON structure that is 
        #   delimited with the "ROOT_QUERY" key, ending with "config" key
        #
        #   We might need the ['hits']['pageInfo'] sub-dictionar to
        #   make paged browse requests - so we make that easier to get
        try:
            root_query = self.__preloaded_text_data__.partition('"ROOT_QUERY"')[2][1:]
            root_query = root_query.partition('"config"')[0].strip()[:-2]
            self.__root_query__ = json.loads(root_query)
            #
            #   Some of the dict keys are really awkward - here we keep them
            #   by adding them to a field, and then replacing them with a
            #   simple field name
            #
            #   This is fixing the 'search_result' part of the record
            keys = list(self.__root_query__.keys())
            for k in keys:
                if k.startswith('contentSearch'):
                    self.__root_query__['search_function'] = k
                    self.__root_query__['search_result'] = self.__root_query__[k]
                    del self.__root_query__[k]
            #   This is fixing the 'hits' part of the record
            keys = list(self.__root_query__['search_result'].keys())
            for k in keys:
                if k.startswith('hits'):
                    #   Special, extract the 'pageInfo'
                    self.__page_info__.append(self.__root_query__['search_result'][k]['pageInfo'])
                    #   Now, fix the other parts of the record
                    self.__root_query__['search_result']['hits'] = self.__root_query__['search_result'][k]
                    count = k.partition(":")[2].replace(")","").replace("}","").strip()
                    self.__root_query__['search_result']['hits']['count'] = count
                    del self.__root_query__['search_result'][k]
            #   
            #   This basically removes a long list of article IDs - probably not needed
            if "edges@filterEmpty" in self.__root_query__['search_result']['hits']:
                self.__root_query__['search_result']['hits']['edges@filterEmpty'] = ['node_list_was_removed']
            #print(json.dumps(self.__root_query__,indent=4))
            #print(json.dumps(self.__page_info__,indent=4))
        except:
            self.log(f"Could not extract the __root_query__ and __page_info__ from the data <script>.",
                    level="WARNING")
            self.__root_query__ = dict()
            self.__page_info__ = list()
        #
        self.log(f"returning", level="DEBUG")
        return        


    ###
    #   This parses the individual tiles of the page to
    #   collect the movie information
    #
    def _extractArticleLinks_(self, main_div=None):
        '''
        Parses the browse page to extract title and links.
        
        Parameters:
        main_div:       a single div with the body of the browse page
        
        Returns
            a single MOVIE_REVIEW_DATA_TEMPLATE partially filled, or empty dict
        '''
        self.log(f"entering", level="DEBUG")
        record = self.__review_template__.copy()
        #
        #   The list item has an anchor that is what we need
        review_anchor = ""
        try:
            review_anchor = main_div.article.div.a
        except:
            review_anchor = ""
        #
        #   Make sure we have what we need to do the data extraction
        if not review_anchor: 
            self.log(f"missing review anchor", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return dict()
        #
        #   Grab the link from the first anchor <A ...> found in the div
        url = review_anchor['href']
        self.log(f"got anchor with: '{url}'", level="DEBUG")
        if not url.startswith(self.getHost()):
            url = self.getHost()+url
        #
        #   Under the anchor is an H2 that contains the title
        try:
            review_title = review_anchor.div.h2.text.strip()
        except:
            review_title = ""
        #
        review_title = review_title.strip()
        #
        #   If we don't have a title for the review article then we're done
        if not review_title: 
            self.log(f"returning", level="DEBUG")
            return dict()
        #
        #   Extract the title of the movie
        title = self._extractMovieTitleFromArticleTitle_(review_title)        
        
        #   Now save the data for this article and return it
        record['title'] = title
        record['review_url'] = url
        record['review_title'] = review_title
        self.log(f"returning", level="DEBUG")
        return record


    def _filterReview_(self, review=None):
        '''
        Implements filtering on a given review to decide if it should be included
        
        Parameters:
        review:         a single review dictionary record
        
        Returns
            either the dictionary record that should be included, or None when
            the review should not be included
        '''
        #
        #   Make sure that the review has some basic information, movie title,
        #   review body, and an author
        review = super()._filterReview_(review)
        if not review: return dict()
        #
        #   Filtering specific to the Guardian reviews, review types
        rtype = review['review_type'].lower()
        #   Keep stuff about movies and film
        if ('movie' not in rtype) and ('film' not in rtype):
            self._removed_reviews_.append(review)
            self.log(f"removed (not movie/film): '{review['title']}'", level="INFO")
            return dict()
        return review


    def _extractMovieTitleFromArticleTitle_(self, review_title=None):
        '''
        Extracts a movie title from a review article title
        
        Parameters:
        review_title:   the title of the review article
        
        Returns
            the title of the extracted movie or an empty string
        '''
        #
        #   Use the default behavior, apply regex and extract title
        #title = super()._extractMovieTitleFromArticleTitle_(review_title)
        #
        #   Movie title is the review article title
        title = review_title
        #
        #   A little cleaning for the end
        while title and title[-1] in ",.;:":
            title = title[:-1]
        return title
       
#####
#   
#   END class NYTBrowseRequest definition
#   
#####

if __name__ == '__main__':
    print("NYTBrowseRequest.py is a class with no main()")


