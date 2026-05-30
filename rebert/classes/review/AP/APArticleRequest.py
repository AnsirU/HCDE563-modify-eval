#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: APArticleRequest.py
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
#   The Associated Press writes out their rating as text. We need a
#   key find and extract it from a paragraph
#
AP_RUNNING_TEXT = "Running time"
AP_RATING_TEXT1 = "stars out of four."
AP_RATING_TEXT2 = "star out of four."

#####
#   
#   START class APArticleRequest definition
#   
#####

###
#   A class/object that interacts with The Associated Press website to collect 
#   review articles.
#
class APArticleRequest(ReviewArticleBase):
    '''
    The APArticleRequest class is a subclass of ReviewArticleBase that connects to the 
    Associated Press website to request a specified article. This is assumed to be a movie
    review. The class parses the HTML web page to collect the review text and 
    fill out a MOVIE_REVIEW_DATA_TEMPLATE (dictionary).
    
    Attributes:
        No attributes beyond those inherited from HTTPConnection
    
    Methods:
        getReviewArticle()  - can be used to request the page, returns a
        _parseHTMLPage_()       - starts parsing of the HTML of the article page
        _extractArticleTitle_() - extract the article title
        _extractAuthor_()       - extract the author of the review
        _extractRating_()       - extract the "star" rating
        _extractContent_()      - extract the main text of the review
        _extractReviewType_()   - extract the type of this review
        _extractPostDate_()     - extract the date the review was posted
        _extractMovieTitleFromArticleTitle_()
                                - extract the movie title from the article title

    '''
    def __init__(self, name="APArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "apnews.com"
        #   
        #   Add an ordered set of regex to extract movie titles
        #   The AP is really bad with movie titles. Extraction requires
        #   some regex and some text processing of the article title
        rex = re.compile(r"Movie Review:.*( '.*' ).*",
                        flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #   Special version for movie titles at the end of the article title
        rex = re.compile(r"Movie Review:.*( '.*'$)",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://apnews.com")
        #
        #   The AP sometimes refuses a request. This will set a specific
        #   User Agent to test if the refusal is due one of the randomly
        #   selected User Agent configurations
        self.setUserAgent("safari")
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
        body = ""           # the main text of the review
        post_date = list()  # a list of posting date info
        rating = list()     # a list of the star rating info
        author = ""         # the author's by-line
        review_type = ""    # the item being reviewed
        #
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(text,'html.parser')
        #   Find all the divs
        divs = html_parse.find_all('div')
        #   Look through each div - for the page header
        header_div = ""
        for div in divs:
            #   A div without a 'class' attribute won't be something we want
            if 'class' not in div.attrs: continue
            if 'StoryPage-lede-content' in div['class']:
                header_div = div
                break
        #
        #   Get these from the header_div
        review_title = self._extractArticleTitle_(header_div)
        title = self._extractMovieTitleFromArticleTitle_(review_title)
        review_type = self._extractReviewType_(header_div)
        #
        #print(f"{review_title=}")
        #print(f"{title=}")
        #print(f"{review_type=}")
        #return dict()
        #
        #   The review is contained within an <main ...> tag
        main = html_parse.find('main')
        #   They use a special tag for the actual content - nested in <main ...>
        article = main.find('bsp-story-page')
        #   Details of the review are in a set of divs
        #   Find all the divs
        divs = article.find_all('div')
        #   Look through each div
        for div in divs:
            #   A div without a 'class' attribute won't be something we want
            if 'class' not in div.attrs: continue
            #
            if 'Page-byline' in div['class']:
                author = self._extractAuthor_(div)
                post_date = self._extractPostDate_(div)
            elif 'RichTextStoryBody' in div['class']:
                body = self._extractContent_(div)
                rating = self._extractRating_(div)
        #
        #print(f"{author=}")
        #print(f"{post_date=}")
        #print(f"{rating=}")
        #print(f"{body=}")
        #return dict()
        #
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
            #
            review['review_type'] = review_type
            #
            review['review'] = body
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
            divs = blob_div.find_all('div')
            for div in divs:
                if 'class' not in div.attrs: continue
                if 'Page-authors' in div['class']:
                    author = div.a.text.strip().title()
                    break
        except:
            author = ""
        return author



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
        #   Find the paragraph with the rating in it
        rating_para = ""
        paragraphs = blob_div.find_all("p")
        for para in paragraphs:
            pt = para.text.strip()
            if pt:
                if (((AP_RATING_TEXT1 in pt) or
                    (AP_RATING_TEXT2 in pt)) and 
                    (AP_RUNNING_TEXT in pt)):
                    rating_para = pt
                    break

        if rating_para:
            score_text = ""
            if AP_RATING_TEXT1 in rating_para:
                score_text = rating_para.partition(AP_RATING_TEXT1)[0]
            else:
                score_text = rating_para.partition(AP_RATING_TEXT2)[0]
            #print(f"{score_text=}")
            score_text = score_text.rpartition(".")[2].strip().lower()
            #print(f"{score_text=}")
            
            if "one half" in score_text:
                star_count = 0.5
            else:
                if "and a half" in score_text:
                    score_text = score_text.partition("and a")[0].strip()
                    star_count = 0.5
                else:
                    star_count = 0
                #print(f"{score_text=}")
                if "one" in score_text: star_count = star_count + 1
                if "two" in score_text: star_count = star_count + 2
                if "three" in score_text: star_count = star_count + 3
                if "four" in score_text: star_count = star_count + 4
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
            pt = para.text.strip()
            if pt:
                if ((AP_RATING_TEXT1 not in pt) and
                    (AP_RATING_TEXT2 not in pt) and 
                    (AP_RUNNING_TEXT not in pt)):
                    body = body+"\n"+pt
        body = body.strip()
        return body



    def _extractReviewType_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the type of this review
        
        Parameters:
        blob_div:       a div that contains the review type
        
        Returns
            a string of review type
        '''
        review_type = ""
        try:
            #   The review type is in the title right before a colon
            review_type = blob_div.h1.text.partition(":")[0]
            review_type = review_type.lower().strip()
        except:
            review_type = ""
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
        try:
            #   The AP uses a JavaScript timestamp in milliseconds and some
            #   formatting trick that makes it hard to extract the text.
            #   So, we extract the timestamp value and convert that to
            #   represent the time string that they show in the article
            ts_elt = blob_div.find('bsp-timestamp')
            js_timestamp = int(ts_elt['data-timestamp'])
            timestamp = js_timestamp / 1000.0
            pd = datetime.fromtimestamp(timestamp)
            #print(pd)
            post_date_ts = str(pd)
            post_date = str(pd.strftime("%I:%M %p, %B %d, %Y"))
            if post_date.startswith('0'):
                post_date = post_date[1:]
            #print(post_date)
        except:
            post_date = ""

        if not post_date: return list()

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
        #   Before we try to use the default behavior, we need to standardize the
        #   current article title
        title_edit = review_title.replace("\u2018","'").replace("\u2019","'").replace("`","'")
        #
        #   Now, apply regex and extract title
        title = super()._extractMovieTitleFromArticleTitle_(title_edit)
        #
        #   Still need to clean the title
        title = title.strip()        
        title = title.replace("'","").strip()
        #   'title' should just be the title, but let's remove anything that
        #   might be a little odd off the end of the title - this is most often
        #   a comma character - because of the way the AP writes article titles
        if title and title[-1] in ".,:;-'\u2011\u2012\u2013\u2014\uFE58":
            title = title[:-1].strip()

        return title
       
#####
#   
#   END class APArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("APArticleRequest.py is a class with no main()")

