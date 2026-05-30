#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#   FILE: MovieInfo.py
#   REVISION: July, 2024
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   A web service class that implements some of the Movie information requests of
#   TMDB (The Movie Database) https://www.themoviedb.org
#
#   This class implements movie and keyword
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

TMDB_MOVIE_INFO_ENDPOINTS = ['account_states', 'alternative_titles', 'changes', 'credits', 'external_ids', 'images', 
                             'keywords', 'latest', 'lists', 'recommendations', 'release_dates', 'reviews', 'similar', 
                             'translations', 'videos']
TMDB_APPEND_BASICS = "external_ids"
TMDB_APPEND_REC_REV = "recommendations,reviews"
TMDB_APPEND_ALL = "alternative_titles,changes,credits,external_ids,images,keywords,recommendations,release_dates,reviews,similar,videos"

#
#
#
class MovieInfo(HTTPConnection):
    def __init__(self, name="TMDB-MovieInfo", logger=None, *args, **kwargs):
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
        #   The service endpoint has an embedded movie_id 
        #   We'll need to compose the service endpoint and then
        #   set it right before we queue the request
        self.tmdb_movie_request_path = "/3/movie/{movie_id}"
        self.tmdb_movie_active_path = ""
        #
        #   Set a rate limit so that rogue code won't abuse the site
        #   Docs say this API will allow up to 50 requests per second
        #   We'll stay below that
        self.setThrottleRate(rps=30.0)
        self.throttlingOn()
        #   Pick a random user agent to simulate a browser reqeust
        self.setUserAgent()
        #   Set a request header value to tell the server we accept JSON
        #   as the response data (required)
        self.setHeaderValue('accept', 'application/json')
        return
    
    
    ##
    #   A method that will get the movie details somewhat automatically.
    #   Just provide the movie_id and it will work.  
    #
    def getMovieDetails(self, movie_id=None, lang=None, append="", all=False):
        '''
        Return the details for a specific movie using the TMDB movie id.
        
        Parameters:
            movie_id        : an int, movie_id from a search
            lang            : a str of 2 character language code
            append          : a str, comma separated list of additional items
                              represented as the endpoint names
            all             : bool, True gets just about everything
        
        Returns:
            A list of dictionaries 
        '''
        result = list()
        self.log(f"entering", level="DEBUG")
        if not movie_id: 
            self.log("Must provide the TMDB movie id.", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return result
        
        token = self.getHeaderValue('Authorization')
        key = self.getRequestParam('api_key')
        
        if not key and not token:
            self.log("Set the API Key or Bearer Token to search TMDB", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return result

        self.setMovieID(movie_id)
        self.setServiceEndpoint(self.tmdb_movie_active_path)
        if lang:
            self.setLang(lang)
        
        appends = f"{TMDB_APPEND_BASICS}"
        if all:
            appends = f"{TMDB_APPEND_ALL}"
            if append:
                append_list = append.split(',')
                for endpoint in append_list:
                    ep = endpoint.lower()
                    if (ep in TMDB_MOVIE_INFO_ENDPOINTS) and (ep not in appends):
                        appends = f"{appends},{ep}"
            self.appendToResponse(appends)
        elif append:
            append_list = append.split(',')
            for endpoint in append_list:
                ep = endpoint.lower()
                if (ep in TMDB_MOVIE_INFO_ENDPOINTS) and (ep not in appends):
                    appends = f"{appends},{ep}"
        
        self.appendToResponse(appends)
        self.queueRequest()
        self.makeRequest()
        resp = self.nextResponse()
        result = resp.json()
        self.log(f"returning", level="DEBUG")
        return result
        


    ##
    #   A method that will get the movie recommendations and reviews somewhat automatically.
    #   Just provide the movie_id and it will work.  
    #
    def getMovieRecRev(self, movie_id=None):
        '''
        Return the details for a specific movie using the TMDB movie id,
        including a list of recommendations and a list of reviews
        
        Parameters:
            movie_id        : an int, movie_id from a search
        
        Returns:
            A dictionary containing a lot of information about the movie. The
            'recommendations' key will contain a list of recommendations from 
            TMDB users for other similarly liked movies. The 'reviews' key will
            contain a list of reviews of this movie by TMDB users.
        '''
        result = list()
        self.log(f"entering", level="DEBUG")
        if not movie_id: 
            self.log("Must provide the TMDB movie id.", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return result
        
        token = self.getHeaderValue('Authorization')
        key = self.getRequestParam('api_key')
        
        if not key and not token:
            self.log("Set the API Key or Bearer Token to search TMDB", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return result

        self.setMovieID(movie_id)
        self.setServiceEndpoint(self.tmdb_movie_active_path)
                
        self.appendToResponse(TMDB_APPEND_REC_REV)
        self.queueRequest()
        self.makeRequest()
        resp = self.nextResponse()
        result = resp.json()
        result['recommendations'] = result['recommendations']['results']
        result['reviews'] = result['reviews']['results']
        self.log(f"returning", level="DEBUG")
        return result
        


    ##
    #   A method that will get images related to this movie. This is the way to
    #   get a movie poster
    #   Just provide the movie_id and it will work.  
    #
    def getMoviePosters(self, movie_id=None, all_images=False):
        '''
        Return the details for a specific movie using the TMDB movie id,
        including a list of recommendations and a list of reviews
        
        Parameters:
            movie_id        : an int, movie_id from a search
            poster          : bool, return a movie poster link
        
        Returns:
            
        '''
        result = list()
        self.log(f"entering", level="DEBUG")
        if not movie_id: 
            self.log("Must provide the TMDB movie id.", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return result
        
        token = self.getHeaderValue('Authorization')
        key = self.getRequestParam('api_key')
        
        if not key and not token:
            self.log("Set the API Key or Bearer Token to search TMDB", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return result

        self.setMovieID(movie_id)
        images_service_endpoint = self.tmdb_movie_active_path+"/images"
        self.setServiceEndpoint(images_service_endpoint)
                
        self.queueRequest()
        self.makeRequest()
        resp = self.nextResponse()
        result = resp.json()
        #   Either just return posters or return all of it
        if not all_images:
            posters = result['posters']
            self.log(f"returning (poster data)", level="DEBUG")
            return posters
        
        self.log(f"returning (all image data)", level="DEBUG")
        return result
        


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
    
    
    ##
    #   Set a path parameter to make a movie specific search
    #   The movie id becomes part of the service endpoint so we
    #   embed the movie id into an 'active_path' and will use
    #   that active path when we make the request
    #
    def setMovieID(self, movie_id=0):
        if not movie_id:
            self.tmdb_movie_active_path = ""
        else:
            self.tmdb_movie_active_path = self.tmdb_movie_request_path.format(movie_id=movie_id)
        return
    
    
    ##
    #   Set a string of 
    #
    def appendToResponse(self, append=""):
        if not append:
            self.deleteRequestParam('append_to_response')
        else:
            self.setRequestParam('append_to_response',append)
        return
    
    ##
    #   Set the language of the release 
    #
    def setLanguage(self, lang=""):
        if not lang:
            self.deleteRequestParam('language')
        else:
            self.setRequestParam('language',lang)
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
#   END class MovieInfo definition
#   
#####

if __name__ == '__main__':
    print("MovieInfo.py is a class with no main()")


