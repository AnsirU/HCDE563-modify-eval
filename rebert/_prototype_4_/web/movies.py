#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: movies.py
#   REVISION: March, 2026
#   CREATION DATE: October, 2024
#   Author: David W. McDonald
#
#   A set of functions that access the movie information for the LLM
#
#   March 2026 - update created a dictionary template that allows for
#       better modularizaiton of the browse and article collectors
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
import sys, json

from rebert._prototype_4_.web.config import *
from rebert._prototype_4_.web.utilities import *
from rebert._prototype_4_.web.config_collectors import *
#
#   This is a class that collects data from a website called
#   The Numbers: https://www.the-numbers.com/movies/release-schedule
#from rebert.classes.release.MovieNumbers import MovieNumbers as FetchReleases
#
#   This class uses the Rotten Tomatoes website to get
#   upcoming movie releases https://www.rottentomatoes.com/
#
#   The release data isn't quite as good as The Numbers, but should
#   still work
from rebert.classes.release.TomatoRelease import TomatoRelease as FetchReleases
#
#
#   This class allows us to search The Movie Database (TMDB) to
#   look for movie synopses - and other information. We will add
#   synopsis information to the information we provide the LLM
#   to try and reduce hallucinations.
from rebert.classes.moviedb.TMDB.Search import Search
#
#

MODULE_MOVIES_DEBUG = False

if not MODULE_DEBUG_OVERRIDE:
    MODULE_MOVIES_DEBUG = GLOBAL_DEBUG

##############
#
#   MOVIE RELATED FUNCTIONS
#
##############
#
#   Request data on recently released movies
#   returns a string of KEY:value release information
def get_recent_releases(cutoff=0):
    #
    #   This uses one of the release fetching classes to get
    #   current or recent releases. MovieNumbers is actually a
    #   little better, but the site was under repair in 2026
    #   so we've been using the TomatoRelease version.
    collector = FetchReleases(name="FetchReleases-{REBERT_VERS}")
    #
    #   Set the window that we will consider to be recent
    collector.setRecencyWindow(REBERT_WINDOW_PRIOR_DAYS,
                               REBERT_WINDOW_FUTURE_DAYS)
    #   Get the releases
    movie_list = collector.getRecentReleaseList()
    #
    #   Create a subset if there is a lot of releases
    #   If cutoff is set to 0 (zero) then it returns 
    #   the whole list of movies
    if cutoff and len(movie_list) > cutoff:
        # randomly select a subset of movies
        movie_list = random.sample(movie_list,k=cutoff)
    return movie_list
#
#   Search The Movie Database (TMDB) for information about each
#   movie release. The goal is to find a synopsis that we can
#   use to help give the LLM information about the movie and
#   reduce the amount of hallucination about the movies.
def get_movie_synopses(movie_list=[], tmdb_key=None, cutoff=0):
    #   Create an empty list to store the final result
    openings = list()
    #
    #   Create a TMDB Search query object to search for synopses
    tmdb_search = Search(name="TMDB.Search-{REBERT_VERS}")
    #   Make sure we can authenticate to TMDB
    if tmdb_key:
        tmdb_search.setAPIKey(tmdb_key)
    else:
        print_server_log(f"Need to supply a TMDB API Key",
                        "get_movie_synopses()")
        raise Exception("Need to supply a TMDB API Key")
    #
    #   Run through all of the movies and see if we can get a synopsis
    for movie in movie_list:
        title = movie['title']
        year = movie['year']
        #   Make the search with the title and year info
        found_items = tmdb_search.movieSearch(title=title,year=year)
        #   It's possible there are multiple matches
        for item in found_items:
            #   Find the first one with an exact match title
            if title == item['title']:
                #   If a synopsis exists, we'll keep the movie
                #   in the list for now, copy over the synopsis
                if item['overview']:
                   #   Fill in the synopsis and save this movie
                    movie['synopsis'] = item['overview']
                    openings.append(movie)
                    #   Don't process more of the response list,
                    #   we just found a movie with the exact title
                    break
    #   If cutoff is set to 0 (zero) then it returns the whole list
    if cutoff and len(openings) > cutoff:
        #   Randomly select a subset of movies
        openings = random.sample(openings,k=cutoff)
    return openings
#
#   Given the configured list of review websites in site_list, run through the
#   sites and collect the movie reviews. This is then aligned with the current
#   known release information to create a current list of known movies
def collect_reviews(site_list=[], releases=[]):
    #
    #   Create a dictionary, with the known titles as the keys and
    #   a list of collected reviews as the values
    collected = dict()
    for movie in releases:
        title_lower = movie['title'].lower()
        collected[title_lower] = list()
    #
    #   Using the supplied site_list, validate that it is a known, configured
    #   site. A site should be one of the short names in the SITE_SHORT_NAMES.
    #   Given a valid short name instantiate a browse collector and then
    #   start collecting the specified number of pages. Hopefully, covering
    #   the window of movies that we need.
    for sitename in site_list:
        if sitename not in SITE_SHORT_NAMES:
            #   Always make a note if we're skipping a site
            print_server_log(f"Skipping '{sitename}' - it has not been configured for collection.",
                             "collect_reviews()")
            continue
        
        #   Create an instance of this browse collector class
        collector = REVIEW_COLLECTOR_CLASSES[sitename]['browse']()        
        #   Always print which websites we're collecting - on startup
        fullname = REVIEW_COLLECTOR_CLASSES[sitename]['fullname']
        print_server_log(f"from '{fullname}'",
                        "collect_reviews()")
        #
        #   Run through the specified browse pages, collecting reviews
        reviews = list()
        try:
            #   The try protects against a failure in the HTTPConnection
            for page in REVIEW_COLLECTOR_CLASSES[sitename]['pages']:
                r = collector.getReviewsByBrowse(page=page)
                print_server_log(f"browse page {page} collected {len(r)} reviews",
                                "collect_reviews()")
                if r: reviews.extend(r)
        except Exception as ex:
            #   If there is a serious failure, then we use what we have from the
            #   specific review site
            print_server_log(f"When retrieving browse page, caught exception: {str(ex)}",
                             "collect_reviews()")
            print_server_log(f"Continuing with {len(reviews)} from site site '{fullname}'",
                             "collect_reviews()")
        #
        if len(reviews) == 0:
            #   Always output a zero collection - this may indicate that a collector
            #   needs updates or revisions
            print_server_log(f"Retrieved 0 (zero) reviews from site '{fullname}'",
                             "collect_reviews()")
            print_server_log(f"Check the '{fullname}' retrieval object for an error.",
                             "collect_reviews()")
        #
        #   Try to de-duplicate reviews. Create a 'unique' key and use that to
        #   see if we find some other versions of the same review.
        uniqueness = dict()
        for review in reviews:
            title_lower = review['title'].lower()
            #   Create a unique key for each review
            t = title_lower.replace(" ","_")
            a = review['author'].replace(" ","_")
            s = review['source'].replace(" ","_")
            key = t+"+"+a+"+"+s
            #print_server_log(f"Checking key: {key}",
            #                "collect_reviews()",
            #                 MODULE_MOVIES_DEBUG)
            #   If we've seen, saved this review, skip the duplicate
            if key in uniqueness: 
                print_server_log(f"Duplicate review for '{review['title']}' with key: '{key}'",
                                "collect_reviews()",
                                 MODULE_MOVIES_DEBUG)
                continue
            uniqueness[key] = 1
            if title_lower in collected:
                collected[title_lower].append(review)
                print_server_log(f"Keeping: '{review['title']}' by {review['author']} in {review['source']}",
                                "collect_reviews()",
                                 MODULE_MOVIES_DEBUG)
            else:
                print_server_log(f"Unrecognized title '{review['title']}' (dropped).",
                                "collect_reviews()",
                                 MODULE_MOVIES_DEBUG)
    return  collected



