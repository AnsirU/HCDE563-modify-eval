#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: mockup.py
#   REVISION: November, 2024
#   CREATION DATE: June, 2024
#   Author: David W. McDonald
#
#   This will display a non-interactive mockup of the prototype
#
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
##
#
import sys, os, datetime, hashlib, json, copy

from flask import Flask, request, render_template
from markupsafe import escape
#
#   Required set up before anything happens
app = Flask(__name__)
#   This also seems to work
#app = Flask("rebert._prototype_7_.web.wsgi")
#
##############
#
#   HOME PAGE GENERATION
#
##############
@app.route("/")
def home_page():
    page = render_template("mockup.html")
    return page

@app.post("/")
def generate_rebert_response():
    page = render_template("mockup.html")
    return page


