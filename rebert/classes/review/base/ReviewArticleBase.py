#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: ReviewArticleBase.py
#   REVISION: June, 2025
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   This is a base class for making article requests for movie review websites. Most movie
#   sites will dedicate a single page to the review for a movie. This class provides an
#   abstract model for requesting and parsing the HTML of the review article page. This
#   class should be subclassed. The method prototypes provide a somewhat standardized way
#   to think about getting the parsing done.
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
###
#
#   Standard python modules
#
import json, copy, re
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
#   This base class is a type of HTTPConnection to connect to the
#   different websites 
#
from rebert.classes.base.HTTPConnection import HTTPConnection
from rebert.classes.review.base.constants import *

#####
#   
#   START class ReviewArticleBase definition
#   
#####

###
#    
#   
#
class ReviewArticleBase(HTTPConnection):
    '''
    The ReviewArticleBase class is a subclass of HTTPConnection that connects to a
    review website to request a specified web page. This is assumed to be a review
    article. The class parses the HTML web page to collect the review text and fill out  
    a MOVIE_REVIEW_DATA_TEMPLATE (dictionary).
    
    This ReviewArticleBase should be sub-classed to create a review article collector
    for a specific review site.
    
    The main method getReviewArticle() will make an HTTP request for the specific article
    and then call the local method _parseHTMLPage_() with the resulting page. A subclass
    should override _parseHTMLPage_() and any other local methods to parse the specific
    review text.
    
    The current subclasses of this class are:
        APArticleRequest            - The Associated Press movie reviews
        EbertArticleRequest         - Roger Ebert movie reviews
        FTArticleRequest            - Film Threat movie reviews
        GuardianArticleRequest      - The Guardian movie reviews
        NYPArticleRequest           - The New York Post movie reviews
        PluggedInArticleRequest     - Plugged In movie reviews
        SlantMagArticleRequest      - Slant Magazine movie reviews
        SRArticleRequest            - Screen Rant movie reviews
        THRArticleRequest           - The Hollywood Reporter movie reviews

    Attributes:
        __review_template__     - holds a copy of MOVIE_REVIEW_DATA_TEMPLATE that can
                                  be tailored to the specifics of the class
        __title_regex__         - a list of regular expressions, regex, that will be
                                  used to try and extract the movie title from the
                                  article title.
    
    Methods:
        getReviewArticle()      - request a movie review page, parse and return results
        _parseHTMLPage_()       - starts parsing of the HTML of the article page
        _extractArticleTitle_() - extract the article title
        _extractMovieTitleFromArticleTitle_()
                                - extract the movie title from the article title
        _extractContent_()      - extract the main text of the review
        _extractReviewType_()   - extract the type of this review
        _extractStandfirst_()   - extract a sub-headline 
        _extractRating_()       - extract the "star" rating or a score
        _extractAuthor_()       - extract the author of the review
        _extractPostDate_()     - extract the date the review was posted
        _extractPosterURL_()    - extract the URL of the movie poster
        
    '''
    def __init__(self, name="ReviewArticleBase", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #
        #   Set a rate limit so that rogue code won't abuse the site
        #   This is quite slow.
        self.setThrottleRate(rps=REBERT_ARTICLE_COLLECTOR_RPS)
        self.throttlingOn()
        #
        #   Pick a random user agent to simulate a browser reqeust
        self.setUserAgent()
        #
        #   A local copy of the review template. This can be modified
        #   and then the modified version should be used when creating
        #   new instances of a review
        self.__review_template__ = MOVIE_REVIEW_DATA_TEMPLATE.copy()
        #
        #   An ordered list of regular expressions that should be applied
        #   when trying to extract a movie title from a movie review
        #   article title
        self.__title_regex__ = list()
        return
        
    
    ###
    #   This method requests an article page, parses the HTML and returns a
    #   MOVIE_REVIEW_DATA_TEMPLATE (dictionary)
    #
    def getReviewArticle(self, url=None, review=None):
        '''
        This requests a review article page using either the supplied URL or the
        'review_url' field in a review dictionary. Must have one of the two
        parameters for a request.
        
        Parameters:
        url:        a URL to an article to be requested and processed
        review:     a MOVIE_REVIEW_DATA_TEMPLATE dictionary with at least the
                    'review_url' field completed
        
        Returns
            a more complete, filled out, MOVIE_REVIEW_DATA_TEMPLATE, or None
        '''
        #   Make sure we have at least one of these two parameters
        if not (url or review): 
            self.log(f"'url' and 'review' were both empty!", level="WARNING")
            return review
        self.log(f"entering", level="DEBUG")
        #   Set which URL to use
        if review:
            url = review['review_url']
            self.log(f"using URL from review parameter", level="DEBUG")
        else:
            self.log(f"using url parameter", level="DEBUG")
        url_lower = url.lower()
        host = self.getHost()
        #   If the URL already has the host as prefix then remove it
        if url_lower.startswith(host):
            url_lower = url_lower.partition(host)[2]
        else:
            self.log(f"non-matching host in URL, request not made", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return review
        #   Use the resulting trimmed URL as the page path for the request
        self.setRequestPath(url_lower)
        #   Try to get the page
        self.queueRequest()
        self.log(f"requesting '{url_lower}'", level="DEBUG")
        self.makeRequest()
        if self.responses():
            resp = self.nextResponse()
            page = resp.text
        else:
            #   No page, return whatever was in 'review' or None
            resp_info = self.getPriorRequests()
            if resp_info:
                error = resp_info[0]['error']
                mesg = f"HTTP response code: {error['status_code']}, {error['error_message']}"
                self.log(f"{mesg}", level="WARNING")
            
            mesg = "request did not return a page"
            self.log(f"{mesg}", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review
        
        #   Got a page, parse it and fill out the review dictionary
        review = self._parseHTMLPage_(page,review)
        #   Save the URL if it was not part of a 'review' parameter
        if review and not review['review_url']:
            review['review_url'] = url
        
        self.log(f"returning", level="DEBUG")
        return review


    ###
    #   This parses the HTML by extracting the 'article' from the
    #   page and extracting text from specific 'div' that contain
    #   the review
    #
    def _parseHTMLPage_(self, text=None, review=None):
        '''
        This parses the HTML article page and tries to complete the
        MOVIE_REVIEW_DATA_TEMPLATE dictionary record.
        
        Parameters:
        text:       the HTML of the page to be parsed
        review:     a movie review template dictionary
        
        Returns
            a more complete, filled out, MOVIE_REVIEW_DATA_TEMPLATE, or None
        '''
        self.log(f"method should be overridden", level="WARNING")
        return review



    def _extractArticleTitle_(self, title_div=None):
        '''
        Parses the main body of the article to extract the review text.
        
        Parameters:
        title_div:      a div that contains the review article title
        
        Returns
            a string of the article title
        '''
        self.log(f"method should be overridden", level="WARNING")
        return str()



    ###
    #   This takes the title of a review article, applies one or more regular
    #   expressions to extract the movie title. The regular expressions are
    #   set up when a subclass is defined.
    #
    def _extractMovieTitleFromArticleTitle_(self, review_title=None):
        '''
        Extracts a movie title from a review article title
        
        Parameters:
        review_title:   the title of the review article
        
        Returns
            the title of the extracted movie or an empty string
        '''
        #
        #   Run through the ordered, compiled regular expressions to find
        #   any matching data
        for regex in self.__title_regex__:
            matches = regex.findall(review_title)
            if matches:
                return matches[0]
        return str()
    
    
    def _extractContent_(self, blob_div=None):
        '''
        Parses the main body of the article to extract the review text.
        
        Parameters:
        blob_div:       a single div with the review items, there may
                        be sub-items that are parsed to extract text
        
        Returns
            a string of the review text
        '''
        self.log(f"method should be overridden", level="WARNING")
        return str()
        
    
    def _extractReviewType_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the type of this review
        
        Parameters:
        blob_div:      a div that contains the review type
        
        Returns
            a string of the standfirst text
        '''
        self.log(f"method should be overridden", level="WARNING")
        return str()    
    
    
    def _extractStandfirst_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract an article sub-heading text that
        is descriptive of the movie
        
        Parameters:
        blob_div:      a div standfirst text in it
        
        Returns
            a string of the standfirst text
        '''
        self.log(f"method should be overridden", level="WARNING")
        return str()    
        

    def _extractRating_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract movie rating info
        
        Parameters:
        blob_div:     a div with the ratings info
        
        Returns
            a list with a numeric score and a rating string
        '''
        self.log(f"method should be overridden", level="WARNING")
        return list()    
    
    
    def _extractAuthor_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the author name
        
        Parameters:
        blob_div:     a div with the author info
        
        Returns
            a string of the author info
        '''
        self.log(f"method should be overridden", level="WARNING")
        return str()    
        

    def _extractPostDate_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the article post date
        
        Parameters:
        blob_div:         a div with the posting date information
        
        Returns
            a list consisting of the post date string and a standardized
            timestamp of that posting date
        '''
        self.log(f"method should be overridden", level="WARNING")
        return list()   
    
    
    def _extractPosterURL_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract a movie poster URL
        
        Parameters:
        blob_div:     a div with the poster URL
        
        Returns
            a string, poster URL
        '''
        self.log(f"method should be overridden", level="WARNING")
        return str()
        
    
#####
#   
#   END class ReviewArticleBase definition
#   
#####

if __name__ == '__main__':
    print("ReviewArticleBase.py is a class with no main()")


