#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: NYPBrowseRequest.py
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
#   https://nypost.com/tag/movie-reviews/
#   
#   The browse page can be indexed to go back in time for prior reviews
#   https://nypost.com/tag/movie-reviews/page/2/
#   https://nypost.com/tag/movie-reviews/page/75/
#   https://nypost.com/tag/movie-reviews/page/100/
#   https://nypost.com/tag/movie-reviews/page/102/
#
#   Looks like page 149 is the max
#
#   Things change ... as of Nov. 2024
#   Looks like page 103 is the max browse page
#   But maybe, somethimg more important is that there was a significant format change
#   around page 30, that makes movie reviews more parseable. So, we only really start
#   recognizing movie reviews aroune page 30
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
from rebert.classes.review.NYPost.NYPArticleRequest import NYPArticleRequest
from rebert.classes.review.base.constants import *

#####
#   
#   CONSTANTS
#   
#####


#####
#   
#   START class NYPBrowseRequest definition
#   
#####

###
#   A class/object that interacts with The New website to collect 
#   movie reviews.
#
class NYPBrowseRequest(ReviewBrowseBase):
    '''
    The NYPBrowseRequest connectes to The New York Post website and requests a 'browse' page
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
        #   
        #   This is our collector class
        self.__article_collector_class__ = NYPArticleRequest
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "nypost.com"
        #
        #   The NY Post has a couple different ways that it represents titles
        #   of the movie in an article title. The 'embedded' case is rare,  
        #   but needs special handling. These four regex, wille handle most
        #   of the cases with some checking after extraction. 
        rex = re.compile(r"^['\u2018](.*)['\u2019] [Rr]eview",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        rex = re.compile(r"\b\s['\u2018](.*)['\u2019] [Rr]eview",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        rex = re.compile(r"^['\u2018](.*)['\u2019] ",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        rex = re.compile(r"\b\s['\u2018](.*)['\u2019]",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://nypost.com")
        #   This is the service endpoint for the current reviews
        self.browse_service_endpoint = "/tag/movie-reviews"
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
        #   Run through all of the divs looking for those that have class story
        for d in divs:
            if ('class' in d.attrs) and ("story__text" in d['class']):
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
            #   An H3 element holds the article title, anchor href, and movie title
            heading = main_div.find('h3')
            #   Grab the link from the anchor <A ...> found in the heading
            url = heading.a['href']
            #print(f"URL: {url} ")
            #   The text of that first anchor is the title of the review article
            review_title = heading.a.text.strip()
            #print(f"reivew_title: {review_title} ")
        except:
            url = ""
            review_title = ""
        
        #   If we don't have a title for the review article then we're done
        if not review_title: 
            self.log(f"returning", level="DEBUG")
            return dict()
        
        #   See if the article title has a movie title
        title = self._extractMovieTitleFromArticleTitle_(review_title)
        if title:
            title = title.replace("\u2018","'").replace("\u2019","'")
            title = title.replace("\u00a0"," ")
        
        #   Try to extract the author
        author = ""
        subdivs = main_div.find_all("div")
        for d in subdivs:
            if ('class' in d.attrs) and ("flag--stamp--author" in d['class']):
                try:
                    author = d.a.text.strip()
                except:
                    author = ""
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
        #   This is not in all of the NYPost reviews - in fact this might not apply
        #   to NYPost reviews at all - this is almost standard clean up
        rtype = review['review_type'].lower()
        #   Keep stuff about movies and film
        if ('movie' in rtype) or ('film' in rtype):
            #   Don't keep if it is about streaming
            if ('streaming' in rtype):
                self._removed_reviews_.append(review)
                self.log(f"removed (streaming): '{review['title']}'", level="INFO")
                return dict()
            
            #   Don't keep if it is about DVD release
            elif ('dvd' in rtype):
                self._removed_reviews_.append(review)
                self.log(f"removed (on dvd): '{review['title']}'", level="INFO")
                return dict()
            
            #   Don't keep if it is about a film festival
            elif ('festival' in rtype):
                self._removed_reviews_.append(review)
                self.log(f"removed (film festival): '{review['title']}'", level="INFO")
                return dict()
        #
        #   Remove stuff that's not about movies - like music and theater
        else:
            self._removed_reviews_.append(review)
            self.log(f"removed (not movie/film): '{review['title']}'", level="INFO")
            return dict()
        #
        #   Only want actual reviewers - not services - only saw this service once
        if "associated press" == review['author'].lower():
            self._removed_reviews_.append(review)
            self.log(f"removed AP article'", level="INFO")
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
#   END class ReviewBrowseRequest definition
#   
#####

if __name__ == '__main__':
    print("ReviewBrowseRequest.py is a class with no main()")


