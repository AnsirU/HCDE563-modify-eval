#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: wsgi.py
#   REVISION: November, 2024
#   CREATION DATE: June, 2024
#   Author: David W. McDonald
#
#   Rebert server web page dispatch. This maps the incoming URLs to specific functions
#   in the code base.
#
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
##
#
import sys, os

from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
#
from rebert.classes.data.KeyManager import KeyManager
#
from rebert._prototype_7_1_.web.config import *
from rebert._prototype_7_1_.web.setup import *
from rebert._prototype_7_1_.web.access_dbs import *
from rebert._prototype_7_1_.web.serve_main_page import *
from rebert._prototype_7_1_.web.serve_ephem_rec import *
from rebert._prototype_7_1_.web.serve_rating import *
from rebert._prototype_7_1_.web.serve_login import *
#
#   Required set up before any serving actions
app = Flask(__name__)
#   This also seems to work
#app = Flask("rebert._prototype_7_1_.web.wsgi")
#
#   We need to set the 'secret_key' attribute on the Flask app. The
#   app.secret_key is used for signing session cookies, this should
#   not be visible in the code - we'll use the KeyManager to save/restore
#   the secret value. This is the same key management techniques that we
#   use for accessing any other controlled API
#
key_manager = KeyManager()
#   The KeyManager was used to set up a set of long-ish secret tokens. These
#   can be rotated/swapped any time the server is rebooted. Here we just pick
#   one of them (registered under recs.rebert.net; see register_rec_server_key.py).
key_list = key_manager.findRecord(username="rebert.server0",
                                  domain="recs.rebert.net")
#key_list = key_manager.findRecord(username="rebert.server1")
#key_list = key_manager.findRecord(username="rebert.server2")
#key_list = key_manager.findRecord(username="rebert.server3")
#
if not key_list:
    raise RuntimeError(
        "No KeyManager record for username='rebert.server0' domain='recs.rebert.net'. "
        "Register one with: PYTHONPATH=<repo-root> python3 rebert/tools/register_rec_server_key.py '<secret>'"
    )
#   Now set the secret - this is used by the login manager to sign cookies 
app.secret_key = key_list[0]['key']
#
#   Set up the Flask login manager - it must also be given the 'app'
#login_manager = flask_login.LoginManager() - this is in utilities.py
login_manager.init_app(app) 
#
#
#
global SERVER_STATE
SERVER_STATE = initalize_server_state()
#
#
MODULE_WSGI_DEBUG = True
#
if not MODULE_DEBUG_OVERRIDE:
    MODULE_WSGI_DEBUG = GLOBAL_DEBUG
#
#
#
##############
#
#   HOME PAGE GENERATION
#
##############
@app.route("/", methods=['GET', 'POST'])
def home_page():
    #   comes from serve_main_page.py
    page = serve_home_page(request, SERVER_STATE)
    return page


##############
#
#   ASK REBERT PAGE GENERATION
#
##############
#
@app.route("/ask_rebert", methods=['POST'])
def ask_rebert():
    #   comes from serve_main_page.py
    page = serve_ask_rebert_response(request, SERVER_STATE)
    return page


##############
#
#   EPHEMERAL RECOMMENDATION GENERATION
#
##############
#
@app.route("/next_question", methods=['POST'])
def ephem_next_question():
    #   comes from serve_ephem_rec.py
    page = serve_next_ephem_question(request, SERVER_STATE)
    return page
#
#
@app.route("/ephem_recommend", methods=['POST'])
def ephem_recommendation():
    #   comes from serve_ephem_rec.py
    page = serve_ephem_recommendation(request, SERVER_STATE)
    return page


##############
#
#   USER LOGIN AND AUTHENTICATION
#
##############
#
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    #   comes from serve_login.py
    page = serve_create_account(request, SERVER_STATE)
    return page
#
#
@app.route("/signin_page", methods=['GET'])
def signin_page():
    #   comes from serve_login.py
    #   show the signin or login page
    page = serve_signin_page(request, SERVER_STATE)
    return page
#
#
@app.route('/user_login', methods=['POST'])
def user_login():
    #   comes from serve_login.py
    #   process the user authentication
    page = serve_user_login(request, SERVER_STATE)
    return page
#
#
@app.route('/user_profile', methods=['GET', 'POST'])
@flask_login.login_required
def update_profile():
    #   comes from serve_login.py
    page = serve_update_profile(request, SERVER_STATE)
    return page
#
#
@app.route('/user_security', methods=['GET', 'POST'])
@flask_login.login_required
def update_password():
    #   comes from serve_login.py
    page = serve_update_password(request, SERVER_STATE)
    return page
#
#
@app.route('/user_logout', methods=['GET', 'POST'])
def user_logout():
    #   comes from serve_login.py
    #   Logout the user
    serve_user_logout(request, SERVER_STATE)
    #   comes from serve_main_page.py
    #   Then show them the main page
    page = serve_home_page(request, SERVER_STATE)
    return page
#
#
@login_manager.unauthorized_handler
def unauthorized_handler():
    session_id = ""
    #   If this was just a 'GET' then produce the form page for this
    if request.method == 'GET':
        #   Get the session id from the URL
        session_id = secure_filename(str(escape(request.args.get('session_id'))))    
    elif request.method == 'POST':
        #   Get the session id from the post form
        session_id =  secure_filename(str(escape(request.form["session_id"])))
    #
    #   Render the restricted resource page
    page = render_template("restricted.html",
                            session = {'session_id':session_id})
    return page


##############
#
#   PREFERENCE ELICITATION - RATING GENERATION
#
##############
#
@app.route("/rate_movies", methods=['GET', 'POST'])
@flask_login.login_required
def rate_movies():
    #   comes from serve_rating.py
    page = serve_rating_page(request, SERVER_STATE)
    return page
#
#
@app.route("/rating_next", methods=['POST'])
@flask_login.login_required
def rate_next_question():
    #   comes from serve_rating.py
    page = serve_rating_next(request, SERVER_STATE)
    return page
#
#
@app.route("/rating_edit", methods=['GET', 'POST'])
@flask_login.login_required
def rate_edit_rating():
    #   comes from serve_rating.py
    page = serve_rating_edit_rating(request, SERVER_STATE)
    return page
#
#
@app.route("/transcribe", methods=['POST'])
@flask_login.login_required
def rate_transcribe():
    #   comes from serve_rating.py
    page = serve_transcribe_rating_audio(request, SERVER_STATE)
    return page
#
#
@app.route("/movie_info", methods=['GET','POST'])
@flask_login.login_required
def movie_info():
    #   comes from serve_rating.py
    page = serve_movie_data_request(request, SERVER_STATE)
    return page



