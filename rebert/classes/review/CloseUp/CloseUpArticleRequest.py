#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: CloseUpArticleRequest.py
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
#   Some reviews have a closing sentence related to social media
#   sharing. We'll try to remove that
CLOSEUP_ON_SOCIAL = "\nShare on Facebook"


#####
#   
#   START class CloseUpArticleRequest definition
#   
#####

###
#   A class/object that interacts with The Guardian website to collect 
#   review articles.
#
class CloseUpArticleRequest(ReviewArticleBase):
    '''
    The CloseUpArticleRequest class is a subclass of ReviewArticleBase that connects to 
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
    def __init__(self, name="CloseUpArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "close-upfilm.co.uk"
        #   
        #   Add an ordered set of regex to extract movie titles
        rex = re.compile(r"^(.*)[ \u0020\u00A0\u2013]*\(.*\)[ \u0020\u00A0]*|Close-up[ \u0020\u00A0]*Film Review",
                        flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://close-upfilm.co.uk")
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
        #   
        #   This site, Close-up Film, has some problems with the HTML that is
        #   generated - either by the site or by scripts that are run to fill out 
        #   the page contents. Those problems confuse the default Python HTML parser.
        #   The 'html5lib' parser seems to parse the page better, but that requires
        #   an installation. 
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
        #
        #   This page sends content in a <script> tag that is used to fill out the
        #   page content. Let's first see if we can find that <script>
        script_dict = dict()
        scripts = html_parse.find_all('script')
        for s in scripts:
            if (('type' in s.attrs and "application/ld+json" in s['type']) and
                ('class' in s.attrs and 'yasr-schema-graph' in s['class'])):
                script_dict = json.loads(s.contents[0])
                break
        #
        #   Actually, if we get the script dict, then we can pull almost 
        #   everything from that. BUT, because the HTML page parsing was 
        #   completed prior to finding this script data, we'll just use
        #   the script data to get the body
        if script_dict:
            #   This debug shows a pretty print of the dictionary as JSON
            #print(json.dumps(script_dict, indent=4))
            #
            #   Traverse the dictionary structure, to extract what we want
            review_contents = script_dict['Review']['reviewBody']
            author = script_dict['Review']['author']['name']
            #   The author name is actually a separator between some
            #   review context info and the review body
            body = review_contents.partition(author)[2].strip()
            body = body.partition(CLOSEUP_ON_SOCIAL)[0].strip()
            #
            #   Ok, a bunch of clean up, they scatter all kinds of HTML entities
            #   and UNICODE markup through their reviews. It's not very standardized.
            body = body.replace("\n\n\n\n","\n\n")
            body = body.replace("\n\n\n","\n\n")
            body = body.replace("&amp;","&").replace("&#38;","&")
            body = body.replace("&endash;"," ").replace("&#8211;","-").replace("&#8212;","-")
            body = body.replace("&rsquo;"," ").replace("&#8216;","'").replace("&#8217;","'")
            body = body.replace("&#8220;",'"').replace("&#8221;",'"')
            body = body.replace("&nbsp;"," ").replace("&#160;"," ").replace("\u00A0"," ")
            body = body.replace("    "," ").replace("   "," ").replace("  "," ")
        #    
        #   We are looking for one specific <article> item that contains
        #   the essential contents
        art_elt = ""
        divs = html_parse.find_all('div')
        for d in divs:
            if 'class' in d.attrs and "cm-container" in d['class']:
                try:
                    elt = d.div.div
                    if 'class' in elt.attrs and 'id' in elt.attrs:
                        if 'cm-primary' in elt['id']:
                            art_elt = elt.div.article
                            break
                except:
                    main_elt = ""
        #
        #   Check that we actually got something that we might be able to parse
        if not art_elt:
            self.log(f"returning, missing main content element", level="DEBUG")
            return dict()
        #   
        review_title = self._extractArticleTitle_(art_elt.header)
        title = self._extractMovieTitleFromArticleTitle_(review_title)
        review_type = self._extractReviewType_(art_elt.header)
        #
        author_elt = ""
        body_elt = ""
        divs = art_elt.find_all('div')
        for d in divs:
            if 'class' in d.attrs and "cm-below-entry-meta" in d['class']:
                author_elt = d
            if 'class' in d.attrs and "cm-entry-summary" in d['class']:
                body_elt = d
            if author_elt and body_elt: break
        #
        #   Extracted from the author_elt
        if not author:
            #   but only parse it out if we didn't get it earlier
            author = self._extractAuthor_(author_elt)
        #   Post date from 
        post_date = self._extractPostDate_(author_elt)
        #
        #   Extracted from the body_elt
        rating = self._extractRating_(body_elt)
        #   If something went wrong with the <script> extraction
        #   maybe we can get what we need another way.
        if not body:
            body = self._extractContent_(body_elt)
        #
        #print(f"{review_title=}")
        #print(f"{title=}")
        #print(f"{review_type=}")
        #print(f"{author=}")
        #print(f"{post_date=}")
        #print(f"{rating=}")
        #print(f"{body=}")
        #print(body)
        #return dict()
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
            #   Make sure we keep the review itself
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
            #review_title = review_title.replace("\u0020"," ")
            review_title = review_title.replace("\u00A0"," ").strip()
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
            spans = blob_div.find_all("span")
            for s in spans:
                if 'class' in s.attrs and 'cm-author' in s['class']:
                    author = s.a.text.strip()
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
        try:
            rate_div = blob_div.div.div.div
            #print(f"{rate_div=}")
            if 'yasr-rater-stars' in rate_div['class']:
                star_data = rate_div['data-rating']
                #print(f"{star_data=}")
                try:
                    star_count = int(star_data)
                except:
                    try:
                        star_count = float(star_data)
                    except:
                        star_count = -1
        except:
            star_count = -1
        #
        #   If we didn't find any star ratings, return an empty list
        if star_count < 0: return list()
        #
        #   A little bit of standardization
        whole = int(star_count)
        frac = star_count - whole
        if frac < 0.250:
            star_count = whole
        elif frac >= 0.25 and frac < 0.750:
            star_count = whole + 0.50
        else:
            star_count = whole + 1
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
        try:
            #   
            for elt in blob_div.children:
                #   Keep this testing code to help "see" children if this
                #   format is changed
                #if not elt.name:
                #    print(f"{elt=}")
                #else:
                #    print(f"{elt.name=}")
                #
                #   The contents of the body are just the paragraphs
                #   at this level
                if elt.name == 'p': 
                    body = body+"\n"+elt.text
        except:
            body = ""
        #
        #   If we actually extracted something, then it needs some cleaning
        if body:
            #body = body.replace("<p>"," ").replace("</p>"," ")
            #body = body.replace("\u0020"," ")
            body = body.replace("\u00A0"," ")
            body = body.replace("  "," ").replace("  "," ")
            body = body.strip()
            if ((body.startswith("Dir. ") or body.startswith("Dir: ")) and 
                "Cast: " in body):
                return ""
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
            title_info = blob_div.h1.text.strip().lower()
            if title_info.endswith("film review"):
                review_type = "film_review"
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
            spans = blob_div.find_all("span")
            for s in spans:
                if 'class' in s.attrs and 'cm-post-date' in s['class']:
                    post_date_ts = s.time['datetime'].replace("T"," ")
                    post_date_ts = post_date_ts.partition("+")[0]
                    post_date = s.time.text.strip()
                    break
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
        #   A little bit of fix up
        #title = title.replace("\u0020","")
        title = title.replace("\u00A0"," ")
        title = title.strip()
        #
        #   Clean the end - just one char in most cases
        if title and title[-1] in '\u2011\u2012\u2013\u2014\uFE58':
            title = title[:-1].strip()
        return title
       
#####
#   
#   END class CloseUpArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("CloseUpArticleRequest.py is a class with no main()")

