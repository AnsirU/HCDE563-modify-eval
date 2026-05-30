#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: access_dbs.py
#   REVISION: March, 2025
#   CREATION DATE: March, 2025
#   Author: David W. McDonald
#
#   Code that accesses the rebert system databases. 
#   User profile database
#   User movie rating database
# 
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
import sys, os, datetime, hashlib, json, copy
#
from flask import render_template
import flask_login
#
from rebert.classes.base.Logger import Logger
from rebert.classes.data.JSONDataFolder import JSONDataFolder
from rebert.classes.server.RebertUser import *
#
from rebert._prototype_7_1_.web.config import *
from rebert._prototype_7_1_.web.utilities import *
#
# 
#
MODULE_ACCESS_DBS_DEBUG = True
#
if not MODULE_DEBUG_OVERRIDE:
    MODULE_ACCESS_DBS_DEBUG = GLOBAL_DEBUG
#
#
#   This will generate a log of the database activity - separate from the
#   output to the server log. This shows some internals of the DB
#
db_log = None
#   Uncomment the next two lines to start the database loging
#db_log = Logger(name="db_log", filename="database.log.txt", format="LONG", level="DEBUG")
#db_log.log("STARTING: database logging")
#
#
#   USER PROFILES DATABASE
#
REBERT_PROFILES_FILENAME = os.path.join(REBERT_PROFILES_DIRECTORY, REBERT_PROFILES_FOLDER)
user_profiles = JSONDataFolder(name=REBERT_PROFILES_FILENAME,logger=db_log)
try:
    user_profiles.load(REBERT_PROFILES_FILENAME)
except Exception as ex:
    user_profiles.setMaxItems(2500)
    user_profiles.setBaseName("users")
#
#   SESSION DATABASE - unused for now
#
REBERT_SESSIONS_FILENAME = os.path.join(REBERT_SESSIONS_DIRECTORY, REBERT_SESSIONS_FOLDER)
user_sessions = JSONDataFolder(name=REBERT_SESSIONS_FILENAME,logger=db_log)
try:
    user_sessions.load(REBERT_SESSIONS_FILENAME)
except Exception as ex:
    user_sessions.setMaxItems(2500)
    user_sessions.setBaseName("sessions")
#
#   USER RATINGS DATABASE
#
REBERT_RATINGS_FILENAME = os.path.join(REBERT_RATINGS_DIRECTORY, REBERT_RATINGS_FOLDER)
user_ratings = JSONDataFolder(name=REBERT_RATINGS_FILENAME,logger=db_log)
try:
    user_ratings.load(REBERT_RATINGS_FILENAME)
except Exception as ex:
    user_ratings.setMaxItems(2500)
    user_ratings.setBaseName("ratings")





#
#   Drop old profile indexes, and reindex with the new user data
#
def profiles_reindex():
    #   Try to remove the existing indexes
    try:
        #db_log.log(f">>> Dropping index 'username'")
        user_profiles.dropIndex("username")
        #db_log.log(f">>> Dropping index 'email'")
        user_profiles.dropIndex("email")
        #db_log.log(f">>> Dropping index 'account_id'")
        user_profiles.dropIndex("account_id")
        #db_log.log(f">>> Finished dropping indexes")
    except Exception as ex:
        print_server_log(f"Caught exception: {str(ex)}",
                        "profiles_reindex()",
                        True)
        print_server_log(f"Could not drop existing profile indexes",
                        "profiles_reindex()",
                        MODULE_ACCESS_DBS_DEBUG)
        return ex
    #
    #   Try to create the new indexes - reindex upon account creation
    try:
        #db_log.log(f">>> Creating index of 'username'")
        user_profiles.createIndex(field="username", index_type="string")
        #db_log.log(f">>> Creating index of 'email'")
        user_profiles.createIndex(field="email", index_type="string")
        #db_log.log(f">>> Creating index of 'account_id'")
        user_profiles.createIndex(field="account_id", index_type="string")
        #db_log.log(f">>> Finished creating indexes")
    except Exception as ex:
        print_server_log(f"Caught exception: {str(ex)}",
                        "profiles_reindex()",
                        True)
        print_server_log(f"Could not create new profile indexes",
                        "profiles_reindex()",
                        MODULE_ACCESS_DBS_DEBUG)
        return ex
    return None

#
#   Drop old ratings indexes and reindex (with additional rating)
#
def ratings_reindex():
        #   Try to remove the existing indexes
    try:
        #db_log.log(f">>> Dropping index 'title'")
        user_ratings.dropIndex("title")
        #db_log.log(f">>> Dropping index 'rating_id'")
        user_ratings.dropIndex("rating_id")
        #db_log.log(f">>> Dropping index 'account_id'")
        user_ratings.dropIndex("account_id")
        #db_log.log(f">>> Finished dropping indexes")
    except Exception as ex:
        print_server_log(f"Caught exception: {str(ex)}",
                        "ratings_reindex()",
                        True)
        print_server_log(f"Could not drop existing ratings indexes",
                        "ratings_reindex()",
                        MODULE_ACCESS_DBS_DEBUG)
        return ex
    #
    #   Try to create the new indexes - reindex upon account creation
    try:
        #db_log.log(f">>> Creating index of 'title'")
        user_ratings.createIndex(field="title", index_type="string")
        #db_log.log(f">>> Creating index of 'rating_id'")
        user_ratings.createIndex(field="rating_id", index_type="string")
        #db_log.log(f">>> Creating index of 'account_id'")
        user_ratings.createIndex(field="account_id", index_type="string")
        #db_log.log(f">>> Finished creating indexes")
    except Exception as ex:
        print_server_log(f"Caught exception: {str(ex)}",
                        "ratings_reindex()",
                        True)
        print_server_log(f"Could not create new ratings indexes",
                        "ratings_reindex()",
                        MODULE_ACCESS_DBS_DEBUG)
        return ex
    return None



def get_user_ratings(account_id=""):
    ratings = list()
    try:
        ratings = user_ratings.search(field="account_id", query=account_id)
    except Exception as ex:
        print_server_log(f"Caught exception: {str(ex)}",
                        "get_user_ratings()",
                        True)
        print_server_log(f"Could not search index 'account_id' for '{account_id}'",
                        "get_user_ratings()",
                        MODULE_ACCESS_DBS_DEBUG)
    return ratings




def update_movie_rating(rated_movie=None):
    ratings = list()
    try:
        ratings = user_ratings.search(field="rating_id", query=rated_movie['rating_id'])
    except Exception as ex:
        print_server_log(f"Caught exception: {str(ex)}",
                        "update_movie_rating()",
                        True)
        print_server_log(f"Could not search index 'rating_id' for '{rated_movie['rating_id']}'",
                        "update_movie_rating()",
                        MODULE_ACCESS_DBS_DEBUG)
        print_server_log(f"Rating was NOT updated",
                        "update_movie_rating()",
                        MODULE_ACCESS_DBS_DEBUG)
        return None
    
    if len(ratings) != 1:
        print_server_log(f"Found more than 1 item with 'rating_id' '{rated_movie['rating_id']}'",
                        "update_movie_rating()",
                        MODULE_ACCESS_DBS_DEBUG)
        print_server_log(f"Rating was NOT updated",
                        "update_movie_rating()",
                        MODULE_ACCESS_DBS_DEBUG)
        return None
    #
    #   Made it here - attempt to write into the DB record
    ratings[0]['title'] = rated_movie['title']
    ratings[0]['tmdb_id'] = rated_movie['tmdb_id']
    ratings[0]['matched'] = rated_movie['matched']
    ratings[0]['score'] = rated_movie['score']
    ratings[0]['last_viewed'] = rated_movie['last_viewed']
    ratings[0]['creation_ts'] = rated_movie['creation_ts']
    #   Only need to change slot zero of candidates
    if ratings[0]['candidates']:
        candidate_0 = ratings[0]['candidates'][0]
        candidate_0['title'] = rated_movie['candidates'][0]['title']
        candidate_0['tmdb_id'] = rated_movie['candidates'][0]['tmdb_id']
        candidate_0['imdb_id'] = rated_movie['candidates'][0]['imdb_id']
        candidate_0['wikidata_id'] = rated_movie['candidates'][0]['wikidata_id']
        candidate_0['year'] = rated_movie['candidates'][0]['year']
        candidate_0['release_date'] = rated_movie['candidates'][0]['release_date']
        candidate_0['synopsis'] = rated_movie['candidates'][0]['synopsis']
        candidate_0['genre_ids'] = rated_movie['candidates'][0]['genre_ids']
        candidate_0['genre'] = rated_movie['candidates'][0]['genre']
        candidate_0['poster_path'] = rated_movie['candidates'][0]['poster_path']
    #
    #   Update the Q&A just in case
    if ratings[0]['qna']:
        index = 0
        while index<len(ratings[0]['qna']):
            ratings[0]['qna'][index]['question'] = rated_movie['qna'][index]['question']
            ratings[0]['qna'][index]['answer'] = rated_movie['qna'][index]['answer']
            index += 1
    #
    #   Now save - unfortunately right now this saves the entire DB
    user_ratings.save(force_save=True)
    print_server_log(f"Updated rating for '{rated_movie['title']}' with tmdb_id '{rated_movie['tmdb_id']}'",
                     "update_movie_rating()",
                     MODULE_ACCESS_DBS_DEBUG)
    return None



#   =========================
#
#   USER PROFILES DATABASE - LIBRARY TYPE FUNCTIONS
#
#   =========================
#
@login_manager.user_loader
def user_loader(identifier):
    print_server_log(f"Loading user with user identifier: '{identifier}'",
                    "user_loader()",
                    MODULE_ACCESS_DBS_DEBUG)
    #
    #   Find the 'set' or a list of users that match - actually this should be
    #   a list of exactly one user - but we should probably be careful about
    #   possilbe multiple matches.
    user_set = user_profiles.search(field="account_id", query=identifier)
    if not user_set:
        user_set = user_profiles.search(field="email", query=identifier)
        if not user_set:
            cleaned_id = clean_username(identifier)
            user_set = user_profiles.search(field="username", query=cleaned_id)
    
    if user_set:
        #   the results of search are always a list, in this case it should
        #   be a list of exactly one thing - user record from the user DB
        user_record = user_set[0]
        user = RebertUser()
        #user.id = user_record['email']
        user.id = user_record['account_id']
        user.account_id = user_record['account_id']
        user.record = user_record
        print_server_log(f"User FOUND: '{identifier}'",
                        "user_loader()",
                        MODULE_ACCESS_DBS_DEBUG)
        return user

    print_server_log(f"NO user with id: '{identifier}'",
                    "user_loader()",
                    MODULE_ACCESS_DBS_DEBUG)
    return None
#
#
#
@login_manager.request_loader
def request_loader(request):
    #   Trap an exception on the form. This is activated on any post and not
    #   all post actions will have this field. If access to this form field
    #   fails, then we don't have a way to get the user. No user identifier.
    try:
        identifier = request.form['username_text_input']
    except:
        identifier = ""
    
    print_server_log(f"Loading user with user identifier: '{identifier}'",
                    "request_loader()",
                    MODULE_ACCESS_DBS_DEBUG)
    #
    #   If there is no identifier then None
    if not identifier: 
        print_server_log(f"NO user with empty identifier!",
                        "request_loader()",
                        MODULE_ACCESS_DBS_DEBUG)
        return None
    
    #   this should only be one user - but we should be careful
    user_set = user_profiles.search(field="account_id", query=identifier)
    if not user_set:
        user_set = user_profiles.search(field="email", query=identifier)
        if not user_set:
            cleaned_id = clean_username(identifier)
            user_set = user_profiles.search(field="username", query=cleaned_id)
    
    if user_set:
        #   the results of search are always a list, in this case it should
        #   be a list of exactly one thing - user record from the user DB
        user_record = user_set[0]
        user = RebertUser()
        #user.id = user_record['email']
        user.id = user_record['account_id']
        user.account_id = user_record['account_id']
        user.record = user_record
        print_server_log(f"User FOUND: '{identifier}'",
                        "request_loader()",
                        MODULE_ACCESS_DBS_DEBUG)
        return user
    
    print_server_log(f"NO user with id: '{identifier}'",
                    "request_loader()",
                    MODULE_ACCESS_DBS_DEBUG)
    return None

