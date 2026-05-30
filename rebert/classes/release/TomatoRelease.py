#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: TomatoRelease.py
#   REVISION: April, 2026
#   CREATION DATE: March, 2024
#   AUTHOR: David W. McDonald
#
#   A web service object to collect a set of new/open movies. This uses the RottenTomatoes
#   web site and 'screen scrapes' data by parsing the HTML in the response. The
#   RottenTomatoes site is structured as a set of tiles as <span></span> elements.
#
#   The main page requested is a browse for current movies
#   https://www.rottentomatoes.com/browse/movies_in_theaters/
#   https://www.rottentomatoes.com/browse/movies_in_theaters/sort:newest
#
#   The set of items can be paged - which increases the number of items returned in
#   the sort/filter
#   https://www.rottentomatoes.com/browse/movies_in_theaters/sort:newest?page=3
#   
#   It's possible that this class might need to collect the "Coming Soon" page
#   https://www.rottentomatoes.com/browse/movies_coming_soon/
#   https://www.rottentomatoes.com/browse/movies_coming_soon/?page=2
#
#
#   March 2026 - Fleshed out the draft version to return more complete release
#       records. Also updated the extraction of the audience and critic scores
#       to reflect changed HTML format. Added paging to allow this to return
#       a larger window of previously released movies.
#
#   April 2026 - HTML/CSS formatting change to the 'tiles' that describe each
#       movie. This impacted extraction of title and opening date, once those
#       were fixed, it started working. The extraction of the opening status
#       info was also updated.
#
#       Turns out that since it was "easy" to extract the poster URL, that was
#       added in the April update. The poster URL is actually coming from 
#       Fandango. The images are large - can be scaled using src tags or CSS.
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
###
#
import json, copy
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
#   This class is a sub-class of HTTPConnection
from rebert.classes.base.HTTPConnection import HTTPConnection

#####
#   
#   CONSTANTS
#   
#####

#
#   Dictionary template that will be used to return the collected data for 
#   each movie that is found within a given time window.
#
MOVIE_RELEASE_DATA_TEMPLATE = {
    'title'             : "",
    'opening_date_str'  : "",
    'opening_date_ts'   : "", 
    'opening_week'      : -1,
    'year'              : -1,
    'notes'             : "",
    'poster_url'        : "",
    'source'            : "RottenTomatoes.com"
}

#
#   The object maintains a recency window, a start date and an
#   end date that is used to collect recent moving openings
#   These constants are the defaults for days prior to the 
#   current day and days into the future.
#
MOVIE_RECENCY_WINDOW_PRIOR = 14
MOVIE_RECENCY_WINDOW_FUTURE = 7
MOVIE_RECENCY_MAX_DAYS = 120
#MOVIE_RECENCY_MAX_DAYS = 366
#
MOVIE_RECENCY_MAX_PAGES = 5
MOVIE_RECENCY_DEFAULT_PAGES = 3
#

#####
#   
#   START class TomatoRelease definition
#   
#####

###
#   A class/object that interacts with Rotten Tomatoes movie website 
#   to collect movie release date information.
#
class TomatoRelease(HTTPConnection):
    '''
    Provides web access to movie release information.
    
    This is a web service class designed to make a specific type of request from
    Rotten Tomatoes movie information website. This requests a browse page that
    lists the current movies in theaters.
    
    This is a subclass of the HTTPConnection class (rebert.classes.connection.HTTPConnection). 
    Inherits all methods and attributes of HTTPConnection.
    
    The attribute variables for this class are not meant to be publicly changed.
    There are internal variables that are calculated based on the values provided.
    Use the accessor methods to set them - or results will be problematic.
    
    Attributes:
        _days_past_         : integer, window starts days past/prior to today
        _days_future_       : integer, window ends days in the future
        _min_date_          : datetime, start date of window
        _max_date_          : datetime, end date of the window
        
    Methods:
        setRecencyWindow()      - set the beginning and ending of the recency window
        getRecentReleaseList()  - returns a list of recent movie releases
        
    '''
    def __init__(self, name="TomatoRelease", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #
        #   Set attributes specific to this website
        self.setHost("https://www.rottentomatoes.com")
        #   This is the service endpoint for the current releases
        self.current_release_service_endpoint = "/browse/movies_in_theaters/sort:newest"
        self.setServiceEndpoint(self.current_release_service_endpoint)
        #   Set a rate limit so that rogue code won't abuse the site
        self.setThrottleRate(rps=1.0)
        self.throttlingOn()
        #   Pick a random user agent to simulate a browser reqeust
        self.setUserAgent()
        #
        #   For managing the recency window
        self._days_prior_ = MOVIE_RECENCY_WINDOW_PRIOR
        self._days_future_ = MOVIE_RECENCY_WINDOW_FUTURE
        self._min_date_ = None
        self._max_date_ = None
        #   Now initialize the recency window
        self.setRecencyWindow()
        #
        #   The Rotton Tomatoes site will return a longer list of
        #   'recent' releases if we request a larger page number.
        #   We'll default to 2 pages, assuming that will get us past
        #   the 'prior' days recency window.
        self._default_pages_ = MOVIE_RECENCY_DEFAULT_PAGES
        #
        return
    
    
    
    ###
    #   Allows setting the start and stop dates of the recency
    #   window. That window determines how many days in the
    #   'past' a movie will be considered recent, and how many
    #   days in the 'future' a movie will be considered recent
    #
    def setRecencyWindow(self, prior=0, future=0):
        '''
        Sets the recency window.
        
        This object only collects movie release information
        in a specific window of time - the recency window.
        This sets the window by considering a number of days
        in the past, to set the start date of the window, and
        a number of days in the future to set the end date.
        
        Parameters:
        prior        : The number of days in the past to start
                      the recency window (as a positive value)
        future      : The number of days in the future to end
                      the recency window
        '''
        self.log(f"entering", level="DEBUG")
        #
        #   Set the number of days in the past and future
        #   These make sure the window is something reasonable
        if prior <= 0:
            self._days_prior_ = MOVIE_RECENCY_WINDOW_PRIOR
        if prior > MOVIE_RECENCY_MAX_DAYS:
            self._days_prior_ = MOVIE_RECENCY_MAX_DAYS
        if future <= 0:
            self._days_future_ = MOVIE_RECENCY_WINDOW_FUTURE
        if future > MOVIE_RECENCY_MAX_DAYS:
            self._days_future_ = MOVIE_RECENCY_MAX_DAYS
        #
        #   We need to calculate a time window to determine
        #   whether a movie release is or is not 'recent'
        #
        #   Start with the current date
        today = datetime.now()
        #   These directly represent the days as time delta
        days_past = timedelta(days=self._days_prior_)
        days_future = timedelta(days=self._days_future_)
        #   Use the time deltas to get the actual dates
        self._min_date_ = (today - days_past)
        self._max_date_ = (today + days_future)
        #self.log(f"new recency window {str(self._min_date_)} -({days_past}) past to {str(self._max_date_)} +({days_future}) future", 
        #            level="DEBUG")
        self.log(f"returning", level="DEBUG")
        return
    
    
    ###
    #   This method will parse a text page response from the
    #   web and will return a list of dictionaries of 
    #   MOVIE_RELEASE_DATA_TEMPLATE for each movie parse from
    #   the supplied (or requested) HTML web page
    #
    def getRecentReleaseList(self, page=None):
        '''
        Find and return movie releases from web site.
        
        This method accepts one parameter 'page' which should be
        an HTML page that should be parsed for movie release
        data. If no page is supplied, this method will attempt
        to make a request
        
        Parameters:
        page        : an HTML page to be parse, or None
        
        Returns:
        a list of MOVIE_RELEASE_DATA_TEMPLATE dictionaries,
        one for each movie that was found to have a release
        date within the rececy window.
        '''
        self.log(f"entering", level="DEBUG")
        #   Initialize the list
        movie_list = list()
        #
        #   If the requester is asking for some pages then do that
        if not page:
            page = self._default_pages_
        
        if page > MOVIE_RECENCY_MAX_PAGES:
            page = MOVIE_RECENCY_MAX_PAGES

        if page > 1:
            self.setRequestParam('page',page)
            mesg = f"{self.current_release_service_endpoint}?page={page}"
        else:
            #   Make sure there are no left over params from
            #   a prior request
            self.clearRequestParams()
            mesg = f"{self.current_release_service_endpoint}"
        #   Try to get a page
        self.queueRequest()
        self.log(f"requesting '{mesg}'", level="DEBUG")
        self.makeRequest()
        if self.responses():
            resp = self.nextResponse()
            page_text = resp.text
        else:
            mesg = "request did not return a page"
            self.log(f"{mesg}", level="WARNING")
            self.log(f"returning", level="DEBUG")
            return movie_list
        
        movie_list = self._parseHTMLPage_(page_text)
        self.log(f"returning, {len(movie_list)} items", level="DEBUG")
        return movie_list


    ###
    #   This parses the individual tiles of the page to
    #   collect the movie information
    #
    def _parseHTMLPage_(self, page=None):
        '''
        Parse the HTML page for movie release data.
        
        Parameters:
        page        : an HTML page to be parse, or None
        
        Returns:
        a list of MOVIE_RELEASE_DATA_TEMPLATE dictionaries,
        one for each movie that was found to have a release
        date within the recency window.
        '''
        movie_list = list()
        #   No HTML page, return empty list
        if not page: 
            self.log(f"page data was empty!", level="DEBUG")
            return movie_list
        self.log(f"entering", level="DEBUG")
        
        #   Now, parse the text of the page
        html_parse = BeautifulSoup(page,'html.parser')
        #   The web page is a set of 'tiles' that are
        #   represented by a movie poster image (or
        #   similar). Each tile contains movie release
        #   information. First, we find all of the tiles
        # Changed on 4/28/2026
        #tile_dynamic_tags = html_parse.find_all("tile-dynamic")
        #
        #   New tag for the movie tiles
        tile_media_info_tags = html_parse.find_all("media-info-tile")
        for tile in tile_media_info_tags:
            #   Extract title from the tile
            movie_title = self._parseMovieTitle_(tile)
            #   Extract the opening date from tile
            movie_dt = self._parseMovieDate_(tile)
            #   Do we have the primary data
            if movie_title and movie_dt:
                #   Is this opening in our recency window
                if ((movie_dt > self._min_date_) and 
                    (movie_dt < self._max_date_)):
                    #   Attempt to get release info
                    rel_notes = self._parseReleaseDateInfo_(tile)
                    #   Attempt to extract scores
                    score_notes = self._parseDeprecatedScores_(tile)
                    #   Prep the notes field
                    if score_notes:
                        notes = rel_notes+"; "+score_notes
                    else:
                        notes = rel_notes
                    #
                    #   Now, create a dict, append to list
                    self.log(f"adding '{movie_title}'", level="DEBUG")
                    md = MOVIE_RELEASE_DATA_TEMPLATE.copy()
                    md['title'] = movie_title
                    ods = movie_dt.strftime("%b %d, %Y")
                    md['opening_date_str'] = ods
                    odts = str(movie_dt).split()[0]
                    md['opening_date_ts'] = odts
                    ow = movie_dt.isocalendar().week
                    md['opening_week'] = ow
                    md['notes'] = notes
                    md['year'] = str(movie_dt.year)
                    md['poster_url'] = self._parseMoviePosterURL_(tile)
                    #
                    movie_list.append(md)
                else:
                    self.log(f"filter removed '{movie_title}'", level="DEBUG")
                    #if movie_dt < self._min_date_ :
                    #    self.log(f"too old {str(movie_dt)} < {str(self._min_date_)}", level="DEBUG")
                    #if movie_dt > self._max_date_ :
                    #    self.log(f"too early {str(movie_dt)} > {str(self._max_date_)}", level="DEBUG")
        self.log(f"returning, {len(movie_list)} items", level="DEBUG")
        return movie_list
    
    
    ###
    #   This parses one tile, looking for a set of elements
    #   that have been marked as deprecated scores. These *may*
    #   have scores for the movie.
    #
    def _parseDeprecatedScores_(self, tile=None):
        '''
        Parse one tile looking for movie scores/ratings info.
        
        Parameters:
        tile       : a css tile (BeautifulSoup parse object)
        
        Returns:
        a string, notes, containing the parsed scores
        '''
        if not tile: return ""
        self.log(f"entering", level="DEBUG")
        notes = ""
        #
        #   Looke for specific attributes in the 'tile'
        #   Then try to collect the values in notes string
        score_pairs = tile.find("score-pairs-deprecated")
        if score_pairs:
            #
            #   New style - look for a specific text field and
            #   extract the text which should be some percent
            scores = score_pairs.find_all('rt-text')
            for score in scores:
                if 'slot' in score.attrs:
                    if 'criticsScore' in score['slot']:
                        st = score.text.strip()
                        if not st: continue
                        if notes:
                            notes = notes+", Critics_Score="+st
                        else:
                            notes = "Critics_Score="+st
                        continue
                    if 'audienceScore' in score['slot']:
                        st = score.text.strip()
                        if not st: continue
                        if notes:
                            notes = notes+", Audience_Score="+st
                        else:
                            notes = "Audience_Score="+st
        if notes:
            self.log(f"returning, {notes}", level="DEBUG")
        else:
            self.log(f"returning, <no_score_info>", level="DEBUG")
        return notes
    
    
    ###
    #   This parses one tile, looking for the movie title
    #
    def _parseMovieTitle_(self, tile=None):
        '''
        Parse one tile looking for the movie title.
        
        Parameters:
        tile       : a css tile (BeautifulSoup parse object)
        
        Returns:
        a string, movie_title, containing the title or empty string
        '''
        if not tile: return ""
        movie_title = ""
        self.log(f"entering", level="DEBUG")
#   Changed on 4/28/2026
#        #   Look for a <span> that is marked 'p--small' this
#        #   generally contains the title of the movie
#        title_span = str(tile.find("span",class_="p--small"))
#        if title_span :
#            #   Grab everything in front of the end span tag
#            title_span = title_span.partition("</span>")[0]
#            #   Now, take everying after the start of the span
#            movie_title = title_span.partition(">")[2].strip()
        #
        #   The updated formatting use a special tag and defined attribute
        text_tags = tile.find_all("rt-text")
        for tt in text_tags:
            if 'data-qa' in tt.attrs and 'discovery-media-list-item-title' in tt['data-qa']:
                movie_title = tt.text.strip()
                break
        self.log(f"returning, '{movie_title}'", level="DEBUG")
        return movie_title
    
    
    ###
    #   This parses one tile, looking for the release date
    #
    def _parseMovieDate_(self, tile=None):
        '''
        Parse one tile looking for the movie opening date.
        
        Parameters:
        tile       : a css tile (BeautifulSoup parse object)
        
        Returns:
        datetime of opening date or None
        '''
        if not tile: return None
        movie_dt = None
        self.log(f"entering", level="DEBUG")
#   Changed on 4/28/2026
#        #   Look for a <span> that is marked 'smaller' this
#        #   generally contains the opening date for the movie
#        date_span = str(tile.find("span",class_="smaller"))
#        if date_span :
#            #   Grab everything in front of the end span tag
#            date_span = date_span.partition("</span>")[0]
#            #   Now, take everying after the start of the span
#            date_str = date_span.partition(">")[2].strip()
#            #   Remove 'opening' text in front of date
#            date_str = date_str.partition(" ")[2].strip()
#            try:
#                #   date_str should be something like "Mar 15, 2024"
#                movie_dt = datetime.strptime(date_str,"%b %d, %Y")
#            except:
#                movie_dt = None
        #
        #   The updated formatting use a special tag and defined attribute
        text_tags = tile.find_all("rt-text")
        for tt in text_tags:
            if 'data-qa' in tt.attrs and 'discovery-media-list-item-start-date' in tt['data-qa']:
                open_str = tt.text.strip()
                #   want the stuff after a space character
                date_str = open_str.partition(" ")[2]
                try:
                    #   date_str should be something like "Mar 15, 2024"
                    movie_dt = datetime.strptime(date_str,"%b %d, %Y")
                except:
                    movie_dt = None
                break
        self.log(f"returning, {str(movie_dt)}", level="DEBUG")
        return movie_dt
    
    
    ###
    #   This parses one tile, to find the release status
    #
    def _parseReleaseDateInfo_(self, tile=None):
        '''
        Parse one tile looking for the opening info.
        
        Parameters:
        tile       : a css tile (BeautifulSoup parse object)
        
        Returns:
        string of opening information
        '''
        if not tile: return None
        info_str = None
        self.log(f"entering", level="DEBUG")
#   Changed on 4/28/2026
#        #   Look for a <span> that is marked 'smaller' this
#        #   generally contains the opening info for the movie
#        info_span = str(tile.find("span",class_="smaller"))
#        if info_span :
#            #   Grab everything in front of the end span tag
#            info_span = info_span.partition("</span>")[0]
#            #   Now, take everying after the start of the span
#            info_str = info_span.partition(">")[2].strip()
#            #   Now remove the date info off the end
#            info_str = info_str.partition(" ")[0].strip().lower()
#            if info_str=="opens": info_str = "coming soon"
#            if info_str=="opened": info_str = "now showing"
#            if info_str=="re-releasing": info_str = "coming soon, re-release"
#            if info_str=="re-released": info_str = "now showing, re-release"
        #
        #   The updated formatting use a special tag and defined attribute
        text_tags = tile.find_all("rt-text")
        for tt in text_tags:
            if 'data-qa' in tt.attrs and 'discovery-media-list-item-start-date' in tt['data-qa']:
                open_str = tt.text.strip()
                #   want the stuff in front of a space character
                info_str = open_str.partition(" ")[0].lower()
                if info_str=="opens": info_str = "coming soon"
                if info_str=="opened": info_str = "now showing"
                if info_str=="re-releasing": info_str = "coming soon, re-release"
                if info_str=="re-released": info_str = "now showing, re-release"
        self.log(f"returning, '{info_str}'", level="DEBUG")
        return info_str
                
    ###
    #   This parses one tile, looking for the URL to the movie poster
    #
    def _parseMoviePosterURL_(self, tile=None):
        '''
        Parse one tile looking for the movie poster URL.
        
        Parameters:
        tile       : a css tile (BeautifulSoup parse object)
        
        Returns:
        a string, a URL to a movie poster for this movie
        '''
        if not tile: return ""
        poster_url = ""
        self.log(f"entering", level="DEBUG")
        img_tags = tile.find_all("rt-img")
        for img in img_tags:
            if 'class' in img.attrs and 'posterImage' in img['class']:
                try:
                    # extract the URL - and then fix it
                    poster_url = img['src'].partition("/https:")[2]
                    if poster_url:
                        poster_url = "https:"+poster_url
                except:
                    poster_url = ""
                break
        self.log(f"returning, '{poster_url}'", level="DEBUG")
        return poster_url
    
    
#####
#   
#   END class TomatoRelease definition
#   
#####

if __name__ == '__main__':
    print("TomatoRelease.py is a class with no main()")


