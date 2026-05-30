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
import sys, os, datetime, hashlib, json

from rebert._prototype_4_.web.config import *



MODULE_UTILITIES_DEBUG = False

if not MODULE_DEBUG_OVERRIDE:
    MODULE_UTILITIES_DEBUG = GLOBAL_DEBUG


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
    except Exception as e:
        #print_server_log(f"Caught exception","generate_session_id()")
        #print_server_log(f"{e}","generate_session_id()")
        agent = "No.User-Agent"
    #
    #   Adding the time to the session id will help make it unique
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
            session_state = None
            session_file = None
    return session_state
#
#
#   We need this class to serialize the chat message turns in the session state
from rebert.classes.data.DictionaryValidatorFromTemplate import DVFTJSONEncoder

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



def print_server_log(text="", proc="", emit=True):
    if emit:
        if proc:
            sys.stderr.write(f"{REBERT_VERS_STR}@{proc}: {text}\n")
        else:
            sys.stderr.write(f"{REBERT_VERS_STR}: {text}\n")
    return
