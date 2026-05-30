#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: GuardianBrowseRequest.py
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
#   They restructured the browse page in July 2025. The revision nested review items
#   in unordered lists, and they changed the URLs for new reviews.
#
#   The browse page 
#
#   The main page requested is a browse for current reviews
#   https://www.theguardian.com/film+tone/reviews
#   
#   The browse page can be indexed to go back in time for prior reviews
#   https://www.theguardian.com/film+tone/reviews?page=4
#
#   As of roughly the end of November 2024 the last page is approx. 1260
#   https://www.theguardian.com/film+tone/reviews?page=1260
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
from rebert.classes.review.Guardian.GuardianArticleRequest import GuardianArticleRequest
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
GUARD_MOVIE_COF = "century of film"
GUARD_MOVIE_FOTW = "film of the week"
GUARD_MOVIE_OBSERVER = "The Observer"
GUARD_BOOK_BOTD = "Book of the day"


#####
#   
#   START class GuardianBrowseRequest definition
#   
#####

###
#   A class/object that interacts with The Guardian website to collect 
#   movie reviews.
#
class GuardianBrowseRequest(ReviewBrowseBase):
    '''
    The GuardianBrowseRequest connectes to The Guardian website and requests a 'browse' 
    page that lists a set of recent reviews for cultural events. The class will parse the 
    requested browse page to identify links to review articles, and then uses a 
    GuardianArticleRequest instance to get data from those reviews.
    
    Attributes:
        browse_service_endpoint     - a string service endpoint for a basic browse
    
    Methods:
        getReviewsByBrowse()        - parses the browse page, returns review article data
        _parseHTMLPage_()           - parse the browse page HTML
        _extractArticleLinks_()     - extract URL, article links, for the review articles
        _filterReview_()            - filter review articles based on features
        _extractMovieTitleFromArticleTitle_()  - extract the movie title from article title

    '''
    def __init__(self, name="GuardianBrowseRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   This is our collector class
        self.__article_collector_class__ = GuardianArticleRequest
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "theguardian.com"
        #   
        #   Add an ordered set of regex
        rex = re.compile(r"^(.*) [Rr]eview[: ]*[-\u2013\u2014]*",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://www.theguardian.com")
        #   This is the service endpoint for the current reviews
        self.browse_service_endpoint = "/film+tone/reviews"
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
        #   Indexing really starts at page 2
        if page > 1:
            #   Check that we are not past our max
            if page < REVIEW_BROWSE_INDEX_MAX:
                self.setRequestParam('page',page)
                mesg = f"{self.browse_service_endpoint}?page={page}"
            else:
                mesg = f"index {page} > {REVIEW_BROWSE_INDEX_MAX} (max)"
                self.log(f"{mesg}", level="WARNING")
                self.log(f"returning", level="DEBUG")
                return review_list
        else:
            #   Make sure there are no left over params from
            #   a prior request
            self.clearRequestParams()
            mesg = f"{self.browse_service_endpoint}"
        
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
        
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(text,'html.parser')
        #   The page is composed of sections - each section reflects the
        #   dated that the review article was published or posted
        sections = html_parse.find_all('section')
        #   Run through all of the sections looking for the sections that
        #   have dates in the id attribute
        for s in sections:
            #   Within each section there is an unordered list <ul> that we want
            list_elts = s.find_all('ul')
            for l in list_elts:
                record = self._extractArticleLinks_(l)
                if record: 
                    review_list.append(record)
            
            #
            #   OLD structure was named div - prior to July 2025
            #divs = s.find_all('div')
            #for d in divs:
            #    #   Running through the divs, look for one that has a sepcific value
            #    if 'class' in d.attrs and "fc-item__header" in d['class']:
            #        record = self._extractArticleLinks_(d)
            #        if record: 
            #            review_list.append(record)
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
        #   Grab the link from the first anchor <A ...> found in the div
        url = main_div.a['href']
        if not url.startswith(self.getHost()):
            url = self.getHost()+url
        
        #   The text of an H3 header is the title
        try:
            review_title = main_div.h3.text.strip()
        except:
            review_title = ""
        #
        #   Clean up of the review article title before moving on
        if GUARD_MOVIE_FOTW in review_title:
            review_title = review_title.partition(GUARD_MOVIE_FOTW)[2]
        elif GUARD_MOVIE_OBSERVER in review_title:
            review_title = review_title.partition(GUARD_MOVIE_OBSERVER)[2]
        elif GUARD_MOVIE_COF in review_title:
            review_title = review_title.partition(GUARD_MOVIE_COF)[2]
        elif GUARD_BOOK_BOTD in review_title:
            review_title = review_title.partition(GUARD_BOOK_BOTD)[2]
        review_title = review_title.strip()

        #   If we don't have a title for the review article then we're done
        if not review_title: 
            self.log(f"returning", level="DEBUG")
            return dict()
        
        #
        #   Extract the title of the movie
        title = self._extractMovieTitleFromArticleTitle_(review_title)
        if title:
            title = title.replace("\u2018","'").replace("\u2019","'")
            title = title.replace("\u00a0"," ")
        
        
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
#   END class GuardianBrowseRequest definition
#   
#####

if __name__ == '__main__':
    print("GuardianBrowseRequest.py is a class with no main()")


