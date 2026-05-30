#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: PluggedInArticleRequest.py
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
#   The website writes reviews a little differently covering movies by
#   describing specific elements that are of specific interest to the
#   community of readers - and that reflect specific religious values
#   associated with the site sponsor. 
#
#   The 'map' is used by the collector to specify which sections of the
#   review to keep when composing the body of the review. By default if
#   a section is empty when it is extracted from an article - it will be omitted.
#
PLUGGED_IN_SECTION_MAP = {
    "Jump to:": False,              #   special case section, always skip
    "Movie Review": True,
    "Positive Elements": True,
    "Spiritual Elements": True,
    "Sexual & Romantic Content": True,
    "Violent Content": True,
    "Crude or Profane Language": True,
    "Drug & Alcohol Content": True,
    "Other Noteworthy Elements": True,
    "Conclusion": True
}
#
#   This template is filled in by the extractor when applying the map
#   to create the body of the review.
#
PLUGGED_IN_SECTION_TEMPLATE = {
    "Movie Review": "",
    "Positive Elements": "",
    "Spiritual Elements": "",
    "Sexual & Romantic Content": "",
    "Violent Content": "",
    "Crude or Profane Language": "",
    "Drug & Alcohol Content": "",
    "Other Noteworthy Elements": "",
    "Conclusion": ""
}
#
#   We're going to guess that the the review is posted 5 days prior to
#   the first date we can find in the review. This is consistent, but
#   may not be accurate.
#
PLUGGED_IN_POST_DATE_OFFSET = 5
#
#


#####
#   
#   START class PluggedInArticleRequest definition
#   
#####

###
#   A class/object that interacts with the PluggedIn website to collect 
#   review articles.
#
class PluggedInArticleRequest(ReviewArticleBase):
    '''
    The PluggedInArticleRequest class is a subclass of ReviewArticleBase that connects
    to the PluggedIn site to request a specified article. This is assumed to be a review
    article. The class parses the HTML web page to collect the review text and fill 
    out a MOVIE_REVIEW_DATA_TEMPLATE (dictionary).
    
    These reviews have several sections. A "map" is used to specify what sections should
    be collected and added to the body text of the returned review.
    
    Attributes:
        No attributes beyond those inherited from HTTPConnection
    
    Methods:
        getReviewArticle()      - can be used to request the page, returns a movie review
        _parseHTMLPage_()       - parse the HTML and return a movie review record
        _extractArticleTitle_() - get the title of the movie
        _extractAuthor_()       - extract the author/reviewer
        _extractContent_()      - extract the body content
        _extractReviewType_()   - get the type of the review, in theaters or dvd/streaming
        _extractRating_()       - extract the caution text
        _estimatePostingDate_() - estimate posting date based on credits
        _extractCredits_()      - extract the credits to try and help estimate post date
    
    '''
    def __init__(self, name="PluggedInArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "pluggedin.com"
        #   A map of the sections that are to be kept when extracting these reviews
        #   You can modify what is kept by providing a different section map.
        self.__section_map__ = PLUGGED_IN_SECTION_MAP.copy()
        #
        #   Set attributes specific to this website
        self.setHost("https://www.pluggedin.com")
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
        review_title = ""   # the article title
        body = ""           # the main text of the review
        post_date = ""      # a string of the posting date, with time
        author = ""         # the author/reviewer name
        review_type = ""    # the item being reviewed
        rating = list()     # an extracted rating "content caution"
        credits_info = dict()
        #
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(text,'html.parser')
        divs = html_parse.find_all('div')
        main_content = None
        for div in divs:
            if 'data-elementor-type' in div.attrs and 'single' in div['data-elementor-type']:
                main_content = div
                break
        #
        #   Early header elements contain some key information as <li> list items
        #   and <h1> header items - see if we can extract those first
        review_title = self._extractArticleTitle_(main_content)
        #   Movie title is the same as review title
        title = review_title
        #   This is the review type from the header
        review_type = self._extractReviewType_(main_content)
        #   Attempt to get the content of the review
        body = self._extractContent_(main_content)
        #   Extract the review author
        author = self._extractAuthor_(main_content)
        rating = self._extractRating_(main_content)
        #   The credits can help us set the review type and the
        #   potential post date.
        credits_info = self._extractCredits_(main_content)
        #   Extract the credits first, then estimate the posting date.
        #   Plugged In does not provide a review posting date - so we
        #   estimate it a few days prior to the earliest date we can find
        #   This might not be too accurate - but it is consistent.
        post_date = self._estimatePostingDate_(review_type,credits_info)
        #
        #print(f"{title=}")
        #print(f"{review_title=}")
        #print(f"{review_type=}")
        #print(f"{author=}")
        #print(f"{post_date=}")
        #print(json.dumps(credits_info,indent=4))
        #print(f"{body=}")
        #
        #   Supposing we collected at least the body of an article
        #   then we'll fill out the review record as best possible
        if body:
            #   Create a new one if one was not provided
            if not review:
                review = self.__review_template__.copy()
            if author:
                review['author'] = author
            elif credits_info:
                review['author'] = credits_info['reviewer']
            if title and not review['title']:
                review['title'] = review_title
            if review_title:
                review['review_title'] = review_title
            review['review_type'] = review_type
            review['review'] = body
            if rating:
                review['rating'] = rating[0]
                review['rating_str'] = rating[1]
            if post_date:
                review['review_date_str'] = post_date[0]
                review['review_date_ts'] = post_date[1]
        
        self.log(f"returning", level="DEBUG")
        return review



    def _extractArticleTitle_(self, blob_div=None):
        '''
        Parses the main body of the article to extract the review text
        
        Parameters:
        blob_div:       a div that contains the review article title
        
        Returns
            a string of the article title
        '''
        #   The first <h1> header item should be the article title
        review_title = ""
        try:
            title_header = blob_div.find('h1')
            if title_header:
                review_title = title_header.text.strip()
                #   Clean the title- not efficient, but simple
                review_title = review_title.replace("\u2018","'").replace("\u2019","'")
                review_title = review_title.replace("\u201c",'"').replace("\u201d",'"')
                review_title = review_title.replace("\u2013","-").replace("\u2014","-")
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
        #self.log(f"entering", level="DEBUG")
        #
        #   We're extracting the author data from a chunk of the page that is
        #   very near the bottom (visually). This is one of the few places where
        #   there is an attribute in the HTML that we can use to grab the
        #   review author's name.
        #
        author = ""
        divs = blob_div.find_all("div")
        for div in divs:
            if 'class' in div.attrs and 'contributor-bio-block' in div['class']:
                name_heading = div.find('h5')
                if name_heading:
                    author = name_heading.text
                break
        #self.log(f"returning", level="DEBUG")
        return author



    def _extractContent_(self, blob_div=None):
        '''
        Parses the main body of the article to extract the review text.
        
        Parameters:
        blob_div:       a single div with the review items, there may
                        be sub-items that are parsed to extract text
        
        Returns
            a string of the review text
        '''
        #
        #   Parsing is navigating down to the items that we need
        #   There are no specific keys that are useful to identifying
        #   the specific data we want.
        #
        body = ""
        concluded = False
        contents_section = None
        contents_div = None
        content_dict = PLUGGED_IN_SECTION_TEMPLATE.copy()
        #
        #   We're looking for all sections that have a sub div of type 'review-column'
        sections = blob_div.find_all("section")
        header_keys = list(content_dict.keys())
        for sec in sections:
            divs = sec.find_all("div")
            for div in divs:
                if 'class' in div.attrs and 'review-column' in div['class']:
                #if 'class' in div.attrs and 'review-container' in div['class']:
                    header_div = div.find("h2")
                    header = header_div.text.strip()
                    for h in header_keys:
                        if header.startswith(h):
                            header = h
                            break
                    #
                    #   Only collect/keep sections in the map, that have not been filled in
                    if self.__section_map__[header] and not content_dict[header]:
                        paras = div.find_all("p")
                        contents = ""
                        for para in paras:
                            contents = contents+" "+para.text.strip()
                        contents = contents.strip()
                        #   Clean out an "empty" review section
                        if  contents.startswith("None") or  contents.startswith("none"):
                             contents = ""
                        else:
                            #   Clean the text- not efficient, but simple
                            contents = contents.replace("\t\t"," ").replace("\n\n"," ")
                            contents = contents.replace("\t"," ").replace("\n"," ")
                            contents = contents.replace("   "," ").replace("  "," ")
                            contents = contents.replace("  "," ").replace("  "," ")
                        content_dict[header] = contents.strip()
                    #   
                    #   The 'Conclusion' section is the last one we might collect
                    if header == "Conclusion": 
                        #   The 'find_all' will find the sections with the content
                        #   multiple times. The sections should always be in order, so
                        #   once we've found it all at least once then stop processing 
                        #   sections too - we don't need to find it all multiple times
                        concluded = True
                        break
            #   Got to break out of the section loop too
            if concluded: break
            
        #   Create the body text only once
        #print(json.dumps(content_dict,indent=4))
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
            a string of the review type text
        '''
        #   Early in the header of the article a list item <li> contains the
        #   type of the review. Given what is passed in we assume that the
        #   first unordered list, and first list item contain the review type
        review_type = ""
        ulist = blob_div.find('ul')
        if ulist:
            ilist = ulist.find('li')
            anchor = ilist.find('a')
            review_type = anchor.text.strip().lower()
        
        return review_type



    def _extractRating_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract movie rating info. Actually,
        this is less a rating and more like a content warning. PluggedIn
        does not give a star rating or score
        
        Parameters:
        blob_div:       a div with the ratings info
        
        Returns
            a list with a star_count and rating string, the rating string
            is the only valid value for this site
        '''
        rating_str = ""
        star_count = -1
        caution_col = list()
        divs = blob_div.find_all("div")
        for div in divs:
            if 'class' in div.attrs and 'caution-column' in div['class']:
                caution_col.append(div)
                if len(caution_col)>=3: break
        if caution_col:
            for div in caution_col:
                anchor = div.find("a")
                warn_target = ""
                warn_level = "\u2013"
                try:
                    warn_level = anchor.text.strip()
                except:
                    pass
                try:
                    warn_target = div.text.strip().replace(warn_level,"")
                except:
                    pass
                if warn_level == "\u2013":
                    warn_level = "<none_set>"
                if rating_str:
                    rating_str = rating_str + f", {warn_target}={warn_level}"
                else:
                    rating_str = f"{warn_target}={warn_level}"
            if rating_str:
                rating_str = "Content caution: "+rating_str
        return [star_count, rating_str]



    def _estimatePostingDate_(self, review_type=None, credits_info=None):
        '''
        Takes the current review type, and the parsed out credits info to
        make an estimate of the posting date. The assumption is the review
        is posted 5 days prior to the
        
        Parameters:
        review_type:        a string of the review type
        credits_info:       a dictionary of the parsed credits info
        
        Returns
            a string of the review type text
        '''
        post_date = ""
        post_date_ts = ""
        dt_offset_days = timedelta(days=PLUGGED_IN_POST_DATE_OFFSET)
        if (review_type == "in theaters") or (credits_info['release_type'] == "in theaters"):
            #   Simplest case it's an 'in theaters' review
            dt_post = None
            try:
                #   Going to assume that the post date of the review
                #   is offset prior to the in theaters release date
                release = credits_info['release_date']
                #print(f"RELEASE: {release}")
                dt_release = datetime.strptime(release,"%B %d, %Y")
                #print(f"{str(dt_release)=}")
                dt_post = dt_release - dt_offset_days
                #print(f"{str(dt_post)=}")
            except:
                dt_post = None
            if dt_post:
                post_date_ts = str(dt_post)
                post_date = dt_post.strftime("%B %d, %Y")
        else:
            if not credits_info['home_release_date'] == "TBD":
                release = credits_info['home_release_date']
            if not credits_info['release_date'] == "TBD":
                release = credits_info['home_release_date']
            dt_post = None
            try:
                #   Going to assume that the post date of the review
                #   is offest prior to whatever was the 
                dt_release = datetime.strptime(release,"%B %d, %Y")
                dt_post = dt_release - dt_offset_days
            except:
                dt_post = None
            if dt_post:
                post_date_ts = str(dt_post)
                post_date = dt_post.strftime("%B %d, %Y")
                
        return [post_date, post_date_ts]



    def _extractCredits_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the credits info in this review
        
        Parameters:
        blob_div:       a div that contains credit info
        
        Returns
            a dictionary of credits
        '''
        #
        #   Parsing is navigating down to the items that we need
        #   There are no specific keys that are useful to identifying
        #   the specific data we want.
        #
        credits = dict()
        items = list()
        want_div = None
        sections = blob_div.find_all("section")
        for sec in sections:
            if 'class' in sec.attrs and 'elementor-top-section' in sec['class']:
                divs = sec.find_all("div")
                for div in divs:
                    if 'data-element_type' in div.attrs and 'column' in div['data-element_type']:
                        header = div.find("h3")
                        if header and header.text.lower() == "credits":
                            #print(f"{header.text.lower()=}")
                            want_div = div
                            break
            if want_div: break
        #
        #
        if want_div:
            #print(want_div)
            divs = want_div.find_all("div")
            for div in divs:
                if 'class' in div.attrs and 'elementor-widget-container' in div['class']:
                    value_header = div.find("h4")
                    value_item = div.find("li")
                    if value_header:
                        #print(f"{value_header.text.strip()=}")
                        items.append(value_header.text.strip())
                    if value_item:
                        #print(f"{value_item.text.strip()=}")
                        items.append(value_item.text.strip())
                #   Special 'fixup' for the reviewer field
                #   This assumes that the fields are presented in order
                if 'class' in div.attrs and 'contributor-name' in div['class']:
                    if items[-1] == "Reviewer":
                        items.append(div.text.strip())
        
        if items:
            credits['release_type'] = items[0].lower()
            credits['release_date'] = items[1]
            items = items[2:]
            try:
                while items:
                    key = items[0].lower().replace(" ","_")
                    credits[key] = ""
                    credits[key] = items[1]
                    items = items[2:]
            except:
                pass
        
        return credits

#####
#   
#   END class PluggedInArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("PluggedInArticleRequest.py is a class with no main()")


