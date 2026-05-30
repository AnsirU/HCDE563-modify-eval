#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: tmdb_genres.py
#   REVISION: February, 2025
#   CREATION DATE: February, 2025
#   Author: David W. McDonald
#
#   A set of constants - and a bit of code to convert tmdb genre ids into text equivalent
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#

#
#   This is a dictionary that maps TMDB genre ids to their string terms. This is a merged
#   set for movies and TV. This list was last updated in early 2025
#
TMDB_GENRES_MERGED_FORWARD = {
    '12': "Adventure",
    '14': "Fantasy",
    '16': "Animation",
    '18': "Drama",
    '27': "Horror",
    '28': "Action",
    '35': "Comedy",
    '36': "History",
    '37': "Western",
    '53': "Thriller",
    '80': "Crime",
    '99': "Documentary",
    '878': "Science Fiction",
    '9648': "Mystery",
    '10402': "Music",
    '10749': "Romance",
    '10759': "Action & Adventure",
    '10751': "Family",
    '10752': "War",
    '10762': "Kids",    
    '10763': "News",
    '10764': "Reality",
    '10765': "Sci-Fi & Fantasy",
    '10766': "Soap",
    '10767': "Talk",
    '10768': "War & Politics",
    '10770': "TV Movie"
}

#
#   Convert a single id or a list of ids to their terms
#
def convert_tmdb_genre_ids_to_terms(data, skip=False):
    results = list()
    #   
    if isinstance(data,int):
        #  Assume its a number thing and convert it
        try:
            results.append(TMDB_GENRES_MERGED_FORWARD[str(data)])
        except:
            if not skip:
                results.append(data)
    elif isinstance(data,str):
        #  Assume its a number thing and convert it
        try:
            results.append(TMDB_GENRES_MERGED_FORWARD[data])
        except:
            if not skip:
                results.append(data)
    elif isinstance(data,list):
        #  Assume its a number thing and convert it
        for item in data:
            try:
                results.append(TMDB_GENRES_MERGED_FORWARD[str(item)])
            except:
                if not skip:
                    results.append(data)
    return results


if __name__ == '__main__':
    print("tmdb_genres.py has no main()")

