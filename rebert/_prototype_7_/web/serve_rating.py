#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: serve_rating.py
#   REVISION: February, 2025
#   CREATION DATE: December, 2024
#   Author: David W. McDonald
#
#   This collects user ratings. One feature is the use of audio transcription.
#
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
##
#
import sys, os, datetime, random, hashlib, json, copy

from flask import render_template
from markupsafe import escape
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
#
#
#   Need these for the transcription API
from rebert.classes.OpenAI.Transcription import Transcription
from rebert.classes.OpenAI.payload.TranscriptionPayload import TranscriptionPayload
#
#
#
from rebert._prototype_7_.web.config import *
from rebert._prototype_7_.web.prompts import *
from rebert._prototype_7_.web.llm import *
from rebert._prototype_7_.web.movies import *
from rebert._prototype_7_.web.utilities import *
#
#  
#
MODULE_RATING_DEBUG = True
#
if not MODULE_DEBUG_OVERRIDE:
    MODULE_RATING_DEBUG = GLOBAL_DEBUG
#
#
#   A path on the server side that will be used to store the audio file
REBERT_AUDIO_FOLDER = 'web/tmp'
#REBERT_AUDIO_EXTENSIONS = ['.flac', '.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.ogg', '.wav', '.weba', '.webm']
#
#   Basic browser support on MacOS
#       Chrome: mp4, webm
#       Opera: mp4, webm
#       Safari: mp4
#       Firefox: ogg, webm
#   
REBERT_AUDIO_EXTENSIONS = ['.mp4', '.ogg', '.webm', '.weba']

#
#   Should we save the audio at all
REBERT_SAVE_USER_AUDIO_FILES = True
#   An audio filename template
REBERT_AUDIO_FILENAME_TEMPLATE = "user_audio_{session_id}_{seq}" 
#
#   The length of the transcribe history - also used for audio
REBERT_USER_TRANSCRIBE_HISTORY_LENGTH = 5
#
#   The minimum number of questions the user needs to answer
REBERT_MINIMUM_RATING_QNA = 3
#
#   The minimum length of answer in words
REBERT_MINIMUM_RATING_WORDS = 225
#REBERT_MINIMUM_RATING_WORDS = 5000

REBERT_MINIMUM_ANSWER_WORDS = 15


#
#   This flag will have the system load a canned set of rated movies
#   so there is some rating data to see what happens in the interface
#
#   If this is set to False, then no canned data is loaded
REBERT_LOAD_RATED_MOVIES_TEST = True
REBERT_RATED_MOVIES_TEST_FNAME = "web/data/_rated_movies_test_.json"


#
##############
#
#   Rating and preference elicitation pages
#
##############
#
def serve_rating_page(request, server_state):
    session_id = ""
    #
    #   We need a session id to be able to get the current state
    if request.method == 'GET':
        session_id = escape(request.args.get('session_id'))
    elif request.method == "POST":
        session_id = escape(request.form["session_id"])
    #
    if not session_id:
        raise Exception("Need the session_id before rating movies.")
    #
    #   This could still fail ... if the session_id is something problematic
    session_state = load_session_state(session_id)
    #
    #   This page is for initializing the first step in a rating 
    #   interaction. Let's get the session information set so that
    #   we can get a UI set up
    session_state['rating'] = REBERT_RATING_SESSION_INFO_TEMPLATE.copy()
    session_state['rating']['history_length'] = REBERT_USER_TRANSCRIBE_HISTORY_LENGTH
    session_state['rating']['transcripts'] = list()
    #random.shuffle(session_state['rating']['question_starts'])
    #   Initialize the in progress rating
    session_state['rating']['in_progress'] = REBERT_MOVIE_RATING_TEMPLATE.copy()
    session_state['rating']['in_progress']['qna'] = list()
    #   Create an empty list of rated items
    session_state['rating']['rated'] = list()
    #   Create audio state
    session_state['rating']['audio'] = REBERT_RATING_AUDIO_TEMPLATE.copy()
    session_state['rating']['audio']['keep'] = REBERT_SAVE_USER_AUDIO_FILES
    session_state['rating']['audio']['files'] = list()
    
    #
    #   Here we might load a small set of 'rated' movies to test UI 
    #   interactions that require some previously rated movies
    if REBERT_LOAD_RATED_MOVIES_TEST:
        try:
            f = open(REBERT_RATED_MOVIES_TEST_FNAME,"r")
            test_ratings = json.load(f)
            f.close()
            session_state['rating']['rated'] = test_ratings['rated']
            print_server_log(f"Initialized 'rated' list with {len(test_ratings['rated'])} test ratings",
                              "serve_rating_page()",
                              MODULE_RATING_DEBUG)
        except:
            print_server_log(f"Could not load test ratings from: {REBERT_RATED_MOVIES_TEST_FNAME}",
                              "serve_rating_page()",
                              MODULE_RATING_DEBUG)

    #   Save the session state 
    save_session_state(session_state)
    
    page = render_template("rate_start.html",
                            session = session_state)
    return page


#
def serve_rating_next(request, server_state):
    #   Collect the data from the form submission
    ui_state = extract_rate_page_form_data(request)
    #   Attempt to load a state file for this session
    session_state = load_session_state(ui_state['session_id'])
    session_state['ui_state'] = ui_state
    #
    #   This is an in_progress rating - collect the question and answer pair
    qna = dict()
    if ui_state['rate_start']:
        #   All of our starter questions begin with 'that' and use the UI to
        #   prompt "Tell me about a movie " ...
        qna['question'] = "Tell me about a movie "+ ui_state['rate_question']
        print_server_log(f"Collecting first Q&A: '{qna['question']}'",
                          "serve_rating_next()",
                          MODULE_RATING_DEBUG)
    else:
        qna['question'] = ui_state['rate_question']
        print_server_log(f"Collecting follow-up Q&A: '{qna['question']}'",
                          "serve_rating_next()",
                          MODULE_RATING_DEBUG)
    qna['answer'] = ui_state['rate_answer']
    #
    #   We're only going to count this answer if it's at least 15 'words'
    if qna['answer'] and (len(qna['answer'].split()) >= REBERT_MINIMUM_ANSWER_WORDS):
        session_state['rating']['in_progress']['qna'].append(qna)
    
    #
    #   We need to see if we have a matched movie ... if not then we
    #   should try to find a matched movie
    if ui_state['edit_matched_index'] > 0:
        session_state['rating']['in_progress']['matched'] = ui_state['edit_matched_index']
    #
    #   If we do not already have a match, then we'll try to guess
    if session_state['rating']['in_progress']['matched'] < 0:
        #   If we do not have a matched movie, but have a title that's been
        #   seen - and supposedly confirmed by the user ... then try to
        #   find that movie using a movie DB
        if ui_state['rate_title']:
            identify_movie_being_rated(session_state, ui_state, server_state)
        else:
            #   Get the current answer text - all that we have
            answers = ""
            for item in session_state['rating']['in_progress']['qna']:
                #   This is the "word" based version
                answers = answers + item['answer'] + "\n"
            #   Need a record that we can use to pass into the title extractor
            extract = dict()
            extract['text'] = answers
            extract['titles'] = list()
            #   Only try to extract movie titles if an answer is long enough
            if len(extract['text'].split()) >= REBERT_MINIMUM_ANSWER_WORDS:
                #   Try to extract movie titles 
                extract = movie_title_extract_request(extract,server_state['OPENAI_KEY'])
            #   Add these titles to the ui_state
            ui_state['title_candidates'] = extract['titles']
            #
            #   If this is the last shot ... then attempt to identify a best
            #   candidate and then call it done
            if ui_state['complete']:
                identify_movie_being_rated(session_state, ui_state, server_state)

    else:
        m = session_state['rating']['in_progress']['matched']
        title = session_state['rating']['in_progress']['candidates'][m]['title']
        print_server_log(f"Already matched the movie: '{title}'",
                           "serve_rating_next()",
                            MODULE_RATING_DEBUG)
    #
    #   Check - did we just complete this rating
    if ui_state['complete']:
        #   Save the rated movie and update the current session
        save_rated_movie(ui_state, session_state)
        #   Return a starting page - to start rating a new movie
        page = render_template("rate_start.html",
                                session = session_state)
        return page
    #
    #   The number of questions answered
    answer_count = len(session_state['rating']['in_progress']['qna'])
    #   The total length of their answers in "words" (or characters)
    answer_length = 0
    for item in session_state['rating']['in_progress']['qna']:
        #   This is a character based version
        #answer_length = answer_length + len(item['answer'])
        #   This is the "word" based version
        answer_length = answer_length + len(item['answer'].split())
    #
    #   Report on the answer status
    print_server_log(f"Have {answer_count} answers, with {answer_length} total words.",
                       "serve_rating_next()",
                        MODULE_RATING_DEBUG)
    #
    #   We want to ask the user another question about this movie
    if ((answer_count <= REBERT_MINIMUM_RATING_QNA) and
        (answer_length <= REBERT_MINIMUM_RATING_WORDS) ):
        qna_str = create_rating_qna_str(session_state)
        chat_turn = qna_question_request(None,qna_str,server_state['OPENAI_KEY'])
        ui_state['new_question'] = chat_turn['content']
        print_server_log(f"New question: {ui_state['new_question']}",
                          "serve_rating_next()",
                          MODULE_RATING_DEBUG)
        #
        #   If answering the next question would complete our Q&A then
        #   set up the returned page to indicate we're complete
        if (answer_count+1) > REBERT_MINIMUM_RATING_QNA:
            ui_state['complete'] = True
        #
        #   Save the session state 
        save_session_state(session_state)
    else:
        #   In this case we don't need a new question
        #   Save the rated movie and update the current session
        save_rated_movie(ui_state, session_state)
        #   Return a starting page - to start rating a new movie
        page = render_template("rate_start.html",
                                session = session_state)
        return page
    #
    #   At this point, we render another rating page ... see if we can get
    #   some more information from the user about this movie
    page = render_template("rate_movies.html",
                            state = ui_state,
                            session = session_state)
    return page


#
#
#
def serve_rating_edit_rating(request, server_state):
    session_id = ""
    tmdb_id = ""
    title = ""
    if request.method == 'GET':
        session_id = escape(request.args.get('session_id'))
        if 'title' in request.args:
            title = escape(request.args.get('title'))        
        if 'tmdb_id' in request.args:
            tmdb_id = escape(request.args.get('tmdb_id'))        
        #
        #   Attempt to load a state file for this session
        session_state = load_session_state(session_id)
        #
        #   find that *rated* movie by tmdb_id
        for movie in session_state['rating']['rated']:
            if tmdb_id and (str(movie['tmdb_id']) == str(tmdb_id)):
                for m in movie['candidates']:
                    if m['genre']:
                        m['genre'] = ", ".join(m['genre'])
                page = render_template("rate_edit.html",
                                        session_id = session_id,
                                        movie = movie)
                return page
        print_server_log(f"Could not find a movie matching title '{title}' and tmdb_id {tmdb_id}",
                          "serve_rating_edit_rating()",
                          MODULE_RATING_DEBUG)
        #
        #   Error condition - just return the general rate a movie page
        #   
        page = render_template("rate_start.html",
                                session = session_state)
        #
        #   DONE with anything that might be a GET
    
    elif request.method == "POST":
        #   Collect the data from the form submission
        ui_state = extract_rate_page_form_data(request)
    #
    #   Everything after this assumes that this was a POST   
    #
    #   Attempt to load a state file for this session
    session_state = load_session_state(ui_state['session_id'])
    session_state['ui_state'] = ui_state
    #
    #   Check for updated/changed values, make the change
    #
    #   First, need to find which rated movie was being edited
    movie = None
    for movie in session_state['rating']['rated']:
        if (str(movie['tmdb_id']) == str(ui_state['edit_tmdb_id'])):
            candidates = movie['candidates']
            break
    print_server_log(f"Edited rating for '{movie['title']}' and tmdb_id {ui_state['edit_tmdb_id']}",
                       "serve_rating_edit_rating()",
                       MODULE_RATING_DEBUG)
    #
    #   If we collected Q&A data - then update it
    if ui_state['edit_qna']:
        movie['qna'] = ui_state['edit_qna']
        movie['timestamp'] = str(datetime.datetime.now()).partition('.')[0]
        print_server_log(f"Updating the Q&A information.",
                           "serve_rating_edit_rating()",
                           MODULE_RATING_DEBUG)
    #
    #   If we collected a new score - then update it
    if ui_state['edit_score'] != movie['score']:
        movie['score'] = ui_state['edit_score']
        movie['timestamp'] = str(datetime.datetime.now()).partition('.')[0]
        print_server_log(f"Updating the movie score.",
                           "serve_rating_edit_rating()",
                           MODULE_RATING_DEBUG)
    #
    #   Now, if any of the matched movie info was changed then we need to do something
    #   special - use our 'blank' and modify the tmdb_id
    #   Start by setting the basic information to the matched movie THEN see if they
    #   changed any of the default information
    matched = ui_state['edit_matched_index']
    print_server_log(f"Matched index: {matched}",
                       "serve_rating_edit_rating()",
                       MODULE_RATING_DEBUG)
    if matched > 0:
        movie['title'] = movie['candidates'][matched]['title']
        movie['tmdb_id'] = movie['candidates'][matched]['tmdb_id']
        movie['matched'] = matched
    #
    #   Convert the genre list to a list of terms
    genre_list = [str(x) for x in ui_state['edit_genres'].replace(',',' ').replace(';',' ').split()]
    genre_matched = (len(genre_list) == len(movie['candidates'][matched]['genre']))
    #
    #print_server_log(f"NEW genre_list: {str(genre_list)}",
    #                   "serve_rating_edit_rating()",
    #                   MODULE_RATING_DEBUG)
    #print_server_log(f"OLD genre_list: {str(movie['candidates'][matched]['genre'])}",
    #                   "serve_rating_edit_rating()",
    #                   MODULE_RATING_DEBUG)
    if genre_matched:
        for item in genre_list:
            if not item in movie['candidates'][matched]['genre']:
                genre_matched = False
                break
    
    #
    #   Update 'matched' movie info if they edit *anything* of the defaults
    if ((matched == 0) or
        (ui_state['edit_title'] != movie['candidates'][matched]['title']) or 
        (ui_state['edit_year'] != movie['candidates'][matched]['year']) or 
        (ui_state['edit_synopsis'] != movie['candidates'][matched]['synopsis']) or
        (not genre_matched) ):
        #
        #   Use the zero slot to hold a changed/modifed movie info
        print_server_log(f"Edited title, year, synopsis or genre list. Create movie record!\n"+
                         f"Title: {ui_state['edit_title']} :: {movie['candidates'][matched]['title']}\n"+
                         f"Year: {ui_state['edit_year']} :: {movie['candidates'][matched]['year']}\n"+
                         f"Synopsis: {ui_state['edit_synopsis']} :: {movie['candidates'][matched]['synopsis']}\n"+
                         f"Genre: {genre_list} :: {movie['candidates'][matched]['genre']}\n",
                           "serve_rating_edit_rating()",
                           MODULE_RATING_DEBUG)
        #   Create that record in the zero slot
        movie['candidates'][0]['title'] = ui_state['edit_title']
        movie['candidates'][0]['year'] = ui_state['edit_year']
        movie['candidates'][0]['synopsis'] = ui_state['edit_synopsis']
        movie['candidates'][0]['genre'] = genre_list
        if not str(movie['candidates'][matched]['tmdb_id']).startswith("mod"):
            movie['candidates'][0]['tmdb_id'] = "mod-"+str(movie['candidates'][matched]['tmdb_id'])
        #
        #   Changed stuff - then we set the matched to the info in the new zero record
        matched = 0
        #   Now update which was the 'matched' information
        movie['title'] = movie['candidates'][matched]['title']
        movie['tmdb_id'] = movie['candidates'][matched]['tmdb_id']
        movie['matched'] = matched
        movie['timestamp'] = str(datetime.datetime.now()).partition('.')[0]

    if matched > 0:
        #   User picked some known movie as the best match for the movie they were describing 
        #   clear out information in the slot that is used for a modified movie
        movie['candidates'][0]['title'] = ""
        movie['candidates'][0]['tmdb_id'] = ""
        movie['candidates'][0]['year'] = ""
        movie['candidates'][0]['synopsis'] = ""
        movie['candidates'][0]['genre'] = []
    
    #
    #   Remember to save the current session state
    save_session_state(session_state)
    #
    #   Colleted all we need - go back to the start rating page
    page = render_template("rate_start.html",
                            session = session_state)
    return page




#
#   When the user has completed their rating, save that data
#
def save_rated_movie(ui_state, session_state):
    #   Move the in_progress item to the list of rated items
    current_time = datetime.datetime.now()
    session_state['rating']['in_progress']['creation_ts'] = str(current_time).partition('.')[0]
    session_state['rating']['rated'].append(session_state['rating']['in_progress'])
    #
    #   Re-initialize the in_progress rating - to empty
    session_state['rating']['in_progress'] = REBERT_MOVIE_RATING_TEMPLATE.copy()
    session_state['rating']['in_progress']['qna'] = list()
    #
    #   Save the session state 
    save_session_state(session_state)
    return




#
#   Try to match the title based on the value from the title field
#   supplied by the user
#
def identify_movie_being_rated(session_state, ui_state, server_state):
    #   No movie title - skip it - can't do anything
    if not ui_state['rate_title']: return
    #
    #   If the new title is the same as a previous title, skip search
    new_title = ui_state['rate_title'].lower()
    if new_title == session_state['rating']['in_progress']['title'].lower(): return
    #
    #   Make the search
    match, candidates = search_by_movie_title(new_title, server_state['TMDB_KEY'])
    
    print_server_log(f"Have {len(candidates)} match candidates.",
                      "identify_movie_being_rated()",
                      MODULE_RATING_DEBUG)
    session_state['rating']['in_progress']['candidates'] = candidates
    session_state['rating']['in_progress']['matched'] = match
    
    if match >= 0:
        #   In this condition there is an exact title match
        movie = session_state['rating']['in_progress']['candidates'][match]
        session_state['rating']['in_progress']['title'] = movie['title']
        session_state['rating']['in_progress']['tmdb_id'] = movie['tmdb_id']
        print_server_log(f"Have a movie match: '{movie['title']}'",
                          "identify_movie_being_rated()",
                          MODULE_RATING_DEBUG)
    else:
        #   In this condition there are candidate titles, but not an exact
        #   match - we should return the titles as title candidates
        title_candidates = list()
        for movie in candidates:
            title_candidates.append(movie['title'])
        ui_state['title_candidates'] = title_candidates
    return


#
#
#   This serves the transcription process - makes two different API calls
#
def serve_transcribe_rating_audio(request, server_state):
    #print_server_log(f"Starting a '/transcribe' request",
    #                  "serve_transcribe_rating_audio()",
    #                  MODULE_RATING_DEBUG)
    #
    #   See if we can get a session_id from this request
    session_id = ""
    try:
        session_id = request.form["session_id"]
        print_server_log(f"Got session_id: '{session_id}'",
                        "serve_transcribe_rating_audio()",
                        MODULE_RATING_DEBUG)
    except:
        session_id = ""
        print_server_log(f"No 'session_id' field in the form data!",
                        "serve_transcribe_rating_audio()",
                        MODULE_RATING_DEBUG)
    #
    #   Load the session state - useful for maintaining the audio
    session_state = None
    if session_id:
        session_state = load_session_state(session_id)
    #
    #   Start validation of the required audio file
    if 'file' not in request.files:
        print_server_log(f"There was no 'file' in the request object!",
                        "serve_transcribe_rating_audio()",
                        MODULE_RATING_DEBUG)
        raise Exception("There was no 'file' in the request object!")
    #
    #   In Flask - file_contents is a werkzeug.datastructures.FileStorage type
    file_contents = request.files['file']
    #
    #   Check that there actually IS some content
    if not file_contents:
        print_server_log(f"The file was empty, no contents!",
                        "serve_transcribe_rating_audio()",
                        MODULE_RATING_DEBUG)
        raise Exception("There was no 'file' in the request object!")
    #
    #   Create a "safe" filename for use with a request if we are not saving
    safe_fname = secure_filename(os.path.basename(file_contents.filename))
    saved_file = session_state['rating']['audio']['keep']
    #   Now check to see whether we should save this audio file
    if session_state and session_state['rating']['audio']['keep']:
        manage_transcription_audio_files(session_state,file_contents)
        record = session_state['rating']['audio']['files'][-1]
        safe_fname = record['filename']
    #
    #   If we made it here, then we probably have something we can work with to
    #   make a transcription request
    #   
    #   Create the transcriber object
    transcriber = Transcription()
    transcriber.setBearerToken(server_state['OPENAI_KEY'])
    #
    #   Create a payload object
    request_data = TranscriptionPayload()
    #
    #   This version simply passes the MIME type object into the payload
    #   Above we possibly saved the file, so reset the file pointer
    #   to the start of the file, or the stream may be at its end already
    file_contents.stream.seek(0)
    request_data.setFile(stream=file_contents,filename=safe_fname)
    #
    #   Set the audio request
    transcriber.setRequestPayload(request_data)
    transcriber.queueRequest()
    #
    #   Get the start time for the request
    start_time = datetime.datetime.now()
    #   Make the request
    transcriber.makeRequest() 
    #   Get the transcribed response
    response = transcriber.nextResponse()
    #   Get the ending time
    finish_time = datetime.datetime.now()
    
    #   Check that there was a response
    if response:
        #   We'll return a JSON of this dictionary
        transcription = dict()
        #   Convert the response JSON to a python dictionary
        rjson = response.json()
        transcription['text'] = rjson['text']
        transcription['titles'] = list()
        transcription['timestamp'] = str(datetime.datetime.now()).partition('.')[0]
        #   Calculate the total run time of the transcription
        runtime = finish_time-start_time
        print_server_log(f"Transcription elapsed time: {runtime}",
                          "serve_transcribe_rating_audio()",
                          MODULE_RATING_DEBUG)
        #
        #   Only try to extract movie titles from transcript if its long enough
        if len(transcription['text'].split()) >= REBERT_MINIMUM_ANSWER_WORDS:
            #   Try to extract movie titles 
            transcription = movie_title_extract_request(transcription,server_state['OPENAI_KEY'])
        #   Save this transcription
        session_state['rating']['transcripts'].append(transcription)
        #   Check to see how many transcripts we have
        saved = len(session_state['rating']['transcripts']) 
        hist = session_state['rating']['history_length']
        print_server_log(f"Saved {saved} of {hist} transcripts.",
                        "serve_transcribe_rating_audio()",
                        MODULE_RATING_DEBUG)
        #
        #   Trim the list of the transcripts if it's too long
        if saved > hist:
            short_list = session_state['rating']['transcripts'][1:]
            session_state['rating']['transcripts'] = short_list
        #
        #   Save the session state 
        save_session_state(session_state)
        #
        #   Return what we have - formatted to be easy to read
        #return json.dumps(transcription,indent=4)
        #   Return what we have - compact, hard to read
        return json.dumps(transcription)
    else:
        #   Get the last response - hopefully it says something 
        #   about why we didn't get a response
        prior = transcriber.getPriorRequests()
        prior_resp = prior[0]['response']
        prior_err = prior[0]['error']
        #   Dump the error message into the server log
        error = "ERROR:\n"+json.dumps(prior_err,indent=4)+"\n"
        print_server_log(f"{error}",
                          "serve_transcribe_rating_audio()",
                          MODULE_RATING_DEBUG)
        #   Dump the response text - error response - into the server log
        response = f"RESPONSE:\ntype: {type(prior_resp)}\n"
        response = response+json.dumps(prior_resp.text,indent=4)+"\n"
        print_server_log(f"{response}",
                          "serve_transcribe_rating_audio()",
                          MODULE_RATING_DEBUG)
    #
    #   If we get to this return, then something bad happened
    #   Above we logged the error in the server - here we're sending an error back
    #   to the user's browser
    status = "We're very sorry. Something went wrong with the transcription request.\n"
    status = status + "You could try again, or check the rebert server status.\n"
    transcription['text'] = status
    transcription['titles'] = list()
    transcription['timestamp'] = str(datetime.datetime.now()).partition('.')[0]
    return json.dumps(transcription)


#
#   This manages the rating audio file history. This saves audio files
#   and will delete files if the file history is too long
#
def manage_transcription_audio_files(session_state, file_contents):
    #
    #   Get the MIME content type - two slightly different ways to get that. 
    #   The are formatted slightly differently.
    #content_type = file_contents.content_type
    content_type = file_contents.mimetype
    #
    #   Make sure we have some kind of filename for this thing. Our own
    #   jQuery should have set some value for this.
    if not file_contents.filename:
        print_server_log(f"The file_contents.filename was empty!",
                        "manage_transcription_audio_files()",
                        MODULE_RATING_DEBUG)
        raise Exception("The file_contents.filename was empty!")
    #
    #   Even so, never trust that the filename is safe. We're going to
    #   munge it to something that we could use locally.
    #
    #   Extract the leaf - filename - from the file path
    raw_fname = os.path.basename(file_contents.filename)    
    #   Split the file name into the base part and a file extension
    fname_base, fname_ext = os.path.splitext(raw_fname)
    #   Check that the extension is something we allow - a sound file type
    if fname_base and fname_ext and (fname_ext.lower() in REBERT_AUDIO_EXTENSIONS):
        sid = session_state['session_id']
        session_state['rating']['audio']['sequence'] += 1
        seq = session_state['rating']['audio']['sequence']
        new_fname = REBERT_AUDIO_FILENAME_TEMPLATE.format(session_id=sid,
                                                          seq=seq)
        new_fname = new_fname+fname_ext.lower()
        safe_fname = secure_filename(new_fname)
        safe_fname = os.path.join(REBERT_AUDIO_FOLDER, safe_fname)
        #
        #   Create a record of the file we - are supposedly writing
        record = {'type':content_type, 'filename':safe_fname}
        session_state['rating']['audio']['files'].append(record)
        #   write the file ...
        file_contents.save(safe_fname)
        print_server_log(f"Saved the file '{safe_fname}' type: {content_type}",
                        "manage_transcription_audio_files()",
                        MODULE_RATING_DEBUG)
        #
        #   Check that we have not saved too many audio files - delete the
        #   oldest file in the list if there are too many
        saved = len(session_state['rating']['audio']['files']) 
        #   Keeping as many audio files as we have transcribed transcripts
        hist = session_state['rating']['history_length']
        print_server_log(f"Have {saved} of {hist} audio files for {sid}",
                        "manage_transcription_audio_files()",
                        MODULE_RATING_DEBUG)
        #   Are there too many files?
        if saved > hist:
            record = session_state['rating']['audio']['files'][0]
            short_list = session_state['rating']['audio']['files'][1:]
            session_state['rating']['audio']['files'] = short_list
            if os.path.isfile(record['filename']):
                os.remove(record['filename'])
                print_server_log(f"Deleted '{record['filename']}'",
                                "manage_transcription_audio_files()",
                                MODULE_RATING_DEBUG)
    else:
        if fname_base and fname_ext:
            print_server_log(f"Audio type '{fname_ext}' is not supported.",
                            "manage_transcription_audio_files()",
                            MODULE_RATING_DEBUG)
            raise Exception(f"Audio type '{fname_ext}' is not supported.")
        else:
            print_server_log(f"Filename error: '{raw_fname}'",
                            "manage_transcription_audio_files()",
                            MODULE_RATING_DEBUG)
            raise Exception(f"Filename error: '{raw_fname}'")
    return 


#
#   When the interface needs movie data
#
def serve_movie_data_request(request, server_state):
    session_id = ""
    title = ""
    tmdb_id = -1
    match_index = -1
    editing_tmdb_id = ""
    #
    #   We need a session id to be able to get the current state
    #   But also, to get movie information, we need something about 
    #   the movie we're requesting
    if request.method == 'GET':
        session_id = escape(request.args.get('session_id'))
        if 'title' in request.args:
            title = request.args.get('title')
        if 'tmdb_id' in request.args:
            tmdb_id = request.args.get('tmdb_id')
        if 'match_index' in request.args:
            match_index = request.args.get('match_index')
    elif request.method == "POST":
        session_id = escape(request.form["session_id"])
        if 'title' in request.form:
            title = request.form['title']
        if 'tmdb_id' in request.form:
            tmdb_id = request.form['tmdb_id']
        if 'match_index' in request.form:
            match_index = request.form['match_index']
        if 'edit_rating' in request.form:
            editing_tmdb_id = request.form['edit_rating']
    #
    #
    if not session_id:
        raise Exception("Need the session_id to request movie data.")
    
    #
    #   This could still fail ... if the session_id is something problematic
    session_state = load_session_state(session_id)

    #
    #   These were useful for debugging an issue with values extracted from
    #   Flask forms. Turns out they don't quite work as naturally as you
    #   would expect.
    #   
    #print_server_log(f"title type: {str(type(title))} :: {title}",
    #                "serve_movie_data_request()",
    #                MODULE_RATING_DEBUG)
    #print_server_log(f"match_index type: {str(type(match_index))} :: {match_index}",
    #                "serve_movie_data_request()",
    #                MODULE_RATING_DEBUG)
    #
    #   Convert the match_index - a <class 'markupsafe.Markup'> thing - to an int
    try:
        match_index = int(str(match_index))
    except Exception as ex:
        print_server_log(f"match_index was: {match_index}",
                        "serve_movie_data_request()",
                        MODULE_RATING_DEBUG)
        print_server_log(f"Exception converting match_index to int: {str(ex)}",
                        "serve_movie_data_request()",
                        MODULE_RATING_DEBUG)
        match_index = -1
    
    #
    #   Set up, from which set of movie candidates are we getting the
    #   movie information?
    #
    candidates = session_state['rating']['in_progress']['candidates']
    #
    if editing_tmdb_id:
        for movie in session_state['rating']['rated']:
            if (str(movie['tmdb_id']) == str(editing_tmdb_id)):
                candidates = movie['candidates']
    
    #
    #   Priority 1 - get the named index
    #   If we got the 'index' value - that is an index into the list of candidates
    #   just return that one
    if (match_index >= 0):
        movie = candidates[match_index].copy()
        if movie['genre']:
            movie['genre'] = ", ".join(movie['genre'])
        movie['matched_index'] = match_index
        return json.dumps(movie)
    #
    #   Priority 2 - get the one with the same tmdb_id
    #   Match using the tmdb_id
    index = -1
    for movie in candidates:
        index += 1
        if tmdb_id and (str(movie['tmdb_id']) == str(tmdb_id)):
            movie = movie.copy()
            if movie['genre']:
                movie['genre'] = ", ".join(movie['genre'])
            movie['matched_index'] = index
            return json.dumps(movie)
    #
    #   Priority 3 - get the one with the same title
    #   Match using the title
    tl = str(title).lower()
    index = -1
    for movie in candidates:
        index += 1
        if title and (movie['title'].lower() == tl):
            movie = movie.copy()
            if movie['genre']:
                movie['genre'] = ", ".join(movie['genre'])
            movie['matched_index'] = index
            return json.dumps(movie)
    
    error = dict()
    error['error'] = "No match for title or tmdb_id"
    error['title'] = title
    error['tmdb_id'] = tmdb_id
    error['matched_index'] = match_index
    error['matched'] = session_state['rating']['in_progress']['matched'] 
    return json.dumps(error)