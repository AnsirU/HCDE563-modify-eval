#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: RSBrowseRequest.py
#   REVISION: July, 2025
#   CREATION DATE: June, 2024
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
#   https://www.rollingstone.com/tv-movies/
#   
#   The browse page can be indexed to go back in time for prior reviews
#   https://www.rollingstone.com/tv-movies/page/101/
#
#   As of roughly the end of August 2025 the last page is approx. 1000
#   https://www.rollingstone.com/tv-movies/page/1000/
#
#   It looks like they simply refuse to serve any 'pages' above 1000
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
from rebert.classes.review.RStone.RSArticleRequest import RSArticleRequest
from rebert.classes.review.base.constants import *

#####
#   
#   CONSTANTS
#   
#####
#
#   The URL actually has some important information about whether or not the
#   item is a movie review. We'll keep a list of things that we should
#   filter out - if the URL contains the string.
#
#   We want to keep it if it has "/tv-movie-reviews" - for sure, but there
#   might be some other things we might want as well.
#
RS_URL_FILTER_LIST = [
    "/tv-movie-lists/",
    "/tv-movie-features/",
    "/tv-movie-news/"
]
#
#   For testing - we can just turn off the URL filtering by uncommenting
#RS_URL_FILTER_LIST = []
#
#
#####
#   
#   START class RSBrowseRequest definition
#   
#####

###
#   A class/object that interacts with The Guardian website to collect 
#   movie reviews.
#
class RSBrowseRequest(ReviewBrowseBase):
    '''
    The RSBrowseRequest connectes to the Rolling Stone website and requests a 'browse' 
    page that lists a set of recent reviews for cultural events. The class will parse the 
    requested browse page to identify links to review articles, and then uses a 
    RSArticleRequest instance to get data from those reviews.
    
    Attributes:
        browse_service_endpoint     - a string service endpoint for a basic browse
    
    Methods:
        getReviewsByBrowse()        - parses the browse page, returns review article data
        _parseHTMLPage_()           - parse the browse page HTML
        _extractArticleLinks_()     - extract URL, article links, for the review articles
        _filterReview_()            - filter review articles based on features
        _extractMovieTitleFromArticleTitle_()  - extract the movie title from article title

    '''
    def __init__(self, name="RSBrowseRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   This is our collector class
        self.__article_collector_class__ = RSArticleRequest
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "rollingstone.com"
        #   
        #   Add an ordered set of regex
        #   '<movie_title>': article tag title
        #   ‘Happy Gilmore 2’: Hooray! Adam Sandler’s Brawling Golf Bro Is Back
        rex = re.compile(r"^['‘](.*)['’][: ].*",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   article title with '<movie_title>'
        #   Nerdy Vengeance Will Be Rami Malek’s in ‘The Amateur’
        rex = re.compile(r".* ['‘](.*)['’]$",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   article title with '<movie_title>' in the middle
        #   <<< need example >>>
        rex = re.compile(r".* ['‘](.*)['’] .*",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://www.rollingstone.com")
        #   This is the service endpoint for the current browse page
        self.browse_service_endpoint = "/tv-movies"
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
        #   No HTML text, return empty list
        if not text: 
            self.log(f"HTML text was empty!", level="WARNING")
            return review_list
        self.log(f"entering", level="DEBUG")
        
        #
        #   The article collector relies on HTML5Lib - so we'll use that
        #   parser here in the browse collector
        try:
            #html_parse = BeautifulSoup(text,'html.parser')
            html_parse = BeautifulSoup(text,'html5lib')
        except Exception as ex:
            msg = str(ex)
            self.log(f"Exception: {msg}", level="WARNING")
            self.log(f"This browse collector relies on the python html5lib module.", level="WARNING")
            self.log(f"You will need to install html5lib to use this browse collector.", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review_list

        feat_content = ""
        main_content = list()
        divs = html_parse.body.main.find_all('div')
        for d in divs:
            if 'class' in d.attrs:
            #   The 'featured' stories are always before the story-grid
                if "featured-stories" in d['class']:
                    feat_content = d
                    continue
                #   Once we find a 'story-grid' we can stop processing divs
                if "story-grid" in d['class']:
                    main_content.append(d)
        
        if feat_content:
            story_items = feat_content.find_all("div")
            for story in story_items:
                if 'class' in story.attrs and 'story' in story['class']:
                    record = self._extractArticleLinks_(story)
                    if record: 
                            review_list.append(record)
        
        if main_content:
            for mc in main_content:
                list_items = mc.ul.find_all("li")
                for item in list_items:
                    record = self._extractArticleLinks_(item)
                    if record: 
                            review_list.append(record)
            
        self.log(f"returning {len(review_list)} items", level="DEBUG")
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
        #   Grab the link from the anchor in the h3 header
        try:
            url = main_div.h3.a['href']
            if not url.startswith(self.getHost()):
                url = self.getHost()+url
            review_title = main_div.h3.a.text.strip()
        except:
            url = ""
            review_title = ""
        #        
        #   If we don't have a title for the review article then we're done
        if not review_title: 
            self.log(f"returning", level="DEBUG")
            return dict()
        #
        #   Now, remove items that are probably not movie reviews based on
        #   strings in the URL
        for filt in RS_URL_FILTER_LIST:
            if filt in url:
                self.log(f"ignoring '{filt}' item", level="DEBUG")
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
        if ('movie' in rtype) or ('film' in rtype):
            pass
        #
        #   Remove stuff that's not about movies - like music and theater
        else:
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
        title = super()._extractMovieTitleFromArticleTitle_(review_title)
        #
        while title and title[-1] in ",.;:":
            title = title[:-1]
            
        return title
       
#####
#   
#   END class RSBrowseRequest definition
#   
#####

if __name__ == '__main__':
    print("RSBrowseRequest.py is a class with no main()")


