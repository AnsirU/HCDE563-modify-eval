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
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
##
#
#   Two version strings that are used when logging output to the web server.
#   These are also used when saving server and session files.
#
REBERT_VERS = "p7.0"
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
#REBERT_LLM_MODEL = "gpt-4o"                # the version of the model to be used
REBERT_LLM_MODEL = "gpt-5.3-chat-latest"    # the version of the model to be used
#REBERT_LLM_TEMPERATURE = 1.7               # range 0.0 .. 2.0 - higher values increase variance
#REBERT_LLM_TOKEN_LIMIT = 450               # sets a max number of tokens that can be generated
#REBERT_LLM_PRES_PENALTY = 0.5              # range -2.0 .. 2.0 - higher values decrease repetativeness (Default 0.0)
#REBERT_LLM_FREQ_PENALTY = 1.2              # range -2.0 .. 2.0 - higher values decrease repetativeness (Default 0.0)
#
#   The recency window (aka 'window') reflects the time window tnat will
#   constitute recent movies. The window is set in the MovieNumber object
#   before making the request that collects the movie openings. The window
#   is always relative to "today" - the day the prototype is being run
#
REBERT_WINDOW_PRIOR_DAYS = 21           # the number of days in the past to start the window
REBERT_WINDOW_FUTURE_DAYS = 10          # the number of days in the future to stop the window
#
#   When rebert is trying to match a user supplied movie title, or a guessed
#   title to a movie record, it will keep a set of alternate candidates.
#
REBERT_MAX_ALTERNATE_MATCHES = 7        # max number of alternates
#
#
#   A set of file and directory global varables. The REBERT_TEMP_FILE_DIRECTORY
#   should be a directory where server data and session state files are stored.
#   The other file name templates are for server data and session data files.
#
#REBERT_TEMP_FILE_DIRECTORY = "/var/tmp"
REBERT_TEMP_FILE_DIRECTORY = "web/tmp"
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
    "rec_flags":        None,       # a list of the recommendation flags for session
    "ephem_status":     None,       # the state of the ephemeral Q&A
    "active_branch":    "root",     # the name/key for the chat context
    "chat_turns":       None,       # a dictionary of chat turn lists
    "rating":           None,       # a dictionary that maintains rating state
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
    "release":          "",         # the release date for this movie
#   Added prototype 6
    "rebert_response":  "",         # the rebert response
    "rebert_rating":    "",         # the rebert rating string
    "rebert_rationale": ""          # the extracted rebert rationale
}
#
#   These are the small flags that appear over a movie poster when Rebert
#   makes a recommendation of a movie. There should be six of these, one
#   for each movie in the highlight list. The column is used to keep track
#   of which flag matches which movie in the interface.
#
REBERT_REC_FLAGS_TEMPLATE = {
    "column":           "",         # the slot number, or column that this rec flag matches
    "flag":             "",         # the flag is an image
    "text":             "",         # used for the alt text
    "title":            "",         # movie title, used for look up
    "rating":           -1,         # the best rating found
    "source":           "",         # the source
    "author":           "",         # the author
    "over_3.5":         0,          # number of reviews strictly over 3.5
    "rebert_rating":    "",         # the rebert rating string
    "rebert_rationale": ""          # the extracted rebert rationale
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
    "ephem_s_state":    1,          # the state of the ephemeral soliciation
    "ephem_q_state":    0,          # the state of the ephemeral rec Q&A session
    "ephem_p_text":     "",         # the ephemeral question being asked
    "ephem_answer":     "",         # the user answer to the ephemeral rec question
    "ephem_q_last":     0,          # if this is the last ephemeral Q&A question
    "discuss_content":  None,       # list of REBERT_DISCUSSION_TEMPLATE
    "response_rows":    5,          # the number of rows, estimate to fit a response
    "rebert_response":  ""          # the response being returned to the user
}

#
#
#
REBERT_EPHEM_Q_TEMPLATE = {
    "state":            1,          # if the state is set to zero this
                                    # feature is turned off
    "1": {
        "prompt":       "",         # the prompt that was given to the user
        "response":     ""          # the user's reponse
    },
    "2": {
        "prompt":       "",         # the prompt that was given to the user
        "response":     ""          # the user's reponse
    },
    "3": {
        "prompt":       "",         # the prompt that was given to the user
        "response":     ""          # the user's reponse
    }
}
#
#   These are specific starter questions for the ephemeral recommentation 
#   mini-interview. These are basic questions to try and get the user talking or
#   typing about a movie. Follow-up questions are driven by the LLM.
#
REBERT_EPHEM_Q1_OPTIONS = [
    "What makes a movie a 'good' movie? Will a good movie have certain actors?",
    "What makes a movie a 'good' movie? Will a good movie be a specific type or genere?",
    "Describe the type of story you would like the movie to tell. What makes a good story?",
    "Describe your best movie experience. What was it like? What movie did you see?",
    "Tell me about a movie that you had to see more than once. Why was it so good?",
    "Tell me about a movie that you saw more than once. What aspect brought you back?"
]
#
#   When the user doesn't give us enough information, we use these different prompts
#   to try and explain why we are asking again.
#
REBERT_EPHEM_RETRY_OPTIONS = [
    "I'm going to need a little more description.",
    "What? Maybe you can tell me a bit more information.",
    "I didn't catch that. Could you tell me more?",
    "My recommendation will be better with more description.",
    "I can't make a good suggestion without more info."
]
#
#   When we make a recommendation request of the LLM we run those requests in different
#   threads of execution. This record is used to manage those threads so we can
#   terminate them when they finish.
#
REBERT_TREADED_EPHEM_REC_TEMPLATE = {
    'requester':        None,           # the chat completion object
    'title':            "",             # The title, easy, convenient to keep here 
    'movie':            None,           # The movie 'highlight' 
    'chat':             None,           # The created context
    'count':            0,              # The number of times we've checked on this thread
    'response':         None,           # The whole response, if any
    'message':          ""              # The specific message
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
    'thr',          #   The Hollywood Reporter
    'rstone',       #   The Rolling Stone
    'pluggedin',    #   Plugged-In Media
    'fthreat',      #   Film Threat reviews
    'ap'            #   The Associated Press
]


#
#   A set of questions (human prompts) that try and get a person to tell us about a movie.
#   A number of these are based on the questions for the Blog/Vlog "Movies to be burried with"
#
#   These questions are provided as starters to the user when they start rating a movie.
#   Follow-up questions are asked by the LLM. The required number of answers and the
#   total number of words can be set as configuration parameters.
#
REBERT_RATING_QUESTION_STARTERS = [
    "that you like?",
    "that was the first film you can remember seeing?",
    "that scared you the most?",
    "that is the funniest film you've seen?",
    "that made you cry?",
    "that is SO big, it MUST be seen on the big screen?",
    "that is your favorite, but critically hated film?",
    "that inspired you?",
    "that is best watched with a group of friends?",
    "that means the most to you?",
    "that you most relate to?",
    "that is objectively the greatest film ever?",
    "that you would always recommend to a new friend?",
    "that is the best film in a series or franchise of films?",
    "that you watch over and over?",
    "that exemplifies a loving relationship?",
    "that is your favorite film?",
    "that tells a meaningful story?",
    "that changed your view on something?",
    "that is so bad, it has to be good?",
    "that you watch on special occasions?",
    "that illustrates the meaning of family?",
    "that you remember because of the characters?"
]


REBERT_RATING_SESSION_INFO_TEMPLATE = {
    'ui_state':         None,       #   Save the UI interaction state
    'question_starts':  REBERT_RATING_QUESTION_STARTERS,
    'in_progress':      None,       #   Dict of the movie rating in progress
    'audio':            None,       #   Dict of the audio file information
    'rated':            None,       #   List of completed ratings
    'history_length':   0,          #   How many transcript/audio files to keep
    'transcripts':      None        #   List of transcripts
}

REBERT_RATING_AUDIO_TEMPLATE = {
    'keep':         False,          #   Default is not to keep audio
    'sequence':     1000,           #   The previous audio file sequence number
    'files':        None            #   A list of the file names
}


REBERT_RATEPAGE_UI_STATE_TEMPLATE = {
    "session_id":           "",         # a string session ID
    "rate_start":           False,      # first rating question?
    "rate_question":        "",         # the question extracted from the UI
    "rate_answer":          "",         # the answer to the question extracted from the UI
    "rate_title":           "",         # the guessed title, maybe user corrected it
    "title_candidates":     None,       # list of extracted title candidates
    "new_question":         "",         # the next or new question to ask the user
    "complete":             False,      # the rating has been completed
    "editing":              False,      # is this editing a rating?
    "edit_qna":             [],         # any Q&A collected from a user edit
    "edit_title":           "",         # movie title from a user edit
    "edit_year":            "",         # movie year from a user edit
    "edit_genres":          "",         # movie genre from a user edit
    "edit_synopsis":        "",         # movie synopsis from a user edit
    "edit_matched_index":   -1,         # the index of the 'matched' movie
    "edit_score":           -1          # an optional score for the movie
}


#
#   This is a 'rating' record that represents a rating by the user
#
REBERT_MOVIE_RATING_TEMPLATE = {
    'rtype':                    'rating',   #   A 'record type' for mixed DB search
    'active':                   True,       #   This is still an active rating
    'account_id':               '',         #   The user account_id
    'rating_id':                '',         #   The rating_id for this set
    'title':                    '',         #   The title of the movie
    'tmdb_id':                  '',         #   The tmdb_id - if validated   
    'matched':                  -1,         #   The index of the candidate that was matched
    'candidates':               None,       #   A list of candidate movie records
    'score':                    -1.0,       #   Optional score - available on 'edit'
    'last_viewed':              '',         #   A user supplied guess, recent viewing
    'creation_ts':              '',         #   Timestamp for the creation
    'qna':                      None,       #   A list of question and answer pairs
}

#
#   This is a 'movie' record that represents a movie or 'candidate' that was
#   found as a potential match for the user's rating
#
REBERT_MOVIE_CANDIDATE_TEMPLATE = {
    'title':                    "",         #   The title of the movie
    'tmdb_id':                  -1,         #   The tmdb_id 
    'imdb_id':                  '',         #   The imdb_id       - needs extra request
    'wikidata_id':              '',         #   The wikidata id   - needs extra request
    'year':                     "",         #   The 4 digit year of release
    'release_date':             "",         #   The date of release
    'synopsis':                 "",         #   Text synopsis
    'genre_ids':                [],
    'genre':                    [],
    'poster_path':              ""
}
