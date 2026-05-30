#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: EbertArticleRequest.py
#   REVISION: June, 2025
#   CREATION DATE: July, 2024
#   AUTHOR: David W. McDonald
#
#   A web service object to collect review article text. The main entry is through
#   the method getReviewArticle(). Just pass it a URL or a partially complete
#   MOVIE_REVIEW_DATA_TEMPLATE (it looks for the 'review_url' in that record).
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
#   Depending on how we extract the movie title, we may have to repair 
#   the use of title case. This is a list of the most common title words
#   that should NOT be capitalized in the title of - well - just about
#   anything. ... Certainly, there are exceptions that this will miss
TITLE_WORDS_LOWER = ['A', 'And', 'As', 'At', 'But', 'By', 'Down', 'For', 'From', 
                     'If', 'In', 'Into', 'Like', 'Near', 'Nor', 'Of', 'Off', 'On', 
                     'Once', 'Onto', 'Or', 'Over', 'Past', 'So', 'Than', 'That', 
                     'The', 'To', 'Upon', 'When', 'With', 'Yet']
#
#   Formatting near the end of the review sometimes adds some availablity that
#   can be cut - it's not actually part of the review
EBERT_NOW_AVAILABLE = "Now available on"
EBERT_NOW_STREAMING = "Now streaming on"
#
#####
#   
#   START class EbertArticleRequest definition
#   
#####

###
#   A class/object that interacts with Roger Ebert website to collect 
#   review articles.
#
class EbertArticleRequest(ReviewArticleBase):
    '''
    The EbertArticleRequest class is a subclass of ReviewArticleBase that connects to
    the RogerEbert site to request a specified article. This is assumed to be a review
    article. The class parses the HTML web page to collect the review text and fill 
    out a MOVIE_REVIEW_DATA_TEMPLATE (dictionary).
    
    Attributes:
        No attributes beyond those inherited from HTTPConnection
    
    Methods:
        getReviewArticle()      - can be used to request the page, returns a
        _parseHTMLPage_()       - starts parsing of the HTML of the article page
        _extractAuthor_()       - extract the author of the review
        _extractAltTitle_()     - special to this class, extracts movie title from URL
        _extractPosterURL_()    - extract the URL of the movie poster
        _extractPostDate_()     - extract the date the review was posted
        _extractContent_()      - extract the main text of the review
        _extractReviewType_()   - extract the type of this review
        _extractRating_()       - extract the "star" rating - or thumbs down

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
        This parses the HTML article page and tries to complete the
        MOVIE_REVIEW_DATA_TEMPLATE dictionary record.
        
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
        ###
        #   This page structure changes in Summer 2024
        #divs = html_parse.find_all('div')
        #for div in divs:
        #    if ('class' in div.attrs and "page-content" in div['class'] and
        #        "container" in div['class']):
        #        page_body = div
        #        break
        mains = html_parse.find_all('main')
        for m in mains:
            if ('class' in m.attrs and "site-main" in m['class']):
                page_body = m
        if not page_body:
            self.log(f"could not get main page body!", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review
        #
        #   The header contains by-line, rating, and posting date info
        header = page_body.find('header')
        #
        #   First anchor after this is the review type
        #review_type = self._extractReviewType_(page_body)
        review_type = self._extractReviewType_(header)
        #print(f"{review_type=}")
        #
        #   First heading is the article title, same as movie title
        #   for most of the 'modern' Ebert reviews
        try:
            #review_title = page_body.h1.text.strip()
            review_title = header.h1.text.strip()
            title = review_title.replace("\u00a0"," ")
            title = title.replace("\u2018","'").replace("\u2019","'")
            if title[-1] in '\u2011\u2012\u2013\u2014\uFE58':
                title = title[:-1].strip()
        except:
            review_title = ""
            title = ""
        alt_title = self._extractAltTitle_()
        #print(f"{alt_title=}")
        #
        #   Attempt to get the content of the review
        body = self._extractContent_(page_body)
        #print(f"{body=}")
        
        #
        #   Now, run through the div tags looking for the block that
        #   gets the rest of the fields
        author = self._extractAuthor_(header)
        rating = self._extractRating_(header)
        post_date = self._extractPostDate_(header)
        
        #print(f"{author=}")
        #print(f"{rating=}")
        #print(f"{post_date=}")

        divs = page_body.find_all('div')
        for div in divs:
            if 'id' in div.attrs and 'content-lower' in div['id']:
                poster_url = self._extractPosterURL_(div)
                break

        #
        #   Supposing we collected at least the body of an article
        #   then we'll fill out the review record as best possible
        #self.log(f"Starting to parse body.", level="WARNING")
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



    def _extractAuthor_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the author name
        
        Parameters:
        blob_div:       a div with the author info
        
        Returns
            a string of the author info
        '''
        #self.log(f"entering", level="DEBUG")
        author = ""
        anchors = blob_div.find_all("a")
        for a in anchors:
            if 'href' in a.attrs and 'contributors' in a['href']:
                author = a.text.strip()
                break
        #self.log(f"returning", level="DEBUG")
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
        #
        #   Fix up for title case use
        for word in title_chunks[1:]:
            if word in TITLE_WORDS_LOWER:
                title = title + " " + word.lower()
            else:
                title = title + " " + word
        
        return title



    def _extractPosterURL_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract a movie poster URL
        
        Parameters:
        blob_div:       a div with the poster URL
        
        Returns
            a string, poster URL
        '''
        poster_url = ""
        poster_img = None
        imgs = blob_div.find_all("img")
        for img in imgs:
            if 'class' in img.attrs and 'wp-post-image' in img['class']:
                poster_img = img
                break
        try:
            poster_url = poster_img['src']
            poster_url = poster_url.strip()
        except:
            poster_url = ""
        return poster_url



    def _extractPostDate_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the article post date
        
        Parameters:
        blob_div:       a div with the posting date information
        
        Returns
            a list consisting of the post date string and a standardized
            timestamp of that posting date
        '''
        #self.log(f"entering", level="DEBUG")
        post_date = ""
        post_date_ts = ""
        
        #   Find all of the divs in the header
        hdivs = blob_div.find_all("div")
        for div in hdivs:
            try:
                #   Now, get the text of the div
                post_date = div.text.strip()
            except Exception as e:
                post_date = ""
            #   Have an extracted string, now try to standardize
            #   that string into a timestamp string
            #
            #   They try to use friendly wording to indicate the day/time of the
            #   posting. This creates some parsing to figure out the day/time
            if (('days ago' in post_date) or ('day ago' in post_date) or
                ('Today' in post_date) or ('today' in post_date) or
                ('hour ago' in post_date) or ('hours' in post_date) ):
                
                try:
                    da = None
                    #
                    #   All of these words mean "today" - no offset
                    if (('Today' in post_date) or ('today' in post_date) or
                        ('hour ago' in post_date) or ('hours' in post_date)):
                        da = 0
                    #
                    #   This provides some number of days of offset from today
                    if 'days ago' in post_date:
                        da = post_date.partition("days ago")[0].strip()[-1]
                    #
                    #   This should be one day of offset from today
                    if 'day ago' in post_date:
                        da = post_date.partition("day ago")[0].strip()[-1]               
                    #   
                    #   Get a time delta based on the offset
                    pdi = int(da)
                    ago = timedelta(days=pdi)
                    #   Now, calculate that day
                    pd = datetime.now()-ago
                    #   Make the conversion to a standard timestamp
                    post_date = pd.strftime('%B %d, %Y')
                    pd = datetime.strptime(post_date,"%B %d, %Y")
                    #print(f"Calculated: {str(pd)}")
                    post_date_ts = str(pd)
                except Exception as e:
                    post_date_ts = ""
            else:
                #   Not a friendly time description, then maybe it's just a
                #   date string - try to convert that
                try:
                    pd = datetime.strptime(post_date,"%B %d, %Y")
                    post_date_ts = str(pd)
                except Exception as e:
                    post_date_ts = ""
            #
            #   Stop looking through the divs once we have a timestamp
            if post_date_ts: break
            
        #self.log(f"returning", level="DEBUG")
        if not post_date_ts: return list()
        return [post_date, post_date_ts]



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
        #
        #   In the main body of the article we're looking for an <article> tag
        body_article = blob_div.find("article")
        #   Within the article tag we're looking for paragraphs
        body_paragraphs = body_article.find_all("p")
        #   Each section has to have a specific attrib
        for p in body_paragraphs:
            text = p.text.strip()
            if body:
                body = body +"\n"+ text
            else:
                body = text
        #   Clean up some 'extra' \n characters that get added
        body = body.replace(" \n"," ")
        #
        #   Remove end phrases that can be trimmed
        if EBERT_NOW_AVAILABLE in body:
            body = body.partition(EBERT_NOW_AVAILABLE)[0].strip()
        if EBERT_NOW_STREAMING in body:
            body = body.partition(EBERT_NOW_STREAMING)[0].strip()
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
            review_type = blob_div.a.text.strip()
            #   We will assume that if we got a 'Reviews' as the
            #   type, then it is a movie review
            if review_type == "Reviews":
                review_type = "movie review"
                #   These are kept just in case we need to ressurect
                #   special cases of movie review
                #url = self.getRequestPath()
                #if "movie-review" in url:
                #    review_type = "movie review"
                #if "great-movie" in url:
                #    review_type = "movie review"
        except:
            review_type = ""
        return review_type



    def _extractRating_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract movie rating info
        
        Parameters:
        blob_div:       a div with the ratings info
        
        Returns
            a list with a numeric score and a rating string
        '''
        #self.log(f"entering", level="DEBUG")
        rating_str = ""
        star_count = -1
        img_class = list()
        imgs = blob_div.find_all("img")
        for img in imgs:
            if 'alt' in img.attrs and 'star rating' in img.attrs['alt']:
                img_class = img.attrs['class']
                break
            if 'alt' in img.attrs and 'down rating' in img.attrs['alt']:
                img_class = img.attrs['class']
                break
        # 
        #   Image was a thumbs down!
        if 'rotate-180' in img_class: 
            star_count = 0
        else:
            for item in img_class:
                if item.startswith('star'):
                    try:
                        star_count = int(item.replace('star',''))/10
                    except:
                        star_count = -1
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
        #self.log(f"returning", level="DEBUG")
        return [star_count, rating_str]
        

#####
#   
#   END class EbertArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("EbertArticleRequest.py is a class with no main()")


