#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: ReviewBrowseBase.py
#   REVISION: June, 2025
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   This is a base class for making browse requests for movie review websites. The model
#   is that most movie review sites have a browse page that allows the users to see a
#   simple overview of the movies that have been reviewed.
#
#   This base class prototypes a set of standard methods - standardized names - that form
#   a type of template that can be used to create a browse class implementation for almost
#   any of the review sites that we might want to collect.
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
#   START class ReviewBrowseBase definition
#   
#####


###
#   
#   
#   
class ReviewBrowseBase(HTTPConnection):
    '''
    The ReviewBrowseBase connectes is a base class - a type of template - to create more
    specific browse request classes. Those classes implement the methods (suggested by this
    class) and are used to request reviews for movies by first finding movies with a
    browse and then requesting the invidiual movie reviews with an appropriate subclass
    of ReviewArticleBase.
    
    The current subclasses of this class are:
        APBrowseRequest         - The Associated Press movie reviews
        EbertBrowseRequest      - Roger Ebert movie reviews
        FTBrowseRequest         - Film Threat movie reviews
        GuardianBrowseRequest   - The Guardian movie reviews
        NYPostBrowseRequest     - The New York Post movie reviews
        PluggedInBrowseRequest  - Plugged In movie reviews
        SlantMagBrowseRequest   - Slant Magazine movie reviews
        SRBrowseRequest         - Screen Rant movie reviews
        THRBrowseRequest        - The Hollywood Reporter movie reviews
    
        
    Attributes:
        _removed_reviews_           - a list that contains the reviews that were 'filtered' out
        __review_template__         - a local copy of the movie review template
        __title_regex__             - an ordered list of compiled regular expressions that are
                                      used to extract movie titles from review article titles
        __article_collector__       - a private instance of ReviewArticleRequest used to collect
                                      review article content
        __article_collector_class__ - the class of article collector that will be used if needed
        __article_collector_rate__  - the collection rate for the article collector

    
    Methods:
        getExcludedItems()          - Returns a list of reviews that have been filtered out
        getReviewsByBrowse()        - This is the call that returns the list of movie reviews
        getReviewsUntil()           - Search back 'until' to collect reviews from a browse page
        nextReviews()               - Get the next browse page, and the next set of reviews
        _parseHTMLPage_()           - Top level, method that starts the parsing of the page
        _extractArticleLinks_()     - Tries to extract article links from the page
        _getReviewContents_()       - Makes a request to get an article page
        _filterReview_()            - Post processing to exclude, filter out reviews
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
        #   Set a rate limit so that rogue code won't abuse a site
        self.setThrottleRate(rps=REBERT_BROWSE_COLLECTOR_RPS)
        self.throttlingOn()
        #
        #   Pick a random user agent to simulate a browser reqeust
        self.setUserAgent()
        #
        #   Many of the movie review 'browse' websites will support a
        #   type of random access (e.g., page=10 then page=3, page=15).
        #   A few of the sites - do not support that type of access.
        #   The code can be forced to simulate that, but it is easier
        #   on the review site to use it in a mode aligned with the
        #   underlying model. This flag can help the browse collector 
        #   code behave appropriately.
        self._supports_random_access_ = True
        #
        #   A local copy of the review template. This can be modified
        #   and then the modified version should be used when creating
        #   new instances of a review
        self.__review_template__ = MOVIE_REVIEW_DATA_TEMPLATE.copy()
        #
        #   An ordered list of regular expressions that should be applied
        #   when trying to extract a movie title from a movie review
        #   article title - set by a subclass
        self.__title_regex__ = list()
        #
        #   An article collector object, only create it when needed
        self.__article_collector__ = None
        self.__article_collector_class__ = None
        #
        #   This list will track the items that are removed when the
        #   list of collected reviews is filtered for just the film
        #   or movies.
        self._removed_reviews_ = list()
        #
        #   The 'current' browse page - the last fulfilled request
        #   This is most useful when using the nextReviews() method
        self._current_page_ = -1
        return
        
    
    ###
    #   Return the list of review items that were filtered out, mostly non-movie
    #   related reviews
    #
    def getExcludedItems(self):
        '''Get a list of the reviewed items that were removed as likely not movie related.'''
        self.log(f"entering", level="DEBUG")
        result = self._removed_reviews_
        self._removed_reviews_ = list()
        self.log(f"entering", level="DEBUG")
        return result


    ###
    #   This method collects the browse page. It will optionally deliver
    #   just the results from the browse page.
    #
    def getReviewsByBrowse(self, page=0, browse_only=False):
        '''
        This requests a review browse page. If the page request is succesful this
        calls method _parseHTMLPage_() to extract review article links. It then
        uses the resulting review_list to create an article request object to
        collect each of the review articles in the review_list
        
        Parameters:
        page:           the index of the browse page to request, parse and collect
        browse_only:    a boolean, if True returns just the results of the browse
                        parse, By default it returns the full article.
        
        Returns
            a list of review dictionary items, or an empty list
        '''
        self.log(f"method should be overridden", level="WARNING")
        return list()


    ###
    #   This method collects the browse page and review articles until a
    #   given date.
    #
    def getReviewsUntil(self, until="", days_prior=0):
        '''
        This performs some validation on the 'until' date to make sure it looks
        like a reasonable date.
        
        Parameters:
        until:          a date string in the format "YYYY-MM-DD" - will not return anything
                        older than the specified date
        days_prior:     the number of days prior to today, the number of days in the past 
                        to stop looking for reviews
        
        Returns
            a list of review dictionary items, or an empty list
        '''
        self.log(f"entering", level="DEBUG")
        review_list = list()
        #
        #   Perform some simple consistency checks on the 'until' value
        if until:
            try:
                #   Try to parse the formate YYYY-MM-DD
                ud = datetime.strptime(until,"%Y-%m-%d")
                until = until.replace("-","")+"000000"
            except:
                try:
                    #   Try to parse the formate YYYYMMDD
                    ud = datetime.strptime(until,"%Y%m%d")
                    until = until+"000000"
                except:
                    #   Neither format works - error condition
                    self.log(f"'until' parameter '{until}', is not a recognized format",
                            level="DEBUG")
                    until = ""
        #
        #   Either the format of until is now good - or until is not set
        #   We'll try to create a reasonable 'until' to use for looking back
        if not until:
            #   Set up an timedelta offset - how far back to go
            if days_prior > 0 and days_prior < REVIEW_BROWSE_PRIOR_MAX:
                offset_days = timedelta(days=days_prior)
            else:
                offset_days = timedelta(days=REVIEW_BROWSE_PRIOR_OFFSET)
            #   Use the offset to set up a timestamp string that is
            #   put in to the 'until' variable
            until_date = datetime.now() - offset_days
            ts = str(until_date).partition(" ")[0]
            until = ts.replace("-","")+"000000"
        
        #
        #   At this point we should have a usable until date
        self.log(f"Looking for reviews 'until' {until}",
                 level="DEBUG")
        #
        #   Now page through the browse pages collecting, until we find a review
        #   that is older than the until date
        page = 1
        past_date = False
        while not past_date:
            #   If it supports random access, then access by page number
            #   otherwise, use the nextReview() approach
            if self._supports_random_access_:
                reviews = self.getReviewsByBrowse(page)
            else:
                reviews = self.nextReviews()
            #print(f"Found {len(reviews)} on page {page}")
            if not reviews: break

            self.log(f"Checking the posting/publishing date on {len(reviews)} articles",
                    level="DEBUG")
            #print(f"Checking the posting/publishing date")
            for r in reviews:
                #   Convert the date timestamp to a similar format
                ts = r['review_date_ts'].replace(" ","").replace("-","").replace(":","")
                #print(f"    Is {until} < {ts} : started with '{r['review_date_ts']}'")
                #
                #   If there is no timestamp, then include this in the list
                if not ts:
                    review_list.append(r)
                    continue
                #
                #   We have a timestamp, so check
                if ts >= until:
                    review_list.append(r)
                else:
                    past_date = True
                    break
            page += 1
            
        self.log(f"returning", level="DEBUG")
        return review_list



    ###
    #   This method requests the 'next' browse page, and the articles from
    #   that page. Optionally, it will just return the browse results
    #
    def nextBrowsePage(self, browse_only=False, start_at=0):
        '''
        This method will request the 'next' browse page and the associated
        review article content. 
        
        Parameters:
        browse_only:    a boolean, if True returns just the results of the
                        browse parse. By default it returns the full article.
        start_at:       an integer page number, index, where the code should
                        start returning data.
        
        Returns
            a list of review dictionary items, or an empty list
        '''
        review_list = list()
        self.log(f"entering", level="DEBUG")
        #
        #   This is sort of 'automatic' for random access - with the
        #   caveat that the getReviewsByBrowse() also needs to update the
        #   current page if it is called on its own.
        if self._supports_random_access_:
            if start_at and (self._current_page_ < start_at):
                page = start_at
            else:
                page = 1
            #   Make sure we're requesting the 'next' page
            if (self._current_page_ > 0) and (self._current_page_ > start_at):    
                page = self._current_page_ + 1
            #   Now request that page
            review_list = self.getReviewsByBrowse(page,browse_only)
            #   If we got a browse page, update the current page to reflect
            #   the page that we got and return the data
            if review_list: self._current_page_ = page
            self.log(f"returning", level="DEBUG")
            return review_list
        else:
            #
            #   If it's not random access, then the method needs to be
            #   overridden for the correct behavior
            self.log(f"method should be overridden", level="WARNING")
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
        self.log(f"method should be overridden", level="WARNING")
        return list()
        
        
    ###
    #   This parses the individual stories of the browse page to start filling
    #   out movie data records
    #
    def _extractArticleLinks_(self, main_div=None):
        '''
        Parses the browse page to extract title and links.
        
        Parameters:
        main_div:       a single div with the body of the browse page
        
        Returns
            a single MOVIE_REVIEW_DATA_TEMPLATE partially filled, or empty dict
        '''
        self.log(f"method should be overridden", level="WARNING")
        return dict()
    
    
    ###
    #   This takes a list composed of partially completed MOVIE_REVIEW_DATA_TEMPLATE
    #   dictionaries. This uses the URL field and an article collector object to
    #   request the review, parse the review, and then decide if the review should
    #   be kept, collected. 
    #
    def _getReviewContents_(self, review_list=None):
        '''
        Requests the article pages in the review_list.
        
        This uses an article collector class, provided when a browse class is
        defined, to request invidiual articles. The results of each review
        request are then filtered by the _filterReview_() method.
        
        Parameters:
        review_list:    a list of MOVIE_REVIEW_DATA_TEMPLATE partially filled
        
        returns:        a filtered set of movie/film reviews
        '''
        if not review_list: 
            self.log(f"review_list was empty!", level="WARNING")
            return review_list
        self.log(f"entering", level="DEBUG")
        
        #   This will hold the reviews that are filtered for inclusion
        collected_reviews = list()
        #   Initialize a collector once and use the same one each time
        if self.__article_collector_class__:
            coll_class = self.__article_collector_class__
            if not self.__article_collector__:
                try:
                    #   We need an object that will actually do the collecting
                    coll = coll_class(name="Browse_Request_Managed",
                                      logger=self.getLogger())
                    self.__article_collector__ = coll
                except:
                    self.__article_collector__ = None
                    coll_type = str(type(self.__article_collector_class__))
                    self.log(f"could not instantiate {coll_type}", 
                             level="WARNING")
        else:
            self.log(f"self.__article_collector_class__ has not been set", 
                     level="WARNING")

        #
        #   Run through each of the items (URLs) collected from the parse
        #   of the browse page - request and parse that review article
        #   filling out the review in the review list - lastly, filter
        #   reviews that do not look like movie reviews
        for review in review_list:
            r = self.__article_collector__.getReviewArticle(review=review)
            #
            #   Now we filter to make sure the resulting list is basically
            #   just movies
            keep = self._filterReview_(r)
            if keep:
                collected_reviews.append(r)
                self.log(f"keep review: '{r['title']}'", level="INFO")
        
        self.log(f"removed {len(self._removed_reviews_)} items", level="DEBUG")
        self.log(f"kept {len(collected_reviews)} items", level="DEBUG")
        self.log(f"returning", level="DEBUG")
        return collected_reviews
        
        
    ###
    #   This filters the review. This base level validates that the review
    #   has three basic elements, title, author, and review body.
    #
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
        if not review['title']:
            self._removed_reviews_.append(review)
            self.log(f"removed item with empty 'title' field", level="INFO")
            return None
        if not review['review']:
            self._removed_reviews_.append(review)
            self.log(f"removed item with empty 'review' field: '{review['title']}'", level="INFO")
            return None
        if not review['author']:  
            self._removed_reviews_.append(review)
            self.log(f"removed item with empty 'author' field: '{review['title']}'", level="INFO")
            return None
        return review
    

    
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
    

#####
#   
#   END class ReviewBrowseBase definition
#   
#####

if __name__ == '__main__':
    print("ReviewBrowseBase.py is a class with no main()")


