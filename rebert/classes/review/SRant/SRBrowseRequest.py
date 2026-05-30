#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: SRBrowseRequest.py
#   REVISION: June, 2024
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
#   https://screenrant.com/movie-reviews/
#   
#   The browse page can be indexed to go back in time for prior reviews
#   https://screenrant.com/movie-reviews/2/
#   https://screenrant.com/movie-reviews/3/
#   https://screenrant.com/movie-reviews/23/
#   https://screenrant.com/movie-reviews/75/
#
#   Looks like page 75 is the max
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
from rebert.classes.review.SRant.SRArticleRequest import SRArticleRequest
from rebert.classes.review.base.constants import *

#####
#   
#   CONSTANTS
#   
#####

#####
#   
#   START class SRBrowseRequest definition
#   
#####

###
#   A class/object that interacts with The New website to collect 
#   movie reviews.
#
class SRBrowseRequest(ReviewBrowseBase):
    '''
    The SRBrowseRequest connectes to the Screen Rant website and requests a 'browse' page
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
        #   This is our collector class
        self.__article_collector_class__ = SRArticleRequest
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "screenrant.com"
        #   
        #   Add an ordered set of regex
        rex = re.compile(r"^(.*) Review:",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        rex = re.compile(r"^(.*) Review [-\u2013\u2014]",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Set attributes specific to this website
        self.setHost("https://screenrant.com")
        #   This is the service endpoint for the current reviews
        self.browse_service_endpoint = "/movie-reviews"
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
                paged_endpoint = self.browse_service_endpoint+f"/{page}/"
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
    def _parseHTMLPage_(self, page=None):
        '''
        Parses the browse page to extract title and links.
        
        Parameters:
        page:       the HTML text of the browse page
        
        returns:    a list of review dictionary items, or None
        '''
        review_list = list()
        #   No HTML page, return empty list
        if not page: 
            self.log(f"HTML text was empty!", level="WARNING")
            return review_list
        self.log(f"entering", level="DEBUG")
        #
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(page,'html.parser')
        #
        #   First, try to find the 'featured' reviews in the browse page
        feat_section = None
        divs = html_parse.find_all("div")
        for d in divs:
            if ('class' in d.attrs and "listing-featured" in d['class'] and
                "featured-4-pin-single" in d['class']):
                feat_section = d
                break
        if feat_section:       
            articles = feat_section.find_all('article')
        else:
            articles = list()
        #
        #   Extract the article links in the featured part of a browse page
        for a in articles:
            record = self._extractArticleLinks_(a)
            if record: 
                review_list.append(record)
        #
        #   Next, try to find the latest reviews in the page
        main_section = None
        sections = html_parse.find_all("section")
        for s in sections:
            if 'class' in s.attrs and "listing-content" in s['class']:
                main_section = s
                break
        #
        #   The main_section is composed of divs that contain a 'card'
        #   for each movie review - we need to parse out each card
        if main_section:
            divs = main_section.find_all('div')
        else:
            divs = list()
        #   Run through all of the divs looking for those that have class article
        for d in divs:
            if (('class' in d.attrs) and ("display-card" in d['class']) and
                ("article" in d['class'])):
                record = self._extractArticleLinks_(d)
                if record: 
                    review_list.append(record)
        self.log(f"returning", level="DEBUG")
        return review_list
        
        
    ###
    #   This parses the individual stories of the browse page to start filling
    #   out the record item
    #
    def _extractArticleLinks_(self, div=None):
        '''
        Parses the browse page to extract title and links.
        
        Parameters:
        div:        a single div (BeautifulSoup) item that contains review basics
        
        returns:    single MOVIE_REVIEW_DATA_TEMPLATE partically filled, or None
        '''
        self.log(f"entering", level="DEBUG")
        record = self.__review_template__.copy()
        #   For a main body section of a review browse page
        #   An H5 element holds the article title, anchor href, and movie title
        heading = div.find('h5')
        if heading:
            #   Grab the link from the anchor <A ...> found in the heading
            url = heading.a['href']
        else:
            #   For a 'feature' section of a review browse page
            #   An H3 element has article title, anchor href, and movie title
            heading = div.find('h3')
            if heading:
                url = heading.a['href']

        #   ScreenRant URLs don't include the host - let's fix that
        if not url.startswith(self.getHost()):
            url = self.getHost()+url
        #   The text of that first anchor is the title of the review article
        review_title = heading.a.text.strip()
        #   See if the article title has a movie title at the very start
        title = self._extractMovieTitleFromArticleTitle_(review_title)
                
        author = ""
        sub_divs = div.find_all("div")
        for d in sub_divs:
            if ('class' in d.attrs) and ("w-author-name" in d['class']):
                author = d.a.text.strip()
                break
        
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
        if not review: return dict()
        #
        #   For some review sites, we can get a review type and use
        #   that to make sure we have a movie. Screen Rant does not do it
        #   that way. We'll assume that a movie title, a review body, and
        #   a movie review rating get us a movie.
        #
        #   For ScreenRant make sure we found a rating
        if not review['rating_str']:
            self._removed_reviews_.append(review)
            self.log(f"removed item without a rating '{review['title']}'", level="INFO")
            return dict()
        #   If we pass these thresholds, we'll call it a movie review
        if not review['review_type']:
            review['review_type'] = "movie review"
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
#   END class SRBrowseRequest definition
#   
#####

if __name__ == '__main__':
    print("SRBrowseRequest.py is a class with no main()")


