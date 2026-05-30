#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: PluggedInBrowseRequest.py
#   REVISION: December, 2024
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
#   https://www.pluggedin.com/movie-reviews/
#   
#   The browse page can be indexed to go back in time for prior reviews
#   https://www.pluggedin.com/movie-reviews/page/2/
#   https://www.pluggedin.com/movie-reviews/page/3/
#   https://www.pluggedin.com/movie-reviews/page/5/
#   https://www.pluggedin.com/movie-reviews/page/75/
#   https://www.pluggedin.com/movie-reviews/page/250/
#   https://www.pluggedin.com/movie-reviews/page/473/
#
#   Looks like page 473 is the max
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
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
from rebert.classes.review.PluggedIn.PluggedInArticleRequest import PluggedInArticleRequest
from rebert.classes.review.base.constants import *

#####
#   
#   CONSTANTS
#   
#####


#####
#   
#   START class PluggedInBrowseRequest definition
#   
#####

###
#   A class/object that interacts with PluggedIn website to collect 
#   movie reviews.
#
class PluggedInBrowseRequest(ReviewBrowseBase):
    '''
    The PluggedInBrowseRequest connectes to PluggedIn website and requests a 'browse' page
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
    def __init__(self, name="PluggedInBrowseRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   This is our collector class
        self.__article_collector_class__ = PluggedInArticleRequest
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "pluggedin.com"
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://www.pluggedin.com")
        #   This is the service endpoint for the current reviews
        #self.browse_service_endpoint = "/movie-reviews"
        self.browse_service_endpoint = "/movie-reviews/"
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
        #   The page is composed div with archives-right in class 
        #   This is the "right hand" column list of movie reviews
        reviews_column = None
        divs = html_parse.find_all('div')
        for div in divs:
            if 'class' in div.attrs and 'archives-right' in div['class']:
                reviews_column = div
                break
        #
        #   Once we have that right hand column, then, look through all of
        #   the divs in that colum for ones that have 'post-row'
        if reviews_column:
            divs = reviews_column.find_all('div')
            for row in divs:
                if 'class' in row.attrs and 'post-row' in row['class']:
                    record = self._extractArticleLinks_(row)
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
        main_div:       a single movie row entry in the browse page
        
        Returns
            a single MOVIE_REVIEW_DATA_TEMPLATE partially filled, or empty dict
        '''
        self.log(f"entering", level="DEBUG")
        record = self.__review_template__.copy()
        content_div = None
        divs = main_div.find_all("div")
        for div in divs:
            if 'class' in div.attrs and 'archive-col-right' in div['class']:
                content_div = div
        #print(f"{content_div=}")
        
        try:
            #   Looks like there should only be one anchor in this block
            #   Grab the link from the anchor <A ...> found in the heading
            anchor = content_div.find('a')
            url = anchor['href'].strip()
            review_title = anchor.text.strip()
        except:
            url = ""
            review_title = ""
        
        #print(f"{review_title=}")
        #print(f"{url=}")
        
        #   If we don't have a title for the review article then we're done
        if not review_title: 
            self.log(f"returning", level="DEBUG")
            return dict()
        
        #   The article title and the movie title are the same - we'll do
        #   just a little fix up here to clean a title from special chars
        review_title = review_title.replace("\u00a0"," ")
        review_title = review_title.replace("\u2018","'").replace("\u2019","'")
        review_title = review_title.replace("\u201c",'"').replace("\u201d",'"')
        review_title = review_title.replace("\u2013","-").replace("\u2014","-")
        title = review_title
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
        #   
        #   Here we're going to check that the review minimally includes something
        #   to indicate that it might be a movie - this could mistake some TV shows
        #   as movies - because they could be 'streaming'
        if review:
            if 'tv' in review['review_type']:
                self._removed_reviews_.append(review)
                self.log(f"removed item review_type: '{review['review_type']}'", level="INFO")
                return None
            if 'episode' in review['review_type']:
                self._removed_reviews_.append(review)
                self.log(f"removed item review_type: '{review['review_type']}'", level="INFO")
                return None
            if 'theaters' in review['review_type']:
                return review
            if 'dvd' in review['review_type']:
                return review
            if 'streaming' in review['review_type']:
                return review
            self._removed_reviews_.append(review)
            self.log(f"removed unrecognized review_type: '{review['review_type']}'", level="INFO")
            return dict()
        return review
        
        
#####
#   
#   END class PluggedInBrowseRequest definition
#   
#####

if __name__ == '__main__':
    print("PluggedInBrowseRequest.py is a class with no main()")


