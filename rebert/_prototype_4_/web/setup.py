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
import sys, os, datetime, hashlib, json, copy

#
#   This comes from the rebert class library and manages API keys
#   You should use it to store your OpenAI API key locally, so your
#   key is not stored as a constant in the code.
from rebert.classes.data.KeyManager import KeyManager

from rebert._prototype_4_.web.config import *
from rebert._prototype_4_.web.movies import *
from rebert._prototype_4_.web.utilities import *

MODULE_SETUP_DEBUG = False

if not MODULE_DEBUG_OVERRIDE:
    MODULE_SETUP_DEBUG = GLOBAL_DEBUG

##############
#
#   SERVER SETUP
#
##############

def initalize_server_state():
    server_state = REBERT_SERVER_STATE_TEMPLATE.copy()
    #   Create a key manager object - it automatically loads the
    #   available key information - if you added a key, you can
    #   access it using the domain name or the user associated with
    #   the key
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
        #   This queries the Movie Numbers website to find the openings
        movie_releases = get_recent_releases() 
        movie_data['title_list'] = list()
        for movie in movie_releases:
            movie_data['title_list'].append(movie['title'])
        #
        #   Now make a request to TMDB to find synopses
        print_server_log(f"Collecting synopses ...",
                        "initalize_server_state()",
                        MODULE_SETUP_DEBUG)
        #   We only keep a movie 'opening' if we can find/match a title in TMDB
        movie_data['openings'] = get_movie_synopses(movie_releases, 
                                                    server_state['TMDB_KEY'])
        #
        #   When debugging - output the complete list of collected openings
        if MODULE_SETUP_DEBUG:
            openings = str()
            count = 1
            for opening in movie_data['openings']:
                openings += f"\t[{count}] '{opening['title']}'\n"
                count += 1
            print_server_log(f"Known openings\n{openings}",
                            "initalize_server_state()")
        #
        #   Lastly, collect the reviews
        print_server_log(f"Collecting reviews ...",
                        "initalize_server_state()",
                        MODULE_SETUP_DEBUG)
        movie_data['reviews'] = collect_reviews(REBERT_REVIEW_SITES,
                                                movie_releases)
        #
        #
        save_movie_data(movie_data)
    #
    #   Add the movie data to the current state - this was either loaded
    #   from a file - to save time - or it was created above
    server_state['movie_data'] = movie_data
    return server_state
