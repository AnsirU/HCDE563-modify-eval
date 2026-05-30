#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: movies.py
#   REVISION: November, 2024
#   CREATION DATE: October, 2024
#   Author: David W. McDonald
#
#   A set of functions that access the movie information for the LLM
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
##
#
import sys, json, re

from rebert._prototype_7_.web.config import *
from rebert._prototype_7_.web.utilities import *
from rebert._prototype_7_.web.collector_config import *
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
#   This class allows us to search The Movie Database (TMDB) to
#   look for movie synopses - and other information. We will add
#   synopsis information to the information we provide the LLM
#   to try and reduce hallucinations.
from rebert.classes.moviedb.TMDB.Search import Search
from rebert.classes.moviedb.TMDB.MovieInfo import MovieInfo
from rebert.classes.moviedb.TMDB.Configuration import Configuration
from rebert.classes.moviedb.TMDB.tmdb_genres import *
#
#

MODULE_MOVIES_DEBUG = True

if not MODULE_DEBUG_OVERRIDE:
    MODULE_MOVIES_DEBUG = GLOBAL_DEBUG

#
#   Quick little regex to pull a '(year)' off of a movie title 
#   This helps "fix" some information collection and some presentation issues
#
REBERT_TAIL_YEAR_1 = re.compile(r'\([0-9]{4}\)$')
REBERT_TAIL_YEAR_2 = re.compile(r'\([0-9]{4} film\)$')

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
        #wl.log(f"requesting: [{count}]: '{title}' ({year})")
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
                    movie['tmdb_id'] = item['id']
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
def collect_reviews(site_list=[], known_titles=[]):
    #
    #   Create a dictionary, with the known titles as the keys and
    #   a list of collected reviews as the values
    collected = dict()
    for title in known_titles:
        title_lower = title.lower()
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
            print_server_log(f"Skipping '{sitename}' - it has not be configured for collection.",
                             "collect_reviews()")
            continue
        #
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
            for page in REVIEW_COLLECTOR_CLASSES[sitename]['pages']:
                r = collector.getReviewsByBrowse(page=page)
                print_server_log(f"browse page {page} collected {len(r)} reviews",
                                "collect_reviews()")
                if r: reviews.extend(r)
        except Exception as ex:
            print_server_log(f"When retrieving browse page, caught exception: {str(ex)}",
                             "collect_reviews()")
            print_server_log(f"Continuing with {len(reviews)} from site site '{fullname}'",
                             "collect_reviews()")
        #
        if len(reviews) == 0:
            #   Always output a zero collection - this may indicate that a collector
            #   needs updates or revisions
            print_server_log(f"Retrieved 0 (zero) reviews from site '{sitename}'",
                             "collect_reviews()")
            print_server_log(f"Check the '{fullname}' retrieval object for an error.",
                             "collect_reviews()")
    
        #   We're going to make sure we don't have duplicate reviews
        uniqueness = dict() 
        saved = 0           #   count of how many reviews kept for this site
        duplicates = 0      #   count of duplicates for this site
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
                duplicates += 1
                print_server_log(f"Duplicate review for '{review['title']}' with key: '{key}'",
                                "collect_reviews()",
                                 MODULE_MOVIES_DEBUG)
                continue
            #   Assign some value using that unique key
            uniqueness[key] = 1
            if title_lower in collected:
                saved += 1
                collected[title_lower].append(review)
                print_server_log(f"Keeping review: '{review['title']}' by {review['author']} in {review['source']}",
                                "collect_reviews()",
                                 MODULE_MOVIES_DEBUG)
            else:
                print_server_log(f"Unrecognized title '{review['title']}' (dropped).",
                                "collect_reviews()",
                                 MODULE_MOVIES_DEBUG)
        print_server_log(f"Kept {saved} reviews from site '{fullname}'",
                        "collect_reviews()",
                         MODULE_MOVIES_DEBUG)
            
    return  collected
#
#   This fills out what we can know about a movie opening by retrieving
#   meta data from TMDB. One key thing that we want is a movie poster.
#   That poster provides a way to provide a visual in an interactive interface.
def collect_movie_meta(openings=[], tmdb_key=None):
    #
    base_url = ""
    meta_info = dict()
    #   Create a TMDB configuration object. We use this to get the URL base path for movie
    #   poster URLs, which is a key reason we collect the movie meta data.
    c = Configuration(name="TMDB.Config-{REBERT_VERS}")
    #   Make sure we can authenticate to TMDB
    if tmdb_key:
        c.setAPIKey(tmdb_key)
    else:
        print_server_log(f"Need to supply a TMDB API Key",
                        "collect_movie_meta()")
        raise Exception("Need to supply a TMDB API Key")
    
    config = c.getConfiguration()
    #print_server_log(f"TMDB Configuration: {json.dumps(config,indent=4)}",
    #                  "collect_movie_meta()",
    #                    MODULE_MOVIES_DEBUG)
    if config:
        base_url = config['images']['secure_base_url']
        #base_url = config['images']['base_url']
        print_server_log(f"from TMDB configuration, base_url: {base_url}",
                        "collect_movie_meta()",
                        MODULE_MOVIES_DEBUG)
    
    #   Create a TMDB metadata infor query object to search for synopses
    tmdb_info = MovieInfo(name="TMDB.Info-{REBERT_VERS}")
    #   Make sure we can authenticate to TMDB
    if tmdb_key:
        tmdb_info.setAPIKey(tmdb_key)
    else:
        print_server_log(f"Need to supply a TMDB API Key",
                        "collect_movie_meta()")
        raise Exception("Need to supply a TMDB API Key")
    #
    #   poster_size should probably come from the Configuration response
    image_size ="w500"
    print_server_log(f"Trying to collect meta info for {len(openings)} movies",
                      "collect_movie_meta()",
                        MODULE_MOVIES_DEBUG)
    for movie in openings:
        print_server_log(f"Getting: '{movie['title']}' with tmdb_id {movie['tmdb_id']}",
                          "collect_movie_meta()",
                          MODULE_MOVIES_DEBUG)
        movie_meta = tmdb_info.getMovieDetails(movie['tmdb_id'])
        if movie_meta:
            title_lower = movie_meta['title'].lower()
            #title_lower = movie['title'].lower()
            if base_url:
                #   A TMDB movie poster URL requires three parts, the base url from Configuration,
                #   an image size (also available from Configuration) and the poster path from
                #   the movie details response
                if movie_meta['poster_path']:
                    movie_meta['poster_path'] = base_url+image_size+movie_meta['poster_path']
                else:
                    movie_meta['poster_path'] = str()
                    print_server_log(f"missing poster_path for: '{movie['title']}'",
                                      "collect_movie_meta()",
                                      MODULE_MOVIES_DEBUG)
            meta_info[title_lower] = movie_meta
        else:
            print_server_log(f"NO metadata for: '{movie['title']}' with tmdb_id {movie['tmdb_id']}",
                              "collect_movie_meta()",
                              MODULE_MOVIES_DEBUG)
    return meta_info
#
#   When users attempt to tell us about a movie this searches for a matching
#   movie title. It tries to match the movie - and returns the index of the
#   most likely match in a list of potential matches
def search_by_movie_title(title="", tmdb_key=None):
    #   Set to the tmdb_rec if we find a match
    match = None
    #   Create a TMDB Search query object to search for synopses
    tmdb_search = Search(name="TMDB.Search-{REBERT_VERS}")
    #   Make sure we can authenticate to TMDB
    if tmdb_key:
        tmdb_search.setAPIKey(tmdb_key)
    else:
        print_server_log(f"Need to supply a TMDB API Key",
                        "search_by_movie_title()")
        raise Exception("Need to supply a TMDB API Key")
    print_server_log(f"Looking for the movie: '{title}'",
                      "search_by_movie_title()",
                      MODULE_MOVIES_DEBUG)
    #
    #   See if there is a '(year)' added to the end of the title
    matches = REBERT_TAIL_YEAR_2.findall(title)
    matches.extend(REBERT_TAIL_YEAR_1.findall(title))
    if matches:
        for m in matches:
            title = title.replace(m,'').strip()
            print_server_log(f"Looks like movie title has year appended - '{m}' - removing it",
                             "search_by_movie_title()",
                              MODULE_MOVIES_DEBUG)
    #
    #   Make the search with the title - that's all we have
    title_lower = title.lower()
    found_items = tmdb_search.movieSearch(title=title_lower)
    print_server_log(f"Found {len(found_items)} possible matches for title: {title}",
                      "search_by_movie_title()",
                      MODULE_MOVIES_DEBUG)
    index = -1
    #   We'll return a list of matching candidates
    candidates = list()
    #   Temporary list of items
    found = list()
    #   It's possible there are multiple matches
    for item in found_items:
        #print_server_log(f"{json.dumps(item,indent=4)}",
        #                  "search_by_movie_title()",
        #                  MODULE_MOVIES_DEBUG)
        try:
            #   Copy over some basic info
            movie = REBERT_MOVIE_CANDIDATE_TEMPLATE.copy()
            movie['title'] = item['title']
            movie['tmdb_id'] = item['id']
            movie['synopsis'] = item['overview']
            movie['year'] = item['release_date'][:4]
            movie['release_date'] = item['release_date']
            movie['genre_ids'] = item['genre_ids']
            movie['genre'] = convert_tmdb_genre_ids_to_terms(data=item['genre_ids'], 
                                                             skip=True)
        except:
            #   If a field is missing, then skip this candidate
            continue
        #
        #   Find the first one with an exact match title
        if (title_lower == item['title'].lower()) and not match:
            match = movie
        else:
            if len(found) < REBERT_MAX_ALTERNATE_MATCHES:
                found.append(movie)
        #
        #   If our list of candidates is too long, skip the rest
        #   of the possible matches.
        if (len(found) >= REBERT_MAX_ALTERNATE_MATCHES) and match:
            break
    #
    #   Do a fix up of the candidates to make sure we return the index of
    #   the matched record, and all the found candidates
    #
    #   Slot zero is going to be a blank record - a hack to make creating
    #   a user defined movie record easier later
    candidates.append(REBERT_MOVIE_CANDIDATE_TEMPLATE.copy())
    if match:
        candidates.append(match)
        index = 1
    candidates.extend(found)
    return index, candidates



