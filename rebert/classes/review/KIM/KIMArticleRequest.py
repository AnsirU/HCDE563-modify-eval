#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: KIMArticleRequest.py
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
#   Days offset
KIM_DAYS_OFFSET = 3
KIM_TITLE_COUNT = 3
#
#   Kids in Mind review specific aspects of a movie. This 'map'
#   determines which sections to keep when parsing the body of
#   a review.
#
KIM_CONTENT_SECTION_MAP = {
    "Why is ": True, 
    "SEX/NUDITY": True,
    "VIOLENCE/GORE": True,
    "LANGUAGE": True,
    "SUBSTANCE USE": True,
    "DISCUSSION TOPICS": True,
    "MESSAGE": True
}
#
#   This template is filled in by the extractor when applying the map
#   to create the body of the review.
#
KIM_CONTENT_SECTION_TEMPLATE = {
    "Why is ": "", 
    "SEX/NUDITY": "",
    "VIOLENCE/GORE": "",
    "LANGUAGE": "",
    "SUBSTANCE USE": "",
    "DISCUSSION TOPICS": "",
    "MESSAGE": ""
}
#
#
KIM_GUID_SEP = "Read our parents’ guide below for details on sexual content, violence & strong language."
KIM_GLOSS_SEP = "| profanity glossary |"
KIM_SPEC_CHARS_1 = "– "
KIM_SPEC_CHARS_2 = "► "
#
#####
#   
#   START class KIMArticleRequest definition
#   
#####

###
#   A class/object that interacts with The Associated Press website to collect 
#   review articles.
#
class KIMArticleRequest(ReviewArticleBase):
    '''
    The KIMArticleRequest class is a subclass of ReviewArticleBase that connects to the 
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
    def __init__(self, name="KIMArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "kids-in-mind.com"
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://kids-in-mind.com")
        #
        #   A map of the sections that are to be kept when extracting these reviews
        #   You can modify what is kept by providing a different section map. 
        self.__section_map__ = KIM_CONTENT_SECTION_MAP.copy()
        #
        #   There are no official post dates on any of the reviews. This is a
        #   dictionary of estimated post dates based on the list of movie titles
        #   in the 'sidebar' of the article page.
        self.__est_post_dates__ = dict()
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
        poster_url = ""     # a possible poster URL
        post_date = list()  # a list of posting date info
        rating = list()     # a list of the star rating info
        author = "kids_in_mind"         # no author by-line
        review_type = "movie review"    # default for site
        #
        #   Parse the HTML page
        html_parse = BeautifulSoup(text,'html.parser')
        #
        sidebar_elt = ""
        body_elt = ""
        poster_side = ""
        #   Extract the divs that contain specific chunks
        divs = html_parse.body.article.find_all('div')
        for d in divs:
            if 'class' not in d.attrs: continue
            #   Find the first div that is likely a sidebar
            if 'et_pb_code_1' in d['class'] and 'sidebar' in d['class']:
                if not sidebar_elt: sidebar_elt = d
            #   Find the first div that is likely a body
            if (('et_pb_column_1_2' in d['class']) and 
                ('et_pb_column_2' in d['class']) and 
                ('custom-row' in d['class'])):
                if not body_elt: body_elt = d
            #   Find a div that might contain a movie poster
            if (('et_pb_column' in d['class']) and 
                ('et_pb_column_1_4' in d['class']) and 
                ('et_pb_column_3' in d['class'])):
                if not poster_side: poster_side = d
            if body_elt and sidebar_elt and poster_side: break
        #
        #   
        review_title = self._extractArticleTitle_(body_elt)
        title = self._extractMovieTitleFromArticleTitle_(review_title)
        #
        #   Try to extract a poster URL
        poster_url = self._extractPosterURL_(poster_side)
        #
        #   Extract an estimated post date
        self._buildEstimatedPostDates_(sidebar_elt)
        t = title.lower()
        try:
            post_date = self.__est_post_dates__[t]
        except:
            post_date = list()
        #        
        #   Try to extract the body
        rating = self._extractRating_(body_elt)
        #        
        #   Try to extract the body
        body = self._extractContent_(body_elt)
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
            if poster_url:
                review['poster_url'] = poster_url
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


    def _buildEstimatedPostDates_(self, sidebar_div=None):
        '''
        Uses the page sidebar to create an estimate of the post date for 
        
        Parameters:
        sidebar_div         a div that contains a list of movie titles and
                            the links to those movie reviews
        
        Returns
            <nothing>
        '''
        inner_div = ""
        divs = sidebar_div.find_all("div")
        for d in divs:
            if "class" in d.attrs and "et_pb_code_inner" in d["class"]:
                inner_div = d
                break
        #
        #   Now process each of the following elements in order
        header_text = ""
        title_count = 0
        #
        #   Hack up an estimated date based on today's date
        post_date_ts = str(datetime.now()).partition(" ")[0]
        post_date = datetime.strptime(post_date_ts,"%Y-%m-%d")
        offset_days = timedelta(days=KIM_DAYS_OFFSET)
        post_date = post_date - offset_days
        post_date_str = post_date.strftime("%B %d, %Y")
        post_date_ts = str(post_date)
        est_post_date = [post_date_str, post_date_ts]

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
                title = ""
                try:
                    title = elt.text.strip().lower()
                except:
                    title = ""
                if title:
                    #   As we work through the movie titles in order
                    #   and make the post_date go back in time
                    if title_count > KIM_TITLE_COUNT: 
                        title_count = 0
                        post_date = post_date - offset_days
                        post_date_str = post_date.strftime("%B %d, %Y")
                        post_date_ts = str(post_date)
                        est_post_date = [post_date_str, post_date_ts]
            
                    if header_text == "this week":
                        #print(f"THIS WEEK '{title}' ({post_date_str})")
                        self.__est_post_dates__[title] = est_post_date
                    
                    if header_text == "current releases":
                        #print(f"CURRENT RELEASES '{title}' ({post_date_str})")
                        title_count = title_count + 1
                        self.__est_post_dates__[title] = est_post_date
            
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
        try:
            movie_info = blob_div.h1.text.strip()
            movie_info = movie_info.split("|")
            review_title = movie_info[0].strip()
        except:
            review_title = ""
        return review_title


    def _extractRating_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract movie rating info
        
        Parameters:
        blob_div:       a div with the ratings info
        
        Returns
            a list with a numeric score and a rating string
        '''
        score = -1
        rating_str = ""
        #   Find the portion of the title block with the scores
        triple = []
        try:
            movie_info = blob_div.h1.text.strip()
            movie_info = movie_info.split("|")
            triple = movie_info[-1].replace("-","").replace("–","")
            triple = triple.replace(" ","").strip()
            #print(f"{triple=}")
            triple = triple.split(".")
            triple = [int(x) for x in triple]
        except:
            triple = []
        #
        #   Check that we actually extracted the score/warning triple
        if not triple: return list()
        #
        #   At this point we should have a list of numeric scores in triple
        #   one for each of 'Sex & Nudity', 'Violence & Gore', and 'Language'.
        #   In these dimensions lower scores are a lower warning.
        #
        #   Now, let's create a scaled value that inverts those to create a
        #   1 to 10 scale where 10 is a completely worry free movie.
        score = [(10-x) for x in triple]
        score = sum(score)/3
        whole = int(score)
        frac = score - whole
        if frac < 0.250:
            score = whole
        elif frac >= 0.25 and frac < 0.750:
            score = whole + 0.50
        else:
            score = whole + 1
        #print(f"{score=}")
        #
        #   Now create a rating string that reflects the specific warning that
        #   this site made
        rating_str = f"Levels of concern: "
        rating_str = rating_str + f"Sex & Nudity {triple[0]} out of 10, "
        rating_str = rating_str + f"Violence & Gore {triple[1]} out of 10, "
        rating_str = rating_str + f"Language {triple[2]} out of 10"

        #self.log(f"rating: '{str([star_count, rating_str])}'",level="DEBUG")
        return [score, rating_str]



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
        content_dict = KIM_CONTENT_SECTION_TEMPLATE.copy()
        divs = blob_div.find_all("div")
        review_grid = ""
        for d in divs:
            if 'class' in d.attrs:
                if 'et_pb_text' in d['class'] and 'review' in d['class']:
                    self._extractReviewComponent_(d,content_dict)
        
        header_keys = list(content_dict.keys())
        for hk in header_keys:
            header = hk
            if hk == "Why is ": header = "REVIEW CONTEXT"
            #   If there is content, append to the body
            if content_dict[hk]:
                if body:
                    body = body+"\n\n"+header+"\n"+content_dict[hk]
                else:
                    body = header+"\n"+content_dict[hk]
        return body


    def _extractReviewComponent_(self, review_elt=None, content_dict={}):
        '''
        One of the review sections - determined by the section map
        
        Parameters:
        review_elt:     a div that has a chunk of the review that might need to
                        be extracted
        content_dict:   a dict that contains the sections already extracted
        
        Returns
            nothing
        '''
        #
        #   This is a special case to handle the first paragraph of a review
        text = review_elt.text.strip()
        if self.__section_map__["Why is "] and text.startswith("Why is "):
            #   Collect this opening section
            #print(f"{text=}")
            text = text.replace(KIM_GUID_SEP," ").strip()
            text = text.replace(KIM_SPEC_CHARS_1," ")
            text = text.replace(KIM_SPEC_CHARS_2," ")
            text = text.replace("  "," ").replace(" \n","\n").strip()
            if not content_dict["Why is "]:
                content_dict["Why is "] = text
            return
        #
        section_keys = list(content_dict.keys())
        section = ""
        heading = ""
        try:
            heading = review_elt.h2.text.strip()
            for s in section_keys:
                if s in heading:
                    section = s
                    break
            #   Found a section heading and we want to keep it
            if section and (not self.__section_map__[section]):
                section = ""
            #   Found a section heading and we do not have that text
            if section and content_dict[section]:
                section = ""
        except:
            heading = ""
            section = ""
        #
        #   If we get to this code then if we have both heading
        #   text and a section title - then we need to keep the text
        if heading and section:
            #   Find all the nested paragraphs
            paras = review_elt.find_all("p")
            for p in paras:
                ptext = ""
                try:
                    ptext = p.text.strip()
                    ptext = ptext.replace(KIM_GLOSS_SEP," ")
                    ptext = ptext.replace(KIM_SPEC_CHARS_1," ")
                    ptext = ptext.replace(KIM_SPEC_CHARS_2," ")
                    ptext = ptext.replace(" \n","\n").replace("\n ","\n")
                    ptext = ptext.replace("  "," ").strip()
                    if content_dict[section]:
                        content_dict[section] = content_dict[section] + "\n" + ptext
                    else:
                        content_dict[section] = ptext
                except:
                    pass
        return


    def _extractPosterURL_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract a movie poster URL
        
        Parameters:
        blob_div:     a div with the poster URL
        
        Returns
            a string, poster URL
        '''
        poster_url = ""
        img_src = ""
        try:
            poster_url = blob_div.a['href']
            #print(f"found {poster_url=}")
        except Exception as ex:
            #print("No <a href=")
            poster_url = ""
        try:
            img_src = blob_div.a.img['src']
            #print(f"found {img_src=}")
        except Exception as ex:
            #print("No <img src=")
            img_src = ""
        if img_src == poster_url:
            return poster_url
        if "criticsinc.com" in poster_url:
            return poster_url
        if "criticsinc.com" in img_src:
            return img_src
        return poster_url


    def _extractMovieTitleFromArticleTitle_(self, review_title=None):
        '''
        Extracts a movie title from a review article title
        
        Parameters:
        review_title:   the title of the review article
        
        Returns
            the title of the extracted movie or an empty string
        '''
        #   Article title is the movie title
        title = review_title
        return title



#####
#   
#   END class KIMArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("KIMArticleRequest.py is a class with no main()")

