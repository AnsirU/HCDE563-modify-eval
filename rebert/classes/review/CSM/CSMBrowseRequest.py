#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: CSMBrowseRequest.py
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
#   Common Sense Media does provide an API - it doesn't work quite the same as
#   this browsing option. One would need to frame the requests in a different way
#   to get something similar to what is displayed in the browse. CSM requires an
#   API Key for access to their API - which requires signing a "partnership agreement".
#   This approach skips that requirement, but with the caveat that this screen
#   scraping could break at anytime when they change layout or the structure
#   of their AJAX/JSON calls.
#
#
#   The browse page for Common Sense Media:
#   https://www.commonsensemedia.org/movie-reviews
#   
#   Currently, there is no paging - this returns just one page
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
from rebert.classes.review.base.ReviewBrowseBase import ReviewBrowseBase
from rebert.classes.review.CSM.CSMArticleRequest import CSMArticleRequest
from rebert.classes.review.base.constants import *
from rebert.classes.base.HTTPConnection import HTTPConnection

#####
#   
#   CONSTANTS
#   
#####
#
#   This is the complete list of 'sections' for the CSM browse page
CSM_COLLECT_SECTIONS = [
    'new streaming movies',
    'new in theaters',
    'great watch-together picks',
    'popular with parents',
    'family laughs'
]
#
#   This is the subset that we will actually collect from CSM. It's just
#   a list of strings. You could copy and paste to add sections to collect.
CSM_COLLECT_SECTIONS = [
    'new in theaters'
]

#
#####
#   
#   START class CSMBrowseRequest definition
#   
#####

###
#   A class/object that interacts with Common Sense Media website to collect 
#   movie reviews.
#
class CSMBrowseRequest(ReviewBrowseBase):
    '''
    The CSMBrowseRequest connectes to Common Sense Media website and requests a 'browse' 
    page that lists a set of recent reviews for cultural events. The class will parse the 
    requested browse page to identify links to review articles, and then uses a 
    CSMArticleRequest instance to get data from those reviews.
    
    Attributes:
        browse_service_endpoint     - a string service endpoint for a basic browse
    
    Methods:
        getReviewsByBrowse()        - parses the browse page, returns review article data
        _parseHTMLPage_()           - parse the browse page HTML
        _extractArticleLinks_()     - extract URL, article links, for the review articles
        _filterReview_()            - filter review articles based on features
        _extractMovieTitleFromArticleTitle_()  - extract the movie title from article title

    '''
    def __init__(self, name="CSMBrowseRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   This is our collector class
        self.__article_collector_class__ = CSMArticleRequest
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "commonsensemedia.org"
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://www.commonsensemedia.org")
        #   This is the service endpoint for the current reviews
        self.browse_service_endpoint = "/movie-reviews"
        self.setServiceEndpoint(self.browse_service_endpoint)
        #
        #   Local attributes that are specific to the Common Sense Media
        #   site. These are useful for getting the actual page contents
        #   that we will need.
        self._site_params_ = dict()
        self._site_query_string_ = ""
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
        self.setServiceEndpoint(self.browse_service_endpoint)
        mesg = f"{self.browse_service_endpoint}"
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
        if browse_only:
            self.log(f"returning, browse_only=True", level="DEBUG")
            return review_list
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
        #
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(text,'html.parser')
        #
        #   Common Sense Media is a fully asynchronous content page. That means
        #   the page we just got does not have any of the content we need to
        #   be able to parse out possible articles/reviews. We will need to
        #   construct specific URLs to make different types of requests of
        #   the remote server.
        #
        #   First we need to find a specific <script></script> to extract
        #   parameters that we need for the request   
        script_elt = ""
        scripts = html_parse.find_all('script')
        for s in scripts:
            if ('data-drupal-selector' in s.attrs and 
                'drupal-settings-json' in s['data-drupal-selector']):
                script_elt = s
                break
        if not script_elt: 
            self.log(f"Could not find the <script> in the HTML page.",
                     level="WARNING")
            self.log(f"The <script> element contains essential request parameters.",
                     level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review_list
        #
        #   The text of the script is a big JSON dictionary. We convert that
        #   to a python dictionary so we can use it.
        try:
            self._site_params_ = json.loads(script_elt.text)
            #print(f"{site_params['ajaxPageState']['libraries']=}")
            #
            #   All of the requests require a query string that has a particular format
            #   Create that query string 
            self._site_query_string_ = "?ajax_page_state[libraries]="+self._site_params_['ajaxPageState']['libraries'] 
        except:
            self.log(f"Could not parse <script> element JSON.",
                     level="WARNING")
            self.log(f"returning", level="DEBUG")
            return review_list
        #
        #   We will still need some parameters from the main body of the page
        main_elt = ""
        divs = html_parse.find_all('div')
        for d in divs:
            if 'id' in d.attrs and 'role' in d.attrs:
                if 'content' in d['id'] and 'main' in d['role']:
                    main_elt = d
                    break
        #
        #   Now looking for divs that contain 'data-url' attribute. That attribute
        #   contains the format of the URL. The same div also contains a set of
        #   parameters that we will need to extract
        divs = main_elt.find_all('div')
        for d in divs:
            if 'data-url' in d.attrs and 'data-filter' in d.attrs:
                section_title = d.h2.text.strip().lower()
                if section_title in CSM_COLLECT_SECTIONS:
                    #print(f"{section_title=}")
                    #   Extract the values of the specific attributes
                    data_url = d['data-url']
                    filter_str = d['data-filter'].replace("&quot;","'")
                    data_filter = json.loads(filter_str)
                    #print(f"{data_url=}")
                    #print(f"{data_filter=}")
                    #   Some data_filter items have to be processed to be put
                    #   into a formatted_params URL
                    #   
                    #   This this has been tested and works for all CSM_COLLECT_SECTIONS
                    df_keys = list(data_filter.keys())
                    for k in df_keys:
                        if isinstance(data_filter[k],list):
                            data_filter[k] = [str(x) for x in data_filter[k]]
                            data_filter[k] = "+".join(data_filter[k])
                    #   Once the lists are converted, then we can format the params
                    formatted_params = data_url.format(**data_filter)
                    #print(f"{formatted_params=}")
                    rlist = self._requestBrowseElements_(formatted_params)
                    if rlist:
                        review_list.extend(rlist)
                    
        self.log(f"returning {len(review_list)} items", level="DEBUG")
        return review_list


    ###
    #   This creates a nested HTTP request object to make a data request from the
    #   remote server
    #
    def _requestBrowseElements_(self, formatted_params=""):
        '''
        Creates an HTTPConnection object to make a request for a chunk of the 
        browse page. That chunk is then parsed by _extractArticleLinks_() to
        collect the links to specific articles.
        
        Parameters:
        formatted_params:   the base of a URL that will be used to make an HTTP
                            request, for the chunk of a movie page
        
        Returns
            a list of MOVIE_REVIEW_DATA_TEMPLATE partially filled, or empty dict
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
            url = ""
            if not formatted_params.startswith(self.getHost()):
                url = self.getHost()+formatted_params+self._site_query_string_
            else:
                url = formatted_params+self._site_query_string_
            #print(f"{url=}")
            connect.queueRequest(url=url)
            connect.makeRequest()
            response = connect.nextResponse()
            response = response.json()
            #
            #   What comes back is a JSON object - a list. The fourth item, index 3
            #   contains a dictionary, where the 'data' field is HTML text that is
            #   used to replace the temporary 'slider' elements in the browse page
            html_text = response[3]['data']
        except:
            self.log(f"could not instantiate a conntection object", 
                     level="WARNING")
        #
        if not html_text:
            self.log(f"there was no data from the request, nothing to parse!", level="DEBUG")
            return review_list
        #
        #print(f"{html_text=}")
        #
        #   If we got some HTML text, then we need to parse that before we can find
        #   the elements that we need, to extract article links
        html_parse = BeautifulSoup(html_text,'html.parser')
        #
        #   We will still need some parameters from the main body of the page
        list_items = html_parse.find_all('li')
        for li in list_items:
            #print(f"\n{str(li)=}")
            record = self._extractArticleLinks_(li)
            if record: 
                review_list.append(record)

        return review_list
        
        
    ###
    #   This parses the individual articles once they have been requested
    #
    def _extractArticleLinks_(self, main_div=None):
        '''
        Parses the browse page to extract title and links.
        
        Parameters:
        main_div:       a single div with a single review element to parse
        
        Returns
            a single MOVIE_REVIEW_DATA_TEMPLATE partially filled, or empty dict
        '''
        self.log(f"entering", level="DEBUG")
        record = self.__review_template__.copy()
        
        #   There is an anchor <a...> in an h3 header for the URL
        url = main_div.h3.a['href']
        #print(f"{url=}")
        if not url.startswith(self.getHost()):
            url = self.getHost()+url
        #
        #   The text of that H3 header is the title
        try:
            review_title = main_div.h3.text.strip()
        except:
            review_title = ""
        #print(f"{review_title=}")

        #   If we don't have a title for the review article then we're done
        if not review_title: 
            self.log(f"returning", level="DEBUG")
            return dict()
        #
        #   Save the title and url info
        record['title'] = review_title
        record['review_url'] = url
        record['review_title'] = review_title
        #
        #   Look for some additional items - poster URL and rating
        poster_url = ""
        age_rating = ""
        star_count = 0
        divs = main_div.find_all('div')
        for d in divs:
            #   Skip any divs that don't have a class attribute
            if 'class' not in d.attrs: continue
            #
            #   Possibly get a poster image
            if 'review-image' in d['class']:
                try:
                    #print(f"\n{str(d.img)=}")
                    #   This one isn't what we want - not a poster
                    #poster_url = d.img['src']
                    #   This one is a poster but can vary in size
                    poster_url = d.img['data-src']
                    #   Now try to get a "large" one
                    posters = d.img['data-srcset'].split(",")
                    for p in posters:
                        if '_large' in p:
                            poster_url = p.partition(' ')[0].strip()
                    #   Make it a proper URL with host
                    if not poster_url.startswith(self.getHost()):
                        poster_url = self.getHost()+poster_url
                except:
                    poster_url = ""
                continue
            #
            #   Possibly get the rating of this review
            if 'review-rating' in d['class']:
                try:
                    age_rating = d.div.span.text.strip()
                except:
                    age_rating = ""
                icon_elts = d.find_all('i')
                for icon in icon_elts:
                    #print(f"{str(icon)=}")
                    if 'class' not in icon.attrs: continue
                    if 'icon-star-solid' in icon['class'] and 'active' in icon['class']:
                        star_count += 1
                continue
        #
        #   Now save the data for this article and return it
        record['poster_url'] = poster_url
        if star_count > 0:
            record['rating'] = star_count
            record['rating_str'] = f"{star_count} out of 5 stars"
        if age_rating:
            if record['rating_str']:
                record['rating_str'] = f"for {age_rating}, "+record['rating_str']
            else:
                record['rating_str'] = f"for {age_rating}"
        
        self.log(f"returning", level="DEBUG")
        return record
        
    
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
        #   Get the review type
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
        #   The title of the review is the same as the movie
        title = review_title
        return title
       
#####
#   
#   END class CSMBrowseRequest definition
#   
#####

if __name__ == '__main__':
    print("CSMBrowseRequest.py is a class with no main()")


