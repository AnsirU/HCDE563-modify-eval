#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: APBrowseRequest.py
#   REVISION: March, 2026
#   CREATION DATE: July, 2025
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
#   https://apnews.com/hub/film-reviews
#   
#   There does not appear to be a mechanism to "page" to other reviews. If a page
#   other than page=1 is requested this will return an empty dictionary to indicate
#   that the page is not available.
#
#   March 2026 - This update modified tag identification to address a
#       top level format change for the AP browse page
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
###
#
#   Standard python modules
import json, copy, time, re
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
from rebert.classes.review.AP.APArticleRequest import APArticleRequest
from rebert.classes.review.base.constants import *

#####
#   
#   CONSTANTS
#   
#####
#
AP_MAX_REQUEST_COUNT = 3
#
#####
#   
#   START class APBrowseRequest definition
#   
#####

###
#   A class/object that interacts with the Slant Magazine website to collect 
#   movie reviews.
#
class APBrowseRequest(ReviewBrowseBase):
    '''
    The APBrowseRequest connectes to the Associated Press film review site and requests a  
    'browse' page that lists a set of recent movie reviews. The class will parse the 
    requested browse page to identify links to review articles, and then uses a 
    APArticleRequest instance to get data from those reviews.
    
    Attributes:
        browse_service_endpoint     - a string service endpoint for a basic browse
    
    Methods:
        getReviewsByBrowse()        - parses the browse page, returns review article data
        _parseHTMLPage_()           - parse the browse page HTML
        _extractArticleLinks_()     - extract URL, article links, for the review articles
        _filterReview_()            - filter review articles based on features
        _extractMovieTitleFromArticleTitle_()  - extract the movie title from article title

    '''
    def __init__(self, name="APBrowseRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   This is our collector class
        self.__article_collector_class__ = APArticleRequest
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "apnews.com"
        #   
        #   Add an ordered set of regex to extract movie titles
        #   The AP is really bad with movie titles. Extraction requires
        #   some regex and some text processing of the article title
        rex = re.compile(r"Movie Review:.*( '.*' ).*",
                        flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #   Special version for movie titles at the end of the article title
        rex = re.compile(r"Movie Review:.*( '.*'$)",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://apnews.com")
        #   This is the service endpoint for the current reviews
        self.browse_service_endpoint = "/hub/film-reviews" 
        self.setServiceEndpoint(self.browse_service_endpoint)
        #
        #   The AP was consistently rejecting the 'firefox' browser User-Agent with
        #   a 403 status code. The firefox simulated user agent string was updated
        #   in HTTPConnection to reflect the 2025 version of that string.
        #
        #   That appears to work, but the commented out code allowed testing of
        #   individual user agents to figure out which one was the problem.
        #
        #self.setUserAgent("chrome_2023")
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
            #
            #   Currently ONLY 1 PAGE - the AP doesn't really do paging
            self.log(f"page {page}, is not a valid page, no results returned", level="WARNING")
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
        #
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
        #   Find the first <main> tag
        main = html_parse.find('main')
        print(f"tag attrs {main.attrs}")
#        #
#        #   Looking for a specific main tag
#        main_content = ""
#        mains = html_parse.find_all('main')
#        for m in mains:
#            #   Running through the divs, look for one that is 'primary'
#            if 'class' in m.attrs and "SearchResultsModule-main" in m['class']:
#                main_content = m
#                break
        #
        #   Looking for a divs that are "PageList-items-item"
#        divs = main_content.find_all('div')
        divs = main.find_all('div')
        for d in divs:
            #   When we find this - its a single movie item - hopefully
            if 'class' in d.attrs and "PageList-items-item" in d['class']:
                #print(f"{d['class']=}")
                record = self._extractArticleLinks_(d)
                if record: 
                    review_list.append(record)
        self.log(f"returning", level="DEBUG")
        return review_list
        
        
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
        #   Grab the link from the first anchor <A ...> nested in the first H3
        url = main_div.h3.a['href']
        #
        #   The text of that first anchor is the title of the review article
        try:
            review_title = main_div.h3.a.text.strip()
        except:
            review_title = ""
        #
        #print(f"{review_title=}")
        #print(f"{url=}")
        #
        #
        #   If we don't have a title for the review article then we're done
        if not review_title: 
            self.log(f"returning", level="DEBUG")
            return dict()
        #
        #   Extract the title of the movie
        title = self._extractMovieTitleFromArticleTitle_(review_title)
        #
        #   There is no 'author' at this level
        #   There *is* a star rating - that could be extracted
        
        #   Now save the data for this article and return it
        record['title'] = title.strip()
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
        #   Filtering specific to the AP News reviews, review types
        rtype = review['review_type'].lower()
        #   Keep stuff about movies and film
        if 'movie' not in rtype and 'film' not in rtype:
            self._removed_reviews_.append(review)
            self.log(f"removed, not a movie review: '{review['title']}'", level="INFO")
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
        #   Before we try to use the default behavior, we need to standardize the
        #   current article title
        title_edit = review_title.replace("\u2018","'").replace("\u2019","'").replace("`","'")
        #
        #   Now, apply regex and extract title
        title = super()._extractMovieTitleFromArticleTitle_(title_edit)
        #
        #   Still need to clean the title
        title = title.strip()        
        title = title.replace("'","").strip()
        #   'title' should just be the title, but let's remove anything that
        #   might be a little odd off the end of the title - this is most often
        #   a comma character - because of the way the AP writes article titles
        if title and title[-1] in ".,:;-'\u2011\u2012\u2013\u2014\uFE58":
            title = title[:-1].strip()

        return title
       
#####
#   
#   END class APBrowseRequest definition
#   
#####

if __name__ == '__main__':
    print("APBrowseRequest.py is a class with no main()")


