#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: EbertBrowseRequest.py
#   REVISION: July, 2024
#   CREATION DATE: July, 2024
#   AUTHOR: David W. McDonald
#
#   A web service object to collect movie review text. This object starts by
#   collecting a review browse page - a web page that lists the reviews that are
#   available roughly by date. The page is parsed to collect the individual URLs
#   for the reviews listed on the browse page. This class then uses the
#   ReviewArticleRequest class to collect the text of the individual reviews.
#
#   The browse page 
#
#   The main page requested is a browse for current reviews
#   https://www.rogerebert.com/reviews
#   
#   The browse page can be indexed to go back in time for prior reviews
#   https://www.rogerebert.com/reviews/page/2/
#   https://www.rogerebert.com/reviews/page/3/
#   https://www.rogerebert.com/reviews/page/5/
#   https://www.rogerebert.com/reviews/page/75/
#   https://www.rogerebert.com/reviews/page/149/
#   https://www.rogerebert.com/reviews/page/499/
#
#   Looks like page 500 is the max
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
###
#
#   Standard python modules
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
from rebert.classes.review.base.ReviewBrowseBase import ReviewBrowseBase
from rebert.classes.review.Ebert.EbertArticleRequest import EbertArticleRequest
from rebert.classes.review.base.constants import *

#####
#   
#   CONSTANTS
#   
#####


#####
#   
#   START class EbertBrowseRequest definition
#   
#####

###
#   A class/object that interacts with The New website to collect 
#   movie reviews.
#
class EbertBrowseRequest(ReviewBrowseBase):
    '''
    The EbertBrowseRequest connectes to The New York Post website and requests a 'browse' page
    that lists a set of recent reviews for movies. The class will parse the requested browse 
    page to identify links to review articles, and then uses a ReviewArticleRequest instance to  
    get text of those reviews.
    
    Attributes:
        browse_service_endpoint     - string of the base browse request url

    Methods:
        getReviewsByBrowse()        - 
        _parseHTMLPage_()           - 
        _extractArticleLinks_()     - 
        _filterReview_()            - 
        
    '''
    def __init__(self, name="EbertBrowseRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   This is our collector class
        self.__article_collector_class__ = EbertArticleRequest
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "rogerebert.com"
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://www.rogerebert.com")
        #   This is the service endpoint for the current reviews
        self.browse_service_endpoint = "/reviews"
        self.setServiceEndpoint(self.browse_service_endpoint)
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
        #   Set the request to the default browse request
        self.setServiceEndpoint(self.browse_service_endpoint)
        mesg = f"{self.browse_service_endpoint}"
        #   Indexing really starts at page 2
        if page > 1:
            #   Check that we are not past our max
            if page < REVIEW_BROWSE_INDEX_MAX:
                #   This is a paged request so format the service endpoint to
                #   reflect the page that we want
                paged_endpoint = self.browse_service_endpoint+f"/page/{page}/"
                self.setServiceEndpoint(paged_endpoint)
                mesg = f"{paged_endpoint}"
            else:
                #   Outside the bounds - exit
                mesg = f"page {page} > {REVIEW_BROWSE_INDEX_MAX} (max)"
                self.log(f"skipping request, {mesg}", level="WARNING")
                self.log(f"returning", level="DEBUG")
                return review_list
        
        #   Clear out any prior list of review items that were filtered out
        #   If you want them, get them before starting a new request!
        self._removed_reviews_ = list()        
        
        #   Try to get a page
        self.queueRequest()
        self.log(f"requesting '{mesg}'", level="DEBUG")
        self.makeRequest()
        if self.responses():
            resp = self.nextResponse()
            text = resp.text
        else:
            mesg = "request did not return a page"
            self.log(f"{mesg}", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review_list
        
        #   Parse out the basic information from the 
        review_list = self._parseHTMLPage_(text)
        if browse_only:
            self.log(f"returning, browse_only=True", level="DEBUG")
            return review_list
        #   Now, get the individual article text - and filter the list so that
        #   it hopefully only contains movies/films
        review_list = self._getReviewContents_(review_list)

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
        #   No HTML page, return empty list
        if not text: 
            self.log(f"HTML text was empty!", level="WARNING")
            return review_list
        self.log(f"entering", level="DEBUG")
        
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(text,'html.parser')
        #   The page is composed div with class == story
        divs = html_parse.find_all('div')
        #
        #   Run through all of the divs looking for the one that has 'js--reviews'
        #   that one is the main container for a gridded set of reviews
        grid_columns = None
        for d in divs:
            if ('class' in d.attrs) and ("js--reviews" in d['class']):
                grid_columns = d
                break
        if not grid_columns:
            self.log(f"could not find the gridded columns", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review_list
        
        divs = grid_columns.find_all('div')
        for d in divs:
            #   In the grid, looking for 'column' divs
            if ('class' in d.attrs) and ("column" in d['class']):
                record = self._extractArticleLinks_(d)
                if record: 
                    review_list.append(record)
        self.log(f"returning", level="DEBUG")
        return review_list
    
    
    ###
    #   This parses the individual stories of the browse page to start filling
    #   out the record item
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
        try:
            #   An H5 element holds the article title, anchor href, and movie title
            heading = main_div.find('h5')
            #   Grab the link from the anchor <A ...> found in the heading
            url = heading.a['href']
            #   The text of that first anchor is the title of the review article
            review_title = heading.a.text.strip()
        except:
            url = ""
            review_title = ""
        
        #   If we don't have a title for the review article then we're done
        if not review_title: 
            self.log(f"returning", level="DEBUG")
            return dict()
        
        #   The article title and the movie title are the same - we'll do
        #   just a little fix up here to clean a title from special chars
        title = review_title.replace("\u00a0"," ")
        title = title.replace("\u2018","'").replace("\u2019","'")
        
        #   Extract the author of the review
        author = ""
        try:
            heading = main_div.find('h6')
            author = heading.text.strip()
        except:
            author = ""
        
        #   Extract the url of the movie poster in the interface
        try:
            poster_img = main_div.img
            poster_url = poster_img['src']
        except:
            poster_url = ""
        
        #   Now save the data for this article and return it
        record['title'] = title
        record['review_url'] = self.getHost()+url
        record['review_title'] = review_title
        record['author'] = author
        record['poster_url'] = poster_url
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
        #   If it meets the minimum fields for this site - then it's probably 
        #   a keeper review
        return review
        
        
#####
#   
#   END class EbertBrowseRequest definition
#   
#####

if __name__ == '__main__':
    print("EbertBrowseRequest.py is a class with no main()")


