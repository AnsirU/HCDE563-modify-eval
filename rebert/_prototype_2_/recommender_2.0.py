#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: recommender_2.0.py
#   REVISION: March, 2026
#   CREATION DATE: April, 2024
#   AUTHOR: David W. McDonald
#
#   Prototype: 2
#   Version: 0
#
#   This is the code for a very simple chat prototype of a movie recommender. The primary 
#   enhancement for this version is the addition of release information. The release
#   information is provided by the MovieNumbers class.
#
#   March 2026 - The Numbers (MovieNumbers) is undergoing a sitewide update. The changes
#   are to adapt fit the other release class into the recommendation. The Rotten Tomatoes
#   site doesn't quite provide the same information.
#   
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#

#   These are standard python modules/packages
import sys, datetime, json, random, re
#
#   If you got any version of Protype 1 working then you should have
#   this available on your machine
import requests
#
#   This comes from the rebert class library and manages API keys
#   You should use it to store your OpenAI API key locally, so your
#   key is not stored as a constant in the code.
from rebert.classes.data.KeyManager import KeyManager
#
#   NOTE: As of March 2026, The Numbers is undergoing a sitewide update
#   we need to use another 'release' class
#
#   This is a class that collects data from a website called
#   The Numbers: https://www.the-numbers.com/movies/release-schedule
#from rebert.classes.release.MovieNumbers import MovieNumbers as FetchReleases
#
#
#   This class uses the Rotten Tomatoes website to get
#   upcoming movie releases https://www.rottentomatoes.com/
#
#   The release data isn't quite as good as The Numbers, but should work
from rebert.classes.release.TomatoRelease import TomatoRelease as FetchReleases
#
#
#
#   CONSTANTS
#
#   This example will use an OpenAI service
OAI_HOST = "https://api.openai.com"
OAI_SERVICE_ENDPOINT = "/v1/chat/completions"
#OAI_MODEL = "gpt-4-turbo-preview"
OAI_MODEL = "gpt-5.4-nano-2026-03-17"
#
#   This is a modified prompt. We inject some recent movie release info
#   into the prompt to see if we can get the recommender to say something
#   about the recent movies
#
MOVIE_RECOMMENDER_PERSONA_PROMPT = '''You are a movie critic who wants to make sure that you make the best movie recommendations. Make sure that the movie you recommend satisfies the user across many movie attributes including genre, actors, visuals, music, plot line, character development, dialog, mood, and many other movie attributes. To help you make your recommendations, here is a list of recently released movies. The list contains the MOVIE TITLE, the RELEASE TYPE, the OPENING DATE, and when available a CRITIC SCORE (Rotten Tomatoes critics percentage) for each movie.

{movie_data_str}

Your responses should always focus on making movie recommendations.'''
#
#
#
#   Request data on recently released movies. This function can
#   optionally trim the list of movies to a specified number.
#   Returns a dictionary of release information
def get_recent_releases(cutoff=0):
    #
    #   This uses one of the release fetching classes to
    #   get recently released movies. Neither of them will
    #   require an API key. The data is collected from a
    #   public facing web page and uses screen scraping to
    #   parse the HTML and collect data
    collector = FetchReleases(name="FetchReleases-p2.v0")
    movie_list = collector.getRecentReleaseList()
    #
    #   Create a subset if there is a lot of releases
    #   If cutoff is set to 0 (zero) then it returns 
    #   the whole list of movies
    if cutoff and len(movie_list) > cutoff:
        # randomly select a subset of movies
        movie_list = random.sample(movie_list,k=cutoff)
    return movie_list
#
#   Rotten Tomatoes (TomatoRelease) stores extra fields inside 'notes', for example:
#   "now showing; Critics_Score=85%, Audience_Score=72%"
#   We must not use the first comma for splitting release vs. scores — that comma sits between scores.
_CRITIC_SCORE_RE = re.compile(r"Critics_Score=([^,;]+)")
#
#   Generate a string of KEY:value items for each movie
#   Keys should correspond to the keys defined in the
#   MOVIE_RECOMMENDER_PERSONA_PROMPT
def create_prompt_data_str(movie_list=[]):
    movie_info_str = ""
    for movie in movie_list:
        data = f"\tMOVIE TITLE: {movie['title']}\n"
        notes = movie.get("notes") or ""
        #   TomatoRelease joins "release phrase" and "score blob" with "; ".
        #   Older / other sources may use "wide release, re-release" with no semicolon — keep first comma segment then.
        if "; " in notes:
            release_type = notes.split("; ", 1)[0].strip()
        else:
            release_type = notes.partition(",")[0].strip()
        if release_type:
            data = data + f"\tRELEASE TYPE: {release_type}\n"
        else:
            data = data + f"\tRELEASE TYPE: unspecified\n"
        #   Pull Critics_Score=... from anywhere in notes (only present when the scraper found it).
        critic_m = _CRITIC_SCORE_RE.search(notes)
        if critic_m:
            critic_val = critic_m.group(1).strip()
            data = data + f"\tCRITIC SCORE (Rotten Tomatoes): {critic_val}\n"
        data = data + f"\tOPENING DATE: {movie['opening_date_str']}\n"
        movie_info_str = movie_info_str + "\n" + data
    return movie_info_str
#
#   Create a new chat turn.
#   Each chat turn is a dictionary with a 'role' and 'content'
def new_chat_turn(role="",content=""):
    turn = dict()
    turn['role'] = role
    turn['content'] = content
    return turn
#
#   The program needs to maintain the status of the chat. This status 
#   will include parameters that tell the model how it should respond
#   as well as all of the user questions and the responses.
#   This procedure creates a chat context to maintain that status.
def new_chat_context(movie_data_str=""):
    chat_context = dict()
    chat_context['model'] = OAI_MODEL
    chat_context['messages'] = list()    
    sprompt = MOVIE_RECOMMENDER_PERSONA_PROMPT.format(movie_data_str=\
                                                      movie_data_str)
    system_turn = new_chat_turn("system",sprompt)
    chat_context['messages'].append(system_turn)
    return chat_context
#
#   Making a request is about modifying the growing chat_context,
#   setting up the HTTP request URL and request headers, and making
#   the request.
def make_chat_request(user_text="", chat_context=None, chat_key=None):
    #   If there is no chat context, raise an error
    if not chat_context:
        raise Exception("No chat_context has been supplied")
    
    #   We use the text we got from the user to create a user turn
    user_turn = new_chat_turn("user",user_text)
    #   Add that user turn to the list of messages in the context
    chat_context['messages'].append(user_turn)
    
    #   The whole context is payload for the request - a request body
    payload = json.dumps(chat_context)
    
    #   Create header information for the request - this must include
    #   the 'Content-Type' key set to 'application/json' and the
    #   'Authorization' key set to include your API key
    header = dict()
    header['Content-Type'] = "application/json"
    header['Authorization'] = f"Bearer {chat_key}"
    
    #   The service URL is the host and the service endpoint
    service_url = OAI_HOST + OAI_SERVICE_ENDPOINT
    
    #   Make this as a POST request
    response = requests.post(service_url,
                             headers=header,
                             data=payload)
    #   The response should be 'application/json' so extract the JSON
    resp_dict = response.json()
    #   There is a lot in the response - just extract the message
    assistant_turn = resp_dict['choices'][0]['message']
    #   Add the response to our chat context
    chat_context['messages'].append(assistant_turn)
    return chat_context

#
#   The main is called from the command line and just loops asking
#   for user ask a question.
def main():
    #   Initialize some variables
    assistant_name = sys.argv[0].rpartition('.')[0]
    
    #   Create a key manager object - it automatically loads
    #   the available key information - if you added a key    
    key_manager = KeyManager()
    #
    #   Returns a list of keys - should only be one
    key_list = key_manager.findRecord(domain="api.openai.com")
    #
    #   Extract just the api key from the key record
    chat_key = key_list[0]['key']
    #
    #   Get some recent release information
    movie_releases = get_recent_releases(cutoff=7) 
    #
    #   Convert the movie data to a string that can be
    #   inserted into the system prompt
    movie_info_str = create_prompt_data_str(movie_releases)
    #
    #   Create the chat context, now including the new
    #   release information that we just retrieved
    chat_context = new_chat_context(movie_info_str)
    
    print()
    #   A rather simple chat loop
    user_text = input(f"You > ").strip()
    print()
    #   While the user enters some text - not 'quit'
    while len(user_text)>0 and (user_text.lower() != "quit"):
        
        #   Use that user text to make the request
        chat_context = make_chat_request(user_text, chat_context, chat_key)
        
        #   Get the last message - it should be the text response
        assistant_turn = chat_context['messages'][-1]
        
        #   Show that response
        print(f"{assistant_name} > {assistant_turn['content']}")
        print()
        
        #   Get the next user turn
        user_text = input(f"You > ").strip()
        print()
    
    return

if __name__ == '__main__':
    main()   

