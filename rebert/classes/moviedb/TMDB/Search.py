#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: Search.py
#   REVISION: July, 2024
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   A web service class that implements some of the Search functionality of the
#   TMDB (The Movie Database) https://www.themoviedb.org
#
#   As of middle 2024 TMDB Search capabilities covered the following:
#   Collection      https://developer.themoviedb.org/reference/search-collection
#   Company         https://developer.themoviedb.org/reference/search-company
#   Keyword         https://developer.themoviedb.org/reference/search-keyword
#   Movie           https://developer.themoviedb.org/reference/search-movie
#   Multi           https://developer.themoviedb.org/reference/search-multi
#   Person          https://developer.themoviedb.org/reference/search-person
#   TV              https://developer.themoviedb.org/reference/search-tv
#
#   This class implements movie, TV, and keyword type searches. This seems to be the most
#   likely use cases.
#
#   languages (ISO 639-1 tags)
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
TMDB_REQUESTS_PER_SEC = 30.0    #   This is to be a little below the stated limits
TMDB_MAX_COUNT = 1500           #   Assumes 20 items per page 1500 = 20 * 75
TMDB_MAX_PAGE = 75              #   This is a guess, there may be some use cases
                                #   where there are more than 75 pages
#
#
#
#
class Search(HTTPConnection):
    def __init__(self, name="TMDB-Search", logger=None, *args, **kwargs):
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
        #   Three different services that we will implement with one class
        #   All of these are different search type actions
        self.tmdb_search_movie_service_endpoint = "/3/search/movie"
        self.tmdb_search_keyword_service_endpoint = "/3/search/keyword"
        self.tmdb_search_tv_service_endpoint = "/3/search/tv"
        #   Start with movie search
        self.setServiceEndpoint(self.tmdb_search_movie_service_endpoint)
        #
        #   Set a rate limit so that rogue code won't abuse the site
        #   Docs say this API will allow up to 50 requests per second
        self.setThrottleRate(rps=TMDB_REQUESTS_PER_SEC)
        self.throttlingOn()
        #   Pick a random user agent to simulate a browser reqeust
        self.setUserAgent()
        #   Set a request header value to tell the server we accept JSON
        #   as the response data (required)
        self.setHeaderValue('accept', 'application/json')
        #   Default setting is as movie request
        self.tmdb_request_is_movie = True      
        self.tmdb_request_is_keyword = False      
        self.tmdb_request_is_tv = False      
        return
    
    
    ##
    #   A method that performs a movie search request somewhat automatically.
    #   Just provide the title and it will work.  
    #
    def movieSearch(self, title=None, year=None, lang=None, count=0):
        '''
        Find and return a list of movies in TMDB that match the provided
        parameters.
        
        This method composes a request with the given parameters and 
        makes the request. It extracts the results data from the response
        to generate the reults list. This method will attempt to return 
        the 'count' number of items if there are at least that many items
        that match the provided parameters.
        
        Parameters:
            title           : str of the movie title, or title substring
            year            : an int four digit year of the movie release
            lang            : a str of 2 character language code
            count           : an int number of items that should be returned
                              zero or negative will try to return everything
        
        Returns:
            A list of dictionaries, movies matching the title search 
        '''
        search_result = list()
        self.log(f"entering", level="DEBUG")
        #
        #   Validate the minimum required parameters
        if not title: 
            self.log("Provide a search title for a movie search of TMDB.", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return search_result
        #
        #   Make sure there is an API key for this request
        token = self.getHeaderValue('Authorization')
        key = self.getRequestParam('api_key')
        if not key and not token:
            self.log("Set the API Key or Bearer Token to search TMDB", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return search_result
        
        if count <= 0:
            self.log(f"parameter count zero or negative was set to {TMDB_MAX_COUNT}", level="INFO")
            count = TMDB_MAX_COUNT
        elif count > TMDB_MAX_COUNT:
            self.log(f"parameter count {count} is larger than {TMDB_MAX_COUNT}, was set to {TMDB_MAX_COUNT}", 
                     level="INFO")
            count = TMDB_MAX_COUNT

        #
        #   Make sure this is handled as a movie search
        self.setRequestAsMovieSearch()
        #
        #   Set the parameter values
        self.setTitle(title)
        if year:
            self.setPrimaryReleaseYear(year)
        if lang:
            self.setLanguage(lang)
        #
        #   Queue the request and make it
        self.queueRequest()
        self.makeRequest()
        resp = self.nextResponse()
        if not resp:
            self.log(f"request returned an empty response or an error response", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return search_result
        data = resp.json()
        search_result.extend(data['results'])
        search_result_count = data['total_results']
        total_result_pages = data['total_pages']
        self.log(f"response page {data['page']}, have {len(search_result)} of {data['total_results']} possible ({data['total_pages']} pages)", 
                 level="DEBUG")
        #   If there was only one page of results, then we just return that
        if total_result_pages < 2:
            self.log(f"returning", level="DEBUG")
            return search_result
        #
        #   If there are additional results, then try to collect them
        #   by requesting each additional page - starting with page 2
        page = 2
        while (len(search_result) < count) and (len(search_result) < search_result_count):
            self.log(f"paging, requesting page {page}", level="DEBUG")
            self.setPage(page)
            self.queueRequest()
            self.makeRequest()
            resp = self.nextResponse()
            if not resp:
                self.log(f"request returned an empty response or an error response", level="DEBUG")
                self.log(f"returning", level="DEBUG")
                return search_result
            data = resp.json()
            search_result.extend(data['results'])
            self.log(f"response page {data['page']}, have {len(search_result)} of {data['total_results']} possible ({data['total_pages']} pages)", 
                     level="DEBUG")
            page += 1
            if (page > total_result_pages) or (page > TMDB_MAX_PAGE): break

        self.log(f"returning", level="DEBUG")
        return search_result
    
    
    ##
    #   A method that performs a TV search  
    #
    def tvSearch(self, title=None, year=None, lang=None, count=0):
        '''
        Find and return a list of TV items in TMDB that match the
        parameters.
        
        This method composes a request with the given parameters and 
        makes the request. It extracts the results data from the response
        to generate the reults list. This method will attempt to return 
        the 'count' number of items if there are at least that many items
        that match the provided parameters.
        
        Parameters:
            title           : str of the TV title, or title substring
            year            : an int four digit year of the first air date
            lang            : a str of 2 character language code
            count           : an int number of items that should be returned
                              zero or negative will try to return everything
        
        Returns:
            A list of dictionaries, TV shows or series matching the title search 
        '''
        search_result = list()
        self.log(f"entering", level="DEBUG")
        #
        #   Validate the minimum required parameters
        if not title: 
            self.log("Provide a title for a TV search of TMDB.", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return search_result
        #
        #   Make sure there is an API key for this request
        token = self.getHeaderValue('Authorization')
        key = self.getRequestParam('api_key')
        if not key and not token:
            self.log("Set the API Key or Bearer Token to search TMDB", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return search_result
        if count <= 0:
            self.log(f"parameter count zero or negative was set to {TMDB_MAX_COUNT}", level="INFO")
            count = TMDB_MAX_COUNT
        elif count > TMDB_MAX_COUNT:
            self.log(f"parameter count {count} is larger than {TMDB_MAX_COUNT}, was set to {TMDB_MAX_COUNT}", 
                     level="INFO")
            count = TMDB_MAX_COUNT
        #
        #   Make sure this is handled as a TV search
        self.setRequestAsTVSearch()
        #
        #   Set the parameter values
        self.setTitle(title)
        if year:
            self.setFirstAirDateYear(year)
        if lang:
            self.setLanguage(lang)
        #
        #   Queue the request and make it
        self.queueRequest()
        self.makeRequest()
        resp = self.nextResponse()
        if not resp:
            self.log(f"request returned an empty response or an error response", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return search_result
        data = resp.json()
        search_result.extend(data['results'])
        search_result_count = data['total_results']
        total_result_pages = data['total_pages']
        self.log(f"response page {data['page']}, have {len(search_result)} of {data['total_results']} possible ({data['total_pages']} pages)", 
                 level="DEBUG")
        #   If there was only one page of results, then we just return that
        if total_result_pages < 2:
            self.log(f"returning", level="DEBUG")
            return search_result
        #
        #   If there are additional results, then try to collect them
        #   by requesting each additional page - starting with page 2
        page = 2
        while (len(search_result) < count) and (len(search_result) < search_result_count):
            self.log(f"paging, requesting page {page}", level="DEBUG")
            self.setPage(page)
            self.queueRequest()
            self.makeRequest()
            resp = self.nextResponse()
            if not resp:
                self.log(f"request returned an empty response or an error response", level="DEBUG")
                self.log(f"returning", level="DEBUG")
                return search_result
            data = resp.json()
            search_result.extend(data['results'])
            self.log(f"response page {data['page']}, have {len(search_result)} of {data['total_results']} possible ({data['total_pages']} pages)", 
                     level="DEBUG")
            page += 1
            if (page > total_result_pages) or (page > TMDB_MAX_PAGE): break

        self.log(f"returning", level="DEBUG")
        return search_result
        

    ##
    #   A method that performs a keyword search  
    #
    def keywordSearch(self, keyword=None, count=0):
        '''
        Search for items with a matching keyword.
        
        This method composes a keyword search, and will attempt to return
        'count' items.
        
        Parameters:
            keyword         : str keyword to search for
            count           : an int number of items that should be returned
                              zero or negative will try to return everything
        
        Returns:
            A list of dictionaries, items with matching keywords 
        '''
        search_result = list()
        self.log(f"entering", level="DEBUG")
        #
        #   Validate the minimum required parameters
        if not keyword: 
            self.log("Provide a keyword for a keyword search of TMDB.", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return search_result
        #
        #   Make sure there is an API key for this request
        token = self.getHeaderValue('Authorization')
        key = self.getRequestParam('api_key')
        if not key and not token:
            self.log("Set the API Key or Bearer Token to search TMDB", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return search_result
        if count <= 0:
            self.log(f"parameter count zero or negative was set to {TMDB_MAX_COUNT}", level="INFO")
            count = TMDB_MAX_COUNT
        elif count > TMDB_MAX_COUNT:
            self.log(f"parameter count {count} is larger than {TMDB_MAX_COUNT}, was set to {TMDB_MAX_COUNT}", 
                     level="INFO")
            count = TMDB_MAX_COUNT
        #
        #   Make sure this is handled as a keyword search
        self.setRequestAsKeywordSearch()
        #
        #   Set the parameter value
        self.setKeyword(keyword)
        #
        #   Queue the request and make it
        self.queueRequest()
        self.makeRequest()
        resp = self.nextResponse()
        if not resp:
            self.log(f"request returned an empty response or an error response", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return search_result
        data = resp.json()
        search_result.extend(data['results'])
        search_result_count = data['total_results']
        total_result_pages = data['total_pages']
        self.log(f"response page {data['page']}, have {len(search_result)} of {data['total_results']} possible ({data['total_pages']} pages)", 
                 level="DEBUG")
        #   If there was only one page of results, then we just return that
        if total_result_pages < 2:
            self.log(f"returning", level="DEBUG")
            return search_result
        #
        #   If there are additional results, then try to collect them
        #   by requesting each additional page - starting with page 2
        page = 2
        while (len(search_result) < count) and (len(search_result) < search_result_count):
            self.log(f"paging, requesting page {page}", level="DEBUG")
            self.setPage(page)
            self.queueRequest()
            self.makeRequest()
            resp = self.nextResponse()
            if not resp:
                self.log(f"request returned an empty response or an error response", level="DEBUG")
                self.log(f"returning", level="DEBUG")
                return search_result
            data = resp.json()
            search_result.extend(data['results'])
            self.log(f"response page {data['page']}, have {len(search_result)} of {data['total_results']} possible ({data['total_pages']} pages)", 
                     level="DEBUG")
            page += 1
            if (page > total_result_pages) or (page > TMDB_MAX_PAGE): break

        self.log(f"returning", level="DEBUG")
        return search_result
        

    ##########
    #
    #   REQUEST TYPE SETTING
    #
    ##########
    
    
    ###
    #   Set the object to perform a movie search
    #
    def setRequestAsMovieSearch(self):
        self.log(f"entering", level="DEBUG")
        self.setServiceEndpoint(self.tmdb_search_movie_service_endpoint)
        self.tmdb_request_is_movie = True      
        self.tmdb_request_is_keyword = False      
        self.tmdb_request_is_tv = False      
        key = self.getRequestParam('api_key')
        self.clearRequestParams()
        self.setAPIKey(key)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ###
    #   Set the object to perform a TV search
    #
    def setRequestAsTVSearch(self):
        self.log(f"entering", level="DEBUG")
        self.setServiceEndpoint(self.tmdb_search_tv_service_endpoint)
        self.tmdb_request_is_movie = False      
        self.tmdb_request_is_keyword = False      
        self.tmdb_request_is_tv = True      
        key = self.getRequestParam('api_key')
        self.clearRequestParams()
        self.setAPIKey(key)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ###
    #   Set the object to perform a keyword search
    #
    def setRequestAsKeywordSearch(self):
        self.log(f"entering", level="DEBUG")
        self.setServiceEndpoint(self.tmdb_search_keyword_service_endpoint)
        self.tmdb_request_is_movie = False      
        self.tmdb_request_is_keyword = True      
        self.tmdb_request_is_tv = False      
        key = self.getRequestParam('api_key')
        self.clearRequestParams()
        self.setAPIKey(key)
        self.log(f"returning", level="DEBUG")
        return
    

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
        self.log(f"entering", level="DEBUG")
        bearer_str = ""
        if token:
            bearer_str = f"Bearer {token}"
        self.setAuthorization(bearer_str)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ##
    #   This uses the "API Key" from TMDB as a key in the
    #   request parameters. This is another form of auth
    #   for TMDB
    #
    def setAPIKey(self, key=""):
        self.log(f"entering", level="DEBUG")
        self.setRequestParam('api_key',key)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ##
    #   Set a title as a query
    #
    def setTitle(self, title=""):
        self.log(f"entering", level="DEBUG")
        self.setQuery(title)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ##
    #   Set a keyword as a query
    #
    def setKeyword(self, keyword=""):
        self.log(f"entering", level="DEBUG")
        self.setQuery(keyword)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ##
    #   Set a query string or substring
    #
    def setQuery(self, query=""):
        self.log(f"entering", level="DEBUG")
        if not query:
            self.deleteRequestParam('query')
        else:
            self.setRequestParam('query',query)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ##
    #   Set the language of the release 
    #
    def setLanguage(self, lang=""):
        #   This parameter does not apply to keyword search
        if self.tmdb_request_is_keyword: return
        self.log(f"entering", level="DEBUG")
        if not lang:
            self.deleteRequestParam('language')
        else:
            self.setRequestParam('language',lang)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ##
    #   Search the year of the inital release, and all possible
    #   subsequent special release dates. Movies are sometiems
    #   re-released into theaters - or maybe a streaming release,
    #   or a video release - or ... there are lots of possible 
    #   reasons for an alternate release date
    #
    def setYear(self, year=""):
        #   This parameter does not apply to keyword search
        if self.tmdb_request_is_keyword: return
        self.log(f"entering", level="DEBUG")
        if not year:
            self.deleteRequestParam('year')
        else:
            if self.tmdb_request_is_movie:
                self.setRequestParam('year',str(year))
            else:
                #   The TV year search case
                try:
                    y = int(year)
                except:
                    raise Exception("Year must be an integer in range 1000 to 9999.")
                if (y < 1000) or (y > 9999):
                    raise Exception("Year must be an integer in range 1000 to 9999.")
                self.setRequestParam('year',y)
        self.log(f"returning", level="DEBUG")
        return
        
    
    ##
    #   Search the year of the initial movie release. This is probably
    #   what most people want to search. The first year it was released.
    #
    def setPrimaryReleaseYear(self, year=""):
        #   This parameter does not apply to keyword nor TV search
        if self.tmdb_request_is_keyword: return
        if self.tmdb_request_is_tv: return
        self.log(f"entering", level="DEBUG")
        if not year:
            self.deleteRequestParam('primary_release_year')
        else:
            self.setRequestParam('primary_release_year',str(year))
        self.log(f"returning", level="DEBUG")
        return
        
    
    ##
    #   Search the year of the initial TV air date. The original date
    #   is probably what people want to search. They are generally
    #   not looking for all of the rerun, syndication air dates.
    #
    def setFirstAirDateYear(self, year=""):
        #   This parameter does not apply to keyword nor movie search
        if self.tmdb_request_is_keyword: return
        if self.tmdb_request_is_movie: return
        self.log(f"entering", level="DEBUG")
        if not year:
            self.deleteRequestParam('first_air_date_year')
        else:
            self.setRequestParam('first_air_date_year',str(year))
            try:
                y = int(year)
            except:
                raise Exception("Year must be an integer in range 1000 to 9999.")
            if (y < 1000) or (y > 9999):
                raise Exception("Year must be an integer in range 1000 to 9999.")
            self.setRequestParam('first_air_date_year',y)
        self.log(f"returning", level="DEBUG")
        return
        
    
    ##
    #   Set the movie release region
    #
    def setRegion(self, region=""):
        #   This parameter does not apply to keyword nor TV search
        if self.tmdb_request_is_keyword: return
        if self.tmdb_request_is_tv: return
        self.log(f"entering", level="DEBUG")
        if not region:
            self.deleteRequestParam('region')
        else:
            self.setRequestParam('region',str(region))
        self.log(f"returning", level="DEBUG")
        return
    
    
    ##
    #   Set the page number to return, when there are a lot of results 
    #
    def setPage(self, page=0):
        self.log(f"entering", level="DEBUG")
        if not page:
            self.deleteRequestParam('page')
        else:
            self.setRequestParam('page',page)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ##
    #   Whether or not to include adult films in the response 
    #
    def adultFilms(self, adult="False"):
        #   This parameter does not apply to keyword search
        if self.tmdb_request_is_keyword: return
        self.log(f"entering", level="DEBUG")
        if not adult:
            self.deleteRequestParam('include_adult')
        else:
            self.setRequestParam('include_adult',adult)
        self.log(f"returning", level="DEBUG")
        return
        
#####
#   
#   END class Search definition
#   
#####

if __name__ == '__main__':
    print("Search.py is a class with no main()")


