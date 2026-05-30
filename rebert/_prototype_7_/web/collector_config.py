#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: collector_config.py
#   REVISION: March, 2026
#   CREATION DATE: June, 2025
#   Author: David W. McDonald
#
#   This configuration creates a dictionary for the review collector classes.
#   The goal is to simplify access to a large-ish number of collection objects
#   and allow a simple 'name' style configuration of data collection.
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
##
#
import sys, json, time
#
from rebert.classes.base.Logger import Logger
#
#
#   A complete list of the article collection and browse collection classes
#   This is the set of collectors that might be used with the rebert system
#   NOTE: Not all of these are fully working at all times. Different collectors
#   will have regressions as a function of the individual sites.
#
#
from rebert.classes.review.AP.APBrowseRequest import APBrowseRequest
from rebert.classes.review.AP.APArticleRequest import APArticleRequest
#
from rebert.classes.review.CloseUp.CloseUpBrowseRequest import CloseUpBrowseRequest
from rebert.classes.review.CloseUp.CloseUpArticleRequest import CloseUpArticleRequest
#
from rebert.classes.review.CSM.CSMBrowseRequest import CSMBrowseRequest
from rebert.classes.review.CSM.CSMArticleRequest import CSMArticleRequest
#
from rebert.classes.review.Ebert.EbertBrowseRequest import EbertBrowseRequest
from rebert.classes.review.Ebert.EbertArticleRequest import EbertArticleRequest
#
from rebert.classes.review.FilmThreat.FTBrowseRequest import FTBrowseRequest
from rebert.classes.review.FilmThreat.FTArticleRequest import FTArticleRequest
#
from rebert.classes.review.Guardian.GuardianBrowseRequest import GuardianBrowseRequest
from rebert.classes.review.Guardian.GuardianArticleRequest import GuardianArticleRequest
#
from rebert.classes.review.KIM.KIMBrowseRequest import KIMBrowseRequest
from rebert.classes.review.KIM.KIMArticleRequest import KIMArticleRequest
#
from rebert.classes.review.NYPost.NYPBrowseRequest import NYPBrowseRequest
from rebert.classes.review.NYPost.NYPArticleRequest import NYPArticleRequest
#
from rebert.classes.review.NYTimes.NYTBrowseRequest import NYTBrowseRequest
from rebert.classes.review.NYTimes.NYTArticleRequest import NYTArticleRequest
#
from rebert.classes.review.PluggedIn.PluggedInBrowseRequest import PluggedInBrowseRequest
from rebert.classes.review.PluggedIn.PluggedInArticleRequest import PluggedInArticleRequest
#
from rebert.classes.review.RStone.RSBrowseRequest import RSBrowseRequest
from rebert.classes.review.RStone.RSArticleRequest import RSArticleRequest
#
from rebert.classes.review.SRant.SRBrowseRequest import SRBrowseRequest
from rebert.classes.review.SRant.SRArticleRequest import SRArticleRequest
#
from rebert.classes.review.Slant.SlantMagBrowseRequest import SlantMagBrowseRequest
from rebert.classes.review.Slant.SlantMagArticleRequest import SlantMagArticleRequest
#
from rebert.classes.review.THR.THRBrowseRequest import THRBrowseRequest
from rebert.classes.review.THR.THRArticleRequest import THRArticleRequest
#
#
#   A dictionary of collector classes - using the short name as a key
#   The site short names are used to select which review collector is
#   used for collecting
#
REVIEW_COLLECTOR_CLASSES = {
    'ap' : {
            'fullname'  : "The Associated Press",
            'browse'    : APBrowseRequest,
            'article'   : APArticleRequest,
            #   The AP maintains exactly 1 browse page
            'pages'     : [1]
    },
    'closeup' : {
            'fullname'  : "Close-up Media",
            'browse'    : CloseUpBrowseRequest,
            'article'   : CloseUpArticleRequest,
            'pages'     : [1, 2, 3]
    },
    'csm' : {
            'fullname'  : "Common Sense Media",
            'browse'    : CSMBrowseRequest,
            'article'   : CSMArticleRequest,
            'pages'     : [1, 2, 3]
    },
    'ebert' : {
            'fullname'  : "Roger Ebert",
            'browse'    : EbertBrowseRequest,
            'article'   : EbertArticleRequest,
            'pages'     : [1, 2, 3]
    },
    'fthreat' : {
            'fullname'  : "Film Threat",
            'browse'    : FTBrowseRequest,
            'article'   : FTArticleRequest,
            'pages'     : [1, 2, 3]
    },
    'guardian' : {
            'fullname'  : "The Guardian",
            'browse'    : GuardianBrowseRequest,
            'article'   : GuardianArticleRequest,
            'pages'     : [1, 2, 3, 4, 5, 6]
    },
    'kim' : {
            'fullname'  : "Kids-in-Mind",
            'browse'    : KIMBrowseRequest,
            'article'   : KIMArticleRequest,
            'pages'     : [1, 2, 3]
    },
    'nypost' : {
            'fullname'  : "The New York Post",
            'browse'    : NYPBrowseRequest,
            'article'   : NYPArticleRequest,
            'pages'     : [1, 2, 3]
    },
    'nytimes' : {
            'fullname'  : "The New York Times",
            'browse'    : NYTBrowseRequest,
            'article'   : NYTArticleRequest,
            'pages'     : [1, 2, 3]
    },
    'pluggedin' : {
            'fullname'  : "Plugged In",
            'browse'    : PluggedInBrowseRequest,
            'article'   : PluggedInArticleRequest,
            'pages'     : [1, 2, 3]
    },
    'rstone' : {
            'fullname'  : "Rolling Stone",
            'browse'    : RSBrowseRequest,
            'article'   : RSArticleRequest,
            #   Rolling Stone only has 1 or 2 'reviews' per browse page, so we
            #   collect a lot more browse pages to get a good window of reviews
            'pages'     : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    },
    'slant' : {
            'fullname'  : "Slant Magazine",
            'browse'    : SlantMagBrowseRequest,
            'article'   : SlantMagArticleRequest,
            'pages'     : [1, 2, 3]
    },
    'srant' : {
            'fullname'  : "Screen Rant",
            'browse'    : SRBrowseRequest,
            'article'   : SRArticleRequest,
            'pages'     : [1, 2, 3]
    },
    'thr' : {
            'fullname'  : "The Hollywood Reporter",
            'browse'    : THRBrowseRequest,
            'article'   : THRArticleRequest,
            'pages'     : [1, 2, 3]
    }
}
#
#
#   A list of the known, configured collection classes. The keys in the
#   dictionary of the review collectors, defines the set of short names
#   that can be used to configure the rebert movie review collection
#
SITE_SHORT_NAMES = list( REVIEW_COLLECTOR_CLASSES.keys() )

