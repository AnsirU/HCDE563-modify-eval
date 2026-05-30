#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: serve_ephem_rec.py
#   REVISION: February, 2025
#   CREATION DATE: October, 2024
#   Author: David W. McDonald
#
#   Server code to generate ephemeral recommendations. Question generation by the LLM
#   and recommendations based on the user's answers to the questions.
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
MODULE_EPHEM_REC_DEBUG = True
#
if not MODULE_DEBUG_OVERRIDE:
    MODULE_EPHEM_REC_DEBUG = GLOBAL_DEBUG
#
#
#
#
##############
#
#   EPHEMERAL RECOMMENDATION PAGE GENERATION
#
##############
#
#
#
def serve_next_ephem_question(request, server_state):
    #   Collect the data from the form submission
    ui_state = extract_main_page_form_data(request)
    #   Attempt to load a state file for this session
    session_state = load_session_state(ui_state['session_id'])
    #
    #   Set the last discussion turns
    ui_state['discuss_content'] = get_discussion_content_list(session_state)
    #
    #   Return the basic page when done with Q&A
    state = session_state['ephem_status']['state']
    if not state:
        #   Empty emphem_status state - means we're done with ephem Q&A
        ui_state['ephem_p_text'] = ""
        ui_state['ephem_s_state'] = 0
        ui_state['ephem_q_state'] = 0
        ui_state['ephem_q_last'] = 1
        page = render_template("mainpage.html",
                                state = ui_state,
                                session = session_state)
        print_server_log(f"Q&A is done!",
                        "serve_next_ephem_question()",
                        MODULE_EPHEM_REC_DEBUG)
        return page
    #
    #   Try to get more from the user when their response is really short
    answer_words = ui_state['ephem_answer'].split()
    if (len(answer_words) < 3) or (len(ui_state['ephem_answer']) < 10):
        old_prompt = session_state['ephem_status'][str(state)]['prompt']
        retry = random.sample(REBERT_EPHEM_RETRY_OPTIONS,1)[0]
        new_prompt = f"{retry} ... {old_prompt}"
        ui_state['ephem_p_text'] = new_prompt
        page = render_template("mainpage.html",
                                state = ui_state,
                                session = session_state)
        print_server_log(f"Short response for question {state}, trying to get more.",
                        "serve_next_ephem_question()",
                        MODULE_EPHEM_REC_DEBUG)
        return page
    #
    #   The response must have been something, so save that response and move to
    #   the next Q&A prompt pair
    session_state['ephem_status'][str(state)]['response'] = ui_state['ephem_answer']
    state += 1
    session_state['ephem_status']['state'] = state
    if (state == 3) or (state == 0):
        ui_state['ephem_q_last'] = 1
    elif state > 3:
        #   This code is here as a - just in case - this should not execute
        #   The UI should show a button that calls serve_ephemeral_rec()
        session_state['ephem_status']['state'] = 0
        ui_state['ephem_p_text'] = ""
        ui_state['ephem_s_state'] = 0
        ui_state['ephem_q_state'] = 0
        ui_state['ephem_q_last'] = 1
        page = render_template("mainpage.html",
                                state = ui_state,
                                session = session_state)
        print_server_log(f"Q&A is done!",
                        "serve_next_ephem_question()",
                        MODULE_EPHEM_REC_DEBUG)
        return page
    #
    #   Get a question from the LLM and save that
    qna_str = create_ephem_qna_str(session_state)
    assistant_turn = qna_question_request(session_state, qna_str, server_state['OPENAI_KEY'])
    session_state['ephem_status'][str(state)]['prompt'] = assistant_turn['content']
    ui_state['ephem_p_text'] = assistant_turn['content']
    ui_state['ephem_s_state'] = 0
    ui_state['ephem_q_state'] = 1
    #   Save the session state 
    save_session_state(session_state)
    #
    page = render_template("mainpage.html",
                            state = ui_state,
                            session = session_state)
    return page


#
#
#
def serve_ephem_recommendation(request, server_state):
    #   Collect the data from the form submission
    ui_state = extract_main_page_form_data(request)
    #   Attempt to load a state file for this session
    session_state = load_session_state(ui_state['session_id'])
    #
    #   Try to get more from the user when their response is really short
    state = session_state['ephem_status']['state']
    answer_words = ui_state['ephem_answer'].split()
    if (len(answer_words) < 3) or (len(ui_state['ephem_answer']) < 10):
        old_prompt = session_state['ephem_status'][str(state)]['prompt']
        retry = random.sample(REBERT_EPHEM_RETRY_OPTIONS,1)[0]
        new_prompt = f"{retry} ... {old_prompt}"
        ui_state['ephem_p_text'] = new_prompt
        if (state == 3) or (state == 0):
            ui_state['ephem_q_last'] = 1
        page = render_template("mainpage.html",
                                state = ui_state,
                                session = session_state)
        print_server_log(f"Short response for question {state}, trying to get more.",
                        "serve_ephem_recommendation()",
                        MODULE_EPHEM_REC_DEBUG)
        return page
    #
    #   Save the response and update the state count
    session_state['ephem_status'][str(state)]['response'] = ui_state['ephem_answer']
    state += 1
    session_state['ephem_status']['state'] = state
    print_server_log(f"User completed Q&A",
                    "serve_ephem_recommendation()",
                    MODULE_EPHEM_REC_DEBUG)
    if (state == 3) or (state == 0):
        ui_state['ephem_q_last'] = 1
    elif state > 3:
        #   This sets the last question - below we make the recommendation
        session_state['ephem_status']['state'] = 0
        ui_state['ephem_p_text'] = ""
        ui_state['ephem_s_state'] = 0
        ui_state['ephem_q_state'] = 0
        ui_state['ephem_q_last'] = 1
    #
    #
    print_server_log(f"Starting ephemeral recommendation request.",
                    "serve_ephem_recommendation()",
                    MODULE_EPHEM_REC_DEBUG)
    start_time = datetime.datetime.now()
    session_state = make_ephem_rec_request(session_state, server_state['OPENAI_KEY'])
    finish_time = datetime.datetime.now()
    runtime = finish_time-start_time
    print_server_log(f"Ephemeral recommendation elapsed time: {runtime}",
                    "serve_ephem_recommendation()",
                    MODULE_EPHEM_REC_DEBUG)
    #
    #   Need to update the flag images based on the recommendation results
    rec_flags = update_recommendation_flags(session_state)
    session_state['rec_flags'] = rec_flags
    #
    #   Set the last discussion turns - with the data from the recommendations
    ui_state['discuss_content'] = get_discussion_content_list(session_state)
    #   Save the session
    save_session_state(session_state)
    #
    page = render_template("mainpage.html",
                            state = ui_state,
                            session = session_state)
    return page



def get_discussion_content_list(session_state):
    discussion_contents = list()
    for i in range(0,6):
        discussing = REBERT_DISCUSSION_TEMPLATE.copy()
        discussing['column'] = str(i+1)
        discussing['last_turn'] = INIT_DISCUSSION_CONVERSATION
        if session_state['rec_flags'] and session_state['rec_flags'][i]['rebert_rationale']:
            rating = session_state['rec_flags'][i]['rebert_rating'].lower()
            turn = f"Based on the answers you gave to my mini interview, I predict this movie is {rating} with your interests.\n\n"
            turn = turn + session_state['rec_flags'][i]['rebert_rationale']+"\n\n"
            turn = turn + "What else would you like to know about this movie?" 
            discussing['last_turn'] = turn
            #title = session_state['rec_flags'][i]['title']
            #print_server_log(f"Set 'rebert_rationale' as 'last_turn' for movie [{discussing['column']}] '{title}'.",
            #                  "get_discussion_content_list()",
            #                   MODULE_EPHEM_REC_DEBUG)
        discussion_contents.append(discussing)
    #
    #
    if session_state['chat_turns']:
        for movie in session_state['highlights']:
            column = int(movie['column'])-1
            title_lower = movie['title'].lower()
            if title_lower in session_state['chat_turns']:
                last_turn = session_state['chat_turns'][title_lower][-1]
                discussion_contents[column]['last_turn'] = last_turn['content']
                print_server_log(f"Replaced 'rebert_rationale' with last turn for '{title_lower}'.",
                                  "get_discussion_content_list()",
                                  MODULE_EPHEM_REC_DEBUG)
            else:
                print_server_log(f"Kept 'rebert_rationale' as last turn for '{title_lower}'.",
                                  "get_discussion_content_list()",
                                  MODULE_EPHEM_REC_DEBUG)
    return discussion_contents



def update_recommendation_flags(session_state):
    rec_list = session_state['rec_flags']
    if session_state['highlights'] and rec_list:
        for movie in session_state['highlights']:
            column = int(movie['column'])-1
            title_lower = movie['title'].lower()
            #
            #   Save the rating and rationale strings with the movie
            rebert_rating = movie['rebert_rating'].lower()
            rec_list[column]['rebert_rating'] = movie['rebert_rating']
            rec_list[column]['rebert_rationale'] = movie['rebert_rationale']
            #
            #   Now, assign a recommendation flag
            if 'highly' in rebert_rating:
                #   Rebert thinks there is a strong match, check the best review
                if rec_list[column]['rating'] >= 4.0:
                    #   High match, high score - highly recommended
                    rec_list[column]['flag'] = "rec-highly-small.png"
                    rec_list[column]['text'] = "recommendation: highly recommended"
                    rec_list[column]['rebert_rationale'] = rec_list[column]['rebert_rationale'] +\
                    " Additionally, this movie seems to be getting strong reviews from reviewers."
                elif rec_list[column]['rating'] >= 2.5:
                    #   High match, middling score - suggested
                    rec_list[column]['flag'] = "rec-suggested-small.png"
                    rec_list[column]['text'] = "recommendation: suggested"
                else:
                    #   High match - but generally low scores
                    rec_list[column]['flag'] = "rec-meh-small.png"
                    rec_list[column]['text'] = "recommendation: meh"
                    rec_list[column]['rebert_rationale'] = rec_list[column]['rebert_rationale'] +\
                    " A potential risk with this recommendation is that reviewers seem to dislike this movie."
            elif 'mildly' in rebert_rating:
                #   Rebert thinks there is some match, check the best review
                #   If the best rating is above a middling score, give it a
                #   suggested rating
                if rec_list[column]['rating'] >= 3.5:
                    rec_list[column]['flag'] = "rec-suggested-small.png"
                    rec_list[column]['text'] = "recommendation: suggested"
                else:
                    # Low score, mild match stay silent
                    rec_list[column]['flag'] = ""
                    rec_list[column]['text'] = ""
                    #rec_list[column]['flag'] = "rec-meh-small.png"
                    #rec_list[column]['text'] = "recommendation: meh"
            elif 'unknown' in rebert_rating:
                #   No guess from Rebert, stay silent
                pass
            elif 'hard to' in rebert_rating:
                #   No guess from Rebert, stay silent
                pass
            elif 'not' in rebert_rating:
                #   Rebert says its not a match, give it a big reject 
                #   if it also has a middling or lower score
                if rec_list[column]['rating'] < 3.0:
                    rec_list[column]['flag'] = "rec-not_rec-small.png"
                    rec_list[column]['text'] = "recommendation: thumbs down"
            else:
                pass            
            print_server_log(f"Recommendation for '{title_lower}' is '{rec_list[column]['text']}'",
                             "make_recommendation_picks()",
                             MODULE_EPHEM_REC_DEBUG)
                             
    return rec_list




