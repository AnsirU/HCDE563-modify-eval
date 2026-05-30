#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: THRBrowseRequest.py
#   REVISION: July, 2024
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
#   https://www.hollywoodreporter.com/c/movies/movie-reviews/
#   
#   The browse page can be indexed to go back in time for prior reviews
#   https://www.hollywoodreporter.com/c/movies/movie-reviews/page/20/
#   https://www.hollywoodreporter.com/c/movies/movie-reviews/page/100/
#   https://www.hollywoodreporter.com/c/movies/movie-reviews/page/625/
#
#   Looks like page 625 is the max
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
from rebert.classes.review.THR.THRArticleRequest import THRArticleRequest
from rebert.classes.review.base.constants import *

#####
#   
#   CONSTANTS
#   
#####
#
#   Some constants that help with the extraction of the
#   review type - and help filter out non-review contents
#
THR_NOTEBOOK = "Critic’s Notebook:"
THR_WEEKEND = "In Theaters This Weekend:"
THR_CRITICS_PICKS = "Critics Pick the Best"

#####
#   
#   START class THRBrowseRequest definition
#   
#####

###
#   A class/object that interacts with The Hollywood Reporter website to collect 
#   movie reviews.
#
class THRBrowseRequest(ReviewBrowseBase):
    '''
    The THRBrowseRequest connectes to The Hollywood Reporter website and requests a 'browse'
    page that lists a set of recent reviews for movies. The class will parse the requested  
    browse page to identify links to review articles, and then uses a THRArticleRequest   
    instance to get text of those reviews.
    
    Attributes:
        browse_service_endpoint     - string of the base browse request url

    Methods:
        getReviewsByBrowse()        - 
        _parseHTMLPage_()           - 
        _extractArticleLinks_()     - 
        _filterReview_()            - 
        _extractMovieTitleFromArticleTitle_()
    '''
    def __init__(self, name="ReviewBrowseRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   This is our collector class
        self.__article_collector_class__ = THRArticleRequest
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "hollywoodreporter.com"
        #   
        #   Add an ordered set of regex
        rex = re.compile(r"^['\u2018](.*)['\u2019]: Film",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        rex = re.compile(r"^['\u2018](.*)['\u2019] Review:",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        rex = re.compile(r"^['\u2018](.*)['\u2019] ",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #   Set attributes specific to this website
        self.setHost("https://www.hollywoodreporter.com")
        #
        #   This is the service endpoint for the current reviews
        self.browse_service_endpoint = "/c/movies/movie-reviews/"
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
            page = resp.text
        else:
            mesg = "request did not return a page"
            self.log(f"{mesg}", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review_list
        
        #   Parse out the basic information from the 
        review_list = self._parseHTMLPage_(page)
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
        main_section = html_parse.main.section
        #   The page is composed div with class == story
        divs = main_section.find_all('div')
        #   Run through all of the divs looking for those that have class story
        for d in divs:
            if ('class' in d.attrs) and ("story" in d['class']):
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
        #   An H3 element holds the article title, anchor href, and movie title
        heading = main_div.find('h3')
        if not heading: return dict()
        try:
            #   Grab the link from the anchor <A ...> found in the heading
            url = heading.a['href']
            #   The text of that first anchor is the title of the review article
            review_title = heading.a.text.strip()
        except:
            url = ""
            review_title = ""
        
        #   See if the article title has a movie title at the very start
        title = self._extractMovieTitleFromArticleTitle_(review_title)
        #
        #   Suppress articles that might look like reviews but are not
        #   standard reviews - these might be collected - but probably
        #   for some other purpose - they may not be movie specific
        if title.startswith(THR_NOTEBOOK) or title.startswith(THR_WEEKEND):
            return None
        if THR_CRITICS_PICKS in title:
            return None
        
        author = ""
        list_items = main_div.find_all("li")
        for item in list_items:
            author = item.text.strip()
            if author and author.startswith("By "):
                author = author.partition(" ")[2].strip()
                break
            else:
                author = ""

        #   Now save the data for this article and return it
        record['title'] = title
        record['review_url'] = url
        record['review_title'] = review_title
        record['author'] = author
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
        if not title and not ('review') in review_title:
            title = review_title
        ##
        ##   This cleaning technique is a little too aggressive. It cleans the title
        ##   but also removes valuable title characters on the 'end' of a title
        ##
        ##   Remove special characters from the start
        #while title and (title[0] in ".,:;-'\u2018\u2019\u2011\u2012\u2013\u2014\uFE58\""):
        #    title = title[1:].strip()
        ##
        ##   Remove special characters from the end
        #while title and (title[-1] in ".,:;-'\u2018\u2019\u2011\u2012\u2013\u2014\uFE58\""):
        #    title = title[:-1].strip()
        #
        #   This title cleaning is a little less aggressive, but can result in titles
        #   with some extra characters on the end - that should be cleaned
        #   Remove special characters from the start and end
        while (title and (title[0] in ".,:;-'\u2018\u2019\"") and 
                (title[-1] in ".,:;-'\u2018\u2019\"")):
            title = title[1:].strip()
            if title:
                title = title[:-1].strip()
        if title and title[-1] in '\u2011\u2012\u2013\u2014\uFE58':
            title = title[:-1].strip()
        return title
    

#####
#   
#   END class THRBrowseRequest definition
#   
#####

if __name__ == '__main__':
    print("THRBrowseRequest.py is a class with no main()")


