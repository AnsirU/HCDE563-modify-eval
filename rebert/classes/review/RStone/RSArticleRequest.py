#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: RSArticleRequest.py
#   REVISION: August, 2025
#   CREATION DATE: August, 2024
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

#####
#   
#   START class RSArticleRequest definition
#   
#####

###
#   A class/object that interacts with The Guardian website to collect 
#   review articles.
#
class RSArticleRequest(ReviewArticleBase):
    '''
    The RSArticleRequest class is a subclass of ReviewArticleBase that connects to The
    Rolling Stone website to request a specified article. This is assumed to be a review article, 
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
    def __init__(self, name="RSArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "rollingstone.com"
        #   
        #   Add an ordered set of regex
        #   '<movie_title>': article tag title
        #   ‘Happy Gilmore 2’: Hooray! Adam Sandler’s Brawling Golf Bro Is Back
        rex = re.compile(r"^['‘](.*)['’][: ].*",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   article title with '<movie_title>'
        #   Nerdy Vengeance Will Be Rami Malek’s in ‘The Amateur’
        rex = re.compile(r".* ['‘](.*)['’]$",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   article title with '<movie_title>' in the middle
        #   <<< need example >>>
        rex = re.compile(r".* ['‘](.*)['’] .*",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://www.rollingstone.com")
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
        #   The Rolling Stone pages have some issues with their HTML formatting.
        #   The 'html5lib' parser seems to do parse the page, but that requires an
        #   installation. 
        try:
            #html_parse = BeautifulSoup(text,'html.parser')
            html_parse = BeautifulSoup(text,'html5lib')
        except Exception as ex:
            msg = str(ex)
            self.log(f"Exception: {msg}", level="WARNING")
            self.log(f"This review collector relies on the python html5lib module.", level="WARNING")
            self.log(f"You will need to install html5lib to use this review collector.", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review
        #
        #   The review is contained within an <article ...> tag
        article = html_parse.main.article
        #   A header tag contains title, review type and standfirst 
        header = article.header
        #
        #   Title and standfirst in the header section
        if header:
            review_title = self._extractArticleTitle_(header)
            title = self._extractMovieTitleFromArticleTitle_(review_title)
            review_type = self._extractReviewType_(header)
            standfirst = self._extractStandfirst_(header)
        #
        #   Extract a div with author and posting date info
        divs = article.find_all("div")
        for d in divs:
            if "class" in d.attrs and "author-single-inner" in d['class']:
                author = self._extractAuthor_(d) 
                post_date = self._extractPostDate_(d)
                break
        #
        #   Extract the div with the body paragraphs
        for d in divs:
            if "class" in d.attrs and "a-content" in d['class']:
                body = self._extractContent_(d)
                break
        
#        print(f"{review_title=}")
#        print(f"{title=}")
#        print(f"{review_type=}")
#        print(f"{standfirst=}")
#        print(f"{author=}")
#        print(f"{post_date=}")
#        print(f"{body=}")
#        return dict()
        
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
            anchor = blob_div.button.p.a
            author = anchor.text.strip()
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
        if not blob_div: return standfirst
        divs = blob_div.find_all("div")
        for d in divs:
            if "class" in d.attrs and "article-excerpt" in d['class']:
                try:
                    if not standfirst:
                        standfirst = d.text.strip()
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
        #   The star ratings are a set of SVG items
        svgs = blob_div.find_all('svg')
        if not svgs: return list()
        for svg in svgs:
            #self.log(f"svg: {svg}",level="DEBUG")
            # found an svg - so it must be about stars
            if star_count < 0: star_count = 0
            try:
                path = svg.path
            except:
                path = ""
            if not path: continue
            #   Found at least one svg path (a star), start counting stars
            if 'd' in path.attrs:
                #self.log(f"svg.path['d']: {path['d']}",level="DEBUG")
                star_svg = path['d'].strip()
                if star_svg.startswith(GUARD_FILLED_STAR):
                    star_count += 1
                    #self.log(f"star_count: {star_count}",level="DEBUG")
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
            #   Some "paragraph" like elements are extraneous, so
            #   we will try to filter them out
            if 'class' not in para.attrs: continue
            #if 'class' in para.attrs:
            #    if "editors-pick-module" in para['class']: continue
            #    if "trending-in-article" in para['class']: continue
            #    if "recirculation-modules" in para['class']: continue
            #
            #   If we have a paragraph collect it
            if 'paragraph' in para['class']:
                pt = para.text.strip()
                pt = pt.replace("\t"," ").replace("   "," ").replace("  "," ")
                pt = pt.replace(" \n","\n").replace("\n ","\n").replace("\n\n\n","\n")
                pt = pt.replace("\n\n\n","\n").replace("\n\n\n","\n").replace("\n\n","\n")
                pt = pt.replace("\n\n","\n").strip()
                if pt:
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
        if not blob_div: return review_type
        divs = blob_div.find_all("div")
        for d in divs:
            if "class" in d.attrs and "article-kicker" in d['class']:
                try:
                    if not review_type:
                        review_type = d.text.strip().lower()
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
            time_elt = blob_div.time
            post_date = time_elt.text.strip()
            post_date_ts = time_elt['datetime'].strip()
            post_date_ts = post_date_ts.partition('.')[0].replace("T"," ").strip()
        except:
            return list()
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
        #
        while title and title[-1] in ",.;:":
            title = title[:-1]
            
        return title
       
#####
#   
#   END class RSArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("RSArticleRequest.py is a class with no main()")

