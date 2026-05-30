#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: NYPArticleRequest.py
#   REVISION: June, 2025
#   CREATION DATE: June, 2024
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
#   MOVIE INFO BOX
#   In January 2021 NYPost added a movie info box to the page that includes
#   "MOVIE REVIEW" (a tag to indicate this is a review)
#   <the movie title> 
#   a star rating - out of four stars
#   the film running time
#   
#   PRIOR TO JANUARY 2021 no ratings and category tags are really the only way
#   to know if an article is a movie review
#
###
#
#   Depending on how we extract the movie title, we may have to repair 
#   the use of title case. This is a list of the most common title words
#   that should NOT be capitalized in the title of - well - just about
#   anything. ... Certainly, there are exceptions that this will miss
#
#   This is applied after movie title extraction to fix up the title
#
TITLE_WORDS_LOWER = ['A', 'And', 'As', 'At', 'But', 'By', 'Down', 'For', 'From', 
                     'If', 'In', 'Into', 'Like', 'Near', 'Nor', 'Of', 'Off', 'On', 
                     'Once', 'Onto', 'Or', 'Over', 'Past', 'So', 'Than', 'That', 
                     'The', 'To', 'Upon', 'When', 'With', 'Yet']

#####
#   
#   START class NYPArticleRequest definition
#   
#####

###
#   A class/object that interacts with The New York Post website to collect 
#   review articles. 
#
class NYPArticleRequest(ReviewArticleBase):
    '''
    The NYPArticleRequest class is a subclass of ReviewArticleBase that connects to
    The New York Post to request a specified article. This is assumed to be a review
    article. The class parses the HTML web page to collect the review text and fill 
    out a MOVIE_REVIEW_DATA_TEMPLATE (dictionary).
    
    Attributes:
        No attributes beyond those inherited from HTTPConnection
    
    Methods:
        getReviewArticle()      - request a movie review page, parse and return results
        _parseHTMLPage_()       - starts parsing of the HTML of the article page
        _extractArticleTitle_() - extract the article title
        _extractMovieTitleFromArticleTitle_()
                                - extract the movie title from the article title
        _extractAuthor_()       - extract the author of the review
        _extractPostDate_()     - extract the date the review was posted
        _extractContent_()      - extract the main text of the review

        _extractReviewType_()   - extract the type of this review
        _examineArticleTags_()  - another way to try and extract the review type
        _extractRating_()       - extract the "star" rating
        _extractTitleFromReviewBox_() 
                                - another way to extract the movie title from an infobox
        
    '''
    def __init__(self, name="NYPArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "nypost.com"
        #
        #   The NY Post has a couple different ways that it represents titles
        #   of the movie in an article title. The 'embedded' case is rare,  
        #   but needs special handling. These four regex, wille handle most
        #   of the cases with some checking after extraction. 
        rex = re.compile(r"^['\u2018](.*)['\u2019] [Rr]eview",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        rex = re.compile(r"\b\s['\u2018](.*)['\u2019] [Rr]eview",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        rex = re.compile(r"^['\u2018](.*)['\u2019] ",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        rex = re.compile(r"\b\s['\u2018](.*)['\u2019]",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Set attributes specific to this website
        self.setHost("https://nypost.com")
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
        standfirst = ""     # a one-liner about the review or movie
        body = ""           # the main text of the review
        post_date = []      # a list of posting date info
        rating = []         # a list of the star rating info
        author = ""         # the author's by-line
        review_type = ""    # the item being reviewed
        #
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(text,'html.parser')
        #   The main chunk that we need is inside an 'article' tag
        article = html_parse.find('article')
        #   Review title should be in the first <H1> tag
        title_chunk = article.h1
        #   If we got an <H1> at all, then see if it is the title
        if (title_chunk and ('class' in title_chunk.attrs) and
            "headline" in title_chunk['class']):
            #   Extract the review article title
            review_title = self._extractArticleTitle_(title_chunk)
            #   Then see if we can extract and clean a movie title
            title = self._extractMovieTitleFromArticleTitle_(review_title)
        #
        #   Now, run through the div tags looking for specific values
        divs = article.find_all('div')
        for div in divs:            
            if ('class' in div.attrs):
                if ("article-header__meta" in div['class']):
                    author = self._extractAuthor_(div)
                    continue
                if ("date--updated__item" in div['class']):
                    post_date = self._extractPostDate_(div)
                    continue
                if ("inline-module--review" in div['class']):
                    review_type = self._extractReviewType_(div)
                    title = self._extractTitleFromReviewBox_(div, title)
                    continue
                if ("single__content" in div['class']):
                    body = self._extractContent_(div)
                    continue
                if ("rating" in div['class']):
                    rating = self._extractRating_(div)
                    continue
        #
        #   NOTE: This might add some noise in the collection - this code
        #   runs for "older" review formatting that does not include the
        #   "Movie Review" informational box.
        #
        
        #   If we have not yet found the review_type it might be an old
        #   style review that put the movie review in a tag
        if not review_type:
            try:
                ul_tags = article.footer.ul
                review_type = self._examineArticleTags_(ul_tags)
            except:
                review_type = ""
        
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
        Parses the main body of the article to extract the review text
        
        Parameters:
        blob_div:       a div that contains the review article title
        
        Returns
            a string of the article title
        '''
        review_title = ""
        try:
            review_title = blob_div.text.strip()
        except:
            review_title = ""
        return review_title



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
        #   Remove special characters from the start and end
        while (title and (title[0] in ".,:;-'\u2018\u2019\"") and 
                (title[-1] in ".,:;-'\u2018\u2019\"")):
            title = title[1:]
            if title:
                title = title[:-1]
        #   Clean any terminating whitespace
        if title:
            title = title.strip()
        #   Clean the end of this title
        if title and title[-1] in '\u2011\u2012\u2013\u2014\uFE58':
            title = title[:-1].strip()
        return title



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
            #   This handles the 'new' style pages
            author = blob_div.h4.text.strip()
        except:
            author = ""
        if not author:
            #   This mostly handles the 'old' style pages
            divs = blob_div.find_all("div")
            for d in divs:
                if 'class' in d.attrs and "byline__author" in d['class']:
                    try:
                        author = d.text.strip()
                    except:
                        author = ""
                    #   Not efficient, but clear - remove embedded whitespace
                    author = author.replace("\t\t"," ").replace("\n\n"," ")
                    author = author.replace("\t"," ").replace("\n"," ")
                    author = author.replace("  "," ").replace("  "," ")
                    author = author.replace("  "," ").replace("  "," ")
                    if author.startswith("Social") or author.startswith("social") :
                        author = author.partition('for')[2].strip()
                        author = author.partition("View")[0].strip()
                    break
        return author



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
        #   Extract date from HTML
        try:
            post_date = blob_div.text.strip()
            post_date = post_date.replace("\t","")
        except:
            post_date = ""
        if not post_date: return list()
        post_date = post_date.replace("\n"," ")
        #   Have an extracted string, not try to standardize
        #   that string into a timestamp string
        try:
            #self.log(f"post_date: '{post_date}'", level="DEBUG")
            pd = ""
            pd_fixup = post_date.replace("Published","")
            pd_fixup = pd_fixup.replace("Updated","")
            pd_fixup = pd_fixup.strip()
            #   Strip timezone
            pd_fixup = pd_fixup.rpartition(" ")[0]
            pd_fixup = pd_fixup.strip()
            #   Now, fix the am/pm if possible
            if pd_fixup.endswith("p.m."):
                pd_fixup = pd_fixup.rpartition(" ")[0]
                pd_fixup = pd_fixup+" PM"
                #self.log(f"pd_fixup: '{pd_fixup}'", level="DEBUG")
                try:
                    pd = datetime.strptime(pd_fixup,"%b. %d, %Y, %I:%M %p")
                except Exception as e1:
                    pd = datetime.strptime(pd_fixup,"%B %d, %Y, %I:%M %p")
            elif pd_fixup.endswith("a.m."):
                pd_fixup = pd_fixup.rpartition(" ")[0]
                pd_fixup = pd_fixup+" AM"
                #self.log(f"pd_fixup: '{pd_fixup}'")
                try:
                    pd = datetime.strptime(pd_fixup,"%b. %d, %Y, %I:%M %p")
                except Exception as e2:
                    pd = datetime.strptime(pd_fixup,"%B %d, %Y, %I:%M %p")
            else:
                pd_fixup = pd_fixup.rpartition(" ")[0]
                pd_fixup = pd_fixup.strip()
                #self.log(f"pd_fixup: '{pd_fixup}'", level="DEBUG")
                try:
                    pd = datetime.strptime(pd_fixup,"%b. %d, %Y, %I:%M")
                except Exception as e3:
                    pd = datetime.strptime(pd_fixup,"%B %d, %Y, %I:%M")
            post_date_ts = str(pd)
        except Exception as e:
            post_date_ts = ""
        
        return [post_date, post_date_ts]



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
        aside_text = ""
        #
        #   If there is an 'aside' in the body, with text, we'll
        #   extract that text first, so that it can be removed from
        #   the review - if there are two asides in the body, well
        #   at least we tried
        try:
            aside_text = blob_div.aside.p.text.strip()
        except:
            aside_text = ""
        #
        #   Now, try to collect up all of the paragraph chunks
        #   as the body, ignoring the possible aside text
        paras = blob_div.find_all("p")
        for p in paras:
            text = p.text.strip()
            if text == aside_text: continue
            if text:
                textl = text.lower()
                #   Skip the purely metadata sometimes included
                #   at the end of these reviews
                if textl.startswith("running time:"): continue
                if body:
                    body = body +"\n"+ text
                else:
                    body = text
        return body



    def _extractReviewType_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract the type of this review
        
        Parameters:
        blob_div:      a div that contains the review type
        
        Returns
            a string of the standfirst text
        '''
        review_type = ""
        try:
            review_type = blob_div.span.text.strip()
        except:
            review_type = ""
        return review_type



    def _examineArticleTags_(self, blob_div=None):
        '''
        Parses an unorderd list <ul> of article tags to find a review type
        
        Parameters:
        blob_div:    a chunk consisting of <li> list items
        
        Returns
            a movie review tag or empty string
        '''
        review_type = ""
        list_items = blob_div.find_all("li")
        for li in list_items:
            try:
                tag_text = li.a.text.strip().lower()
                if 'movie review' in tag_text or 'film review' in tag_text:
                    review_type = "movie review"
                    break
            except:
                review_type = ""
        return review_type



    def _extractRating_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract movie rating info
        
        Parameters:
        blob_div:       a div with the ratings info
        
        Returns
            a list with a numeric score and a rating string
        '''
        rating_str = ""
        star_count = -1
        stars = blob_div.find_all("div")
        for star in stars:
            if ('class' in star.attrs):
                if ("rating__star" in star['class']) or ("rating__stars" in star['class']):
                    try:
                        st = star.text.strip().lower
                        if 'zero' in st:
                            star_count = 0
                            break
                    except:
                        st = ""
                    #   The negative star count is a flag value to
                    #   indicate that we didn't find any star ratings
                    if star_count < 0: star_count = 0
                    if ("rating__star--filled" in star['class']):
                        star_count += 1
                    if ("rating__star--half" in star['class']):
                        star_count = star_count + 0.5
        if isinstance(star_count,int):
            rating_str =f"{star_count} out of 4 stars"
        else:
            rating_str =f"{star_count:0.1f} out of 4 stars"
        #   If we didn't find any star ratings, the return empty list
        if star_count < 0:
            return list()
        #   Must have found some star ratings
        return [star_count, rating_str]



    def _extractTitleFromReviewBox_(self, blob_div=None, title=None):
        '''
        Parses a div, or chunk to extract the movie title
        
        Sometimes the title is hard to extract from the review title. The
        NYPost reviews have a review summary box that contains the movie
        title. This attempts to extract the title from the summary box.
        
        Parameters:
        blob_div:       a div that contains the the review summary box
        title:          a string of the movie title as we currently have it
        
        Returns
            a string of the movie title
        '''
        new_title = ""
        try:
            new_title = blob_div.h2.text.strip()
        except:
            new_title = ""
        if new_title:
            new_title = new_title.replace("  "," ").replace("  "," ")
            title_words = new_title.title().split()
            new_title = title_words[0]
            for word in title_words[1:]:
                if word[-1] in ".,:;!?":
                    word_check = word[:-1]
                else:
                    word_check = word
                #   Fix title case of non-upper words
                if word_check in TITLE_WORDS_LOWER:
                    new_title = new_title +" "+ word.lower()
                else:
                    new_title = new_title +" "+ word            
            ##
            ##   This cleaning technique is a little too aggressive. It cleans the title
            ##   but also removes valuable title characters on the 'end' of a title
            ##
            ##   Remove special characters from the start
            #while new_title and (new_title[0] in ".,:;-'\u2018\u2019\u2011\u2012\u2013\u2014\uFE58\""):
            #    new_title = new_title[1:].strip()
            ##
            ##   Remove special characters from the end
            #while new_title and (new_title[-1] in ".,:;-'\u2018\u2019\u2011\u2012\u2013\u2014\uFE58\""):
            #    new_title = new_title[:-1].strip()
            #
            #   This title cleaning is a little less aggressive, but can result in titles
            #   with some extra characters on the end - that should be cleaned
            #   Remove special characters from the start and end
            while (new_title and (new_title[0] in ".,:;-'\u2018\u2019\"") and 
                    (new_title[-1] in ".,:;-'\u2018\u2019\"")):
                new_title = new_title[1:].strip()
                if new_title:
                    new_title = new_title[:-1].strip()
            if new_title and new_title[-1] in '\u2011\u2012\u2013\u2014\uFE58':
                new_title = new_title[:-1].strip()
            
            return new_title
        return title


#####
#   
#   END class NYPArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("NYPArticleRequest.py is a class with no main()")


