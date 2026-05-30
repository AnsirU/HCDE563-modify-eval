#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: OMDbAPI.py
#   REVISION: July, 2024
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   A web service class to connect to OMDb (Open Movie Database). This service is modest
#   and provides basic movie information. The documentation for the API is rather 
#   straight forward and can be found at:
#   https://www.omdbapi.com
#   
#   You need an API key to use this service. 
#   http://www.omdbapi.com/?apikey=[yourkey]&<other parameters>
#
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
OMDBAPI_MEDIA_TYPES = ['movie', 'series', 'episode']
OMDBAPI_PLOT_LENGTHS = ['short', 'full']
OMDBAPI_MAX_PAGE = 100
OMDBAPI_MAX_COUNT = 1000

#
#
#
class OMDbAPI(HTTPConnection):
    def __init__(self, name="OMDbAPI", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #
        #   Set attributes specific to this host - note not an https
        self.setHost("http://www.omdbapi.com")
        #   Set a rate limit so that rogue code won't abuse the site
        self.setThrottleRate(rps=1.0)
        self.throttlingOn()
        #   Pick a random user agent to simulate a browser reqeust
        self.setUserAgent()
        #   Default setting is as search. The API implements either search
        #   requests or information requests. The allowed parameters will
        #   vary depending on whether the API is searching the database
        #   or requesting specific information.
        self.omdb_request_is_search = True      
        return
 
    ##
    #   A method that performs the search request somewhat automatically,
    #   just provide the title and it will work.  
    #
    def movieSearch(self, title=None, year=None, media=None, count=10):
        '''
        Find and return a list of movies in OMDb that match the provided
        parameters.
        
        This method composes a request with the given parameters and 
        makes the request. It extracts the results data from the response
        to generate the reults list. This method will attempt to return 
        the 'count' number of items if there are at least that many items
        that match the provided parameters.
        
        Parameters:
            title           : str of the movie title, or title substring
            year            : an int four digit year of the movie release
            media           : a str of the media type, movie, series or episode
            count           : an int number of items that should be returned
        
        Returns:
            a list of dictionaries with a schema specified by OMDb. This
            should include the 'Title', 'Year', 'imdbID', 'Type' and
            'Poster'.
        '''
        search_result = list()
        self.log(f"entering", level="DEBUG")
        if not title: 
            self.log("Provide a search title to search OMDbAPI.", level="WARNING")
            return search_result
        key = self.getRequestParam('apikey')
        if not key:
            self.log("Set the API Key to search OMDbAPI", level="WARNING")
            return search_result
        if count > OMDBAPI_MAX_COUNT:
            self.log("Count is larger than the max, 1000, setting to 1000", level="INFO")
            count = OMDBAPI_MAX_COUNT

        self.setRequestAsSearch()

        self.setTitle(title)
        if year:
            self.setYear(year)
        if media:
            ml = media.lower()
            if ml in OMDBAPI_MEDIA_TYPES:
                self.setMediaType(ml)
            else:
                self.log("'{media}' is not a valid type, ignored.", level="INFO")
        
        self.queueRequest()
        self.makeRequest()
        resp = self.nextResponse()
        try:
            data = resp.json()
            search_result.extend(data['Search'])
            try:
                search_result_count = int(data['totalResults'])
            except:
                search_result_count = 0
        except:
            data = resp.text
            if '"Error":' in data:
                self.last_error = data
                self.log(f"returning", level="DEBUG")
                return search_result
                    
        page = 2
        while (len(search_result) < count) and (search_result_count >= count):
            self.log(f"paging, requesting page {page}", level="DEBUG")
            self.setPage(page)
            self.queueRequest()
            self.makeRequest()
            resp = self.nextResponse()
            try:
                data = resp.json()
                search_result.extend(data['Search'])
            except:
                data = resp.text
                if '"Error":' in data:
                    self.last_error = data
                    break
            page += 1
            if page >= OMDBAPI_MAX_PAGE: break

        self.log(f"returning", level="DEBUG")
        return search_result
    
    
    ##
    #   Get information for one specific film from the OMDb
    #
    def movieInfo(self, title=None, imdbid=None, year=None, media=None, plot=None):
        '''
        Request information for one specific movie.
        
        This method returns the DB information for one specific film. One of either
        the title or imdbid parameter is required. If title is not specific the
        response will be one closest match film. If you don't have the exact title
        then the year is probably the next best thing to get what you want
        
        Parameters:
            title           : str of the movie title, or title substring
            imdbid          : str of the imdbID movie identifier
            year            : an int four digit year of the movie release
            media           : a str of the media type, movie, series or episode
            plot            : a str, 'short' or 'full' for the plot synopsis
        
        Returns:
            a dictionary of various OMDb fields
        '''
        info_result = dict()
        self.log(f"entering", level="DEBUG")
        
        if not title and not imdbid: 
            self.log("Provide either title or imdbID to get movie info.", level="WARNING")
            return info_result
       
        key = self.getRequestParam('apikey')
        if not key:
            self.log("Set the API Key to request movie info", level="WARNING")
            return info_result

        self.setRequestAsInfo()
        
        if imdbid:
            self.setIMDbID(imdbid)
        else:
            self.setTitle(title)
        if year:
            self.setYear(year)
        if media:
            ml = media.lower()
            if ml in OMDBAPI_MEDIA_TYPES:
                self.setMediaType(ml)
            else:
                self.log("'{media}' is not a valid type, ignored.", level="INFO")
        if plot:
            pl = plot.lower()
            if pl in OMDBAPI_PLOT_LENGTHS:
                self.setPlotLength(pl)
            else:
                self.log("'{plot}' is not a valid plot length, ignored.", level="INFO")
        
        self.queueRequest()
        self.makeRequest()
        resp = self.nextResponse()
        try:
            info_result = resp.json()
        except:
            data = resp.text
            if '"Error":' in data:
                self.last_error = data
        self.log(f"returning", level="DEBUG")
        return info_result
    

    ##########
    #
    #   REQUEST TYPE SETTING
    #
    ##########
    
    
    ##
    #   Set the request type to be an informational request
    #   The object either makes "search" requests or information requests
    #
    def setRequestAsInfo(self):
        self.omdb_request_is_search = False
        key = self.getRequestParam('apikey')
        self.clearRequestParams()
        self.setAPIKey(key)
        return
    
    
    ##
    #   Set the request type to be a search
    #   The object either makes "search" requests or information requests
    #
    def setRequestAsSearch(self):
        self.omdb_request_is_search = True
        key = self.getRequestParam('apikey')
        self.clearRequestParams()
        self.setAPIKey(key)
        return
    

    ##########
    #
    #   REQUEST PARAMETER MANAGEMENT
    #
    ##########
    
    
    ##
    #   Set the API Key
    #
    def setAPIKey(self, key=""):
        self.setRequestParam('apikey',key)
        return
    
    
    ##
    #   Set a title string
    #
    def setTitle(self, title=""):
        if self.omdb_request_is_search:
            self.deleteRequestParam('i')
            self.deleteRequestParam('t')
            self.setRequestParam('s',title)
        else:
            self.deleteRequestParam('i')
            self.deleteRequestParam('s')
            self.setRequestParam('t',title)
        return
    
    
    ##
    #   Set the IMDb ID as the information 
    #
    def setIMDbID(self, id=""):
        if self.omdb_request_is_search:
            raise Exception("Request type is 'search'. The IMDb ID cannot be used for a movie 'search' request.")
        else:
            self.deleteRequestParam('t')
            self.deleteRequestParam('s')
            self.setRequestParam('i',id)
        return
    
    
    ##
    #   Set the size of the plot information - 'short' or 'full' 
    #
    def setPlotLength(self, l=""):
        if self.omdb_request_is_search:
            raise Exception("Request type is 'search'. The 'plot' length is not part of a 'search' request.")
        else:
            plot = l.lower()
            self.setRequestParam('plot',plot)
        return
    
    
    ##
    #   Set the year of the movie release 
    #
    def setYear(self, year=""):
        if not year:
            self.deleteRequestParam('y')
        else:
            self.setRequestParam('y',str(year))
        return
    
    
    ##
    #   Set the type of media for this information request or for the search 
    #
    def setMediaType(self, mtype=""):
        if not mtype:
            self.deleteRequestParam('type')
        else:
            self.setRequestParam('type',mtype)
        return
    
    
    ##
    #   Set the format of the response - can be json or xml
    #   defaults to json 
    #
    def setFormat(self, r="json"):
        if not r:
            self.deleteRequestParam('r')
        else:
            self.setRequestParam('r',r)
        return
    
    
    ##
    #   Set the page number to return, when there are a lot of results 
    #
    def setPage(self, page=0):
        if not page:
            self.deleteRequestParam('page')
        else:
            self.setRequestParam('page',page)
        return
    
    
#####
#   
#   END class OMDbAPI definition
#   
#####

if __name__ == '__main__':
    print("OMDbAPI.py is a class with no main()")


