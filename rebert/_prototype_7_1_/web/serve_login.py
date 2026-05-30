#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: serve_login.py
#   REVISION: March, 2024
#   CREATION DATE: December, 2024
#   Author: David W. McDonald
#
#   Server code for performing a login
#
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
##
#
import sys, os, datetime, hashlib, json, copy
#
from flask import request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from markupsafe import escape
#
import flask_login
#
from rebert.classes.server.RebertUser import *
#
from rebert._prototype_7_1_.web.config import *
from rebert._prototype_7_1_.web.utilities import *
from rebert._prototype_7_1_.web.access_dbs import *
from rebert._prototype_7_1_.web.serve_rating import serve_rating_page
#

#  
#
MODULE_LOGIN_DEBUG = True
#
if not MODULE_DEBUG_OVERRIDE:
    MODULE_LOGIN_DEBUG = GLOBAL_DEBUG
#
#
##############
#
#   CREATE ACCOUNT PROCESSING
#
##############
#
#   Generate the page that facilitates user account creation
#
def serve_create_account(request, server_state):
    #
    #   If this was just a 'GET' then produce the form page for this
    if request.method == 'GET':
        session_id = secure_filename(str(escape(request.args.get('session_id'))))    
        page = render_template("create_account.html",
                               error = "",
                               session = {'session_id':session_id})
        return page
    #
    #   This must be a 'POST'
    #
    #   Get the session_id from the form    
    session_id =  secure_filename(str(escape(request.form["session_id"])))
    #   This could fail ... if the session_id is something problematic
    session_state = load_session_state(session_id)
    #
    #   Copy the template dictionary/record
    user_record = REBERT_USER_PROFILE_TEMPLATE.copy()
    #
    #   Collect a username - do a small amount of cleaning
    user_record['username'] = clean_username(request.form['username_text_input'])
    #   Check that a username was provided
    if not user_record['username']:
        print_server_log(f"Need a username to create an account",
                        "serve_create_account()",
                        MODULE_LOGIN_DEBUG)
        page = render_template("create_account.html",
                               error = REBERT_CREATE_ERROR_INFO_NEEDED,
                               session = {'session_id':session_id})
        return page
    #
    #   Check that this username is NOT already taken
    try:
        #   username has already been cleaned
        #   search the user profile DB for that username
        user_set = user_profiles.search(field="username", query=user_record['username'])
    except Exception as ex:
        print_server_log(f"Caught exception: {str(ex)}",
                        "serve_create_account()",
                        True)
        print_server_log(f"Assuming this is a new user: '{user_record['username']}'",
                        "serve_create_account()",
                        MODULE_LOGIN_DEBUG)
        user_set = list()

    if user_set:
        print_server_log(f"The username '{user_record['username'] }' is taken by another user.",
                        "serve_create_account()",
                        MODULE_LOGIN_DEBUG)
        page = render_template("create_account.html",
                               error = REBERT_CREATE_ERROR_UNAME,
                               session = {'session_id':session_id})
        return page
    #
    #   Collect an email address
    user_record['email'] = request.form['email_text_input']
    #   Check that an email address was provided
    if not user_record['email']:
        print_server_log(f"Need an email address to create an account",
                        "serve_create_account()",
                        MODULE_LOGIN_DEBUG)
        page = render_template("create_account.html",
                               error = REBERT_CREATE_ERROR_INFO_NEEDED,
                               session = {'session_id':session_id})
        return page
    #   Check that this email is NOT already used/taken by another user
    try:
        #   search the user profile DB for the specified email address
        #   one user one email address
        user_set = user_profiles.search(field="email", query=user_record['email'] )
    except Exception as ex:
        print_server_log(f"Caught exception: {str(ex)}",
                        "serve_create_account()",
                        True)
        print_server_log(f"Assuming this is a new email address: '{user_record['email']}'",
                        "serve_create_account()",
                        MODULE_LOGIN_DEBUG)
        user_set = list()
    #
    if user_set:
        print_server_log(f"The email address '{user_record['email'] }' is being used by another user.",
                        "serve_create_account()",
                        MODULE_LOGIN_DEBUG)
        page = render_template("create_account.html",
                               error = REBERT_CREATE_ERROR_EMAIL,
                               session = {'session_id':session_id})
        return page
    #
    #   If we get to this place in the code, then we have unique username AND 
    #   a unique email address for this account creation.
    #
    #   Set a creation timestamp, collect and set zip code
    user_record['creation_ts'] = str(datetime.datetime.now()).partition('.')[0]
    #   Not strictly required, if they provide it we probably want to use it for
    #   localization of future recommendations
    user_record['zipcode'] = request.form['zipcode_text_input']
    #
    #   In theory, https should send these passwords to the server encrypted, so these
    #   should not be 'in the clear' when sent over the internet. They are "clear" now
    #   and we need to check them - and then hash them to something that can be stored.
    #   We want to avoid storing the passwords in clear text, like in a DB or in some
    #   kind of local storage.
    #
    #   First check that the passwords provided are the same. This might also be checked
    #   or validated on the client side with some JavaScript code.
    password1 = request.form['password_text1_input']
    password2 = request.form['password_text2_input']
    if password1 != password2:
        print_server_log(f"The user supplied passwords did not match!",
                        "serve_create_account()",
                        MODULE_LOGIN_DEBUG)
        page = render_template("create_account.html",
                               error = REBERT_CREATE_ERROR_PASS,
                               session = {'session_id':session_id})
        return page
    #
    #   Next, encrypt the password to avoid storing the password in the clear
    user_record['password'] = crypt_password(password1, user_record)
    #
    #   Assign the new account a unique account ID
    user_record['account_id'] = generate_account_id(user_record)
    #
    #   Try to save the user record into our little user database. Then reindex the whole
    #   database. A complete reindex is because the current implementation of the
    #   JSONDataFolder does not support incremental indexing when appending a record.
    #
    try:
        #   adding the record
        user_profiles.append(user_record)
        #   saving the DB
        user_profiles.save(REBERT_PROFILES_FILENAME,compact=False)
    except Exception as ex:
        print_server_log(f"Caught exception: {str(ex)}",
                        "serve_create_account()",
                        True)
        print_server_log(f"Could not save the user database: '{REBERT_PROFILES_FILENAME}'",
                        "serve_create_account()",
                        MODULE_LOGIN_DEBUG)
        page = render_template("create_account.html",
                               error = REBERT_CREATE_ERROR_DB,
                               session = {'session_id':session_id})
        return page
    #
    #   Attempt to reindex the user profiles
    ex = profiles_reindex()
    if ex: 
        page = render_template("create_account.html",
                               error = REBERT_CREATE_ERROR_DB,
                               session = {'session_id':session_id})
        return page
    #
    #   Success condition - show login page
    #   After creating a new user, they need to login and authenticate
    page = render_template("user_login.html",
                           error = "",
                           session = session_state)
    return page



##############
#
#   LOGIN PAGE GENERATION
#
##############
#
def serve_signin_page(request, server_state):
    session_id = secure_filename(str(escape(request.args.get('session_id'))))    
    page = render_template("user_login.html",
                           error = "",
                           session = {'session_id':session_id})
    return page



##############
#
#   LOGIN AUTHENTICATION PROCESSING
#
##############
#
def serve_user_login(request, server_state):
    #   Get the username and password
    form_uname = request.form['username_text_input']
    form_password = request.form['password_text1_input']
    #   Get the session_id from the form    
    session_id =  secure_filename(str(escape(request.form["session_id"])))
    #   This could fail ... if the session_id is something problematic
    session_state = load_session_state(session_id)
    #
    #   Find the 'set' or a list of users that match - actually
    #   this should only be one user - but we should be careful
    user_set = user_profiles.search(field="email", query=form_uname)
    if not user_set:
        cleaned_uname = clean_username(form_uname)
        user_set = user_profiles.search(field="username", query=cleaned_uname)
    
    if user_set:
        #   the results of search are always a list, in this case it should
        #   be a list of exactly one thing
        user_record = user_set[0]
        password = crypt_password(form_password, user_record)
        if user_record['password'] == password:

            user = RebertUser()
            #user.id = user_record['email']
            user.id = user_record['account_id']
            user.account_id = user_record['account_id']
            user.record = user_record
            flask_login.login_user(user)
            #
            #   Login success, show them the user update page for now
            #   there might be a better page to show them
            user_record = flask_login.current_user.record
            #page = render_template("user_profile.html",
            #                        session = session_state,
            #                        rec = user_record)
            #return page
            #
            #   This doesn't quite work - need another way of doing the
            #   redirect - while including post or query string args
            #rating_url = f'rate_movies?session_id={session_id}'
            #return redirect(url_for(rating_url))
            #
            #   After a selective import we can just call the
            #   function that will serve the rating page
            return serve_rating_page(request, server_state)

    #
    #   Render the user login page, but with a failure message
    page = render_template("user_login.html",
                           error = REBERT_LOGIN_ERROR_MESSAGE,
                           session = {'session_id':session_id})
    return page



##############
#
#   SHOW OR UPDATE THE USER PROFILE
#
##############

#@flask_login.login_required
def serve_update_profile(request, server_state):
    #
    #   If this was just a 'GET' then produce the form page for this
    if request.method == 'GET':
        #   Get the session id from the URL
        session_id = secure_filename(str(escape(request.args.get('session_id'))))    
        #   This page needs to be 'filled in" with the current user information
        user_record = flask_login.current_user.record
        page = render_template("user_profile.html",
                               session = {'session_id':session_id},
                               rec = user_record)
        return page
    #
    session_id =  secure_filename(str(escape(request.form["session_id"])))
    #   
    #   This simulates the post back to update the page
    #the_user_id = flask_login.current_user.id
    user_record = flask_login.current_user.record
    page = render_template("user_profile.html",
                           session = {'session_id':session_id},
                           rec = user_record)
    return page
    



##############
#
#   UPDATE THE USER PASSWORD - "Security"
#
##############
#
#@flask_login.login_required
def serve_update_password(request, server_state):
    #
    #   If this was just a 'GET' then produce the form page for this
    if request.method == 'GET':
        #   Get the session id from the URL
        session_id = secure_filename(str(escape(request.args.get('session_id'))))    
        page = render_template("update_password.html",
                               session = {'session_id':session_id})
        return page
    #
    session_id =  secure_filename(str(escape(request.form["session_id"])))
    #   This simulates the post back to update the page
    #   Here we would extract the passwords and update the user record
    #the_user_id = flask_login.current_user.id
    the_user_id = flask_login.current_user.account_id
    page = render_template("update_password.html",
                            session = {'session_id':session_id})

    return page
#
#
#   This just performs the logout. The WSGI logout function actually generates
#   the mainpage. This does not need to produce page output
#
def serve_user_logout(request, server_state):
    session_id = ""
    #   If this was just a 'GET' then produce the form page for this
    if request.method == 'GET':
        #   Get the session id from the URL
        session_id = secure_filename(str(escape(request.args.get('session_id'))))    
    elif request.method == 'POST':
        #   Get the session id from the post form
        session_id =  secure_filename(str(escape(request.form["session_id"])))
    #
    #   THERE MAY BE MORE WORK HERE - UPDATE DBS
    #
    flask_login.logout_user()    
    #
    #   Not using this now
    #session_state = load_session_state(session_id)
    #
    return
#
#
