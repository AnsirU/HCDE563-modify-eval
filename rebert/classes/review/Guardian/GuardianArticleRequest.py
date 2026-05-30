#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: GuardianArticleRequest.py
#   REVISION: March, 2026
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   A web service object to collect review article text. The main entry is through
#   the method getReviewArticle(). Just pass it a URL or a partially complete
#   MOVIE_REVIEW_DATA_TEMPLATE (it looks for the 'review_url' in that record).
#
#   March 2026 - updates to the star rating extraction and to the post date extraction
#       for certain types of postings
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
from rebert.classes.review.base.ReviewArticleBase import ReviewArticleBase
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
GUARD_BOOK_BOTD = "book of the day"
#
#   Some reviews have a closing sentence related to release information
#   that is not consistent - and can be removed.
GUARD_IN_CINEMAS = "is out in cinemas"
GUARD_ON_DIGITAL = "is on digital platforms"
#
#   Guardian uses a star rating system that draws an SVG image
#   of either empty or full stars. This is the SVG drawing of a
#   filled star. It looks like there are no half stars in 
#   The Guardian rating system.
#
#<path fill-rule="evenodd" clip-rule="evenodd" d="m19.151 21.336-2.418-7.386L23 9.348l-.312-.989h-7.75L12.546 1h-1.092L9.087 8.36H1.312L1 9.347l6.267 4.602-2.366 7.386.806.624L12 17.357l6.293 4.603.858-.624Z"></path>
#
#   Ok, one of the problems here is that this string is ever so slightly changed.
#   For example, swapping one "space" character with a "non-breaking space" will
#   make the string look the same, but will break a simple string.startswith()
#   comparison. One way would be to make the check really short
#
#GUARD_FILLED_STAR = "m19.151 21.336-2.418-7.386L23 9.348l-.312-.989h-7.75L12.547 1h-1.092L9.087" 
GUARD_FILLED_STAR = "m19.151" 
GUARD_EMPTY_STAR = "m14.381"

GUARD_FILLED_STAR_CLASS = "dcr-hxw8zi" 
GUARD_EMPTY_STAR_CLASS = "dcr-1m1u7z0"




#####
#   
#   START class GuardianArticleRequest definition
#   
#####

###
#   A class/object that interacts with The Guardian website to collect 
#   review articles.
#
class GuardianArticleRequest(ReviewArticleBase):
    '''
    The GuardianArticleRequest class is a subclass of ReviewArticleBase that connects to 
    The Guardian website to request a specified article. This is assumed to be a review article, 
    hopefully a movie review. The class parses the HTML web page to collect the review text and 
    fill out a MOVIE_REVIEW_DATA_TEMPLATE (dictionary).
    
    Attributes:
        No attributes beyond those inherited from HTTPConnection
    
    Methods:
        getReviewArticle()  - can be used to request the page, returns a
        _parseHTMLPage_()       - starts parsing of the HTML of the article page
        _extractArticleTitle_() - extract the article title
        _extractAuthor_()       - extract the author of the review
        _extractStandfirst_()   - extract a sub-headline 
        _extractRating_()       - extract the "star" rating
        _extractContent_()      - extract the main text of the review
        _extractReviewType_()   - extract the type of this review
        _extractPostDate_()     - extract the date the review was posted
        _extractMovieTitleFromArticleTitle_()
                                - extract the movie title from the article title

    '''
    def __init__(self, name="GuardianArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
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
        review_dict = super().getReviewArticle(url=url,review=review)
        return review_dict


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
        #   No HTML page, return empty list
        if not text: 
            self.log(f"HTML text was empty!", level="WARNING")
            return review
        self.log(f"entering", level="DEBUG")
        #
        #   Initialize variables for the values we want to collect
        title = ""          # the movie title
        review_title = ""   # the article title
        standfirst = ""     # a one-liner about the review or movie
        body = ""           # the main text of the review
        post_date = list()  # a list of posting date info
        rating = list()     # a list of the star rating info
        author = ""         # the author's by-line
        review_type = ""    # the item being reviewed
        #
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(text,'html.parser')
        #   The review is contained within an <article ...> tag
        article = html_parse.find('article')
        #   Details of the review are in a set of divs
        #   Find all the divs
        divs = article.find_all('div')
        #   Look through each div
        for div in divs:
            if 'data-gu-name' not in div.attrs: continue
            #   The interesting divs have specific attribute values
            if div['data-gu-name']=="standfirst":
                standfirst = self._extractStandfirst_(div)
                if not rating:
                    rating = self._extractRating_(div)
                continue
            if div['data-gu-name']=="body":
                body = self._extractContent_(div)
                continue
            if div['data-gu-name']=="headline":
                review_title = self._extractArticleTitle_(div)
                title = self._extractMovieTitleFromArticleTitle_(review_title)
                if not rating:
                    rating = self._extractRating_(div)
                continue
        #
        #   Need to prioritize the 'standfirst' ratings or the ratings
        #   get picked out wrong
        if not rating:
            for div in divs:
                if 'data-gu-name' not in div.attrs: continue
                if div['data-gu-name']=="media":
                    if not rating:
                        try:
                            figure = div.figure.div
                            rating = self._extractRating_(figure)
                            break
                        except:
                            rating = list()
        #
        #   The page 'aside' is a side panel that contains the post date
        #   and author by-line for the review.
        asides = article.find_all('aside')
        for aside in asides:
            if not author:
                author = self._extractAuthor_(aside)
            if 'data-gu-name' not in aside.attrs: continue
            if aside['data-gu-name']=="title":
                review_type = self._extractReviewType_(aside)
                continue
            if aside['data-gu-name']=="meta":
                post_date = self._extractPostDate_(aside)
                #print(f"post_date: {post_date}")
                if not author:
                    try:
                        author = aside.a.text.strip()
                    except:
                        pass
        #
        #   Supposing we collected at least the body of an article
        #   then we'll fill out the review record as best possible
        if body:
            #   Create a new one if one was not provided
            if not review:
                review = self.__review_template__.copy()
            if author:
                review['author'] = author
            if title:
                review['title'] = title
            if review_title:
                review['review_title'] = review_title
            review['review_type'] = review_type
            #
            #   If we found a rating, then it should be two parts
            if rating:
                review['rating'] = rating[0]
                review['rating_str'] = rating[1]
            #
            #   We're merging the one liner headline with the body
            if standfirst:
                if standfirst[-1] in ".!?'\"-":
                    review['review'] = standfirst+"\n"+body
                else:
                    review['review'] = standfirst+".\n"+body
            else:
                review['review'] = body
            #   
            #   If we found a post date it should be in two parts
            if post_date:
                review['review_date_str'] = post_date[0]
                review['review_date_ts'] = post_date[1]
        
        self.log(f"returning", level="DEBUG")
        return review



    def _extractArticleTitle_(self, blob_div=None):
        '''
        Parses the main body of the article to extract the review title
        
        Parameters:
        blob_div:      a div that contains the review article title
        
        Returns
            a string of the article title
        '''
        review_title = ""
        try:
            review_title = blob_div.h1.text.strip()
            #   Some clean up of the review article title before moving on
            if GUARD_MOVIE_FOTW in review_title:
                review_title = review_title.partition(GUARD_MOVIE_FOTW)[2]
            elif GUARD_MOVIE_OBSERVER in review_title:
                review_title = review_title.partition(GUARD_MOVIE_OBSERVER)[2]
            elif GUARD_MOVIE_COF in review_title:
                review_title = review_title.partition(GUARD_MOVIE_COF)[2]
            elif GUARD_BOOK_BOTD in review_title:
                review_title = review_title.partition(GUARD_BOOK_BOTD)[2]
            review_title = review_title.strip()
        except:
            review_title = ""
        return review_title



    def _extractAuthor_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the author name
        
        Parameters:
        blob_div:       a div with the author info
        
        Returns
            a string of the author info
        '''
        author = ""
        try:
            address_block = blob_div.address
            if address_block is not None:
                author = address_block.span.text.strip()
        except:
            author = ""
        return author



    def _extractStandfirst_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract an article sub-heading text
        that is descriptive of the movie
        
        Parameters:
        blob_div:       a div standfirst text in it
        
        Returns
            a string of the standfirst text
        '''
        standfirst = ""
        try:
            standfirst = blob_div.p.text.strip()
        except:
            standfirst = ""
        return standfirst    

#
#   This extracted the old style star ratings. This was based on the SVG outlines
#
#    def _extractRating_(self, blob_div=None):
#        '''
#        Parses a div, or chunk to extract movie rating info
#        
#        Parameters:
#        blob_div:       a div with the ratings info
#        
#        Returns
#            a list with a numeric score and a rating string
#        '''
#        star_count = -1
#        rating_str = ""
#        #   The star ratings are a set of SVG items
#        svgs = blob_div.find_all('svg')
#        if not svgs: return list()
#        for svg in svgs:
#            #self.log(f"svg: {svg}",level="DEBUG")
#            #print(f"svg: {svg}")
#            # found an svg - so it must be about stars
#            if star_count < 0: star_count = 0
#            try:
#                path = svg.path
#            except:
#                path = ""
#            if not path: continue
#            #   Found at least one svg path (a star), start counting stars
#            if 'd' in path.attrs:
#                #self.log(f"svg.path['d']: {path['d']}",level="DEBUG")
#                print(f"svg.path['d']: {path['d']}")
#                star_svg = path['d'].strip()
#                if star_svg.startswith(GUARD_FILLED_STAR):
#                    star_count += 1
#                    #self.log(f"star_count: {star_count}",level="DEBUG")
#        #
#        #   If we didn't find any star ratings, return an empty list
#        if star_count < 0: return list()
#        #
#        #   Found stars now format that to reflect what we got
#        if isinstance(star_count,int):
#            rating_str =f"{star_count} out of 5 stars"
#        else:
#            rating_str =f"{star_count:0.1f} out of 5 stars"
#        #self.log(f"rating: '{str([star_count, rating_str])}'",level="DEBUG")
#        return [star_count, rating_str]


#
#   This is the newer star rating extraction. This is based on the class attribute.
#   The class attribute appears to now be stable - and identifies whether a star SVG
#   is filled or empty. Currently there are no half-stars.
#
    def _extractRating_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract movie rating info
        
        Parameters:
        blob_div:       a div with the ratings info
        
        Returns
            a list with a numeric score and a rating string
        '''
        star_count = -1
        rating_str = ""
        #   The star ratings now specified by a specific type of div
        divs = blob_div.find_all('div')
        if not divs: return list()
        for div in divs:
            #
            if 'class' not in div.attrs: continue
            #
            if GUARD_FILLED_STAR_CLASS in div['class']:
                if star_count < 0 : star_count = 0
                star_count += 1
            if GUARD_EMPTY_STAR_CLASS in div['class']:
                if star_count < 0 : star_count = 0
        
        #
        #   If we didn't find any star ratings, return an empty list
        if star_count < 0: return list()
        #
        #   Found stars now format that to reflect what we got
        if isinstance(star_count,int):
            rating_str =f"{star_count} out of 5 stars"
        else:
            rating_str =f"{star_count:0.1f} out of 5 stars"
        #self.log(f"rating: '{str([star_count, rating_str])}'",level="DEBUG")
        #print(f"rating: '{str([star_count, rating_str])}'")
        return [star_count, rating_str]




    def _extractContent_(self, blob_div=None):
        '''
        Parses the main body of the article to extract the review text.
        
        Parameters:
        blob_div:       a single div with the review items, there may
                        be sub-items that are parsed to extract text
        
        Returns
            a string of the review text
        '''
        body = ""
        paragraphs = blob_div.find_all("p")
        for para in paragraphs:
            pt = para.text.strip()
            if pt:
                if ((GUARD_IN_CINEMAS not in pt) and 
                    (GUARD_ON_DIGITAL not in pt)):
                    body = body+"\n"+pt
        body = body.strip()
        return body



    def _extractReviewType_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the type of this review
        
        Parameters:
        blob_div:       a div that contains the review type
        
        Returns
            a string of the standfirst text
        '''
        review_type = ""
        try:
            review_type = blob_div.text.strip()
        except:
            review_type = ""
        if GUARD_MOVIE_FOTW in review_type:
            review_type = review_type.partition(GUARD_MOVIE_FOTW)[2]
        elif GUARD_MOVIE_OBSERVER in review_type:
            review_type = review_type.partition(GUARD_MOVIE_OBSERVER)[2]
        elif GUARD_MOVIE_COF in review_type:
            review_type = review_type.partition(GUARD_MOVIE_COF)[2]
        elif GUARD_BOOK_BOTD in review_type:
            review_type = review_type.partition(GUARD_BOOK_BOTD)[2]
        review_type = review_type.strip()
        return review_type



    def _extractPostDate_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the article post date
        
        Parameters:
        blob_div:       a div with the posting date information
        
        Returns
            a list consisting of the post date string and a standardized
            timestamp of that posting date
        '''
        post_date = ""
        post_date_ts = ""
        #print(f"aside: {blob_div}")
        try:
            #   Most of the time this works
            post_date = blob_div.details.summary.text.strip()
        except:
            try:
                #   A special case for some review types - Theatre
                divs = blob_div.find_all('div')
                for div in divs:
                    if 'style' in div.attrs:
                        post_date = div.text.strip()
                        break
                    if ('data-gu-name' in div.attrs) and ('dateline' in div['data-gu-name']):
                        post_date = div.text.strip()
                        #print(f"found: {div.text.strip()}")
                        break
            except:
                post_date = ""
        if not post_date: return list()
        pd_fixup = post_date.rpartition(" ")[0]
        try:
            pd = datetime.strptime(pd_fixup,"%a %d %b %Y %H.%M")
            post_date_ts = str(pd)
        except:
            pass
        return [post_date, post_date_ts]



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
#   END class GuardianArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("GuardianArticleRequest.py is a class with no main()")

