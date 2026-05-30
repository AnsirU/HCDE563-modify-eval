#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: KIMBrowseRequest.py
#   REVISION: July, 2025
#   CREATION DATE: July, 2025
#   AUTHOR: David W. McDonald
#
#   A web service object to collect movie review text. This object starts by
#   collecting a review browse page - a web page that lists the reviews that are
#   available roughly by date. The page is parsed to collect the individual URLs
#   for the reviews listed on the browse page. This class then uses the
#   ReviewArticleRequest class to collect the text of the individual reviews.
#
#   The browse page 
#
#   The main page requested is a browse for current reviews
#   https://kids-in-mind.com
#   
#   There does not appear to be a mechanism to "page" to other reviews. If a page
#   other than page=1 is requested this will return an empty dictionary to indicate
#   that the page is not available.
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
###
#
#   Standard python modules
import json, copy, time, re
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
from rebert.classes.base.HTTPConnection import HTTPConnection
#
from rebert.classes.review.base.ReviewBrowseBase import ReviewBrowseBase
from rebert.classes.review.KIM.KIMArticleRequest import KIMArticleRequest
from rebert.classes.review.base.constants import *

#####
#   
#   CONSTANTS
#   
#####
#
#   List of exception pages. These are pages/URLs that are mixed in with the
#   reviews. They are here as constants, and if they are found on the page
#   they are removed before we return the item as a potential review article.
#
KIM_EXCEPTION_URLS = [
    "terms.htm",
    "/donate.htm",
    "/subscribe.htm",
    "/email-protection",
    "/about.htm",
    "/content.time.com",
    "/search-desktop.htm"
]
#
#####
#   
#   START class KIMBrowseRequest definition
#   
#####

###
#   A class/object that interacts with the Slant Magazine website to collect 
#   movie reviews.
#
class KIMBrowseRequest(ReviewBrowseBase):
    '''
    The KIMBrowseRequest connectes to the Kids-in-Mind film review site and requests a  
    'browse' page that lists a set of recent movie reviews. The class will parse the 
    requested browse page to identify links to review articles, and then uses a 
    APArticleRequest instance to get data from those reviews.
    
    Attributes:
        browse_service_endpoint     - a string service endpoint for a basic browse
    
    Methods:
        getReviewsByBrowse()        - parses the browse page, returns review article data
        _parseHTMLPage_()           - parse the browse page HTML
        _extractArticleLinks_()     - extract URL, article links, for the review articles
        _filterReview_()            - filter review articles based on features
        _extractMovieTitleFromArticleTitle_()  - extract the movie title from article title

    '''
    def __init__(self, name="KIMBrowseRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   This is our collector class
        self.__article_collector_class__ = KIMArticleRequest
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "kids-in-mind.com"
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://kids-in-mind.com")
        #   The main URL is the 'browse' page, but there is a little
        #   problem with that, Below we hack the collection of recent
        #   release information
        self.browse_service_endpoint = "" 
        return
        
    
    ###
    #   This method collects the browse page and then all of the articles
    #   associated with the page.
    #
    def getReviewsByBrowse(self, page=0, browse_only=False):
        '''
        This requests review browse page. If the page request is succesful this
        calls method _parseHTMLPage_() to extract review article links. It then
        uses the resulting review_list and calls 
        
        Parameters:
        page:           the index of the browse page to request, parse and collect
        browse_only:    a boolean, if True returns just the results of the browse
                        parse, False by default, returns the full article
        
        Returns
            a list of review dictionary items, or an empty list
        '''
        self.log(f"entering", level="DEBUG")
        #   Initialize the list of the review
        review_list = list()
        #   Set the request to the default browse request
        #self.setServiceEndpoint(self.browse_service_endpoint)
        mesg = f"{self.getHost()}"
        #   Indexing really starts at page 2
        if page > 1:
            #
            #   Currently ONLY 1 PAGE - paging has not been worked out
            self.log(f"page {page}, is not a valid page, no results returned", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review_list
        
        #   Clear out any prior list of review items that were filtered out
        #   If you want them, get them before starting a new request!
        self._removed_reviews_ = list()        
        
        #   Try to get a page
        self.queueRequest()
        self.log(f"requesting '{mesg}'", level="DEBUG")
        self.makeRequest()
        if self.responses():
            resp = self.nextResponse()
            text = resp.text
        else:
            mesg = "request did not return a page"
            self.log(f"{mesg}", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review_list
        
        #   Parse out the basic information from the 
        review_list = self._parseHTMLPage_(text)
        #
        #   Kids-in-Mind is a type of 'blog' site. The main browse page lists
        #   a small number of recent reviews. At this point in the code we
        #   should have that small set.
        #
        #   HOWEVER, a review article page has a larger set of potential
        #   articles. We'll get one article page, and parse that to
        #   see if we can find a larger set of potential reviews that
        #   could be collected.
        #
        if review_list and review_list[0]['review_url']:
            new_reviews = self._collectSidebarReviews_(review_list[0])
            nr_len = len(new_reviews)
            r_len = len(review_list)
            if nr_len > r_len:
                review_list = new_reviews
                self.log(f"Collected {{nr_len-r_len}} additional reviews from extended browse collection", 
                        level="DEBUG")
        #
        #   If it's just requesting the browse page - then return the
        #   browse result without collecting the articles
        if browse_only:
            self.log(f"returning, browse_only=True", level="DEBUG")
            return review_list
        #
        #   Now, get the individual article text - and filter the list so that
        #   it hopefully only contains movies/films
        review_list = self._getReviewContents_(review_list)
        
        self.log(f"returning", level="DEBUG")
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
        review_list = list()
        #   No HTML text, return empty list
        if not text: 
            self.log(f"HTML text was empty!", level="WARNING")
            return review_list
        self.log(f"entering", level="DEBUG")
        
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(text,'html.parser')
        #
        #   Looking for a specific div tag in the <body>
        main_content = ""
        divs = html_parse.body.find_all('div')
        for d in divs:
            #   Running through the divs, look for one that is the main-area
            if 'id' in d.attrs and "et-main-area" in d['id']:
                main_content = d
                break
        #
        #   Now, looking for divs that are "et_pb_text_inner"
        divs = main_content.find_all('div')
        for d in divs:
            #   When we find this - its a single movie item - hopefully
            if 'class' in d.attrs and "et_pb_text_inner" in d['class']:
                #print(f"{d['class']=}")
                record = self._extractArticleLinks_(d)
                if record: 
                    review_list.append(record)
        self.log(f"returning", level="DEBUG")
        return review_list
        
        
    ###
    #   This parses the individual tiles of the page to
    #   collect the movie information
    #
    def _extractArticleLinks_(self, main_div=None):
        '''
        Parses the browse page to extract title and links.
        
        Parameters:
        main_div:       a single div with the body of the browse page
        
        Returns
            a single MOVIE_REVIEW_DATA_TEMPLATE partially filled, or empty dict
        '''
        self.log(f"entering", level="DEBUG")
        record = self.__review_template__.copy()
        #
        url = ""
        review_title = ""
        try:
            #   Grab the link from the first anchor <A ...>
            url = main_div.a['href']
            #   The text of that first anchor is the title of the review article
            review_title = main_div.a.text.strip()
        except:
            pass
        #
        #print(f"{review_title=}")
        #print(f"{url=}")
        #
        #   If we cannot get a url and a title - then this isn't the right div
        if not (url and review_title): 
            self.log(f"returning", level="DEBUG")
            return dict()
        #
        for u in KIM_EXCEPTION_URLS:
            if u in url:
                #print(f"Removing item with url: {url}")
                self.log(f"returning", level="DEBUG")
                return dict()
        #
        #
        if not url.startswith(self.getHost()):
            url = self.getHost()+url
        #
        #   Extract the title of the movie
        title = self._extractMovieTitleFromArticleTitle_(review_title)
        #
        #   There is no 'author' at this level
        #        
        #   Now save the data for this article and return it
        record['title'] = title.strip()
        record['review_url'] = url
        record['review_title'] = review_title

        self.log(f"returning", level="DEBUG")
        return record


    def _collectSidebarReviews_(self, review={}):
        '''
        Collects a single article page and parses that result for the list of
        movie reviews that are in the sidebar. 
        
        Parameters:
        review:         a single review dictionary record
        
        Returns
            a new review_list that is probably a longer list than the one
            we started with
        '''
        review_list = list()
        html_text = ""
        try:
            #   We need an HTTP connection to make a generic request
            connect = HTTPConnection(name="Nested_Browse_Managed",
                                    logger=self.getLogger())
            #   Pick a random user agent to simulate a browser reqeust
            connect.setUserAgent()
            #   Create a URL that should get us some data
            url = review['review_url']
            if not url.startswith(self.getHost()):
                url = self.getHost()+url
            #print(f"{url=}")
            connect.queueRequest(url=url)
            connect.makeRequest()
            response = connect.nextResponse()
            #   We should get an HTML page
            html_text = response.text
        except:
            self.log(f"could not instantiate a conntection object", 
                     level="WARNING")
        #
        #   Check that we have something to work with
        if not html_text:
            self.log(f"there was no data from the request, nothing to parse!", level="DEBUG")
            return review_list
        #
        #   Parse the HTML page
        html_parse = BeautifulSoup(html_text,'html.parser')
        #
        sidebar_elt = ""
        #   Just extract the sidebar div
        divs = html_parse.body.article.find_all('div')
        for d in divs:
            if 'class' not in d.attrs: continue
            #   Find the first div that is likely a sidebar
            if 'et_pb_code_1' in d['class'] and 'sidebar' in d['class']:
                sidebar_elt = d
                break
        #
        #   Check that we extracted a sidebar
        if not sidebar_elt:
            self.log(f"could not find the page sidebar element", level="DEBUG")
            return review_list
        #
        #   Have the elements, try to extract the movies
        review_list = self._extractSidebarReviews_(sidebar_elt)
        #
        return review_list


    def _extractSidebarReviews_(self, sidebar_div=None):
        '''
        Uses an article page sidebar to find a larger list of potential
        movie reviews. This extends the basic set of reviews from the
        main browse page 
        
        Parameters:
        sidebar_div         a div that contains a list of movie titles and
                            the links to those movie reviews
        
        Returns
            a list of partially complete templates
        '''
        review_list = list()
        inner_div = ""
        divs = sidebar_div.find_all("div")
        for d in divs:
            if "class" in d.attrs and "et_pb_code_inner" in d["class"]:
                inner_div = d
                break
        #
        #   Now process each of the following elements in order
        all_elts = inner_div.find_all()
        for elt in all_elts:
            #print(f"{elt=}")
            elt_str = str(elt)
            if elt_str.startswith("<span "):
                try:
                    header_text = elt.text.strip().lower()
                except:
                    header_text = ""
                continue
            if elt_str.startswith("<a "):
                review_title = ""
                url = ""
                try:
                    review_title = elt.text.strip()
                    url = elt['href']
                    #
                    if not url.startswith(self.getHost()):
                        url = self.getHost()+url
                except:
                    review_title = ""
                    url = ""
                if review_title:
                    record = self.__review_template__.copy()
                    #if header_text == "this week":
                    #    print(f"THIS WEEK '{review_title}' ({url})")                    
                    #if header_text == "current releases":
                    #    print(f"CURRENT RELEASES '{review_title}' ({url})")
                    #
                    #   Now save the data for this article and return it
                    title = self._extractMovieTitleFromArticleTitle_(review_title)
                    record['title'] = title
                    record['review_url'] = url
                    record['review_title'] = review_title
                    review_list.append(record)
        return review_list


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
        review = super()._filterReview_(review)
        if not review: return dict()
        #
        #   Filtering specific to the AP News reviews, review types
        rtype = review['review_type'].lower()
        #   Keep stuff about movies and film
        if 'movie' not in rtype and 'film' not in rtype:
            self._removed_reviews_.append(review)
            self.log(f"removed, not a movie review: '{review['title']}'", level="INFO")
            return dict()
        return review
    
    
    def _extractMovieTitleFromArticleTitle_(self, review_title=None):
        '''
        Extracts a movie title from a review article title
        
        Parameters:
        review_title:   the title of the review article
        
        Returns
            the title of the extracted movie or an empty string
        '''
        #
        #   Review title is the movie title
        title = review_title.strip()
        #
        return title
       
#####
#   
#   END class KIMBrowseRequest definition
#   
#####

if __name__ == '__main__':
    print("KIMBrowseRequest.py is a class with no main()")


