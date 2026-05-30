#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: SlantMagArticleRequest.py
#   REVISION: July, 2025
#   CREATION DATE: July, 2025
#   AUTHOR: David W. McDonald
#
#   A web service object to collect review article text. The main entry is through
#   the method getReviewArticle(). Just pass it a URL or a partially complete
#   MOVIE_REVIEW_DATA_TEMPLATE (it looks for the 'review_url' in that record).
#
#{{RELEASE}}
#
#{{COPYRIGHT}}
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
#
#
#####
#   
#   START class SlantMagArticleRequest definition
#   
#####

###
#   A class/object that interacts with Slant Magazine website to collect 
#   review articles.
#
class SlantMagArticleRequest(ReviewArticleBase):
    '''
    The SlantMagArticleRequest class is a subclass of ReviewArticleBase that connects to the
    Slant Magazine website to request a specified article. This is assumed to be a review article, 
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
    def __init__(self, name="SlantMagArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "slantmagazine.com"
        #   
        #   Add an ordered set of regex to extract movie titles
        rex = re.compile(r"^(.*) [Rr]eview[: ]*",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Some of the VIDEO/DVD review titles look like this
        rex = re.compile(r"Review[: ].*([‘'\"].*[’'\"]) *",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Older MOVIE review titles look a little like this
        rex = re.compile(r"Review[: ](.*)",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://www.slantmagazine.com")
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
        #   The review is contained within an article tag
        article = html_parse.find('article')
        #   In the 'article' there should be a header tag
        header = article.find('header')
        if not header: 
            self.log(f"When processing page {review['review_url']}", level="WARNING")
            self.log(f"Could not extract 'header' from article", level="WARNING")
            return review
        #
        #   All of these things can be extracted from the header
        review_title = self._extractArticleTitle_(header)
        title = self._extractMovieTitleFromArticleTitle_(review_title)
        standfirst = self._extractStandfirst_(header)
        review_type = self._extractReviewType_(header)
        #
        #   If the review_type is "video" - there is currently a slight problem
        #   with how the movie title is extracted. This isn't a problem for regular
        #   movie reviews. For regular movie reviews the editorial standard is
        #   different and the titles should be extracted correctly
        #
        #   There are some article types that have the review_type 'Film' which
        #   make the articles look like a film review. Here we check the article
        #   title for specific indicators that it is a different thing and set
        #   the review_type to reflect something different
        if (review_title.startswith("Poster") or 
            review_title.startswith("Understanding Screen")):
            review_type = "film commentary"
        
        #   
        #   A meta-data area contains the author and the post date
        header_meta = ""
        divs = header.find_all('div')
        for div in divs:
            if 'class' in div.attrs and 'post-item-meta' in div['class']:
                header_meta = div
                break
        #   Extracted from the header - but narrowed
        author = self._extractAuthor_(header_meta)
        post_date = self._extractPostDate_(header_meta)

        #
        #   The next component is the body of the review
        body_div = ""
        divs = article.find_all('div')
        for div in divs:
            #   This works better - closer in the nesting hierarchy
            if 'class' in div.attrs and 'article-content' in div['class']:
                body_div = div
                break
            #   This works but gets some additional content
            #if 'class' in div.attrs and "content-main" in div['class']:
            #    body_div = div
            #    break
        if body_div:
            body = self._extractContent_(body_div)
        
        #
        #   The next component is the movie rating - near the bottom
        #   and part of the credits section of the page
        rate_div = ""
        #   Using the same set of divs
        for div in divs:
            #   This works better - closer in the nesting hierarchy
            if 'id' in div.attrs and 'credits' in div['id']:
                rate_div = div
                break
        if rate_div:
            rating = self._extractRating_(rate_div)
                
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
                review['title'] = title.strip()
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
        title_div = ""
        divs = blob_div.find_all("div")
        for div in divs:
            if 'class' in div.attrs and "title-subtitle" in div['class']:
                title_div = div
                break
        try:
            review_title = title_div.h1.text.strip()
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
            byline = blob_div.span.text.strip()
            if byline:
                author = byline.partition("by ")[2].strip()
        except:
            author = ""
        return author



    def _extractStandfirst_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract an article sub-heading text
        that is descriptive of the movie
        
        Parameters:
        blob_div:       a div with standfirst text in it
        
        Returns
            a string of the standfirst text
        '''
        standfirst = ""
        sf_div = ""
        divs = blob_div.find_all("div")
        for div in divs:
            if 'class' in div.attrs and "title-subtitle" in div['class']:
                sf_div = div
                break
        try:
            standfirst = sf_div.p.text.strip()
        except:
            standfirst = ""
        return standfirst    



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
        #   A set of icons 'i' elements
        icons = blob_div.find_all('i')
        #   Return if there are not icons
        if not icons: return list()
        #   Try to count the number of star icons given
        for icon in icons:
            if star_count < 0: star_count = 0
            if 'class' in icon.attrs:
                #   skip - don't count "open" star icons
                if "fa-star-o" in icon['class']: continue
                #   count the half-full filled in star
                if "fa-star-half-o" in icon['class']:
                    star_count += 0.5
                    continue
                #   count the full filled in star
                if "fa-star" in icon['class']:
                    star_count += 1
                    continue
        #
        #   If we didn't find any star ratings, return an empty list
        if star_count < 0: return list()
        #
        #   Found stars now format that to reflect what we got
        if isinstance(star_count,int):
            rating_str =f"{star_count} out of 4 stars"
        else:
            rating_str =f"{star_count:0.1f} out of 4 stars"
        #self.log(f"rating: '{str([star_count, rating_str])}'",level="DEBUG")
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
            para_text = para.text.strip()
            if para_text:
                body = body+"\n"+para_text
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
        categories = list()
        cat_tags_div = ""
        divs = blob_div.find_all("div")
        for div in divs:
            if 'class' in div.attrs and "meta-categories" in div['class']:
                cat_tags_div = div
                break
        try:
            cats = cat_tags_div.find_all("a")
            for cat in cats:
                c = cat.text.strip().lower()
                if c: categories.append(c)
        except:
            pass
        #
        #   Just looking for the one single category - multiple categories
        #   means its something about film - but probably not a movie review
        if (len(categories) == 1) and "film" in categories:
            review_type = "movie review"
        else:
            review_type = " / ".join(categories)
            
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
        time_elt = blob_div.time
        try:
            #   The text is a nice formatted string
            post_date = time_elt.text.strip()
        except:
            pass
        #   If there's no text there, then give up
        if not post_date: return list()
        #
        #   Try to extract the timestamp
        try:
            if 'datetime' in time_elt.attrs:
                post_date_ts = time_elt['datetime'].rpartition('-')[0]
                post_date_ts = post_date_ts.replace("T"," ")
        except:
            pass
        #
        #   This is a backup - in case the formatting changes
        if not post_date_ts:
            try:
                pd = datetime.strptime(post_date,"%B %d, %Y")
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
#   END class SlantMagArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("SlantMagArticleRequest.py is a class with no main()")

