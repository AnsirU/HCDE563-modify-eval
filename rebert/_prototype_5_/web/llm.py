#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: llm.py
#   REVISION: October, 2024
#   CREATION DATE: October, 2024
#   Author: David W. McDonald
#
#   The parts of the web application that handle interacting with the LLM
#
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
import sys, os, datetime, hashlib, json, copy
#
from rebert._prototype_5_.web.config import *
from rebert._prototype_5_.web.prompts import *
from rebert._prototype_5_.web.utilities import *
#
#
#   This comes from the rebert class library and manages API keys
#   You should use it to store your OpenAI API key locally, so your
#   key is not stored as a constant in the code.
from rebert.classes.data.KeyManager import KeyManager
#
#   This class encapsulates the OpenAI chat completion API. It is
#   a 'souped up' version of the calls that were being made to
#   the requests library in the prior prototypes. This Chat class
#   will help with some error handling and simplify how we make
#   API calls.
from rebert.classes.OpenAI.Chat import Chat
#
#   These two classes are data structures that help construct and
#   manage the chat request body. As our requests get more complex
#   we will want a way to manage them.
from rebert.classes.OpenAI.payload.ChatMessage import ChatMessage
from rebert.classes.OpenAI.payload.ChatRequestPayload import ChatRequestPayload
#
#
#

MODULE_LLM_DEBUG = False

if not MODULE_DEBUG_OVERRIDE:
    MODULE_LLM_DEBUG = GLOBAL_DEBUG


##############
#
#   OpenAI - LLM
#
##############
#
#   The code needs to maintain the status of the chat. This status 
#   will include parameters that tell the model how it should respond
#   as well as all of the user questions and the responses.
#
def new_root_context(movie_data_str=""):
    chat_context = ChatRequestPayload()
    sprompt = ROOT_CONTEXT_PROMPT.format(movie_data_str=movie_data_str)
    
    system_turn = ChatMessage()
    system_turn.setRole("system")
    system_turn.setContent(sprompt)
    
    chat_context.addMessage(system_turn)
    return chat_context
#
#
def new_discussion_context(movie_title="", reviews_str=""):
    chat_context = ChatRequestPayload()
    sprompt = MOVIE_CONTEXT_PROMPT.format(movie_title=movie_title,
                                          movie_review_str=reviews_str)
    system_turn = ChatMessage()
    system_turn.setRole("system")
    system_turn.setContent(sprompt)
    
    chat_context.addMessage(system_turn)
    return chat_context
#
#
#   Making a request is about modifying the growing chat_context
#   setting up the HTTP request URL and request headers, and making
#   the request.
def make_chat_request(chat_context=None, chat_key=""):
    #   If there is no chat context, raise an error
    if not chat_context:
        raise Exception("No chat_context has been supplied")
    
    chat_api = Chat()
    chat_api.setBearerToken(chat_key)
    #
    #   Set configuration values
    used_pres_penalty = False
    try:
        chat_context.setModel(REBERT_LLM_MODEL)
    except NameError as ex:
        print_server_log(f"There must be a model to make a request!","make_chat_request()",
                        MODULE_LLM_DEBUG)
        print_server_log(f"Caught exception","make_chat_request()",MODULE_LLM_DEBUG)
        print_server_log(f"{e}","make_chat_request()",MODULE_LLM_DEBUG)
        raise
    
    try:
        chat_context.setTemperature(REBERT_LLM_TEMPERATURE)
    except NameError as e:
        print_server_log(f"Using default LLM temperature","make_chat_request()",
                        MODULE_LLM_DEBUG)
        #print_server_log(f"Caught exception","make_chat_request()",MODULE_LLM_DEBUG)
        #print_server_log(f"{e}","make_chat_request()",MODULE_LLM_DEBUG)
    
    try:
        chat_context.setPresencePenalty(REBERT_LLM_PRES_PENALTY)
        used_pres_penalty = True
    except NameError as e:
        print_server_log(f"Using default LLM presence_penalty","make_chat_request()",
                        MODULE_LLM_DEBUG)
        #print_server_log(f"Caught exception","make_chat_request()",MODULE_LLM_DEBUG)
        #print_server_log(f"{e}","make_chat_request()",MODULE_LLM_DEBUG)
    
    if not used_pres_penalty:
        try:
            chat_context.setFrequencyPenalty(REBERT_LLM_FREQ_PENALTY)
        except NameError as e:
            print_server_log(f"Using default LLM frequency_penalty","make_chat_request()",
                            MODULE_LLM_DEBUG)
            #print_server_log(f"Caught exception","make_chat_request()",MODULE_LLM_DEBUG)
            #print_server_log(f"{e}","make_chat_request()",MODULE_LLM_DEBUG)
    
    chat_api.setRequestPayload(chat_context.json(clean=True))
    chat_api.queueRequest()
    chat_api.makeRequest()
    response = chat_api.nextResponse()
    resp_dict = response.json()
    
    #   There is a lot in the response - just extract the message
    assistant_turn = ChatMessage()
    message = resp_dict['choices'][0]['message']
    assistant_turn.setRole("assistant")
    assistant_turn.setMessage(message)
    
    return assistant_turn
#
#   Generate a string of KEY:value items for each movie
#   Keys should correspond to the keys defined in the
#   ROOT_CONTEXT_PROMPT
#
#   This prototype adds the SYNOPSIS key and inserts that
#   value when creating the prompt data string.
def create_movie_info_str(movie_list=[]):
    movie_info_str = ""
    for movie in movie_list:
        data = f"\tMOVIE TITLE: {movie['title']}\n"
        note = movie['notes'].partition(',')[0]
        data = data + f"\tRELEASE TYPE: {note}\n"
        data = data + f"\tOPENING DATE: {movie['opening_date_str']}\n"
        data = data + f"\tSYNOPSIS: {movie['synopsis']}\n"
        if not movie_info_str:
            movie_info_str = data
        else:
            movie_info_str = movie_info_str + "\n" + data
    return movie_info_str

def create_movie_review_str(review_list=[]):
    movie_review_str = str()
    for review in review_list:
        data = f"REVIEW OF: {review['title']}\n"
        data = data + f"REVIEW AUTHOR: {review['author']}\n"
        data = data + f"REVIEW TEXT: {review['review']}\n"
        data = data + f"REVIEW SUMMARY SCORE: {review['rating_str']}\n"
        data = data + f"REVIEW SOURCE: {review['source']}\n"
        if not movie_review_str:
            movie_review_str = data
        else:
            movie_review_str = movie_review_str + "\n" + data
    return movie_review_str


def new_user_turn(user_text=""):
    user_turn = ChatMessage()
    user_turn.setRole("user")
    user_turn.setContent(user_text)
    return user_turn

def restore_chat_context(session_state=None):
    chat_context = ChatRequestPayload()
    chat_turns = session_state['chat_turns'][session_state['active_branch']]
    for turn in chat_turns:
        chat_message = ChatMessage()
        chat_message.setMessage(turn)
        chat_context.addMessage(chat_message)
    return chat_context
#


