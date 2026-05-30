#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: config.py
#   REVISION: November, 2024
#   CREATION DATE: October, 2024
#   Author: David W. McDonald
#
#   configuration file for the rebert web app
#
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
##
#
#   Two version strings that are used when logging output to the web server.
#   These are also used when saving server and session files.
#
REBERT_VERS = "p5.0"
REBERT_VERS_STR = "rebert_"+REBERT_VERS
#
#   These flags control which parts of the system generate debugging output.
#   Debugging is by printing information to the server logs. The first flag
#   GLOBAL_DEBUG indicates the global debugging state. It should probably be
#   False in most cases to limit the total amount of output. The second flag
#   MODULE_DEBUG_OVERRIDE determines whether a specific file (module) can
#   override the GLOBAL_DEBUG state. This should probably be True to allow
#   each module to independently produce debug output.
#
GLOBAL_DEBUG = False            # the global state of the debugging
MODULE_DEBUG_OVERRIDE = True    # if True module debugging overrides global debug
#
#   All LLMs have parameters that allow each request to configure how the LLM
#   should respond. This is a set of global variables that can be used to set
#   a small number of OpenAI parameters. If the flag is commented out then the
#   API request uses the default value of the given model.
#
#REBERT_LLM_MODEL = "gpt-4o"                 # the version of the model to be used
REBERT_LLM_MODEL = "gpt-5.3-chat-latest"    # the version of the model to be used
#REBERT_LLM_TEMPERATURE = 1.2                # range 0.0 .. 2.0 - Default 1.0
#REBERT_LLM_PRES_PENALTY = 0.5               # range -2.0 .. 2.0 - Default 0.0
#REBERT_LLM_FREQ_PENALTY = 1.2               # range -2.0 .. 2.0 - Default 0.0
#
#   The recency window (aka 'window') reflects the time window tnat will
#   constitute recent movies. The window is set in the MovieNumber object
#   before making the request that collects the movie openings. The window
#   is always relative to "today" - the day the prototype is being run
#
REBERT_WINDOW_PRIOR_DAYS = 21           # the number of days in the past to start the window
REBERT_WINDOW_FUTURE_DAYS = 10          # the number of days in the future to stop the window
#
#
#   A set of file and directory global varables. The REBERT_TEMP_FILE_DIRECTORY
#   should be a directory where server data and session state files are stored.
#   The other file name templates are for server data and session data files.
#
#REBERT_TEMP_FILE_DIRECTORY = "/var/tmp"
REBERT_TEMP_FILE_DIRECTORY = "web/tmp"
#REBERT_TEMP_FILE_DIRECTORY = ""
#
REBERT_DATA_FILE_TEMPLATE = "rebert-{ver}_data_{date_str}.json"
REBERT_SESS_FILE_TEMPLATE = "rebert_session_{session_id}.json"
#
#
#   This is a template to store state information that is needed by the web
#   server. A copy of this template is created and loaded when the web server
#   is launched.
#
REBERT_SERVER_STATE_TEMPLATE = {
    "TMDB_KEY":         "",         # API key for TMDB - set on server boot up
    "OPENAI_KEY":       "",         # API key for OpenAI - set on server boot up
    "movie_data":       None        # should contain a REBERT_MOVIE_DATA_TEMPLATE
}
#
#
#   This is a template that stores session information. Session information
#   is info that we want to persist for the same user for their entire session
#   with Rebert.
#   
REBERT_SESSION_STATE_TEMPLATE = {
    "session_id":       "",         # a string session ID
    "movie_data":       None,       # should contain a REBERT_MOVIE_DATA_TEMPLATE dict
    "highlights":       None,       # a list of the movies highlighted with posters
    "active_branch":    "root",     # the name/key for the chat context
    "chat_turns":       None        # a dictionary of chat turn lists
}
#
#
#   This is a template that holds the different types of movie data collected
#   when the server launches. This is primarily collected and stored in the
#   SERVER_STATE - but is replicated in the SESSION_STATE for each interaction
#
REBERT_MOVIE_DATA_TEMPLATE = {
    "title_list":       None,       # a list of movie titles that may be opening
    "openings":         None,       # list recent movie release info
    "reviews":          None,       # a dictionary of movies
    "meta":             None        # meta-data collected from TMDB
}
#
#   The interface will show a specific set of movie posters - right now it is 6.
#   These posters are called 'highlights' to note that they are the current
#   set of movies that are showing in the display
#
REBERT_HIGHLIGHT_TEMPLATE = {
    "column":           "",         # the slot number, or column for this poster
    "title":            "",         # the title of this movie
    "synop":            "",         # the text synsopsis of the movie
    "poster":           "",         # a url to the movie poster
    "release":          ""          # the release date for this movie
}
#
#   This template is used in a list where the order of the list corresponds
#   to the order of the movie highlights. This sets the last response that
#   rebert made for a chat on the specific movie in the given slot. This is
#   used by the interface to reset the visual of the last turn when the user
#   switches back to discussing a movie they had previously discussed
#
REBERT_DISCUSSION_TEMPLATE = {
    "column":           "",         # the slot number, or column that this discussion matches
    "last_turn":        ""          # the text of the last turn
}
#
#   The UI state template maintains the variable state of the web interface.
#   These are the interaction elements that appear on the web page, that should
#   be maintained through each round-trip to the server. These variables are
#   collected from the web request, and reset in the web page template before
#   the web server response is sent back to the user.
#
REBERT_MAINPAGE_UI_STATE_TEMPLATE = {
    "session_id":       "",         # a string session ID
    "rebert_text":      "",         # the text of the prior rebert_response
    "user_question":    "",         # the text of the user's next turn in the chat
    "synopsis_state":   0,          # state of the toast - showing the synopsis
    "discuss_state":    0,          # which slot (movie) is being discussed
    "discuss_content":  None,       # list of REBERT_DISCUSSION_TEMPLATE
    "response_rows":    5,          # the number of rows, estimate to fit a response
    "rebert_response":  ""          # the response being returned to the user
}

#
#   This list is a set of names for the movie review web sites that are used.
#   When the name is in the list, that name is matched to a specific web site
#   collection object, that is then used to collect recent movie reviews. 
#
#   Most of the time it makes sense to collect it all. But for testing purposes
#   we might want to limit which review sites are collected. In that case, comment
#   out names from the list - or create another list that contains just the
#   names of the review sites being tested.
#
REBERT_REVIEW_SITES = [
    'srant',        #   Screen Rant
    'nypost',       #   New York Post
    'guardian',     #   The Guardian
    'rstone',       #   The Rolling Stone
    'ap'            #   The Associated Press
]
