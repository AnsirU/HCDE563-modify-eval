#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: MovieNumbers.py
#   REVISION: May, 2024
#   CREATION DATE: March, 2024
#   AUTHOR: David W. McDonald
#
#   A web service object to collect a set of new/open movies. This uses The Numbers 
#   web site and 'screen scrapes' data by parsing HTML. The data is in rows of a
#   single HTML table. One issue is that the rows of the table are all structured
#   slightly differently depending on the data in the row.
#   
#   The website: https://www.the-numbers.com
#   Release data: https://www.the-numbers.com/movies/release-schedule/<YEAR>
#
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
###
#
#   Standard python modules
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
    'source'            : "the-numbers.com"
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

#####
#   
#   START class MovieNumbers definition
#   
#####

###
#   A class/object that interacts with The Numbers movie website 
#   to collect movie release date information.
#
class MovieNumbers(HTTPConnection):
    '''
    Provides web access to movie release information.
    
    This is a web service class designed to make a specific type of request from
    TheNumber.com movie information website. This requests a recent release information
    web page, parses the HTML and extracts movie release dates and titles
    
    This is a subclass of the HTTPConnection class (rebert.classes.connection.HTTPConnection).
    Inherits all methods and attributes of HTTPConnection.
    
    The attribute variables for this class are not meant to be publicly changed.
    There are internal variables that are calculated based on the values provided.
    Use the accessor methods to set them - or results will be problematic.
    
    Attributes:
        _days_prior_        : integer, window starts days past/prior to today
        _days_future_       : integer, window ends days in the future
        _min_date_          : datetime, start date of window
        _max_date_          : datetime, end date of the window
        _past_max_date_     : boolean, parsing dates are past the end of the window
        _current_row_date_  : datetime, current found (parsed) row date
        
    Methods:
        setRecencyWindow()          - set the beginning and ending of the recency window
        getRecentReleaseList()      - returns a list of recent movie releases
        requestReleaseYearPage()    - requests the HTML page for the year supplied
    
    '''
    def __init__(self, name="MovieNumbers", logger=None, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(name=name, logger=logger, *args, **kwargs)
        #
        #   Set attributes specific to this website
        self.setHost("https://www.the-numbers.com")
        #   This is the service endpoint for the current releases
        self.current_release_service_endpoint = "/movies/release-schedule"
        self.setServiceEndpoint(self.current_release_service_endpoint)
        #   Set a rate limit so that rogue code won't abuse the site
        self.setThrottleRate(rps=1.0)
        self.throttlingOn()
        #   Pick a random user agent to simulate a browser request
        self.setUserAgent()
        #
        #   The recency window
        self._request_years_ = None
        self._min_date_ = None
        self._max_date_ = None
        self.setRecencyWindow()
        #
        #   Flag, past the calculated self._max_date_ 
        self._past_max_date_ = False
        #   Date for current row and rows that follow
        self._current_row_date_ = None
        return
    

    ###
    #   Allows setting the start and stop dates of the recency
    #   window. That window determines how many days in the
    #   past a movie will be considered recent, and how many
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
        prior       : The number of days in the past to start
                      the recency window (as a positive value)
        future      : The number of days in the future to end
                      the recency window
        '''
        self.log(f"entering", level="DEBUG")
        #
        #   Set the number of days in the past and future
        #   These make sure the window is something reasonable
        if prior <= 0:
            prior = MOVIE_RECENCY_WINDOW_PRIOR
        if prior > MOVIE_RECENCY_MAX_DAYS:
            prior = MOVIE_RECENCY_MAX_DAYS
        if future <= 0:
            future = MOVIE_RECENCY_WINDOW_FUTURE
        if future > MOVIE_RECENCY_MAX_DAYS:
            future = MOVIE_RECENCY_MAX_DAYS
        #
        #   We need to calculate a time window to determine
        #   whether a movie release is or is not 'recent'
        #
        #   Start with the current date
        today = datetime.now()
        #   These directly represent the days as time delta
        days_prior = timedelta(days=prior)
        days_future = timedelta(days=future)
        #   Use the time deltas to get the actual dates
        self._min_date_ = (today - days_prior)
        self._max_date_ = (today + days_future)
        mesg = f"window: {self._min_date_.strftime('%a %b %d, %Y')}"
        mesg = mesg + f" to {self._max_date_.strftime('%a %b %d, %Y')}"
        self.log(mesg, level="INFO")
        #
        #   If the window start and window end dates are in
        #   different years then we need to consider both years
        #   which will be on different pages
        if self._min_date_.year < self._max_date_.year:
            self._request_years_ = list()
            self._request_years_.append(str(self._min_date_.year))
            self._request_years_.append(str(self._max_date_.year))
        else:
            self._request_years_ = list()
            self._request_years_.append(str(self._max_date_.year))
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
        to make a page request to get the HTML data.
        
        Parameters:
        page        : an HTML page to be parse, or None
        
        Returns:
        a list of MOVIE_RELEASE_DATA_TEMPLATE dictionaries,
        one for each movie that was found to have a release
        date within the rececy window.
        '''
        self.log(f"entering", level="DEBUG")
        movie_list = list()
        #   Have a page - just parse that text
        if page:
            movie_list = self._parseHTMLPage_(page)
            self.log(f"returning", level="DEBUG")
            return movie_list
        
        for year in self._request_years_:
            page = self.requestReleaseYearPage(year)
            if not page:
                mesg = "request did not return a page"
                self.log(f"{mesg}", level="WARNING")
                self.log(f"returning", level="DEBUG")
                return movie_list
            movie_list.extend(self._parseHTMLPage_(page))
        
        self.log(f"returning", level="DEBUG")
        return movie_list


    ###
    #   This method will make a page request for a specific
    #   year of release data.
    #
    def requestReleaseYearPage(self, year=""):
        '''
        Request web page of release data for a specific year.
        
        Parameters:
        year        : a string of a year (e.g., '2022')
        
        Returns:
        an HTML page or None
        '''
        self.log(f"entering", level="DEBUG")
        page_data = None
        #   Add the supplied year to the service endpoint to get
        #   all the data for that year
        release_endpoint = self.current_release_service_endpoint
        release_endpoint = release_endpoint+"/"+year
        self.setServiceEndpoint(release_endpoint)
        self.queueRequest()
        self.log(f"requesting '{release_endpoint}'", level="DEBUG")
        self.makeRequest()
        if self.responses():
            resp = self.nextResponse()
            page_data = resp.text
        else:
            mesg = f"no data for '{release_endpoint}'"
            self.log(f"{mesg}", level="WARNING")
        self.log(f"returning", level="DEBUG")
        return page_data
    
    
    ###
    #   This parses the individual cells of a table row to find
    #   modifications to the movie data
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
            self.log(f"page data was empty!", level="WARNING")
            return movie_list
        self.log(f"entering", level="DEBUG")
        
        #   Initialize or reset parsing flags
        self._past_max_date_ = False
        self._current_row_date_ = None
        
        #   Parse the the HTML, create a document object
        html_parse = BeautifulSoup(page,'html.parser')
        #   All of the release data is in a big HTML
        #   table in the page - there should only
        #   be one table, but who knows...
        tables = html_parse.find_all("table")
        #   We'll process all the tables until we pass
        #   the max date of the date window
        for table in tables:
            #   Extract the rows from this HTML table
            rows = table.find_all("tr")
            for row in rows:
                #   Process each table row ...
                self._parseTableRow_(row, movie_list)
                #   If past the max date, stop parsing rows
                if self._past_max_date_: break
            #   If past the max date, stop parsing tables
            if self._past_max_date_: break
        self.log(f"returning", level="DEBUG")
        return movie_list
    
    
    ###
    #   This parses one table row. There are four types of rows.
    #   - Month, Year rows that span all columns of the table
    #   - Blank rows that span all columns of the table
    #   - Movie data rows that start with a date
    #   - Movie data rows that start with a blank
    #
    def _parseTableRow_(self, row=None, movie_list=None):
        '''
        Parse one table row to find movie information.
        
        Parameters:
        row        : a table row (BeautifulSoup parse object)
        movie_list : the growing list of movies
        '''
        if not row: return
        self.log(f"entering", level="DEBUG")
        #   Want to extract a movie title
        movie_title = str()
        #
        #   If we don't have a self._current_row_date_, 
        #   then we have not started a run of releases
        if not self._current_row_date_:
            #   The 'id' attribute in this row data
            #   generally means there is a full date 
            #   in the row, try to extract that
            if 'id' in row.attrs:
                #   The date is in the 'id' field
                row_id_str = row.attrs['id']
                try:
                    self._current_row_date_ = datetime.strptime(row_id_str,
                                                                "%Y-%m-%d")
                    #   Skip parsing if this is prior to our window
                    if (self._current_row_date_ <= self._min_date_):
                        self._current_row_date_ = None
                    else:
                        mesg = "new current_row_date"
                        self.log(f"{mesg} {str(self._current_row_date_)}", 
                                 level="DEBUG")
                except:
                    pass
        #   Either we already had a self._current_row_date_ 
        #   or just found one that means we're in a set 
        #   of movie release rows
        row_data = None
        if self._current_row_date_:
            #   Find all of the anchors, links in this row
            row_anchors = row.find_all("a")
            for row_anchor in row_anchors:
                #   The anchor text is the title of the movie
                if 'href' in row_anchor.attrs:
                    #   Make sure we have title text to a movie
                    #   and it is not just a trailer
                    if (row_anchor['href'].startswith("/movie") and 
                        (not row_anchor['href'].endswith("trailer"))):
                        #movie_title = row_anchor.string.strip()
                        movie_title = row_anchor.text.strip()
                        if not movie_title.startswith("Untitled"):
                            mesg = f"found movie_title '{movie_title}'"
                            self.log(f"{mesg}", level="DEBUG")
                        else:
                            movie_title = ""
            #   Look through the other columns in this row to
            #   extract special notes - maybe ignore the data
            row_data = self._parseTableColumns_(row)
        #
        #   Check that we have movie data collected
        if (row_data and (not row_data['ignore']) and 
            self._current_row_date_ and movie_title):
            #
            #   Check that this movie data is within the time window
            if ((self._current_row_date_ > self._min_date_) and 
                (self._current_row_date_ < self._max_date_)):
                #
                #   Now, create a dict, append to list
                self.log(f"adding '{movie_title}'", level="INFO")
                md = MOVIE_RELEASE_DATA_TEMPLATE.copy()
                md['title'] = movie_title
                ods = self._current_row_date_.strftime("%b %d, %Y")
                md['opening_date_str'] = ods
                odts = str(self._current_row_date_).split()[0]
                md['opening_date_ts'] = odts
                ow = self._current_row_date_.isocalendar().week
                md['opening_week'] = ow
                md['notes'] = row_data['notes']
                md['year'] = md['opening_date_str'].split(' ')[2]
                #
                movie_list.append(md)
        self.log(f"returning", level="DEBUG")
        return
    
    
    ###
    #   This parses the individual cells of a table row to find
    #   modifications to the movie data
    #
    def _parseTableColumns_(self, row=None):
        '''
        Parse one table row to find movie information.
        
        This takes a single row and parses out the individual
        columns to find any information that is specific to
        the movie that we might want.
        
        Parameters:
        row        : a table row (BeautifulSoup parse object)

        Returns:
        a dictionary of additional information about a movie
        '''
        self.log(f"entering", level="DEBUG")
        #   Default to empty conditions
        ignore = False
        notes = ""
        #   We are in a row, each column of the
        #   row is in a <td></td> HTML markup
        #   Parse out those <td></td> columns
        columns = row.find_all("td")
        #   Process the data in each column
        for column in columns:
            #   Find the month, year rows and possibly blank
            #   rows, both span all 5 columns of a row
            if ('colspan' in column.attrs) and (column['colspan']=="5"):
                #   If this is a whole blank row, then
                #   we've finished a run of releases on
                #   that date, need to look for a new date
                self._current_row_date_ = None
                #   Alternatively this is a row with the
                #   Month, Year format - an intermediate
                #   row header to start a new month
                month_year_str = column.string.strip()
                if month_year_str:
                    try:
                        # original format for a Month, Day in rows
                        my_dt = datetime.strptime(month_year_str, "%B, %Y")
                    except:
                        # "new" format for a Month Day in rows 
                        my_dt = datetime.strptime(month_year_str, "%B %Y")
                    if my_dt > self._max_date_:
                        mesg = f"{month_year_str} > {str(self._max_date_)}"
                        self.log(f"{mesg}", level="INFO")
                        mesg = f"now past max_date"
                        self.log(f"{mesg}", level="INFO")
                        self._past_max_date_ = True
            #
            # Need to look at the text content inside the column
            else:
                #   Get the column text, as plain text
                text = column.text
                if not text: continue
                #   These conditions find special notes and
                #   special cases - depending on the case we
                #   might want to ignore the movie release
                if (("(Wide)" in text) or 
                    ("(Wide, " in text) or (" Wide)" in text)):
                    notes = "wide release"
                    if "re-release" in text:
                        notes = notes+", "+"re-release"
                elif ("(IMAX)" in text) or ("(IMAX, " in text):
                    notes = "IMAX"
                    if "re-release" in text:
                        notes = notes+", "+"re-release"
                    ignore = True
                elif ("(Limited" in text):
                    notes = "limited release"
                    if "re-release" in text:
                        notes = notes+", "+"re-release"
                    ignore = True
                elif (("(Special Engagement)" in text) or 
                        ("(Special Engagement, " in text)):
                    notes = "special engagement"
                    if "re-release" in text:
                        notes = notes+", "+"re-release"
                    ignore = True
                elif (("(Canceled)" in text) or 
                        ("(Canceled, " in text)):
                    notes = "canceled"
                    ignore = True
                elif ("Untitled " in text):
                    notes = "untitled release"
                    ignore = True
        # 
        if "re-release" in notes: ignore = True
        self.log(f"returning", level="DEBUG")
        #   Return what we got from parsing the columns
        return {'ignore': ignore, 'notes': notes}
            
#####
#   
#   END class MovieNumbers definition
#   
#####

if __name__ == '__main__':
    print("MovieNumbers.py is a class with no main()")


