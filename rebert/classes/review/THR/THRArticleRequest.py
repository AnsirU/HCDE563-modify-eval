#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: THRArticleRequest.py
#   REVISION: June, 2025
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   A web service object to collect review article text. The main entry is through
#   the method getReviewArticle(). Just pass it a URL or a partially complete
#   MOVIE_REVIEW_DATA_TEMPLATE (it looks for the 'review_url' in that record).
#
#   This is for the review website The Hollywood Reporter (THR)
#   https://www.hollywoodreporter.com
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
#   Near the end of a review THR will list cast, crew, production, etc. 
#   details in paragraphs that are mostly like regular paragraphs of the
#   review content. These phrases are a selection of them that occur
#   frequently and are used to suppress non-review paragraphs.
#
THR_PRODUCTION_PHRASES = [
    "production company:", "cast:", "distributor", "casting:", 
    "director", "screenwriter", "screenplay", "sales", 
    "producer", "executive producer", "co-producer", "writer-director", 
    "director of", "production designer", "costume designer", "editor", 
    "music:", "production companies:", "rated", "no rating", 
    "venue:"
]

THR_PHRASE_CUTOFF = 2

#####
#   
#   START class THRArticleRequest definition
#   
#####

###
#   A class/object that interacts with The Hollywood Reporter website to collect 
#   review articles. 
#
class THRArticleRequest(ReviewArticleBase):
    '''
    The THRArticleRequest class is a subclass of ReviewArticleBase that connects to the
    Hollywood Reporter to request a specified article. This is assumed to be a review
    article. The class parses the HTML web page to collect the review text and fills out  
    a MOVIE_REVIEW_DATA_TEMPLATE (dictionary).
    
    Attributes:
        No attributes beyond those inherited from HTTPConnection
    
    Methods:
        getReviewArticle()      - request a movie review page, parse and return results
        _parseHTMLPage_()       - starts parsing of the HTML of the article page
        _extractContent_()      - extract the main text of the review
        __appendBodyText__()    - detect extraneous paragraphs, only append review
        _extractReviewType_()   - extract the type of this review
        _extractPostDate_()     - extract the date the review was posted
        _extractStandfirst_()   - extract a sub-headline, like a call out quote
        _extractRating_()       - extract the "star" rating
        _extractAuthor_()       - extract the author of the review
        _extractMovieTitleFromArticleTitle_()
                                - extract the movie title from the article title

    '''
    def __init__(self, name="THRArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "hollywoodreporter.com"
        #   
        #   Add an ordered set of regex
        rex = re.compile(r"^['\u2018](.*)['\u2019]: Film",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        rex = re.compile(r"^['\u2018](.*)['\u2019] Review:",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        rex = re.compile(r"^['\u2018](.*)['\u2019] ",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Set attributes specific to this website
        self.setHost("https://www.hollywoodreporter.com")
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
        #   Overriding this method allows us to make potential changes to the
        #   behavior - if we need to - for now - we just use the default behavior
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
        review_title = ""   # the article title
        standfirst = ""     # a one-liner about the review or movie
        body = ""           # the main text of the review
        author = ""         # the author's by-line
        review_type = ""    # the item being reviewed
        post_date = list()  # a list of the posting date and timestamp
        rating = list()     # a list of the star rating info
        #
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(text,'html.parser')
        #   The main chunk that we need is inside a 'main' tag
        main = html_parse.find('main')
        #   Review title should be in the first <H1> tag
        title_chunk = main.h1
        #   If we got an <H1> at all, then see if it is the title
        if (title_chunk and ('class' in title_chunk.attrs) and
            "article-title" in title_chunk['class']):
            #   Extract the review article title
            try:
                review_title = title_chunk.text.strip()
            except:
                review_title = ""
            #   Then see if we can extract and clean a movie title
            title = self._extractMovieTitleFromArticleTitle_(review_title)
            
        review_type = self._extractReviewType_(main)
        standfirst = self._extractStandfirst_(main)
        
        #
        #   within the 'main' part of the page, is the article
        divs = main.find_all('div')
        #
        #   Now, run through the div tags looking for specific values
        for div in divs:            
            if ('class' in div.attrs):
                if ("a-article-grid__author" in div['class']):
                    author = self._extractAuthor_(div)
                    post_date = self._extractPostDate_(div)
                    continue
                if ("a-content" in div['class']):
                    body = self._extractContent_(div)
                    continue
                if ("review-summary-card" in div['class']):
                    rating = self._extractRating_(div)
                    continue
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
            #   We're merging the one liner headline with the body
            if standfirst:
                if standfirst.endswith('.'):
                    review['review'] = standfirst+"\n"+body
                else:
                    review['review'] = standfirst+".\n"+body
            else:
                review['review'] = body
            #   
            #   THR does not score, just a pithy statement in the 'rating_str',
            #   the 'rating' should always be -1 at this point
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
        tag_count = 0
        paras = blob_div.find_all("p")
        for p in paras:
            if tag_count > 2: break
            text = p.text.strip()
            #   Paragraph selection didn't work correctly, so this was a way
            #   to identify and fix the paragraphs that included content from
            #   additional <div> elements that are not part of the review
            #
            #   First, look for and remove related content text
            if ("\n" in text) and ("Related Stories" in text):
                #   Keep the part that is not related stories
                text = text.partition("Related Stories")[0].strip()
            #
            #   Next if this paragraph has nested paragraphs we break it
            #   up and then process each chunk as a unique paragraph
            elif "\n\t" in text:
                #   Split, and look at teach one
                text_list = text.split("\n")
                for text in text_list:
                    if tag_count > THR_PHRASE_CUTOFF: break
                    text = text.strip()
                    body, tag_count = self.__appendBodyText__(body, text, tag_count)
                    #print(f"2:{tag_count=}")
                continue
            #   If it is none of the above
            body, tag_count = self.__appendBodyText__(body, text, tag_count)
        return body



    #
    #   Specific addtion to help make the parsing work this tracks differet
    #   types content - to filter out production related paragraphs in the body text
    #
    def __appendBodyText__(self, body="", text="", tag_count=0):
        '''
        Helper method to collect the body of the review
        
        Parameters:
        body:           a string, the current body text of the review
        text:           a string that might be added to the body
        tag_count:      an integer that counts how non-review phrases found 
        
        Returns
            a string of the review text, and the current tag_count
        '''
        if not text: return body, tag_count
        tl = text.lower()
        #   Advertisement blocks in the middle
        #   These don't change the tag count 
        if tl.startswith("related stories"): 
            return body, tag_count
        if tl.startswith("the bottom line"): 
            return body, tag_count
        #   Skip the purely metadata sometimes included
        #   at the end of these reviews. We consider these
        #   as signal tokens. If we get three of them then
        #   we'll just skip the rest of the 'review'. Hopefully
        #   we see three of the ones we *know* before we see
        #   any that we don't know.
        for phrase in THR_PRODUCTION_PHRASES:
            if tl.startswith(phrase):
                tag_count += 1
                return body, tag_count
        #print(f">>>{text}<<<")
        #print(f"1:{tag_count=}")
        #print()
        if body:
            body = body +"\n"+ text
        else:
            body = text
        return body, tag_count



    def _extractReviewType_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the type of this review
        
        Parameters:
        blob_div:      a div that contains the review type
        
        Returns
            a string of the review type
        '''
        review_type = ""
        try:
            breadcrumbs = blob_div.ul
            list_items = breadcrumbs.find_all('li')
        except:
            list_items = None
        if list_items:
            last_crumb = None
            for item in list_items:
                last_crumb = item
            if last_crumb:
                review_type = last_crumb.text.strip().lower()
        return review_type



    def _extractPostDate_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the article post date
        
        Parameters:
        blob_div:         a div with the posting date information
        
        Returns
            a list consisting of the post date string and a standardized
            timestamp of that posting date
        '''
        post_date = ""
        post_date_ts = ""
        try:
            post_date = blob_div.time.text.strip()
        except:
            post_date = ""

        if not post_date: return list()

        #   Have an extracted string, now try to standardize
        #   that string into a timestamp string
        try:
            if post_date.endswith("pm"):
                pd = datetime.strptime(post_date,"%B %d, %Y %I:%M%p")
            elif post_date.endswith("am"):
                pd = datetime.strptime(post_date,"%B %d, %Y %I:%M%p")
            else:
                pd = datetime.strptime(post_date,"%B %d, %Y %I:%M")
            post_date_ts = str(pd)
        except Exception as e:
            post_date_ts = ""
        
        return [post_date, post_date_ts]



    def _extractStandfirst_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract an article sub-heading text
        that is descriptive of the movie
        
        Parameters:
        blob_div:      a div standfirst text in it
        
        Returns
            a string of the standfirst text
        '''
        standfirst = ""
        try:
            # in the main body - this callout is the first paragraph
            standfirst = blob_div.p.text.strip()
        except:
            standfirst = ""
        return standfirst



    def _extractRating_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract movie rating info
        
        Parameters:
        blob_div:     a div with the ratings info
        
        Returns
            a list with a numeric score and a rating string
        '''
        #
        #   THR does not really do a numeric rating, it gives a type
        #   of summary description - that is put into the rating string
        star_count = -1
        rating_str = ""
        spans = blob_div.find_all("span")
        for s in spans:
            if ('class' in s.attrs):
                if ("c-span" in s['class']):
                    rating_str = s.text.strip()
        return [star_count, rating_str]



    def _extractAuthor_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the author name
        
        Parameters:
        blob_div:     a div with the author info
        
        Returns
            a string of the author info
        '''
        author = ""
        try:
            # within this div - it is the first anchor
            author = blob_div.a.text.strip()
        except:
            author = ""
        return author



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
#   END class THRArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("THRArticleRequest.py is a class with no main()")


