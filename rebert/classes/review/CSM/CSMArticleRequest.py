#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: CSMArticleRequest.py
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
#   CSM makes specific judgements on several aspects of a movie. This 
#   'map' will determine which sections to keep when parsing the body of
#   the review.
#
CSM_CONTENT_SECTION_MAP = {
    "Parents Need to Know": False,      #   This section is a real pain to get
    "Sex, Romance & Nudity": True,
    "Drinking, Drugs & Smoking": True,
    "Language": True,
    "Violence & Scariness": True,
    "Diverse Representations": True,
    "Positive Messages": True,
    "Positive Role Models": True
}
#
#   This template is filled in by the extractor when applying the map
#   to create the body of the review.
#
CSM_CONTENT_SECTION_TEMPLATE = {
    "Parents Need to Know": "",
    "Sex, Romance & Nudity": "",
    "Drinking, Drugs & Smoking": "",
    "Language": "",
    "Violence & Scariness": "",
    "Diverse Representations": "",
    "Positive Messages": "",
    "Positive Role Models": "",
}

#####
#   
#   START class CSMArticleRequest definition
#   
#####

###
#   A class/object that interacts with The Associated Press website to collect 
#   review articles.
#
class CSMArticleRequest(ReviewArticleBase):
    '''
    The CSMArticleRequest class is a subclass of ReviewArticleBase that connects to the 
    Common Sense Media website to request a specified article. This is assumed to be a movie
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
    def __init__(self, name="CSMArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "commonsensemedia.org"
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://www.commonsensemedia.org")
        #
        #   A map of the sections that are to be kept when extracting these reviews
        #   You can modify what is kept by providing a different section map. 
        self.__section_map__ = CSM_CONTENT_SECTION_MAP.copy()
        #
        #   Local attributes that are specific to the Common Sense Media
        #   site. We might need these for requests, or for filling out the
        #   reivew record template
        self._site_params_ = dict()
        self._article_data_ = dict()
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
        #   Parse the HTML page
        html_parse = BeautifulSoup(text,'html.parser')
        #
        #   Common Sense Media uses a lot of JavaScript to create their pages.
        #   A review article contains a <script> that is just a chunk of JSON
        #   and which contains most of the data we might want to extract.
        #
        #   Let's first see if we can find that chunk of <script>  
        data_json = ""
        article_data = dict()
        scripts = html_parse.find_all('script')
        #
        #   Looking for a review data <script> block
        for s in scripts:
            if 'type' in s.attrs and 'application/ld+json' in s['type']:
                try:
                    data_json = s.text.strip()
                    article_data = json.loads(data_json)
                    #   There could be other JSON type scripts, probe this to see
                    #   if it looks like the one we need.
                    try:
                        self._article_data_ = article_data['@graph'][0]
                    except:
                        data_json = ""
                        article_data = dict()        
                        self.log(f"Found and parsed a data <script>, but structure seems wrong.",
                                 level="WARNING")
                except:
                    data_json = ""
                    article_data = dict()        
                    self.log(f"Found a data <script>, but could not parse it.",
                             level="WARNING")
                # If we found the data - then stop looking
                if self._article_data_: break
        #
        #   Looking for the site parameters <script> block
        for s in scripts:
            if ('data-drupal-selector' in s.attrs and 
                'drupal-settings-json' in s['data-drupal-selector']):
                try:
                    self._site_params_ = json.loads(s.text.strip())
                except:
                    self._site_params_ = dict()
                    self.log(f"Found params <script> block, but parse failed.",
                             level="WARNING")
                #  Stop looking when we find the script block
                if self._site_params_: break
        #
        #   The page still has some content we would want - find the main content
        #   chunk so we can focus in on that.
        main_elt = ""
        divs = html_parse.find_all('div')
        for d in divs:
            if 'id' in d.attrs and 'role' in d.attrs:
                if 'content' in d['id'] and 'main' in d['role']:
                    main_elt = d
                    break
        #
        #   Within that main_elt are a header div and a main body
        #   div that contains the review, see if we can find those
        header_div = ""
        review_div = ""
        divs = main_elt.find_all('div')
        for d in divs:
            if 'class' in d.attrs:
                if ('review-view-top' in d['class'] and 
                    'review-teaser-parent' in d['class']):
                    header_div = d
            if 'id' in d.attrs and 'class' in d.attrs:
                if ('review-view-content-main' in d['id'] and 
                    'review-view-content-main' in d['class']):
                    review_div = d
            if header_div and review_div: break
        #
        #
        #   NOW, BEFORE we parse any further let's see if we can get some
        #   of what we want from the self._article_data_ dictionary
        #
        #self._article_data_ = None  #   TESTING
        if self._article_data_:
            review_type = self._article_data_['itemReviewed']['@type'].lower()
            review_type = review_type +" "+self._article_data_['@type'].lower()
            review_title = self._article_data_['name']
            title = self._article_data_['itemReviewed']['name']
            author = self._article_data_['author']['name']
            try:
                score = int(self._article_data_['reviewRating']['ratingValue'])
            except:
                score = self._article_data_['reviewRating']['ratingValue']
            rate_str = f"for {self._article_data_['typicalAgeRange']}, {score} out of 5 stars"
            rating = [score, rate_str]
            post_ts = self._article_data_['datePublished']
            pd = datetime.strptime(post_ts,"%Y-%m-%d")
            post_date_ts = str(pd)
            post_date = [str(pd.strftime("%B %d, %Y")), post_date_ts]
            body = self._article_data_['reviewBody'].strip()
        else:
            #   If we didn't find the article data then we need to
            #   further parse the header and review divs
            review_title = self._extractArticleTitle_(header_div)
            title = self._extractMovieTitleFromArticleTitle_(review_title)
            review_type = self._extractReviewType_(header_div)
            #   These come from the main body
            author = self._extractAuthor_(review_div)
            rating = self._extractRating_(review_div)
            post_date = self._extractPostDate_(review_div)
        
        #   Try to extract the body
        if not body:
            #   If we didn't get the script data, the just what we parse
            body = self._extractContent_(review_div)
        else:
            #   With the script data we extend that content
            body_2 = self._extractContent_(review_div)
            if body_2:
                body = "What's the Story?\n"+body+"\n\n"+body_2
        #
        #
        #print(f"{review_title=}")
        #print(f"{title=}")
        #print(f"{review_type=}")
        #print(f"{author=}")
        #print(f"{rating=}")
        #print(f"{post_date=}")
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
        spans = blob_div.find_all('span')
        for s in spans:
            try:
                anchor = s.strong.a
                author = anchor.text.strip()
            except:
                author = ""
            if author: break
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
        age_rating = ""
        spans = blob_div.find_all("span")
        for s in spans:
            if 'class' not in s.attrs: continue
            if 'rating__age' in s['class']:
                age_rating = s.text.strip()
            if 'rating__score' in s['class']:
                star_count = 0
                icon_elts = s.find_all('i')
                for icon in icon_elts:
                    #print(f"{str(icon)=}")
                    if 'class' not in icon.attrs: continue
                    if 'icon-star-solid' in icon['class'] and 'active' in icon['class']:
                        star_count += 1
            if age_rating and (star_count > 0): break
        
        if star_count > 0:
            rating_str = f"{star_count} out of 5 stars"

        if age_rating:
            if rating_str:
                rating_str = f"for {age_rating}, "+rating_str
            else:
                rating_str = f"for {age_rating}"

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
        content_dict = CSM_CONTENT_SECTION_TEMPLATE.copy()
        divs = blob_div.find_all("div")
        review_grid = ""
        for d in divs:
            if 'id' in d.attrs and 'class' in d.attrs:
                if ('review-view-content-grid' in d['id'] and 
                    'review-view-content-grid' in d['class']):
                    review_grid = d
                    break
        
        divs = review_grid.find_all("div")
        for d in divs:
            if 'class' in d.attrs and 'content-grid-content' in d['class']:
                #   This is a candidate for a section to collect
                try:
                    sec_key = d.button.span.text.strip()
                    if self.__section_map__[sec_key]:
                        sec_text = d['data-text'].strip()
                        sec_text = sec_text.replace("<p>","").replace("</p>","")
                        content_dict[sec_key] = sec_text
                    else:
                        print(f"FOUND MISSING Section: {sec_key}")
                except:
                    pass

        header_keys = list(content_dict.keys())
        for header in header_keys:
            #   If there is content, append to the body
            if content_dict[header]:
                if body:
                    body = body+"\n\n"+header+"\n"+content_dict[header]
                else:
                    body = header+"\n"+content_dict[header]
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
            review_type = blob_div.div.div.span.text.strip().lower()+" review"
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
        details_div = ""
        divs = blob_div.find_all("div")
        for d in divs:
            if 'id' in d.attrs and 'review-product-details' in d['id']:
                details_div = d
                break
        spans = details_div.find_all('span')
        for s in spans:
            if 'class' in s.attrs and 'detail--last-updated' in s['class']:
                post_date = s.text.strip()

        try:
            pd = datetime.strptime(post_date,"%B %d, %Y")
            post_date_ts = str(pd)
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
        #   Some film titles at this site end with the year - that is
        #   a problem for the title matching that is used. Let's see if
        #   we can detect that and remove that from the title
        rex = re.compile(r" \(\d\d\d\d\)$",flags=re.ASCII)
        year = rex.findall(review_title)
        if year:
            title = review_title.replace(year[0],'').strip()
        else:
            title = review_title
        return title
       
#####
#   
#   END class CSMArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("CSMArticleRequest.py is a class with no main()")

