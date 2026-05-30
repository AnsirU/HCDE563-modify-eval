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

from flask import Flask, request
#
#
from rebert._prototype_7_.web.config import *
from rebert._prototype_7_.web.setup import *
from rebert._prototype_7_.web.serve_main_page import *
from rebert._prototype_7_.web.serve_ephem_rec import *
from rebert._prototype_7_.web.serve_rating import *
#
#   Required set up before any serving actions
app = Flask(__name__)
#   This also seems to work
#app = Flask("rebert._prototype_7_.web.wsgi")
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
#   PREFERENCE ELICITATION - RATING GENERATION
#
##############
#
@app.route("/rate_movies", methods=['GET', 'POST'])
def rate_movies():
    #   comes from serve_rating.py
    page = serve_rating_page(request, SERVER_STATE)
    return page
#
#
@app.route("/rating_next", methods=['POST'])
def rate_next_question():
    #   comes from serve_rating.py
    page = serve_rating_next(request, SERVER_STATE)
    return page
#
#
@app.route("/rating_edit", methods=['GET', 'POST'])
def rate_edit_rating():
    #   comes from serve_rating.py
    page = serve_rating_edit_rating(request, SERVER_STATE)
    return page
#
#
@app.route("/transcribe", methods=['POST'])
def rate_transcribe():
    #   comes from serve_rating.py
    page = serve_transcribe_rating_audio(request, SERVER_STATE)
    return page
#
#
@app.route("/movie_info", methods=['GET','POST'])
def movie_info():
    #   comes from serve_rating.py
    page = serve_movie_data_request(request, SERVER_STATE)
    return page



