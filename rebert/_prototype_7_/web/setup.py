#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: setup.py
#   REVISION: October, 2024
#   CREATION DATE: October, 2024
#   Author: David W. McDonald
#
#   Code that runs before the Flask web server starts
#
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
##
#
import sys, os, datetime, hashlib, json, copy

#
#   This comes from the rebert class library and manages API keys
#   You should use it to store your OpenAI API key locally, so your
#   key is not stored as a constant in the code.
from rebert.classes.data.KeyManager import KeyManager

from rebert._prototype_7_.web.config import *
from rebert._prototype_7_.web.movies import *
from rebert._prototype_7_.web.utilities import *
from rebert._prototype_7_.web.collector_config import *

MODULE_SETUP_DEBUG = True

if not MODULE_DEBUG_OVERRIDE:
    MODULE_SETUP_DEBUG = GLOBAL_DEBUG

##############
#
#   SERVER SETUP
#
##############

def initalize_server_state():
    server_state = REBERT_SERVER_STATE_TEMPLATE.copy()
    #   Create a key manager object - it automatically loads
    #   the available key information - if you added a key    
    key_manager = KeyManager()
    #
    #   Returns a list of keys - should only be one
    key_list = key_manager.findRecord(domain="api.openai.com")
    #
    #   Extract just the api key from the key record
    server_state['OPENAI_KEY'] = key_list[0]['key']
    #
    #   We need the key for the TMDB (The Movie DB) as well
    key_list = key_manager.findRecord(domain="api.themoviedb.org")
    server_state['TMDB_KEY'] = key_list[0]['key']
    #
    movie_data = load_movie_data()
    if not movie_data:
        movie_data = REBERT_MOVIE_DATA_TEMPLATE.copy()
        #
        #   Get some recent release information
        print_server_log(f"Collecting release date info ...",
                        "initalize_server_state()",
                        MODULE_SETUP_DEBUG)
        movie_releases = get_recent_releases() 
        movie_data['title_list'] = list()
        for movie in movie_releases:
            movie_data['title_list'].append(movie['title'])
        #
        #   Now make a request to TMDB to find synopses
        print_server_log(f"Collecting synopses ...",
                        "initalize_server_state()",
                        MODULE_SETUP_DEBUG)
        movie_data['openings'] = get_movie_synopses(movie_releases, 
                                                    server_state['TMDB_KEY'])
        #
        #   Just keep the movies where we have a match and a synopsis
        movie_data['title_list'] = list()
        for movie in movie_data['openings']:
            movie_data['title_list'].append(movie['title'])
        #
        #
        if len(movie_data['title_list']) == 0:
            print_server_log(f"Found no 'recent' movie openings, no movies to collect.",
                            "initalize_server_state()")
            print_server_log(f"Exiting.",
                            "initalize_server_state()")
            sys.exit()
        #
        #   This collects meta data for the set of openings
        print_server_log(f"Collecting movie meta data ...",
                        "initalize_server_state()",
                        MODULE_SETUP_DEBUG)
        movie_data['meta'] = collect_movie_meta(movie_data['openings'], 
                                                server_state['TMDB_KEY'])
        #
        #   Lastly, collect the reviews
        print_server_log(f"Collecting reviews ...",
                        "initalize_server_state()",
                        MODULE_SETUP_DEBUG)
        movie_data['reviews'] = collect_reviews(REBERT_REVIEW_SITES,
                                                movie_data['title_list'])
        #
        #
        save_movie_data(movie_data)
    #
    #   Add the movie data to the current state - this was either loaded
    #   from a file - to save time - or it was created above
    server_state['movie_data'] = movie_data
    return server_state
