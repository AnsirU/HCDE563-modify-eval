#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: utilities.py
#   REVISION: October, 2024
#   CREATION DATE: October, 2024
#   Author: David W. McDonald
#
#   A set of utility functions to support the rebert web app
#
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
##
#
import sys, os, datetime, hashlib, json

#   Used when reading variables from user data fields
from markupsafe import escape

#   This is for use by the login manager user loader code
import flask_login

from rebert._prototype_7_1_.web.config import *



MODULE_UTILITIES_DEBUG = True

if not MODULE_DEBUG_OVERRIDE:
    MODULE_UTILITIES_DEBUG = GLOBAL_DEBUG

#
#   Set up the Flask login manager - it must also be given the 'app'
login_manager = flask_login.LoginManager()


##############
#
#   UTILITIES
#
##############
#
#   We will want a session tracker so that we can keep track of sessions with
#   individuals. It would be best to store this in a DB but we're going to use
#   a set of flat files for the prototypes
#
def generate_session_id(request=None):
    #   HTTP request headers are not provided in a parsed form, they are not a JSON thing
    #   We have to extract key:values manually
    agent = "No.User-Agent"
    try:
        #
        #   Check that we have some kind of string
        headers_str = str(request.headers)
        ua_pos = headers_str.find('User-Agent:')
        if ua_pos >= 0:
            ua_end = headers_str.find('\n',(ua_pos+1))
            ua_pos = ua_pos + len('User-Agent:')
            agent = headers_str[ua_pos:ua_end]
            agent = agent.strip()
            #sys.stderr.write(f"[{ua_pos}:{ua_end}] = {agent}\n")
    except Exception as e:
        #print_server_log(f"Caught exception","generate_session_id()",MODULE_UTILITIES_DEBUG)
        #print_server_log(f"{e}","generate_session_id()",MODULE_UTILITIES_DEBUG)
        agent = "No.User-Agent"
    #
    ts = str(datetime.datetime.now())
    #
    #   create a string of the User-Agent and the current time
    #   make that string a set of 'bytes'
    id_gen = bytes(agent+"++/++"+ts,'utf-8')
    #
    #   With the Blake2 algorithm create a hash that is 'short'
    h = hashlib.blake2s(digest_size=8)
    h.update(id_gen)
    #   Use the text of that short string as a session ID
    new_session_id = "ses_"+str(h.hexdigest())
    print_server_log(f"Generated session id: {new_session_id}",
                    "generate_session_id()",
                    MODULE_UTILITIES_DEBUG)
    return new_session_id


def generate_rating_id(rated_movie=None):
    #   Use rated movie data to create a string
    mov_str = rated_movie['title']+"//"+str(rated_movie['tmdb_id'])
    #   Add a timestamp to that string
    ts_str = str(datetime.datetime.now())
    #   Convert that string to bytes
    id_gen = bytes(mov_str+"//"+ts_str,'utf-8')
    #   With the Blake2 algorithm create a hash that is 'short'
    h = hashlib.blake2s(digest_size=8)
    h.update(id_gen)
    #   Use the text of that short string as a rating ID
    rating_id = "rate_"+str(h.hexdigest())
    print_server_log(f"Generated rating id: {rating_id}",
                    "generate_rating_id()",
                    MODULE_UTILITIES_DEBUG)
    return rating_id


#
#   Generate a unique account ID for this user. Basically a hash of the
#   curent date and time
#
def generate_account_id(record=None):
    ts_str = record['creation_ts']
    uname = record['username']
    cpass = record['password']
    data_str = 'rebert_user++'+uname+cpass+ts_str
    byte_string = bytes(data_str,'utf-8')
    #   Create a hashing object to hash the resulting string
    h = hashlib.blake2s(digest_size=8)
    h.update(byte_string)
    #   Prepend short string to create the account id
    account_id = "user_"+str(h.hexdigest())
    print_server_log(f"Generated account id: {account_id}",
                    "generate_account_id()",
                    MODULE_UTILITIES_DEBUG)
    return account_id

#
#
#   Hash the password text - we store the hash, not the actual password
#   the hash is what is checked
#
#   This approach will *REQUIRE* that a user reset their password if they
#   change their email address.
#
#   That type of change requires specific tracking that is not done here, so
#   the simple approach is no changes to email
#
def crypt_password(password="", record=None):
    #   Make a string of the password, user email, and creation timestamp
    data_str = password + record['email'] + record['creation_ts']
    byte_string = bytes(data_str,'utf-8')
    #   Create a hashing object to hash the resulting string
    h = hashlib.blake2s(digest_size=32)
    h.update(byte_string)
    #   Use the text of the result as the password or to accept a password
    return str(h.hexdigest())


#
#   Clean the username of text, emoji and other stuff we don't want right now
#
def clean_username(uname=""):
    #   Replace a whole set of whitespace char to underscore
    for char in [" ", "\t", "\n", "\r", '\u00A0', '\u1680', '\u2000', '\u2001', '\u2002', '\u2003', 
                 '\u2004', '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200A']:
        uname = uname.replace(char,'_')
    #
    #   Check all the characters in the name. 
    #   If character is allowed, add it to the new_name username
    new_name = ""
    for c in uname:
        if c in REBERT_ALLOWED_USERNAME_CHARS:
            new_name = new_name+c
    return new_name


#
#
def extract_main_page_form_data(request=None):
    ui_state = REBERT_MAINPAGE_UI_STATE_TEMPLATE.copy()
    try:
        ui_state['session_id'] = escape(request.form["session_id"])
        #ui_state['rebert_text'] = escape(request.form["ask_output"])
        ui_state['rebert_text'] = request.form["ask_output"]
        #ui_state['user_question'] = escape(request.form["question_text"])
        ui_state['user_question'] = request.form["question_text"]
        ui_state['synopsis_state'] = request.form["synopsis_state"]
        ui_state['discuss_state'] = request.form["discuss_state"]
        ui_state['ephem_q_state'] = request.form["ephem_q_state"]
        ui_state['ephem_s_state'] = request.form["ephem_s_state"]
        #ui_state['ephem_answer'] = escape(request.form["ephem_answer"])
        ui_state['ephem_answer'] = request.form["ephem_answer"]
    except Exception as e:
        #   An exception here is really, really, bad - always output this exception
        keys_str = str(list(request.form.keys()))
        print_server_log(f"Caught an exception when reading form variables:",
                        "extract_main_page_form_data()")
        print_server_log(f"Request form includes the following variables:\n\t{keys_str}",
                        "extract_main_page_form_data()")
        print_server_log(f"{e}","extract_main_page_form_data()")
        raise
    return ui_state


def extract_rate_page_form_data(request=None):
    ui_state = REBERT_RATEPAGE_UI_STATE_TEMPLATE.copy()
    try:
        ui_state['session_id'] = escape(request.form["session_id"])
        #
        #   This is the basic movie rating info - when the user is in process
        #   of rating something the first time.
        if 'rating_question_input' in request.form:
            #ui_state['rate_question'] = escape(request.form["rating_question_input"])
            ui_state['rate_question'] = request.form["rating_question_input"]
        if 'transcribed_answer' in request.form:
            #ui_state['rate_answer'] = escape(request.form["transcribed_answer"])
            ui_state['rate_answer'] = request.form["transcribed_answer"]
        if 'rate_start' in request.form:
            ui_state['rate_start'] = True
        if 'rate_complete' in request.form:
            ui_state['complete'] = True
        if 'edit_rating' in request.form:
            #ui_state['edit_tmdb_id'] = escape(request.form["edit_rating"])
            ui_state['edit_tmdb_id'] = request.form["edit_rating"]
        if 'title_confirmation_text' in request.form:
            #ui_state['rate_title'] = escape(request.form["title_confirmation_text"])
            ui_state['rate_title'] = request.form["title_confirmation_text"]
        #
        #   This is part of a movie rating edit - if the user changes their answers
        #   Collect the qna questions and answers - if they are in the page
        qna = list()
        loop_index = 0
        missing_field = False
        while not missing_field:
            loop_index += 1
            q_key = f"rate_question_{loop_index}"
            a_key = f"rate_answer_{loop_index}"
            if (q_key in request.form) and (a_key in request.form):
                d = dict()
                #d['question'] = escape(request.form[q_key])
                #d['answer'] = escape(request.form[a_key])
                d['question'] = request.form[q_key]
                d['answer'] = request.form[a_key]
                qna.append(d)
            else:
                missing_field = True
        ui_state['edit_qna'] = qna
        #
        #   This is data collected when editing a movie rating
        if 'rating_movie_title_input' in request.form:
            #ui_state['edit_title'] = escape(request.form["rating_movie_title_input"])
            ui_state['edit_title'] = request.form["rating_movie_title_input"]
        if 'matched_year' in request.form:
            #ui_state['edit_year'] = escape(request.form["matched_year"])
            ui_state['edit_year'] = request.form["matched_year"]
        if 'matched_genres' in request.form:
            #ui_state['edit_genres'] = escape(request.form["matched_genres"])
            ui_state['edit_genres'] = request.form["matched_genres"]
        if 'matched_synopsis' in request.form:
            #ui_state['edit_synopsis'] = escape(request.form["matched_synopsis"])
            ui_state['edit_synopsis'] = request.form["matched_synopsis"]
        if 'matched_index' in request.form:
            try:
                ui_state['edit_matched_index'] = str(request.form["matched_index"])
                ui_state['edit_matched_index'] = int(ui_state['edit_matched_index'])
                print_server_log(f"edit_matched_index: {ui_state['edit_matched_index']}",
                                "extract_rate_page_form_data()",
                                MODULE_UTILITIES_DEBUG)
            except:
                ui_state['edit_matched_index'] = -1
                field_value = str(request.form["matched_index"])
                print_server_log(f"Could not covert '{field_value}' to an int() for edit_matched_index",
                                "extract_rate_page_form_data()")
        #
        #   The movie score part of editing a prior rating action 
        if 'score_movie_input' in request.form:
            try:
                ui_state['edit_score'] = str(request.form["score_movie_input"])
                ui_state['edit_score'] = float(ui_state['edit_score'])
                print_server_log(f"Got score: '{ui_state['edit_score']}'",
                                "extract_rate_page_form_data()",
                                MODULE_UTILITIES_DEBUG)
            except:
                ui_state['edit_score'] = -1
                field_value = str(request.form["score_movie_input"])
                print_server_log(f"Could not covert '{field_value}' to an float() for edit_score",
                                "extract_rate_page_form_data()")
        else:
            print_server_log(f"No 'score_movie_input' field in form.",
                            "extract_rate_page_form_data()",
                            MODULE_UTILITIES_DEBUG)
        #
        #   The movie last viewing is part of editing a prior rating action 
        if 'last_viewing' in request.form:
            ui_state['edit_view_date'] = str(request.form["last_viewing"])
            print_server_log(f"Last viewing date: '{ui_state['edit_view_date']}'",
                              "extract_rate_page_form_data()",
                              MODULE_UTILITIES_DEBUG)
        else:
            print_server_log(f"No 'last_viewing' field in form.",
                            "extract_rate_page_form_data()",
                            MODULE_UTILITIES_DEBUG)
        #
        #   A little debug 
        #keys_str = str(list(request.form.keys()))
        #print_server_log(f"Request form includes the following variables:\n\t{keys_str}",
        #                "extract_rate_page_form_data()")
        #
        #   Quick check of the cookies - is the user logged in?
        if request.cookies:
            print_server_log(f"Login session cookie: {request.cookies['session']}",
                              "extract_rate_page_form_data()",
                              MODULE_UTILITIES_DEBUG)
        else:
            print_server_log(f"NO login session cookies!",
                              "extract_rate_page_form_data()",
                              MODULE_UTILITIES_DEBUG)
    except Exception as e:
        #   An exception here is really, really, bad - always output this exception
        keys_str = str(list(request.form.keys()))
        print_server_log(f"Caught an exception when reading form variables:",
                        "extract_rate_page_form_data()")
        print_server_log(f"Request form includes the following variables:\n\t{keys_str}",
                        "extract_rate_page_form_data()")
        print_server_log(f"{e}","extract_rate_page_form_data()")
        raise
    return ui_state



def load_session_state(session_id=None):
    if not session_id: return None
    session_state = None
    state_filename = REBERT_SESS_FILE_TEMPLATE.format(session_id=session_id)
    state_file_path = os.path.join(REBERT_TEMP_FILE_DIRECTORY,state_filename)
    if os.path.isfile(state_file_path):
        try:
            session_file = open(state_file_path,"r")
            session_state = json.load(session_file)
            session_file.close()
        except Exception as e:
            print_server_log(f"Caught exception","load_session_state()")
            print_server_log(f"{e}","load_session_state()")
            print_server_log(f"Returning 'None' for session_state","load_session_state()")
            session_state = None
            session_file = None
    return session_state
#
#
#   We need this class to serialize the chat message turns in the session state
from rebert.classes.data.DictionaryValidatorFromTemplate import DVFTJSONEncoder
#
def save_session_state(session_info=None):
    if not session_info: 
        print_server_log(f"NO session_info to save",
                        "save_session_state()",
                        MODULE_UTILITIES_DEBUG)
        return
    session_id = session_info['session_id']
    state_filename = REBERT_SESS_FILE_TEMPLATE.format(session_id=session_id)
    state_file_path = os.path.join(REBERT_TEMP_FILE_DIRECTORY,state_filename)
    try:
        print_server_log(f"Saving: {state_file_path}",
                        "save_session_state()",
                        MODULE_UTILITIES_DEBUG)
        session_file = open(state_file_path,"w")
        json.dump(session_info,session_file, cls=DVFTJSONEncoder)
        session_file.close()
    except Exception as e:
        print_server_log(f"Caught exception","save_session_state()")
        print_server_log(f"{e}","save_session_state()")
        session_file = None
    return



def load_movie_data():
    movie_data = None
    current_time = datetime.datetime.now()
    date_str = str(current_time).partition(' ')[0]
    date_str = date_str.replace('-','')
    data_filename = REBERT_DATA_FILE_TEMPLATE.format(ver=REBERT_VERS,
                                                     date_str=date_str)
    data_file_path = os.path.join(REBERT_TEMP_FILE_DIRECTORY,data_filename)
    if os.path.isfile(data_file_path):
        try:
            data_file = open(data_file_path,"r")
            movie_data = json.load(data_file)
            data_file.close()
        except Exception as e:
            print_server_log(f"Caught exception","load_movie_data()")
            print_server_log(f"{e}","load_movie_data()")
            movie_data = None
            data_file = None
    return movie_data



def save_movie_data(movie_data=None):
    if not movie_data: 
        print_server_log(f"NO movie_data to save",
                        "save_movie_data()",
                        MODULE_UTILITIES_DEBUG)
        return
    current_time = datetime.datetime.now()
    date_str = str(current_time).partition(' ')[0]
    date_str = date_str.replace('-','')
    data_filename = REBERT_DATA_FILE_TEMPLATE.format(ver=REBERT_VERS,
                                                     date_str=date_str)
    data_file_path = os.path.join(REBERT_TEMP_FILE_DIRECTORY,data_filename)
    movie_data['filename'] = data_file_path
    movie_data['timestamp'] = str(current_time).partition('.')[0]
    try:
        print_server_log(f"Saving: {data_file_path}",
                        "save_movie_data()",
                        MODULE_UTILITIES_DEBUG)
        movie_file = open(data_file_path,"w")
        json.dump(movie_data,movie_file)
        movie_file.close()
    except Exception as e:
        print_server_log(f"Caught exception","save_movie_data()")
        print_server_log(f"{e}","save_movie_data()")
        movie_file = None
    return
#
#
#   
#
def print_server_log(text="", proc="", emit=True):
    if emit:
        if proc:
            sys.stderr.write(f"{REBERT_VERS_STR}@{proc}: {text}\n")
        else:
            sys.stderr.write(f"{REBERT_VERS_STR}: {text}\n")
    return


def apply_explanation_ui_state(ui_state=None):
    """Set UI flags for baseline vs modified study conditions."""
    if ui_state is None:
        ui_state = {}
    ui_state["show_explanations"] = REBERT_GROUNDED_EXPLANATIONS
    if REBERT_GROUNDED_EXPLANATIONS:
        ui_state["explanation_mode_label"] = "Modified — structured explanations"
    else:
        ui_state["explanation_mode_label"] = "Baseline — original recommendation UI"
    return ui_state

