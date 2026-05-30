#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: serve_main_page.py
#   REVISION: June, 2024
#   CREATION DATE: June, 2024
#   Author: David W. McDonald
#
#   First cut web prototype
#
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
##
#
import sys, os, datetime, hashlib, random, json, copy

from flask import render_template
from markupsafe import escape
#
#
from rebert._prototype_7_.web.config import *
from rebert._prototype_7_.web.prompts import *
from rebert._prototype_7_.web.llm import *
from rebert._prototype_7_.web.utilities import *
#
#  
#
MODULE_MAIN_PAGE_DEBUG = True
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
    #
    #   This is a hit on the main page - create a session for this user
    session_state = REBERT_SESSION_STATE_TEMPLATE.copy()
    session_state['session_id'] = generate_session_id(request)
    session_state['movie_data'] = server_state['movie_data']
    #
    #   Set up a way to track the current state of the UI - what comes
    #   in the request, and some of what we need to send back
    ui_state = REBERT_MAINPAGE_UI_STATE_TEMPLATE.copy()
    ui_state['session_id'] = session_state['session_id']
    #
    #   Pick the six movies that will be shown on the main page
    highlights = pick_movie_highlights(6,session_state)
    session_state['highlights'] = highlights
    print_server_log(f"Highlights: {json.dumps(highlights,indent=4)}",
                    "serve_home_page()",
                    MODULE_MAIN_PAGE_DEBUG)
    #
    #   Need to render the poster sections
    highlights_list = list()
    item = 1
    for title in highlights:
        next_highlight = compose_poster_item(item,title,session_state)
        highlights_list.append(next_highlight)
        #print_server_log(f"Formatted poster/column: {item}",
        #                "serve_home_page()",
        #                MODULE_MAIN_PAGE_DEBUG)
        item += 1
    #
    #
    session_state['highlights'] = highlights_list
    ui_state['discuss_content'] = get_discussion_content_list(session_state)
    #
    #   Iniitalize the list - this relies on the specific highlights
    rec_flags = init_recommendation_list(session_state)
    session_state['rec_flags'] = rec_flags
    #
    #   Need to pick one of the ephemeral question starts at random
    session_state['ephem_status'] = REBERT_EPHEM_Q_TEMPLATE.copy()
    state = session_state['ephem_status']['state']
    if state:
        ui_state['ephem_p_text'] = random.sample(REBERT_EPHEM_Q1_OPTIONS,1)[0]
        session_state['ephem_status'][str(state)]['prompt'] = ui_state['ephem_p_text']
    else:
        #   Empty emphem_status state - means feature is turned off here
        ui_state['ephem_p_text'] = ""
        ui_state['ephem_s_state'] = 0
        ui_state['ephem_q_state'] = 0
    
    #   Save the session state 
    save_session_state(session_state)
    #
    #   Generate the page
    page = render_template("mainpage.html",
                            state = ui_state,
                            session = session_state)
    print_server_log(f"Session ID: {ui_state['session_id']}",
                    "serve_home_page()",
                    MODULE_MAIN_PAGE_DEBUG)
    return page



def init_recommendation_list(session_state):
    rec_list = list()
    #   This initialization assumes we have six movies 
    #   if fewer, then probably not a problem, more, then problem
    for i in range(0,6):
        recitem = REBERT_REC_FLAGS_TEMPLATE.copy()
        recitem['column'] = str(i+1)
        recitem['flag'] = ""
        recitem['text'] = ""
        rec_list.append(recitem)

    if session_state['highlights']:
        for movie in session_state['highlights']:
            column = int(movie['column'])-1
            title_lower = movie['title'].lower()
            rec_list[column]['title'] = movie['title']
            count_over_35 = 0
            highest_review_score = 0.0
            reviews = list()
            if title_lower in session_state['movie_data']['reviews']:
                reviews = session_state['movie_data']['reviews'][title_lower]
                for review in reviews:
                    #   skip all the reviews that don't have ratings
                    if not review['rating']: continue
                    #   track if the ratings are generally more positive
                    if review['rating'] > 3.5:
                        count_over_35 += 1
                    #   keep track of the highest rating 
                    if review['rating'] > highest_review_score:
                        highest_review_score = review['rating']
                        rec_list[column]['rating'] = review['rating']
                        rec_list[column]['author'] = review['author']
                        rec_list[column]['source'] = review['source']
                rec_list[column]['over_3.5'] = count_over_35
    else:
        print_server_log(f"Session 'highlights' is empty. Initialize 'highlights' before call.",
                         "init_recommendation_list()",
                         MODULE_MAIN_PAGE_DEBUG)

    return rec_list



def pick_movie_highlights(count=6, session_state=None):
    movie_list = list()
    highlights = list()
    title_keys = list(session_state['movie_data']['reviews'].keys())
    for title in title_keys:
        reviews = session_state['movie_data']['reviews'][title]
        #   Try to make sure all of 'highlight' movies have a review
        if len(reviews) > 0:
            movie_list.append(reviews[0]['title'])
    #
    #   If we have to few highlights return them all
    if len(movie_list) < count:
        highlights = movie_list
    else:
        highlights = random.sample(movie_list, k=count)
    return highlights



def compose_poster_item(column=1, title="", session_state=None):
    title_lower = title.lower()
    poster_item = REBERT_HIGHLIGHT_TEMPLATE.copy()
    poster_item['column'] = str(column)
    poster_item['title'] = title
    info = session_state['movie_data']['meta'][title_lower]
    poster_item['synop'] = info['overview']
    poster_item['poster'] = info['poster_path']
    poster_item['release'] = info['release_date']
    return poster_item



##############
#
#   ASK REBERT PAGE GENERATION
#
##############
#
def serve_ask_rebert_response(request, server_state):
    #
    #   Collect the data from the form submission
    ui_state = extract_main_page_form_data(request)
    try:
        discuss_slot = int(ui_state['discuss_state'])-1
    except Exception as e:
        print_server_log(f"Could not convert '{ui_state['discuss_state']}' to a slot number.",
                        "generate_rebert_response()",
                        MODULE_MAIN_PAGE_DEBUG)
        raise
    #
    #   Attempt to load a state file for this session
    session_state = load_session_state(ui_state['session_id'])
    #
    #   Pull some session variables that we might need - some came from the POST form
    rec_flags = session_state['rec_flags']
    highlight = session_state['highlights'][(discuss_slot)]
    title = highlight['title']
    title_lower = highlight['title'].lower()
    #
    #   Will need to fill this in before generating the resonse
    chat_context = None
    #
    #   If the user didn't ask a question, return mostly the same page
    #   The question needs to have at least 3 'words' and be at least 
    #   10 characters long - that's still pretty short
    question_words = ui_state['user_question'].split()
    if (len(question_words) < 3) or (len(ui_state['user_question']) < 10):
        ui_state['discuss_content'] = get_discussion_content_list(session_state)
        if ui_state['user_question']:
            ui_state['rebert_response'] = f"I'm not sure how to answer: \"{ui_state['user_question']}\""
            ui_state['discuss_content'][discuss_slot]['last_turn'] = ui_state['rebert_response']
        page = render_template("mainpage.html",
                                state = ui_state,
                                session = session_state)
        return page
    #
    #   We got here, so the user asked a question
    user_turn = new_user_turn(ui_state['user_question'])
    #
    #   Make sure there is a 'root' context for a chat - the interface tries to keep
    #   a discussion on the topic of a specific movie - but the user might go more generic
    if (not session_state['chat_turns']) or ('root' not in session_state['chat_turns']):
        initialize_root_chat_context(session_state)
    #
    #   If we come back to an existing branch context, restore that
    if (session_state['chat_turns'] is not None) and (title_lower in session_state['chat_turns']):
        session_state['active_branch'] = title_lower
        #   Need to reconstitute the chat context
        chat_context = restore_chat_context(session_state)
        session_state['chat_turns'][session_state['active_branch']].append(user_turn)
        chat_context.addMessage(user_turn)
    else:
        review_list = []
        if title_lower in session_state['movie_data']['reviews']:
            review_list = session_state['movie_data']['reviews'][title_lower]
        if review_list:
            movie_review_str = create_movie_review_str(review_list)
        else:
            movie_review_str = NO_REVIEWS_AVAILABLE.format(title=title)
        #   This is a new discussion context
        chat_context = new_discussion_context(title,movie_review_str)
        #   We just created the context - first message is the system
        #   message - we want that for the chat_turns list
        system_turn = chat_context.getLastMessage()
        session_state['active_branch'] = title_lower
        if not session_state['chat_turns']:
            session_state['chat_turns'] = dict()
        session_state['chat_turns'][session_state['active_branch']] = list()
        session_state['chat_turns'][session_state['active_branch']].append(system_turn)
        #
        session_state['chat_turns'][session_state['active_branch']].append(user_turn)
        chat_context.addMessage(user_turn)
    #
    #   Have a session_state that is new - or from an existing chat
    #   The question that was asked by the user in the web form
    #
    #   Make the request of the remote LLM
    assistant_turn = make_chat_request(chat_context, server_state['OPENAI_KEY'])
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
    #   Put the response text into the UI state
    ui_state['rebert_response'] = assistant_turn['content']
    #   Save the session state 
    save_session_state(session_state)
    #   Set the last discussion turns
    ui_state['discuss_content'] = get_discussion_content_list(session_state)
    #   Maintain the state of the ephemeral questions
    state = session_state['ephem_status']['state']
    if state:
        ui_state['ephem_p_text'] = session_state['ephem_status'][str(state)]['prompt']
    else:
        #   Empty emphem_status state - means we're done with ephem Q&A
        ui_state['ephem_p_text'] = ""
        ui_state['ephem_s_state'] = 0
        ui_state['ephem_q_state'] = 0
    #
    #   Quick guess of how large the <textarea> could be
    ui_state = estimate_response_textarea_size(ui_state)
    
    page = render_template("mainpage.html",
                            state = ui_state,
                            session = session_state)
    return page


def estimate_response_textarea_size(ui_state=None):
    #   Calculate the number of characters in the response
    rr_len = len(ui_state['rebert_response'])
    #   Calculate the number of rows in the response
    rr_rows = len(ui_state['rebert_response'].split('\n'))
    
    if (rr_len < 525) and (rr_rows <= 5): 
        ui_state['response_rows'] = "5"
    elif (rr_len < 1025) and (rr_rows <= 8): 
        ui_state['response_rows'] = "8"
    elif (rr_len < 1350) and (rr_rows <= 12): 
        ui_state['response_rows'] = "12"
    else: 
        ui_state['response_rows'] = "15"
    #print_server_log(f"rebert_response length is {rr_len}, setting rows to {response_rows}",
    #                 "estimate_response_textarea_size()",
    #                 MODULE_MAIN_PAGE_DEBUG)
    return ui_state


#
#   This creates a 'root' context for a chat - in case the movie context breaks
#   and the discussion of a specific movie becomes more generic.
#
def initialize_root_chat_context(session_state=None):
    #   Have not yet started answering questions about movies
    movie_info_str = create_movie_info_str(session_state['movie_data']['openings'])
    #   Create a 'root' context, including the new release information
    chat_context = new_root_context(movie_info_str)
    #   In that chat context, the first message is the system message
    #   we want that for the chat_turns list
    system_turn = chat_context.getLastMessage()
    if not session_state['chat_turns']:
        session_state['chat_turns'] = dict()
    session_state['chat_turns']['root']  = list()
    session_state['chat_turns']['root'].append(system_turn)
    return    



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
    review_list = []
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



def get_discussion_content_list(session_state=None):
    discussion_contents = list()
    for i in range(0,6):
        discussing = REBERT_DISCUSSION_TEMPLATE.copy()
        discussing['column'] = str(i+1)
        discussing['last_turn'] = INIT_DISCUSSION_CONVERSATION
        discussion_contents.append(discussing)
    if session_state['chat_turns']:
        for movie in session_state['highlights']:
            column = int(movie['column'])-1
            title_lower = movie['title'].lower()
            if title_lower in session_state['chat_turns']:
                last_turn = session_state['chat_turns'][title_lower][-1]
                discussion_contents[column]['last_turn'] = last_turn['content']
    return discussion_contents


