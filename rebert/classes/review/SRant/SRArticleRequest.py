#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: SRArticleRequest.py
#   REVISION: March, 2026
#   CREATION DATE: July, 2024
#   AUTHOR: David W. McDonald
#
#   A web service object to collect review article text. The main entry is through
#   the method getReviewArticle(). Just pass it a URL or a partially complete
#   MOVIE_REVIEW_DATA_TEMPLATE (it looks for the 'review_url' in that record).
#
#   This is for the review website Screen Rant (SRant)
#   https://screenrant.com
#
#   March 2026 - Update to improve cleaning of the poster URL, new posting date
#       extraction because of format change, added new regex to extract movie titles
#       from review titles that have a new format
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
#   At the end of a review, they often invite a response. This part we want
#   to remove. It almost always starts with this phrase. We'll remove
#   everything after this.
SR_COMMENT_TEXT = "Let us know what you thought of"
SR_COMMENT_NOTSAVED = "Your comment has not been saved"
SR_NOW_PLAYING = "is now playing in theaters"

#####
#   
#   START class SRArticleRequest definition
#   
#####

###
#   A class/object that interacts with Screen Rant website to collect 
#   review articles. 
#
class SRArticleRequest(ReviewArticleBase):
    '''
    The SRArticleRequest class is a subclass of ReviewArticleBase that connects to
    Screen Rant to request a specified article. This is assumed to be a review article.
    The class parses the HTML web page to collect the review text and fill out a 
    MOVIE_REVIEW_DATA_TEMPLATE (dictionary).
    
    Attributes:
        No attributes beyond those inherited from HTTPConnection
    
    Methods:
        getReviewArticle()      - request a movie review page, parse and return results
        _parseHTMLPage_()       - starts parsing of the HTML of the article page
        _extractContent_()      - extract the main text of the review
        _extractPullQuotes_()   - extract block quotes - to use or remove 
        _extractRating_()       - extract the "star" rating
        _extractPosterURL_()    - extract the URL of the movie poster
        _extractAuthor_()       - extract the author of the review
        _extractPostDate_()     - extract the date the review was posted
        _extractMovieTitleFromArticleTitle_()
                                - extract the movie title from the article title
        
    '''
    def __init__(self, name="SRArticleRequest", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #   
        #   Modify the standard template to reflect this collector
        self.__review_template__['source'] = "screenrant.com"
        #   
        #   Add an ordered set of regex
        rex = re.compile(r"^(.*) Review:",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        rex = re.compile(r"^(.*) Review [-\u2013\u2014]",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Some review titles changed to add this style March 2026
        rex = re.compile(r"^(.*) Movie Review",
                         flags=re.IGNORECASE)
        self.__title_regex__.append(rex)
        #
        #   Make sure we set the host for this target collector
        self.setHost("https://screenrant.com")
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
        url:            a URL to an article to be requested and processed
        review:         a MOVIE_REVIEW_DATA_TEMPLATE dictionary with at least the
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
        page:           the HTML of the page to be parsed
        review:         a MOVIE_REVIEW_DATA_TEMPLATE dictionary
        
        Returns:    
            the review dictionary, hopefully filled out
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
        post_date = list()  # a list of the posting date and timestamp
        rating = list()     # a list of the star rating info
        author = ""         # the author's by-line
        synopsis = ""       # a short synopsis of the film
        poster_url = ""     # a URL to a poster for the film
        pullquotes = list() # a list of strings that were pull quotes
        #
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(text,'html.parser')
        #   The main chunk that we need is inside an 'article' tag
        article = html_parse.find('article')
        #   Review title should be in the first <H1> tag
        title_chunk = article.h1
        #   If we got an <H1> at all, then see if it is the title
        if (title_chunk and ('class' in title_chunk.attrs) and
            "article-header-title" in title_chunk['class']):
            #   Extract the review article title
            review_title = title_chunk.text.strip()
            #   Then see if we can extract and clean a movie title
            title = self._extractMovieTitleFromArticleTitle_(review_title)
                
        #
        #   Now, run through the div tags looking for specific values
        sections = article.find_all('section')
        for sect in sections:
            if 'class' in sect.attrs and "article-body" in sect['class']:
                body, synopsis = self._extractContent_(sect)
                break
#
#  Moved the parsing of the post_date into the article-meta 
#        post_date = self._extractPostDate_(article)
        
        #
        #   Now, run through the div tags looking for specific values
        divs = article.find_all('div')
        for div in divs:            
            if ('class' in div.attrs):
                if ("article-meta" in div['class']):
                    author = self._extractAuthor_(div)
                    # post date was moved to this 'article-meta' div around March 2026
                    post_date = self._extractPostDate_(div)
                    continue
                if ("pullquote" in div['class']):
                    pullquotes = self._extractPullQuotes_(div,pullquotes)
                    continue
                if ("w-rating-logo-stars" in div['class']) and ((not rating) or (rating[0]==0.0)):
                    rating = self._extractRating_(div)
                    continue
                #   There was a slight change to the rating in Fall 2024
                #   which made this code slightly wrong
                #if ("w-rating-stars" in div['class']) and not rating:
                #    rating = self._extractRating_(div)
                #    continue
                if ("display-card" in div['class']):
                    if not poster_url:
                        poster_url = self._extractPosterURL_(div)
        #
        #   Supposing we collected at least the body of an article
        #   then we'll fill out the review record as best possible
        if body:
            #   Create a new one if one was not provided
            if not review:
                review = self.__review_template__.copy()
            if author:
                review['author'] = author
            if title and not review['title']:
                review['title'] = title
            if review_title and not review['review_title']:
                review['review_title'] = review_title
            review['review_type'] = "movie review"
            review['review'] = body
            review['poster_url'] = poster_url
            if synopsis:
                review['synopsis'] = synopsis
            #   
            #   If we found pullquotes - it is *VERY* likely that they
            #   were included twice - they should only be there once
            if pullquotes:
                for pq in pullquotes:
                    if pq in review['review']:
                        #   This is a hack to make sure the pullquote is
                        #   only in the article once. This just removes
                        #   the first instance. However, that might be the
                        #   actual text (not the location of the pq). So
                        #   it is possible that the review reads a little
                        #   oddly because of the text removal.
                        parts = review['review'].partition(pq)
                        review['review'] = parts[0]+" "+parts[2]
                        review['review'] = review['review'].replace("  "," ")
            #   
            #   If we found a rating, then it should be two parts
            if rating:
                review['rating'] = rating[0]
                review['rating_str'] = rating[1]
            #   
            #   If there is a post_date, then it's a list of string and timestamp
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
            two items, string of review text and string of synopsis
        '''
        body = ""
        synopsis = ""
        paras = blob_div.find_all("p")
        for p in paras:
            if ('class' in p.attrs):
                if ("display-card-description" in p['class']):
                    try:
                        synopsis = p.text.strip()
                        #   Replace sequence of whitespace with one space
                        synopsis = re.sub('[ \n\t\r]+',' ',synopsis)
                    except:
                        synopsis = ""
                    continue
            try:
                text = p.text.strip()
            except:
                text = ""
            #
            #   Remove paragraphs with canned phrases that signal text
            #   which is not really part of the review
            if SR_COMMENT_TEXT in text:
                text = ""
            if SR_COMMENT_NOTSAVED in text:
                text = ""
            if SR_NOW_PLAYING in text:
                text = ""
            if text:
                #   Replace a sequence of whitespaces with one space
                text = re.sub('[ \n\t\r]+',' ',text)
                if body:
                    body = body +"\n"+ text
                else:
                    body = text
        return body, synopsis



    #
    #   This site has "pull quotes" that are highlighted in the context of a
    #   review. Extracting them allows us to remove them so the pull quote
    #   text does not end up in the review in two different places.
    #
    #   Not all review sites have pull quotes on the review page
    #
    def _extractPullQuotes_(self, blob_div=None, pq_list=None):
        '''
        Parses a div, or chunk to extract pull quotes from the body
        
        Parameters:
        blob_div:       a div with possible pull quote
        pq_list:        the list of current pull quotes
        
        Returns
            a list of the pull quotes, with maybe a new one appended
        '''
        try:
            pq = blob_div.p.text.strip()
        except:
            pq = ""
        if pq and (pq not in pq_list):
            #   Replace a sequence of whitespaces with one space
            pq = re.sub('[ \n\t\r]+',' ',pq)
            pq_list.append(pq)
        return pq_list



    def _extractRating_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract movie rating info
        
        Parameters:
        blob_div:       a div with the ratings info
        
        Returns
            a list with a numeric score and a rating string
        '''
        rating_str = ""
        star_temp = 0
        star_count = -1
        numer = -1
        denom = 5
        stars = blob_div.find_all("div")
        for star in stars:
            #self.log(f"'star' div: {star}",level="DEBUG")
            if 'class' in star.attrs:
                if "rate-number" in star['class']:
                    numer = star.text.strip().lower()
                    numer = numer.replace('<em>','').replace('<em>','')
                    denom = numer.partition("/")[2]
                    numer = numer.partition("/")[0]
                    try:
                        star_count = int(numer)
                    except:
                        try:
                            star_count = float(numer)
                        except:
                            star_count = -1
                    dtemp = 0
                    try:
                        dtemp = int(denom)
                    except:
                        pass
                    if dtemp: denom = dtemp
                    break
                if "rating-stars" in star['class']:
                    #   Now collect the star ratings
                    if "full" in star['class']:
                        if 'style' in star.attrs:
                            if ":100%" in star['style']:
                                star_temp = 1
                            elif ":50%" in star['style']:
                                star_temp = 0.5
                    #   The negative star count is a flag value to
                    #   indicate that we have not yet found star ratings
                    if star_count < 0: 
                        star_count = star_temp
                    else:
                        star_count = star_count + star_temp
                    star_temp = 0
        #
        #   If we didn't find any star ratings, the return empty list
        if star_count < 0:
            return list()
        #
        #   Format a simple integer string
        if isinstance(star_count,int):
            rating_str =f"{star_count} out of {denom} stars"
        else:
            rating_str =f"{star_count:0.1f} out of {denom} stars"

        #   
        #   We'll normalize this to a 5 star scale before returning
        if isinstance(denom,int) and denom:
            normalized = 5.0 * (star_count/denom)
            star_count = normalized 
        #
        #self.log(f""returning rating: {str([star_count, rating_str])}",level="DEBUG")
        return [star_count, rating_str]



    def _extractPosterURL_(self, blob_div=None):
        '''
        Parses a div, or chunk to extract a movie poster URL
        
        Parameters:
        blob_div:       a div with a poster URL
        
        Returns
            a string, poster URL
        '''
        poster_url = ""
        try:
            img = blob_div.img
            if 'alt' in img.attrs:
                alt_tag = img.attrs['alt'].strip().lower()
                if alt_tag and 'poster' in alt_tag:
                    if 'src' in img.attrs:
                        poster_url = img.attrs['src'].strip()
                        if poster_url:
                            poster_url = poster_url.partition('?')[0]
        except:
            poster_url = ""
        return poster_url



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
            # Get the author
            author = blob_div.a.text.strip()
        except:
            author = ""
        return author


#
#   Old style - prior to March 2026
#
#    def _extractPostDate_(self, blob_div=None):
#        '''
#        Parses a div, or chunk to extract the article post date
#        
#        Parameters:
#        blob_div:       a div with the posting date information
#        
#        Returns
#            a list consisting of the post date string and a standardized
#            timestamp of that posting date
#        '''
#        post_date = ""
#        post_date_ts = ""
#        try:
#            time = blob_div.header.time
#            if ('datetime' in time.attrs):
#                post_date = time['datetime'].replace("T"," ").replace("Z","")
#        except:
#            post_date = ""
#        
#        if not post_date: return list()
#        try:
#            pd_fix = post_date.replace("Published","").strip()
#            pd = datetime.strptime(pd_fix,"%Y-%m-%d %H:%M:%S")
#            post_date_ts = str(pd)
#        except Exception as e:
#            post_date_ts = ""
#        
#        return [post_date, post_date_ts]


#
#   Modified for new style date data in March 2026
#
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
        post_date_str = ""
        post_date_ts = ""
        divs = blob_div.find_all('div')
        for div in divs:
            if not 'class' in div.attrs: continue
            if 'article-date' in div['class']:
                time = div.time
                if ('datetime' in time.attrs):
                    post_date = time['datetime'].replace("T"," ").replace("Z","")
                    post_date_str = time.text.strip()
                    post_date_str = post_date_str.rpartition(" ")[0].strip()
                    #print(f"post_date: {post_date}")
                    #print(f"post_date_str: {post_date_str}")
                
        if not post_date: return list()
        try:
            post_date_str = post_date_str.replace("Published","").strip()
            pd = datetime.strptime(post_date,"%Y-%m-%d %H:%M:%S")
            post_date_ts = str(pd)
            #print(f"post_date_str: {post_date_str}")
            #print(f"post_date_ts: {post_date_ts}")
        except Exception as e:
            post_date_ts = ""
        
        return [post_date_str, post_date_ts]



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
        #print(f"extracted title: {title}")
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
#   END class SRArticleRequest definition
#   
#####

if __name__ == '__main__':
    print("SRArticleRequest.py is a class with no main()")


