#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: EbertArticleRequest.py
#   REVISION: July, 2024
#   CREATION DATE: July, 2024
#   AUTHOR: David W. McDonald
#
#   A web service object to collect review article text. The main entry is through
#   the method getReviewArticle(). Just pass it a URL or a partially complete
#   MOVIE_REVIEW_DATA_TEMPLATE (it looks for the 'review_url' in that record).
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
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
#   Depending on how we extract the movie title, we may have to repair 
#   the use of title case. This is a list of the most common title words
#   that should NOT be capitalized in the title of - well - just about
#   anything. ... Certainly, there are exceptions that this will miss
TITLE_WORDS_LOWER = ['A', 'And', 'As', 'At', 'But', 'By', 'Down', 'For', 'From', 
                     'If', 'In', 'Into', 'Like', 'Near', 'Nor', 'Of', 'Off', 'On', 
                     'Once', 'Onto', 'Or', 'Over', 'Past', 'So', 'Than', 'That', 
                     'The', 'To', 'Upon', 'When', 'With', 'Yet']

#####
#   
#   START class EbertArticleRequest definition
#   
#####

###
#   A class/object that interacts with The Guardian website to collect 
#   review articles. This is not specfic to movie reviews. T
#
class EbertArticleRequest(ReviewArticleBase):
    '''
    The EbertArticleRequest class is a subclass of ReviewArticleBase that connects to
    The New York Post to request a specified article. This is assumed to be a review
    article. The class parses the HTML web page to collect the review text and fill 
    out a MOVIE_REVIEW_DATA_TEMPLATE (dictionary).
    
    Attributes:
        No attributes beyond those inherited from HTTPConnection
    
    Methods:
        getReviewArticle()      - can be used to request the page, returns a
        _parseHTMLPage_()       
        _extractAuthor_()       
        _extractAltTitle_()     
        _extractPosterURL_()    - extract the URL of the movie poster
        _extractPostDate_()     
        _extractContent_()      
        _extractReviewType_()   
        _extractRating_()       
    '''
    def __init__(self, name="EbertArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "rogerebert.com"
        #
        #   Set attributes specific to this website
        self.setHost("https://www.rogerebert.com")
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
        This requests a review article page using either the supplied URL or the
        'review_url' field in a review dictionary. Must have one of the two
        parameters for a request.
        
        Parameters:
        page:       the HTML of the page to be parsed
        review:     a MOVIE_REVIEW_DATA_TEMPLATE dictionary
        
        returns:    the review dictionary, hopefully filled out
        '''
        #   No HTML page, return empty list
        if not text: 
            self.log(f"HTML text was empty!", level="WARNING")
            return review
        self.log(f"entering", level="DEBUG")
        #
        #   Initialize variables for the values we want to collect
        title = ""          # the movie title
        alt_title = ""      # different extraction for the title
        review_title = ""   # the article title
        body = ""           # the main text of the review
        post_date = ""      # a string of the posting date, with time
        author = ""         # the author's by-line
        review_type = ""    # the item being reviewed
        rating = ""         # the rating string
        poster_url = ""     # a url to a movie poster
        #
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(text,'html.parser')
        #
        #   Find the main body of the article content
        page_body = ""
        divs = html_parse.find_all('div')
        for div in divs:            
            if ('class' in div.attrs and "page-content" in div['class'] and
                "container" in div['class']):
                page_body = div
                break
        if not page_body:
            self.log(f"could not get main page body!", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review

        #
        #   First anchor after this is the review type
        review_type = self._extractReviewType_(page_body)
        #
        #   First heading is the article title, same as movie title
        #   for most of the 'modern' reviews
        try:
            review_title = page_body.h1.text.strip()
            title = review_title.replace("\u00a0"," ")
            title = title.replace("\u2018","'").replace("\u2019","'")
        except:
            review_title = ""
            title = ""
        alt_title = self._extractAltTitle_()
        #
        #   Attempt to get the content of the review
        body = self._extractContent_(page_body)
        
        #
        #   Now, run through the div tags looking for the block that
        #   gets the rest of the fields
        divs = page_body.find_all('div')
        for div in divs:
            if 'class' in div.attrs:
                #   The first instance of this block gets us the
                #   values of author, rating, post_date
                if "page-content--block" in div['class']:
                    if not author:
                        author = self._extractAuthor_(div)
                    if not rating:
                        rating = self._extractRating_(div)
                    if not post_date:
                        post_date = self._extractPostDate_(div)
                    continue
                if "cast-and-crew--movie-poster" in div['class']:
                    poster_url = self._extractPosterURL_(div)
        
        #
        #   Supposing we collected at least the body of an article
        #   then we'll fill out the review record as best possible
        if body:
            #   Create a new one if one was not provided
            if not review:
                review = self.__review_template__.copy()
            if author:
                review['author'] = author
            if title and not review['title']:
                if review['author'] == "Roger Ebert":
                    review['title'] = alt_title
                else:
                    review['title'] = title
            if review_title:
                review['review_title'] = review_title
            review['review_type'] = review_type
            review['review'] = body
            review['poster_url'] = poster_url
            #   
            #   If we found a rating, then it should be two parts
            if rating:
                review['rating'] = rating[0]
                review['rating_str'] = rating[1]
            #   
            #   If we found a post date it should be in two parts
            if post_date:
                review['review_date_str'] = post_date[0]
                review['review_date_ts'] = post_date[1]
        
        self.log(f"returning", level="DEBUG")
        return review
        
    
    def _extractAuthor_(self, author_div=None):
        '''
        Parses a div, or chunk to extract the author name
        
        Parameters:
        author_div:     a div with the author info
        
        Returns
            a string of the author info
        '''
        author = ""
        divs = author_div.find_all("div")
        for d in divs:
            if 'class' in d.attrs and "page-content--byline-share" in d['class']:
                try:
                    author = d.span.a.text.strip()
                except:
                    author = ""
                break
        return author
    
    
    def _extractAltTitle_(self):
        '''
        Uses the URL to try and generate the movie title
                
        Returns
            a string of the possible movie title
        '''
        title = ""
        url = self.getRequestPath()
        if url.endswith('/'): url = url[:-1]
        #   Take the last item off the URL
        if '/' in url:
            url = url.rpartition('/')[2]
        #   Now remove the year/date
        if '-' in url:
            url = url.rpartition('-')[0]
        #   Remove the '-movie-review'
        url = url.replace('movie-review','')
        #   Remove the 'great-movie'
        url = url.replace('great-movie','')
        #   Change '-' to spaces
        url = url.replace('-',' ')
        url = url.title().strip()
        title_chunks = url.split()
        title = title_chunks[0]
        for word in title_chunks[1:]:
            if word in TITLE_WORDS_LOWER:
                title = title + " " + word.lower()
            else:
                title = title + " " + word
        
        return title
    
    
    def _extractPosterURL_(self, poster_div=None):
        '''
        Parses a div, or chunk to extract a movie poster URL
        
        Parameters:
        poster_div:     a div with the poster URL
        
        Returns
            a string, poster URL
        '''
        poster_url = ""
        try:
            poster_url = poster_div.img['src']
            poster_url = poster_url.strip()
        except:
            poster_url = ""
        return poster_url
        
    
    def _extractPostDate_(self, pd_div=None):
        '''
        Parses a div, or chunk to extract the article post date
        
        Parameters:
        pd_div:         a div with the posting date information
        
        Returns
            a list consisting of the post date string and a standardized
            timestamp of that posting date
        '''
        post_date = ""
        post_date_ts = ""
        try:
            post_date = pd_div.time.text.strip()
        except:
            post_date = ""

        if not post_date: return list()

        #   Have an extracted string, now try to standardize
        #   that string into a timestamp string
        try:
            pd = datetime.strptime(post_date,"%B %d, %Y")
            post_date_ts = str(pd)
        except Exception as e:
            post_date_ts = ""
        
        return [post_date, post_date_ts]
    
    
    def _extractContent_(self, body_div=None):
        '''
        Parses the main body of the article to extract the review text.
        
        Parameters:
        body_div:       a single div with the review items, there may
                        be sub-items that are parsed to extract text
        
        Returns
            a string of the review text
        '''
        body = ""
        #
        #   In the main body of the article we're looking for sections
        body_sections = body_div.find_all("section")
        #   Each section has to have a specific attrib
        for section in body_sections:
            if ('class' in section.attrs and 
                "page-content--block_editor-content" in section['class']):
                #   Within that section find all of the paragraphs and
                #   extract the text
                paras = section.find_all("p")
                for p in paras:
                    text = p.text.strip()
                    if body:
                        body = body +"\n"+ text
                    else:
                        body = text
        return body
    
    
    def _extractReviewType_(self, rtype_div=None):
        '''
        Parses a div, or chunk to extract the type of this review
        
        Parameters:
        rtype_div:      a div that contains the review type
        
        Returns
            a string of the standfirst text
        '''
        review_type = ""
        try:
            review_type = rtype_div.a.text.strip()
            #   We will assume that if we got a 'Reviews' as the
            #   type, then it is a movie review
            if review_type == "Reviews":
                review_type = "movie review"
                #   These are kept just in case we need to ressurect
                #   special cases that are movies for certain
                #url = self.getRequestPath()
                #if "movie-review" in url:
                #    review_type = "movie review"
                #if "great-movie" in url:
                #    review_type = "movie review"
        except:
            review_type = ""
        return review_type
            
    
    
    def _extractRating_(self, rating_div=None):
        '''
        Parses a div, or chunk to extract movie rating info
        
        Parameters:
        rating_div:     a div with the ratings info
        
        Returns
            a list with a numeric score and a rating string
        '''
        rating_str = ""
        star_count = -1
        stars = rating_div.find_all("i")
        for star in stars:
            if ('class' in star.attrs):
                if star_count < 0: star_count = 0
                if ("icon-star-full" in star['class']):
                    star_count += 1
                if ("icon-star-half" in star['class']):
                    star_count = star_count + 0.5
                #   Special, Ebert thumbs down
                if ("icon-thumbsdown" in star['class']):
                    return [0, "Thumbs down, 0 out of 4 stars"]
        #
        #   If we didn't find any star ratings, the return empty list
        if star_count < 0:
            return list()
        #
        #   Found some stars, convert the count to a string too
        if isinstance(star_count,int):
            rating_str =f"{star_count} out of 4 stars"
        else:
            rating_str =f"{star_count:0.1f} out of 4 stars"
        return [star_count, rating_str]
        

#####
#   
#   END class EbertArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("EbertArticleRequest.py is a class with no main()")


