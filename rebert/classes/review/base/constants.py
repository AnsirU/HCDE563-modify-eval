#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: constants.py
#   REVISION: June, 2025
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   These are a set of constants that support ReviewArticleRequests and ReviewBrowseRequest 
#   related classes.
#
#   The MOVIE_REVIEW_DATA_TEMPLATE is the main data structure, dictionary, that is collected 
#   and returned when making requests for movie reviews. A subclass may extend this dictionay with
#   additional fields that are specific to that review site - but should attempt to fill out all
#   of the fields as completely as possible.
#
#{{RELEASE}}
#
#{{COPYRIGHT_NOTICE}}
#
###
#
#
#####
#   
#   CONSTANTS
#   
#####

#
#   Dictionary template that will be used to return the review text
#
MOVIE_REVIEW_DATA_TEMPLATE = {
    'title'             : "",   # the movie title
    'review_type'       : "",   # what kind of review - hopefull just 'movie'
    'review_url'        : "",   # the URL to the review article
    'review_title'      : "",   # the title of the review article
    'review_date_str'   : "",   # the string version of the article post date
    'review_date_ts'    : "",   # a timestame string of post date (standardized)
    'rating'            : 0,    # a numeric score for the film
    'rating_str'        : "",   # a string version of the score
    'author'            : "",   # the review article author
    'review'            : "",   # the body/text of the review
    'synopsis'          : "",   # a short synopsis of the movie
    'poster_url'        : "",   # a URL to a version of the movie poster
    'source'            : ""    # the website (source) of the reiew
}
#
#   The number of requests per second (RPS) that a managed article collector
#   will use when set up by a ReviewBrowseBase type object. This is meant to be
#   a little slow so that we don't abuse the remote data source.
REBERT_ARTICLE_COLLECTOR_RPS = 2.0
#
#   Generally, a browse will first collect a bunch of articles before the next
#   browse page request, so this goes much slower by default. We'll still set
#   this to somewhat slowly collect browse pages.
REBERT_BROWSE_COLLECTOR_RPS = 0.5
#
#   The object restricts the number 'browse' pages it will go back
#   in time. This is somwhat arbitrary. Different review sites have
#   different 'max' values. The goal is to collect *recent* reviews
#   so, we don't really need to go back in time very far.
#
REVIEW_BROWSE_INDEX_MAX = 10
REVIEW_BROWSE_INDEX_MAX = 1265
#
#   When collecting using the getReviewsUntil() method, if no date is given
#   then this will default to 23 days prior to the current date. Some review
#   sites don't publish a lot of reviews each week. Using this window might
#   get 10 reviews for most review sites. 
#
REVIEW_BROWSE_PRIOR_OFFSET = 23
#
#   A maximum number of days to go back in time. This is somewhat arbitrary,
#   but the goal here is to prevent an accidential long runing attack on a 
#   review website
#
REVIEW_BROWSE_PRIOR_MAX = 90
#
#   Just a quick note. Near the end of June 2024 each review site had
#   the following max number of *browse* pages:
#
#   The Guardian            1232    https://www.theguardian.com/film+tone/reviews
#   The New York Post        150    https://nypost.com/tag/movie-reviews/
#   The Hollywood Reporter   625    https://www.hollywoodreporter.com/c/movies/movie-reviews/
#   Screen Rant               75    https://screenrant.com/movie-reviews/
#   Roger Ebert              500    https://www.rogerebert.com/reviews
#   Plugged In               473    https://www.pluggedin.com/movie-reviews
#
#   At the end of June 2025 the max browse indexes were approximately.
#   Slant Magazine           845    https://www.slantmagazine.com/category/film/page/845/
#   Film Threat              285    https://filmthreat.com/category/reviews/page/285/
#
#
#   The Associated Press just maintains one browse page:
#   The Associated Press       1    https://apnews.com/hub/film-reviews
#   For "prior" AP reviews one would need to build a class to interface with the AP Archive
#   or build a class to search Rotten Tomatoes 'publications' for movies.
#





if __name__ == '__main__':
    print("contants.py is a python file with no main()")


