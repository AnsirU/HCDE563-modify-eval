#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: serve_main_page.py
#   REVISION: June, 2024
#   CREATION DATE: June, 2024
#   Author: David W. McDonald
#
#   Implements server main page generation
#
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
import sys, os, datetime, hashlib, json, copy
#
from flask import render_template
from markupsafe import escape
#
from rebert._prototype_4_.web.config import *
from rebert._prototype_4_.web.prompts import *
from rebert._prototype_4_.web.llm import *
from rebert._prototype_4_.web.utilities import *
#
#  
#
MODULE_MAIN_PAGE_DEBUG = False
#
if not MODULE_DEBUG_OVERRIDE:
    MODULE_MAIN_PAGE_DEBUG = GLOBAL_DEBUG
#
#
##############
#
#   MAIN PAGE GENERATION
#
##############
#
def serve_home_page(request, server_state):
    session_id = generate_session_id(request)
    page = render_template("welcome.html",
                            session_id = session_id)
    print_server_log(f"Session ID: {session_id}",
                    "serve_home_page()",
                    MODULE_MAIN_PAGE_DEBUG)
    return page


##############
#
#   ASK REBERT PAGE GENERATION
#
##############
#
def serve_ask_rebert_response(request, server_state):
    #
    #   Collect the fields from the form
    try:
        session_id = escape(request.form["session_id"])
        rebert_text = escape(request.form["ask_output"])
        question = escape(request.form["question_text"])
    except Exception as e:
        print_server_log(f"Caught an exception when reading form variables:",
                        "serve_ask_rebert_response()",
                        MODULE_MAIN_PAGE_DEBUG)
        print_server_log(f"{e}","generate_rebert_response()",
                        MODULE_MAIN_PAGE_DEBUG)
    #
    #   Attempt to load a state file for this session
    session_state = load_session_state(session_id)
    #
    #   If the user didn't ask a question, return the same page
    if not question:
        page = render_template("welcome.html",
                                session_id = session_id,
                                response_rows = 5,
                                rebert_response = rebert_text)
        return page
    #
    #
    if not session_state:
        session_state = REBERT_SESSION_STATE_TEMPLATE.copy()
        session_state['session_id'] = session_id
        session_state['movie_data'] = server_state['movie_data']
        #print_server_log(f"Got {len(session_state['openings'])} openings!",
        #                "serve_ask_rebert_response()",
        #                MODULE_MAIN_PAGE_DEBUG)
    #
    #   Need to fill this in before generating a response
    chat_contex = None
    #
    #   Check where we are with the session chat
    if not session_state['chat_turns']:
        #   Have not yet started answering questions about movies
        movie_info_str = create_movie_info_str(session_state['movie_data']['openings'])
        #
        #   Create the chat context, now including the new
        #   release information that we just retrieved
        chat_context = new_root_context(movie_info_str)
        #   We just created the context - first message is the system
        #   message - we want that for the chat_turns list
        system_turn = chat_context.getLastMessage()
        session_state['active_branch'] = 'root'
        session_state['chat_turns'] = dict()
        session_state['chat_turns'][session_state['active_branch']]  = list()
        session_state['chat_turns'][session_state['active_branch']].append(system_turn)
    else:
        #   Need to reconstitute the chat context
        chat_context = restore_chat_context(session_state)
    #
    #   Have a session_state that is new - or from an existing
    #   The question that was asked by the user in the web form
    user_turn = new_user_turn(question)
    session_state['chat_turns'][session_state['active_branch']].append(user_turn)
    chat_context.addMessage(user_turn)
    #
    #   Make the request of the remote LLM
    assistant_turn = make_chat_request(chat_context,server_state['OPENAI_KEY'])
    #
    #   Check to see if this is a branching response
    if is_branching_response(assistant_turn):
        #   Remove the user turn, because it is part of the 'branch'
        session_state['chat_turns'][session_state['active_branch']] =\
            session_state['chat_turns'][session_state['active_branch']][:-1]
        assistant_turn = follow_branching_context(user_turn, assistant_turn, 
                                                  session_state, server_state)
    elif is_returning_response(assistant_turn):
        #   Remove the user turn, because it is part of the 'root'
        session_state['chat_turns'][session_state['active_branch']] =\
            session_state['chat_turns'][session_state['active_branch']][:-1]
        assistant_turn = restore_root_context(user_turn, assistant_turn, 
                                              session_state, server_state)
    #
    #   Whatever the assistant said, save that
    session_state['chat_turns'][session_state['active_branch']].append(assistant_turn)
    #
    #
    save_session_state(session_state)

    rebert_response = format_chat_transcript(session_state)
    response_rows = estimate_response_textarea_size(rebert_response)

    page = render_template("welcome.html",
                            session_id = session_id,
                            response_rows = response_rows,
                            rebert_response = rebert_response)
    return page



def _turn_role_content(turn):
    if isinstance(turn, dict):
        return turn.get("role"), (turn.get("content") or "")
    role = turn["role"]
    try:
        raw = turn["content"]
    except (KeyError, TypeError):
        raw = None
    return role, raw if raw else ""


def format_chat_transcript(session_state=None):
    """
    Build display text for the active branch: all user questions and assistant
    replies (system prompts omitted).
    """
    if not session_state or not session_state.get("chat_turns"):
        return ""
    branch = session_state.get("active_branch") or "root"
    turns = session_state["chat_turns"].get(branch)
    if not turns:
        return ""
    sections = []
    for turn in turns:
        role, content = _turn_role_content(turn)
        if role == "system":
            continue
        if role == "user":
            sections.append(f"You:\n{content}")
        elif role == "assistant":
            sections.append(f"Rebert:\n{content}")
    return "\n\n".join(sections).strip()


def estimate_response_textarea_size(rebert_response=""):
    response_rows = "5"
    rr_len = len(rebert_response)    
    if rr_len < 525: response_rows = "5"
    elif rr_len < 1025: response_rows = "8"
    elif rr_len < 1350: response_rows = "12"
    else: response_rows = "15"
    #print_server_log(f"rebert_response length is {rr_len}, setting rows to {response_rows}",
    #                 "estimate_response_textarea_size()",
    #                 MODULE_MAIN_PAGE_DEBUG)
    return response_rows



def is_branching_response(assistant_turn=None):
    title = ""
    response = assistant_turn['content']
    if "BRANCH_TO" in response:
        title = response.partition("BRANCH_TO")[2]
        title = title.partition("CONTEXT")[0]
        title = title.replace('"','').strip()
        print_server_log(f"Found branching response to: '{title}'",
                         "is_branching_response()",
                         MODULE_MAIN_PAGE_DEBUG)
    return title



def is_returning_response(assistant_turn=None):
    context = ""
    response = assistant_turn['content']
    if "RETURN_TO" in response:
        context = response.partition("RETURN_TO")[2]
        context = context.partition("CONTEXT")[0]
        context = context.strip()
        print_server_log(f"Found return to: 'root'",
                         "is_returning_response()",
                         MODULE_MAIN_PAGE_DEBUG)
    return context



def follow_branching_context(user_turn=None, assistant_turn=None, 
                             session_state=None, server_state=None):
    #
    movie_list_str = str()
    count = 1
    for title in session_state['movie_data']['title_list']:
        #movie_list_str = movie_list_str + f"\tMOVIE TITLE: {title}\n"
        movie_list_str = movie_list_str + f"\t{count}: {title}\n"
        count += 1
    # use this to get the movie title
    movie_title = is_branching_response(assistant_turn)
    title_lower = movie_title.lower()
    review_list = list()
    if title_lower in session_state['movie_data']['reviews']:
        review_list = session_state['movie_data']['reviews'][title_lower]
    #
    if review_list:
        movie_review_str = create_movie_review_str(review_list)
        print_server_log(f"Using {len(review_list)} reviews for '{title_lower}'",
                         "follow_branching_context()",
                         MODULE_MAIN_PAGE_DEBUG)
    else:
        movie_review_str = NO_REVIEWS_AVAILABLE.format(title=movie_title)
        print_server_log(f"Have no reviews for '{title_lower}'",
                         "follow_branching_context()",
                         MODULE_MAIN_PAGE_DEBUG)
    #
    #   If we come back to an existing branch context, restore that
    if title_lower in session_state['chat_turns']:
        if title_lower != session_state['active_branch']:
            print_server_log(f"Switching to context: '{title_lower}'",
                             "follow_branching_context()",
                             MODULE_MAIN_PAGE_DEBUG)
        session_state['active_branch'] = title_lower
        #   Need to reconstitute the chat context
        chat_context = restore_chat_context(session_state)
        session_state['chat_turns'][session_state['active_branch']].append(user_turn)
        chat_context.addMessage(user_turn)
    else:
        print_server_log(f"New branching context: '{title_lower}'",
                         "follow_branching_context()",
                         MODULE_MAIN_PAGE_DEBUG)
        #
        #   This is a new branching context.
        #   It needs the title, the list of known movies and possibly the reviews
        chat_context = new_branch_context(movie_title, movie_list_str, movie_review_str)
        #   We just created the context - first message is the system
        #   message - we want that for the chat_turns list
        system_turn = chat_context.getLastMessage()
        session_state['active_branch'] = title_lower
        session_state['chat_turns'][session_state['active_branch']]  = list()
        session_state['chat_turns'][session_state['active_branch']].append(system_turn)
        #
        #   Make sure that we ask a generic question specific to the movie context
        #   that we just created. A hack for the discussion context switch
        user_turn['content'] = f"Tell me more about the movie '{movie_title}'"
        session_state['chat_turns'][session_state['active_branch']].append(user_turn)
        chat_context.addMessage(user_turn)
    #
    #   Make the request of the remote LLM
    assistant_turn = make_chat_request(chat_context, server_state['OPENAI_KEY'])
    #
    #   If we return immediately, update that and create a generic response
    if is_returning_response(assistant_turn):
        response = NO_REVIEWS_RESPONSE.format(title=movie_title)
        assistant_turn['content'] = response
        session_state['chat_turns'][session_state['active_branch']].append(assistant_turn)
        session_state['active_branch'] = 'root'
    return assistant_turn



def restore_root_context(user_turn=None, assistant_turn=None, 
                             session_state=None, server_state=None):
    print_server_log("Returning to 'root' context",
                     "restore_root_context()",
                     MODULE_MAIN_PAGE_DEBUG)
    #
    session_state['active_branch'] = 'root'
    chat_context = restore_chat_context(session_state)
    session_state['chat_turns'][session_state['active_branch']].append(user_turn)
    chat_context.addMessage(user_turn)
    assistant_turn = make_chat_request(chat_context, server_state['OPENAI_KEY'])
    return assistant_turn

