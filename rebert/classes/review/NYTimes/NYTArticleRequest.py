#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: NYTArticleRequest.py
#   REVISION: August, 2025
#   CREATION DATE: July, 2025
#   AUTHOR: David W. McDonald
#
#   A web service object to collect review article text. The main entry is through
#   the method getReviewArticle(). Just pass it a URL or a partially complete
#   MOVIE_REVIEW_DATA_TEMPLATE (it looks for the 'review_url' in that record).
#
#   The New York Times makes some efforts to limit how much content is collected.
#   They have an API that can be hard to use. This implements screen scraping to
#   extract the review article content from a 'preloadedData' script block.
#
#   Generally, the NY Times states that the API limits are 5 requests per minute
#   (RPM) and a maximum of 500 pages per day. In this article collection class
#   we can work to respect the rate limits - but the max pages has to be managed
#   by the code that uses this class.
#
#   The NY Times server will sometimes response with a 403 HTTP status code (access
#   forbidden. There are two common reasons for that code, exceeding the rate limits
#   or exceeding the daily total maximum requests.
#
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
#   This string is at the start of a data <script> block. This is page content
#   data that is loaded when the page is sent to the browser. 
#
#   We look for that script and then parse the data to extract specific
#   chunks that can then be converted from JSON to a python dictionary
NYT_DATA_SCRIPT_TAG = "window.__preloadedData ="
#
#   The NY Times has an API and they work to enforce rate limits. They have
#   a max of 5 requests per minute and a maximum total requests of 500 per day.
#   We'll make a best effort to respect those restrictions.
NYT_API_RATE_LIMIT_RPM = 5.0
#
#####
#   
#   START class NYTArticleRequest definition
#   
#####

###
#   A class/object that interacts with The Guardian website to collect 
#   review articles.
#
class NYTArticleRequest(ReviewArticleBase):
    '''
    The NYTArticleRequest class is a subclass of ReviewArticleBase that connects to 
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
    def __init__(self, name="NYTArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "nytimes.com"
        #   
        #   Make sure we set the host for this target collector
        self.setHost("https://www.nytimes.com")
        #
        #   Some of the user agent strings are denied access to
        #   content. The 'opera' user agent seems to work most often.
        self.setUserAgent("opera_2023")
        #
        #   Setting the referer header seems to result in *fewer* 
        #   403 - status code denials - this sort of makes it look
        #   like it's a page request from one of their own pages
        self.setHeaderValue("Referer","https://www.nytimes.com/reviews/movies")
        #
        #   The NY Times implmenets rate limiting for API requests.
        #   Here we'll set a throttle rate that is designed to respect
        #   their rate limits.
        self.setThrottleRate(rpm=NYT_API_RATE_LIMIT_RPM)
        #
        #   Some data components that are parsed and extracted that
        #   contain different portions of the review data. 
        self.__preloaded_text_data__ = ""   #   Text of the preloaded data script
        self.__document_block__ = dict()    #   List of dicts, that contain paragraphs
        self.__movie_data__ = dict()        #   Dict of movie data
        self.__by_lines__ = dict()          #   Author bylines
        #self.__headline__ = dict()
        self.__publication_ts__ = ""        #   Publication timestamp
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
        #
        #   The output here was used to watch/view the approximate rate of
        #   the collection effort and see when article page requests started
        #   failing under request limits.
        #
        #if review:
        #    print(f"Requesting (review_url): {review['review_url']}")
        #else:
        #    print(f"Requesting (url): {url}")
        review_dict = super().getReviewArticle(url=url,review=review)
        #if review_dict:
        #    print(f"Got: {review['title']}")
        #else:
        #    print(f"Empty review")
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
        #
        #   We're looking for a particular <script> with page preloaded data
        scripts = html_parse.find_all('script')
        #   Sometimes we don't actually get a page with content, Booo
        if not scripts:
            self.log(f"NO <script> tags in page",level="DEBUG")
        #   Run through all of the scripts - looking for specific data
        for s in scripts:
            #   The script we're looking for currently has no attributes
            if not s.attrs:
                #print(s.text[0:125])
                script_contents = s.text
                #   First, we need to make sure we have the correct script
                #   block, the one with the data in it
                if script_contents.startswith(NYT_DATA_SCRIPT_TAG):
                    script_contents = script_contents.partition("=")[2].strip()
                    if script_contents.endswith(";"):
                        #   Save that extracted script data
                        self.__preloaded_text_data__ = script_contents[:-1]
                        #print(self.__preloaded_text_data__)
                        #   Now parse that text - once parsed, then we can
                        #   mostly extract the components that we need from
                        #   dictionaries that are already parsed out
                        self.__parsePreloadedData__()
        #
        #   A quick check on whether or not we actually found the data <script>
        #   If not - the subsequent code will likely fail
        if not self.__preloaded_text_data__:
            self.log(f"The preloadedData <script> was not found in the page.",
                    level="WARNING")
        #
        #   The method calls should only need to extract data from the
        #   existing dictionaries - already parsed out
        #
        review_title = self._extractArticleTitle_(None)
        title = self._extractMovieTitleFromArticleTitle_(None)
        review_type = self._extractReviewType_(None)
        author = self._extractAuthor_(None)
        post_date = self._extractPostDate_(None)
        standfirst = self._extractStandfirst_(None)
        body = self._extractContent_(None)
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
            #   No rating scores from the NYTimes
            review['rating'] = -1
            review['rating_str'] = ""
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
                if not review['review_date_str']:
                    review['review_date_str'] = post_date[0]
                if not review['review_date_ts']:
                    review['review_date_ts'] = post_date[1]
            #
        self.log(f"returning", level="DEBUG")
        return review



    def __parsePreloadedData__(self):
        '''
        This is only called when we are able to find the data script that
        is loaded with the page - the 'preloaded' data.
        
        This pulls components from the script and converts them to dictionary
        items that can be used by the 'parsing' code. In the case of the 
        New York Times site. The parsing code mostly needs to extract
        specific fields from the resulting dictionaries.
        
        '''
        self.log(f"entering", level="DEBUG")
        #
        #   Extract the "DocumentBlock" - this is a JSON structure that is 
        #   delimited with the "sprinkledBody" key, ending with "storyFormat" key
        #
        #   Contains the paragraph text of the review - plus other junk
        try:
            doc_block = self.__preloaded_text_data__.partition('"sprinkledBody"')[2][1:]
            doc_block = doc_block.partition('"storyFormat"')[0].strip()[:-1]
            doc_block = json.loads(doc_block)
            if "__typename" in doc_block and doc_block['__typename'] == "DocumentBlock":
                self.__document_block__ = doc_block['content']
                #print(json.dumps(self.__document_block__,indent=4))
        except:
            self.log(f"Could not extract the __document_block__ from the data <script>.",
                    level="WARNING")
            self.__document_block__ = dict()
        #
        #   Extract the "ArticleReviewItem" - this is a JSON structure that is 
        #   delimited with the "reviewItems" key, ending with "reviewSummary" key
        #
        #   Contains information about the movie in this review
        try:
            r_items = self.__preloaded_text_data__.partition('"reviewItems"')[2][1:]
            r_items = r_items.partition('"reviewSummary"')[0].strip()[:-1]
            r_items = json.loads(r_items)
            if len(r_items) == 1:
                self.__movie_data__ = r_items[0]
                #print(json.dumps(self.__movie_data__,indent=4))
        except:
            self.log(f"Could not extract the __movie_data__ from the data <script>.",
                    level="WARNING")
            self.__movie_data__ = dict()
        #
        #   Extract the "ByLine" - this is a JSON structure that is 
        #   delimited with the "bylines" key, ending with "collections" key
        #
        #   For convenience we are always picking the first listed author
        try:
            byl = self.__preloaded_text_data__.partition('"bylines"')[2][1:]
            byl = byl.partition('"collections"')[0].strip()[:-1]
            byl = json.loads(byl)
            if len(byl) >= 1:
                #   Extract the basic author data
                self.__by_lines__ = byl[0]['creators'][0]
                #print(json.dumps(self.__by_lines__,indent=4))
        except:
            self.log(f"Could not extract the __by_lines__ from the data <script>.",
                    level="WARNING")
            self.__by_lines__ = dict()
        #
        #   Don't need this - the article title is in the __document_block__
        #
        #   Extract the "Headline" - another JSON structure. This is 
        #   delimited with the "headline" key, ending with "id" key
        #
        #   For convenience we are always picking the first listed author
        #hl = self.__preloaded_text_data__.partition('"headline"')[2][1:]
        #hl = hl.partition('"id"')[0].strip()[:-1]
        #hl = json.loads(hl)
        #if hl:
        #    #   Extract the basic author data
        #    self.__headline__ = hl
        #    #print(json.dumps(self.__headline__,indent=4))
        #
        #   Extract publication timestamp string
        try:
            #
            #   The data script has a number of possible dates in it. The final pick
            #   was based on trial and error. Ultimately, the browse page data is
            #   has the better timestamp for an article. So, that one is used if it
            #   is supplied in an article record.
            #   
            #   This one seems wrong for older content - like from 2010 and earlier
            #fp = self.__preloaded_text_data__.partition('"firstPublished"')[2][1:]
            #   This one changes on almost every delivery of the web page
            #fp = self.__preloaded_text_data__.partition('"lastModified"')[2][1:]
            #
            #   This one *seems* to be the correct for older and newer content
            fp = self.__preloaded_text_data__.partition('"lastMajorModification"')[2][1:]
            fp = fp.partition(",")[0]
            fp = fp.replace('"',"").partition(".")[0]
            self.__publication_ts__ = fp.replace('T'," ")
            #print(self.__publication_ts__)
        except:
            self.log(f"Could not extract the __publication_ts__ from the data <script>.",
                    level="WARNING")
            self.__publication_ts__ = ""
        #
        self.log(f"returning", level="DEBUG")
        return


    def _extractArticleTitle_(self, blob_div=None):
        '''
        Parses the main body of the article to extract the review title
        
        Parameters:
        blob_div:      a div that contains the review article title
        
        Returns
            a string of the article title
        '''
        review_title = ""
        for chunk in self.__document_block__:
            if "__typename" in chunk and chunk['__typename'] == "HeaderBasicBlock":
                #print(json.dumps(chunk,indent=4))
                try:
                    review_title = chunk['headline']['content'][0]['text']
                except:
                    pass
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
        #
        #   Extraction from the by_lines block
        if ("__typename" in self.__by_lines__ and 
            self.__by_lines__['__typename'] == "Person"):
            try:
                author = self.__by_lines__['displayName']
            except:
                pass
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
        for chunk in self.__document_block__:
            if "__typename" in chunk and chunk['__typename'] == "HeaderBasicBlock":
                #print(json.dumps(chunk,indent=4))
                try:
                    standfirst = chunk['summary']['content'][0]['text'].strip()
                except:
                    standfirst = ""
        return standfirst


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
        #print(json.dumps(self.__document_block__,indent=4))
        for chunk in self.__document_block__:
            if "__typename" in chunk and chunk['__typename'] == "ParagraphBlock":
                #print(chunk['content'][0]['text'])
                if body:
                    try:
                        body = body+"\n\n"+chunk['content'][0]['text'].strip()
                    except:
                        pass
                else:
                    try:
                        body = chunk['content'][0]['text'].strip()
                    except:
                        body = ""
        return body


    def _extractReviewType_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the type of this review
        
        Parameters:
        blob_div:       a div that contains the review type
        
        Returns
            a string of the standfirst text
        '''
        review_type = "movie review"
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
        post_date_ts = self.__publication_ts__
        try:
            pd = datetime.strptime(post_date_ts,"%Y-%m-%d %H:%M:%S")
            post_date = pd.strftime("%B %d, %Y")
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
        #print(json.dumps(self.__movie_data__,indent=4))
        title = ""
        try:
            title = self.__movie_data__['subject']['title']
        except:
            pass
        #
        #   A little cleaning for the end
        while title and title[-1] in ",.;:":
            title = title[:-1]
        return title
       
#####
#   
#   END class NYTArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("NYTArticleRequest.py is a class with no main()")

