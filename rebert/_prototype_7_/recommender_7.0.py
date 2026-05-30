#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: recommender_7.0.py
#   REVISION: February, 2025
#   CREATION DATE: February, 2025
#   Author: David W. McDonald
#
import os, sys, time, datetime, webbrowser
#
from rebert.classes.utilities.Args import Args
from rebert._prototype_7_.web.config import *
#
#
SERVER_PROTOCOL = "http://"
#SERVER_PROTOCOL = "https://"
SERVER_LOCALHOST = "127.0.0.1"
SERVER_PORT = 5000
SERVER_SETUP_DELAY = 5.0
SERVER_APP = "web/wsgi"
MOCKUP_APP = "web/mockup"
#
#   The python webbrowser module knows only a certain set of browsers. This is a few
#   of the ones that it knows - and which are quite popular. Check the documentation
#   before adding other browser keys. In many cases the browser needs to be running
#   before the webbrowser module can open the web page.
#
BROWSER_NAMES = ['chrome', 'chromium', 'epiphany', 'firefox', 'konqueror', 
                 'mozilla', 'opera', 'safari', 'default']
BROWSER_DEFAULT = "default"
#
#
#   A template, dictionary, that describes the command line parameters that
#   this program will accept.
PARAMS_TEMPLATE = {
    "-browser" : {
            "required"  : False,        # wether or not this flag is required
            "type"      : str,          # the value type, used for potential conversion
            "notes"     : "<the browser to launch>",     # a note related to the flag
            "default"   : BROWSER_DEFAULT,  # use this browser
            "options"   : BROWSER_NAMES # the set, list of browsers that python knows
        },
    "-delay" : {
            "required"  : False,        # wether or not this flag is required
            "type"      : float,        # the value type, used for potential conversion
            "notes"     : "<delay before browser launch>",     # a note related to the flag
            "default"   : SERVER_SETUP_DELAY,          
            "range"     : [1.0, 180.0]  # range of delay values
        },
    "-mockup" : {
            "required"  : False,        # wether or not this flag is required
            "type"      : bool,         # the value type, used for potential conversion
            "notes"     : "<show the mockup of this prototype>",     # a note related to the flag
            "default"   : False         # don't show the mockup by default
        },
    "-port" : {
            "required"  : False,        # wether or not this flag is required
            "type"      : int,          # the value type, used for potential conversion
            "notes"     : "<server port>", # a note related to the flag
            "default"   : SERVER_PORT   # the default port
        },
    "-app" : {
            "required"  : False, 
            "type"      : str, 
            "notes"     : "<application to be run in the server>", 
            "default"   : SERVER_APP    # launch this default app
        },
    "-help" : {
            "required"  : False, 
            "type"      : bool, 
            "notes"     : "<print help message>", 
            "default"   : False         # don't ask for help by default
        },
    "-h" : {
            "required"  : False, 
            "type"      : bool, 
            "notes"     : "<print help message>", 
            "default"   : False          # don't ask for help by default
        }
    }
#
#
#
#   Check whether or not the movie data file exists. This determines whether or not
#   the code launches the collection from setup.py. That collection can take a long 
#   time. This is currently set to only collect once per day, upon a launch of the
#   server
#
def movie_data_exists():
    current_time = datetime.datetime.now()
    date_str = str(current_time).partition(' ')[0]
    date_str = date_str.replace('-','')
    data_filename = REBERT_DATA_FILE_TEMPLATE.format(ver=REBERT_VERS,
                                                     date_str=date_str)
    data_file_path = os.path.join(REBERT_TEMP_FILE_DIRECTORY,data_filename)
    return os.path.isfile(data_file_path)
#
#
#   Use the python webbrowser module to get that browser application, launch it.
#   The module doesn't always launch the browser. This often works better if
#   you already have the web browser running on your machine
#
def select_browser(browser_name=""):
    browser = None
    if browser_name=='default':
        # the 'default' should get the default browser
        browser = webbrowser.get()
    elif browser_name in BROWSER_NAMES:
        browser = webbrowser.get(browser_name)
    else:
        # not recognized, then get the default browser
        browser = webbrowser.get()
    return browser
#
#
def main():
    #   Parse the command line params
    p = Args(template=PARAMS_TEMPLATE)
    p.parse(sys.argv)
    #
    #   If the help flag is on the command line show help and exit
    if p['help'] or p['h']:
        p.usage(sys.argv)
        return
    #
    #   Flask --app uses paths relative to the current working directory (e.g. web/wsgi).
    #   config.py also uses relative paths (e.g. web/tmp). If the user runs this script
    #   from the repo root, chdir here so imports and data files resolve correctly.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    #
    if p['mockup']:
        #   Launch the server with the current mockup
        launch_command = f"flask --app {MOCKUP_APP} run --port {p['port']}"
        print(f"Launching mockup app: '{MOCKUP_APP}'")
    else:
        #   Get ready to launch the server and point a browser at it
        launch_command = f"flask --app {p['app']} run --port {p['port']}"
    #
    #   Launch the server, either with the mockup or the full app
    server_output_pipe = os.popen(launch_command)
    #
    #   We only try to launch a browser and automatically connect if
    #   the rebert data already exists or if we're just shoing the mockup
    if p['mockup'] or movie_data_exists():
        #   Try to launch a browser, with the server's URL
        try:
            time.sleep(p['delay'])
            server_url = SERVER_PROTOCOL+SERVER_LOCALHOST+":"+str(p['port'])
            browser = select_browser(p['browser'])
            browser.open(server_url,new=1)
        except Exception as e:
            print(str(e))
            print(f"Was not able to launch the '{p['browser']}' browser.")
    else:
        print("NOTE: The rebert server needs to create a data file containing updated movie data.")
        print("This can take several minutes. A web browser will NOT be launched. Follow the instructions")
        print("below to launch your browser and connect to the server using the indicated URL.")
    #
    #   Now, start printing the output of the server to the terminal window
    print(server_output_pipe.read())
    return


if __name__ == '__main__':
    main()   

