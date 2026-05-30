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
##
#
import sys, os, datetime, time, hashlib, json, copy
#
from rebert._prototype_7_.web.config import *
from rebert._prototype_7_.web.prompts import *
from rebert._prototype_7_.web.utilities import *
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

MODULE_LLM_DEBUG = True

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
#   This sets the configuration parameters, based on constants defined in the
#   config.py file. If a constant is undefined, then this will use the model
#   default value.
def configure_model_params(chat_context=None):
    #   If there is no chat context, raise an error
    if not chat_context:
        raise Exception("No chat_context has been supplied")
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
        pass
        #print_server_log(f"Using default LLM temperature","configure_model_params()",
        #                MODULE_LLM_DEBUG)
        #print_server_log(f"Caught exception","configure_model_params()",MODULE_LLM_DEBUG)
        #print_server_log(f"{e}","configure_model_params()",MODULE_LLM_DEBUG)
    
    try:
        chat_context.setMaxTokens(REBERT_LLM_TOKEN_LIMIT)
    except NameError as e:
        pass
        #print_server_log(f"Using default max completion tokens", "configure_model_params()",
        #                MODULE_LLM_DEBUG)
        #print_server_log(f"Caught exception","configure_model_params()",MODULE_LLM_DEBUG)
        #print_server_log(f"{e}","configure_model_params()",MODULE_LLM_DEBUG)
    
    try:
        chat_context.setPresencePenalty(REBERT_LLM_PRES_PENALTY)
        used_pres_penalty = True
    except NameError as e:
        pass
        #print_server_log(f"Using default LLM presence_penalty","configure_model_params()",
        #                MODULE_LLM_DEBUG)
        #print_server_log(f"Caught exception","configure_model_params()",MODULE_LLM_DEBUG)
        #print_server_log(f"{e}","configure_model_params()",MODULE_LLM_DEBUG)

    #
    #   Can only use one of either frequency penalty or presence penalty
    if not used_pres_penalty:
        try:
            chat_context.setFrequencyPenalty(REBERT_LLM_FREQ_PENALTY)
        except NameError as e:
            pass
            #print_server_log(f"Using default LLM frequency_penalty","configure_model_params()",
            #                MODULE_LLM_DEBUG)
            #print_server_log(f"Caught exception","configure_model_params()",MODULE_LLM_DEBUG)
            #print_server_log(f"{e}","configure_model_params()",MODULE_LLM_DEBUG)
    
    return chat_context
#
#
#   Making a request is about modifying the growing chat_context
#   setting up the HTTP request URL and request headers, and making
#   the request.
def make_chat_request(chat_context=None, chat_key=""):
    #   If there is no chat context, raise an error
    if not chat_context:
        print_server_log(f"No chat_context was supplied","make_chat_request()",
                        MODULE_LLM_DEBUG)
        raise Exception("No chat_context has been supplied")
    
    chat_api = Chat()
    chat_api.setBearerToken(chat_key)
    #
    #   Set configuration values
    chat_context = configure_model_params(chat_context)
    #    
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
#
#
#
def new_user_turn(user_text=""):
    user_turn = ChatMessage()
    user_turn.setRole("user")
    user_turn.setContent(user_text)
    return user_turn
#
#
#
def restore_chat_context(session_state=None):
    chat_context = ChatRequestPayload()
    chat_turns = session_state['chat_turns'][session_state['active_branch']]
    for turn in chat_turns:
        chat_message = ChatMessage()
        chat_message.setMessage(turn)
        chat_context.addMessage(chat_message)
    return chat_context
#
#
#
def create_ephem_qna_str(session=None):
    #
    #   Construct the question and answer string, based on what we have from the user
    qna_str = str()
    for i in range(1,4):
        if session['ephem_status'][str(i)]['response']:
            print_server_log(f"Have Q&A pair {i}",
                            "create_ephem_qna_str()",
                            MODULE_LLM_DEBUG)
            qna_str = qna_str + f"QUESTION:\n\t{session['ephem_status'][str(i)]['prompt']}\n"
            qna_str = qna_str + f"ANSWER:\n\t{session['ephem_status'][str(i)]['response']}\n"
    qna_str = qna_str+"\n"
    return qna_str
#
#
#   If session data is provided, then it produces a prompt that includes
#   both movie information and the data from the prior questions.
#
#   If only qna_str is provided, then it only uses the qna_str to make a
#   request for a new question
#
def qna_question_request(session=None, qna_str="", chat_key=""):
    #   Must have a qna_str to make the request
    if not qna_str:
        print_server_log(f"Missing Q&A string!",
                        "qna_question_request()",
                        MODULE_LLM_DEBUG)
        raise Exception(f"Missing Q&A string!")
    
    #
    #   Construct a movie info string that might help the LLM think about a good question
    if session:
        info_str = str()
        highlights = session['highlights']
        for movie in highlights:
            info_str = info_str + f"TITLE:\n\t{movie['title']}\n"
            info_str = info_str + f"SYNOPSIS:\n\t{movie['synop']}\n"
        info_str = info_str+"\n"
        sprompt = EPHEM_QUESTION_SYSTEM_PROMPT2.format(movie_info=info_str,
                                                       ephem_qna_pairs=qna_str)
    else:
        sprompt = EPHEM_QUESTION_SYSTEM_PROMPT1.format(ephem_qna_pairs=qna_str)

    chat_context = ChatRequestPayload()
    
    system_turn = ChatMessage()
    system_turn.setRole("system")
    system_turn.setContent(sprompt)    
    chat_context.addMessage(system_turn)

    user_turn = ChatMessage()
    user_turn.setRole("user")
    user_turn.setContent(EPHEM_QUESTION_PROMPT)
    chat_context.addMessage(user_turn)
    
    chat_api = Chat()
    chat_api.setBearerToken(chat_key)
    #
    #   Set configuration values
    chat_context = configure_model_params(chat_context)
    #    
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



def make_ephem_rec_request(session=None, chat_key=""):
    #
    #   Construct a description string from what we know about user's likes
    user_description = str()
    for i in range(1,4):
        if session['ephem_status'][str(i)]['response']:
            user_description = user_description +" "+ session['ephem_status'][str(i)]['response']
    user_description = user_description+"\n\n"
    #
    #   Need to create a record for each request - this will be parallelized
    #   
    #   The threaded_requests list holds a dictionary for every running thread
    threaded_requests = list()
    #
    #   Now we need to create and initialise the data for each thread - one per highlight
    for movie in session['highlights']:
        #   Create a dictionary for the threaded request for the movie
        ephem_thread = REBERT_TREADED_EPHEM_REC_TEMPLATE.copy()
        ephem_thread['movie'] = movie
        ephem_thread['title'] = movie['title']
        title_lower = movie['title'].lower()
        reviews = list()
        if title_lower in session['movie_data']['reviews']:
            reviews = session['movie_data']['reviews'][title_lower]
        review_str = create_movie_review_str(reviews)
        if user_description and review_str:
            #   Now, create the chat that we need to make the request
            ephem_thread['chat'] = ChatRequestPayload()
            system_turn = ChatMessage()
            system_turn.setRole("system")
            sprompt = EPHEM_RECOMMENDATION_PROMPT.format(movie_review_str=review_str,
                                                         user_description=user_description)
            system_turn.setContent(sprompt)
            ephem_thread['chat'].addMessage(system_turn)

            user_turn = ChatMessage()
            user_turn.setRole("user")
            uprompt = EPHEM_RECOMMENDATION_QUESTION.format(movie_title=movie['title'])
            user_turn.setContent(uprompt)
            ephem_thread['chat'].addMessage(user_turn)
            print_server_log(f"Creating API requester for '{ephem_thread['title']}'",
                            "make_ephem_rec_request()",
                            MODULE_LLM_DEBUG)
            ephem_thread['requester'] = Chat()
            ephem_thread['requester'].setBearerToken(chat_key)
            #   Set configuration values for the request
            ephem_thread['chat'] = configure_model_params(ephem_thread['chat'])
            ephem_thread['requester'].setRequestPayload(ephem_thread['chat'].json(clean=True))
            #   Start thread running, and launch the request
            ephem_thread['requester'].startThread()
            ephem_thread['requester'].queueRequest()
            ephem_thread['requester'].startRequest()
            print_server_log(f"Started requesting for '{ephem_thread['title']}'",
                            "make_ephem_rec_request()",
                            MODULE_LLM_DEBUG)
            #   Add the record to the list that we use for managing the treads
            threaded_requests.append(ephem_thread)
    #
    #   Now start checking on the running threads - before we start checking we'll
    #   wait a "big" amount to allow the requests time to complete. There is no need
    #   to check right away
    time.sleep(2.5)
    passes = 0
    waiting_completion = True
    #
    #   The waiting completion flag is set to True if any thread is still in
    #   the process of making a request or if the thread has response data that
    #   we have not yet collected from the thread
    while waiting_completion:
        waiting_completion = False
        passes += 1
        #   Sleep a small amount about 0.5 second between checks
        time.sleep(0.5)
        
        for ephem_thread in threaded_requests:
            if not ephem_thread['requester']: continue
            
            if ephem_thread['requester'].isRequesting():
                waiting_completion = True
                ephem_thread['count']+=1
                print_server_log(f"Pass [{passes:2}]: Check {ephem_thread['count']} on '{ephem_thread['title']}' - still requesting",
                                "make_ephem_rec_request()",
                                MODULE_LLM_DEBUG)
                continue
            #
            #   Collect the response - there should only be one response
            if ephem_thread['requester'].responses() > 0:
                waiting_completion = True
                ephem_thread['response'] = ephem_thread['requester'].nextResponse()
                ephem_thread['response'] = ephem_thread['response'].json()
                ephem_thread['message'] = ephem_thread['response']['choices'][0]['message']
                print_server_log(f"Pass [{passes:2}]: COLLECTING response for '{ephem_thread['title']}'",
                                "make_ephem_rec_request()",
                                MODULE_LLM_DEBUG)
            #
            #   Terminate, clean up, and dispose the thread
            if ephem_thread['requester'].isRunning() and ephem_thread['requester'].responses() == 0:
                ephem_thread['requester'].terminateThread()
                ephem_thread['requester'] = None
                print_server_log(f"Pass [{passes:2}]: TERMINATING thread for '{ephem_thread['title']}'",
                                "make_ephem_rec_request()",
                                MODULE_LLM_DEBUG)
        #
        #   At 0.5 seconds sleeping per cycle, this is equivalent to waiting ~50 seconds for
        #   a response from the LLM - that seems like a long time. Even some of the slowest
        #   responses observed are about 40-50 seconds for a complex request. This request
        #   isn't all that complex.
        #if passes > 100: 
        #
        #   This was set to 15 to facilitate reliability testing - so that it won't just run
        #   forever when a relatively high temperature is used.
        if passes > 15: 
            print_server_log(f"Exceeded maximum allowed passes: {passes} > 15 - terminating waiting",
                            "make_ephem_rec_request()",
                             MODULE_LLM_DEBUG)
            waiting_completion = False
    
    #
    #   Run through each of the responses, parse out the response and rationale
    for ephem_thread in threaded_requests:
        #print_server_log(f"For '{ephem_thread['title']}'",
        #                "make_ephem_rec_request()",
        #                MODULE_LLM_DEBUG)
        #
        #   First, kill off any threads that might have been running
        if ephem_thread['requester']:
            ephem_thread['requester'].terminateThread()
            ephem_thread['requester'] = None
            #   Special case, was still requesting - no data to parse
            ephem_thread['movie']['rebert_response'] = "Rebert was not able to complete a match in the allowed time."
            ephem_thread['movie']['rebert_rating'] = "still working"
            ephem_thread['movie']['rebert_rationale'] = "Rebert was not able to complete a match in the allowed time."
        else:
            #   Now, parse out the response
            try:
                content = ephem_thread['message']['content']
                rating = content.partition("<MATCH>")[2]
                rating = rating.partition("</MATCH>")[0].strip()
                rationale = content.partition("<RATIONALE>")[2]
                rationale = rationale.partition("</RATIONALE>")[0].strip()
                ephem_thread['movie']['rebert_response'] = content
                ephem_thread['movie']['rebert_rating'] = rating
                ephem_thread['movie']['rebert_rationale'] = rationale
            except:
                print_server_log(f"Exception retrieving thread information for '{ephem_thread['title']}'",
                                "make_ephem_rec_request()")
                ephem_thread['movie']['rebert_response'] = "Rebert was not able to determine a recommendation. You might improve the recommendation by providing more information about movies you like."
                ephem_thread['movie']['rebert_rating'] = "still working"
                ephem_thread['movie']['rebert_rationale'] = "Rebert was not able to determine a recommendation. You might improve the recommendation by providing more information about movies you like."
        #print_server_log(f"For '{ephem_thread['movie']['title']}' RECOMMENDATION: '{ephem_thread['movie']['rebert_rating'] }'",
        #                  "make_ephem_rec_request()",
        #                  MODULE_LLM_DEBUG)
        #print_server_log(f"For '{ephem_thread['movie']['title']}' RATIONALE: '{ephem_thread['movie']['rebert_rationale'] }'",
        #                  "make_ephem_rec_request()",
        #                  MODULE_LLM_DEBUG)
    return session

#
#   Create a question & answer string to be used in prompt construction
#
def create_rating_qna_str(session=None):
    #
    #   Construct the question and answer string, based on what we have from the user
    qna_str = str()
    for item in session['rating']['in_progress']['qna']:
        qna_str = qna_str + f"QUESTION:\n\t{item['question']}\n"
        qna_str = qna_str + f"ANSWER:\n\t{item['answer']}\n"
    qna_str = qna_str+"\n"
    return qna_str

#
#   The idea here is to use the LLM to extract the potential titles
#   from the user text
#
def movie_title_extract_request(transcript=None, chat_key=""):
    #
    #   Prepare the chat context   
    chat_context = ChatRequestPayload()
    #   Setup the system prompt
    system_turn = ChatMessage()
    system_turn.setRole("system")
    system_turn.setContent(RATE_EXTRACT_PROMPT)
    chat_context.addMessage(system_turn)
    #   Setup the user question, using transcript
    user_turn = ChatMessage()
    user_turn.setRole("user")
    userq = RATE_EXTRACT_QUESTION.format(transcript=transcript['text'])
    user_turn.setContent(userq)
    chat_context.addMessage(user_turn)
    
    #   Grab the starting time
    start_time = datetime.datetime.now()
    chat_api = Chat()
    chat_api.setBearerToken(chat_key)
    #
    #   Set configuration values
    chat_context = configure_model_params(chat_context)
    #    
    chat_api.setRequestPayload(chat_context.json(clean=True))
    chat_api.queueRequest()
    chat_api.makeRequest()
    response = chat_api.nextResponse()
    resp_dict = response.json()
    #   Grab the finishing time
    finish_time = datetime.datetime.now()
    runtime = finish_time - start_time
    print_server_log(f"Title extraction elapsed time: {runtime}",
                      "movie_title_extract_request()",
                      MODULE_LLM_DEBUG)
    #   Get the text of the response
    message = resp_dict['choices'][0]['message']['content']
    #   If there were no titles identified, we're done
    if "MISSING_MOVIE_TITLES" in message: 
        print_server_log(f"No movie titles identified in transcript.",
                          "movie_title_extract_request()",
                          MODULE_LLM_DEBUG)    
        return transcript
    titles = list()
    title_parts = message.partition("<TITLE>")
    title_parts = title_parts[2].partition("</TITLE>")
    while title_parts[1]:
        if title_parts[0]:
            titles.append(title_parts[0])
        title_parts = title_parts[2].partition("<TITLE>")
        title_parts = title_parts[2].partition("</TITLE>")
    print_server_log(f"Extracted titles: {str(titles)}",
                      "movie_title_extract_request()",
                      MODULE_LLM_DEBUG)    
    transcript['titles'] = titles
    return transcript



