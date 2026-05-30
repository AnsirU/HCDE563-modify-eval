#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: recommender_3.0.py
#   REVISION: March, 2026
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   Prototype: 3
#   Version: 0
#
#   This implements a simple chat interface, but adds the use of the 
#   
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#

#   These are standard python modules/packages
import sys, datetime, json, random
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
#   This class allows us to search The Movie Database (TMDB) to
#   look for movie synopses - and other information. We will add
#   synopsis information to the information we provide the LLM
#   to try and reduce hallucinations.
from rebert.classes.moviedb.TMDB.Search import Search

#
#
#   CONSTANTS
#
#
#   This is a modified prompt. In addition to injecting recent movie release 
#   info we provide a movie synopis, and instruct the LLM to only say things
#   that it knows are facutal - things that it has been told. The goal is
#   to help reduce hallucinations.
#
MOVIE_RECOMMENDER_PERSONA_PROMPT = '''You are a movie critic who wants to make sure that you make the best movie recommendations. Make sure that the movie you recommend satisfies the user across many movie attributes including genre, actors, visuals, music, plot line, character development, dialog, mood, and many other movie attributes. To help you make your recommendations, here is a list of recently released movies. The list contains the MOVIE TITLE, the RELEASE TYPE, the OPENING DATE, and a SYNOPSIS for each movie.

{movie_data_str}

Your responses should always focus on making recommendations for a recent movie. You can only say things about a movie that you know are true.'''
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
    collector = FetchReleases(name="FetchReleases-p3.v0")
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
#   Search The Movie Database (TMDB) for information about each
#   movie release. The goal is to find a synopsis that we can
#   use to help give the LLM information about the movie and
#   reduce the amount of hallucination about the movies.
def get_movie_synopses(movie_list=[], tmdb_key=None, cutoff=0):
    #   Create an empty list to store the final result
    openings = list()
    #
    #   Create a TMDB Search query object to search for synopses
    search = Search(name="TMDB.Search-p3.v0")
    #   Make sure we can authenticate to TMDB
    if tmdb_key:
        search.setAPIKey(tmdb_key)
    else:
        raise Exception("Need to supply an API Key (not the API Token)")
    #
    #   Run through all of the movies and see if we can get a synopsis
    for movie in movie_list:
        title = movie['title']
        year = movie['year']
        #wl.log(f"requesting: [{count}]: '{title}' ({year})")
        #   Make the search with the title and year info
        found_items = search.movieSearch(title=title,year=year)
        #   It's possible there are multiple matches
        for item in found_items:
            #   Find the first one with an exact match title
            if title == item['title']:
                #   If a synopsis exists, we'll keep the movie
                #   in the list for now, copy over the synopsis
                if item['overview']:
                   #   Fill in the synopsis and save this movie
                    movie['synopsis'] = item['overview']
                    openings.append(movie)
                    #   Don't process more of the response list,
                    #   we just found a movie with the exact title
                    break
    #   If cutoff is set to 0 (zero) then it returns the whole list
    if cutoff and len(openings) > cutoff:
        #   Randomly select a subset of movies
        openings = random.sample(openings,k=cutoff)
    return openings
#
#   Generate a string of KEY:value items for each movie
#   Keys should correspond to the keys defined in the
#   MOVIE_RECOMMENDER_PERSONA_PROMPT
#
#   This prototype adds the SYNOPSIS key and inserts that
#   value when creating the prompt data string.
def create_prompt_data_str(movie_list=[]):
    movie_info_str = ""
    for movie in movie_list:
        data = f"\tMOVIE TITLE: {movie['title']}\n"
        note = movie['notes'].partition(',')[0]
        data = data + f"\tRELEASE TYPE: {note}\n"
        data = data + f"\tOPENING DATE: {movie['opening_date_str']}\n"
        data = data + f"\SYNOPSIS: {movie['synopsis']}\n"
        movie_info_str = movie_info_str + "\n" + data
    return movie_info_str

#
#   The code needs to maintain the status of the chat. This status 
#   will include parameters that tell the model how it should respond
#   as well as all of the user questions and the responses.
#
def new_chat_context(movie_data_str=""):
    chat_context = ChatRequestPayload()
    sprompt = MOVIE_RECOMMENDER_PERSONA_PROMPT.format(movie_data_str=\
                                                      movie_data_str)
    system_turn = ChatMessage()
    system_turn.setRole("system")
    system_turn.setContent(sprompt)
    
    chat_context.addMessage(system_turn)
    return chat_context

#
#   Making a request is about modifying the growing chat_context
#   setting up the HTTP request URL and request headers, and making
#   the request.
def make_chat_request(chat_api=None, chat_context=None):
    #   If there is no chat context, raise an error
    if not chat_context:
        raise Exception("No chat_context has been supplied")
        
    chat_api.setRequestPayload(chat_context)
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
#   The main is called from the command line and just loops asking
#   for user to input
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
    #   Create a chat request object to interact with the API
    chat_api = Chat()
    #   Add the API key to the object as a bearer token
    chat_api.setBearerToken(chat_key)
    #
    #   We need the key for the TMDB (The Movie DB) as well
    key_list = key_manager.findRecord(domain="api.themoviedb.org")
    tmdb_key = key_list[0]['key']
    #
    #   Get some recent release information
    movie_releases = get_recent_releases() 
    #
    #   Now make a request to TMDB to find synopses - this call
    #   will trim the list to just 10 openings if there happen
    #   to be more than that
    openings = get_movie_synopses(movie_releases, tmdb_key, 10)
    #
    #   Convert the movie data to a string that can be
    #   inserted into the system prompt
    movie_info_str = create_prompt_data_str(openings)
    #
    #   Create the chat context, now including the new
    #   release information that we just retrieved
    chat_context = new_chat_context(movie_info_str)
    
    print()
    #   Start the rather simple chat loop
    user_text = input(f"You > ").strip()
    print()
    #   While the user enters some text - not 'quit'
    while len(user_text)>0 and (user_text.lower() != "quit"):
        user_turn = ChatMessage()
        user_turn.setRole("user")
        user_turn.setContent(user_text)
        chat_context.addMessage(user_turn)
        
        #   Use that user text to make the request
        assistant_turn = make_chat_request(chat_api, chat_context)
        
        #   Show that response
        print(f"{assistant_name} > {assistant_turn['content']}")
        print()
        
        chat_context.addMessage(assistant_turn)
        
        #   Get the next user turn
        user_text = input(f"You > ").strip()
        print()
    
    use = chat_api.getUsageStatus()
    print()
    print("Usage status for this chat session:")
    print(json.dumps(use,indent=4))
    return

if __name__ == '__main__':
    main()   

