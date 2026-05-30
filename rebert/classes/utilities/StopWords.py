#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: StopWords.py
#   REVISION: October, 2024
#   CREATION DATE: January, 2020
#   AUTHOR: David W. McDonald
#
#   Implementation of a simple stop word removal tool as a class. This includes different
#   size stop word lists. 
#   
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
from rebert.classes.base.Object import Object


#####
#   
#   START class StopWords definition
#   
#####
#
#
###
#   A class/object that implements stop word checking
#
class StopWords(Object):
    '''
    The Args class implements a basic command line argument parser. The model is based
    on creating a template dictionary, where the keys to the dictionary are the
    command line parameters that are to be extracted from the command line. How to
    treat the values extracted is specified by an optional dictionary associated with
    each template key.
    
    Attributes:
        __stops__               - a local copy of the command line arguments
        case_sensitive          - a local copy of the specification template
    
    Methods:
        extendStopWords()       - add a list or dictionary of new stop words
        isStopWord()            - check if the supplied word is a stop word
        getStops()              - return a list of the stop words used by this object
        __contains__()          - implements the 'in' operator on this object
        
    '''

    def __init__(self, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        size        : An optional term that describes the size of the stopword list
        '''
        super().__init__(*args, **kwargs)       
        
        #
        #   Start by ignoring the word/term case
        self.case_sensitive = False
        #   Initialize a reasonable size stop word list
        self.__stops__ = UTILITIES_STOP_WORDS_SHORT.copy()
        #
        #   If the 'size' parameter is provided, them we look to see if that is one of
        #   the sizes that we know, and set the stops for that
        if "size" in kwargs:
            sw_size = kwargs["size"].lower()
            #   Check, do we know that size description
            if sw_size == "tiny":
                self.__stops__ = UTILITIES_STOP_WORDS_TINY.copy()
            if (sw_size == "small") or (sw_size == "short") or (sw_size == "google"):
                self.__stops__ = UTILITIES_STOP_WORDS_SHORT.copy()
            if (sw_size == "mysql") or (sw_size == "sql"):
                self.__stops__ = UTILITIES_STOP_WORDS_MYSQL.copy()
            if (sw_size == "huge") or (sw_size == "big"):
                self.__stops__ = UTILITIES_STOP_WORDS_EXTENSIVE.copy()
        return
    
    
    #
    #   Add a list or dict of additional stop words
    #
    def extendStopWords(self, new_stops=None, replace=False):
        '''
        Extend the current set of stopwords with a list or dictionary. If dictionary, then
        the keys of the dictionary are used as the stopwords
        
        new_stops   : A list or dictionary of stop words to add to current set
        replace     : Set to True if new_stops should replace existing stop words
        '''
        if replace:
            self.__stops__ = dict()
        if isinstance(new_stops,dict):
            if self.case_sensitive:
                self.__stops__.update(new_stops)
            else:
                keys = new_stops.keys()
                for k in keys:
                    self.__stops__[str(k).lower()]=1
        elif isinstance(new_stops,list):
            for k in new_stops:
                if self.case_sensitive:
                    self.__stops__[str(k)]=1
                else:
                    self.__stops__[str(k).lower()]=1
        return


    
    #
    #   Check whether or not a word is a stop word
    #
    def isStopWord(self, word=None):
        '''
        Check whether the supplied word is a stop word. Returns True if it is a stopword.
        
        word        : A str, word or token to check
        
        Return
            Will return a True value if the word/token is a stopword
        '''
        #  empty anything should be removed
        if not word: return True
        #
        if self.case_sensitive:
            if( word in self.__stops__ ):
                return True
        else:
            if( word.lower() in self.__stops__ ):
                return True
        return False



    #
    #   Return a list of the stopwords currently in use
    #
    def getStops(self):
        '''
        Get the list of stop words .
        
        word        : A str, word or token to check
        
        Return
            Will return a True value if the word/token is a stopword
        '''
        if not self.__stops__:
            return list()
        stops = list()
        keys = self.__stops__.keys()
        for k in keys:
            stops.append(str(k))
        return stops


    ##
    #
    #   This implements the use of the 'in' operator 
    #
    def __contains__(self, k): 
        return self.isStopWord(word=k)


#####
#   
#   END class StopWords definition
#   
#####


#   =====
#
#   What follows are dictionaries of stop words of various sizes. One of the main sources for
#   these lists is the site: https://www.ranks.nl/stopwords
#   
#   Some of these lists came from generic sources on the web with general claims about who, what,
#   and when they were being used.
#
#   +++++

#
#   Tiny is roughly 30 words and supposedly used by google up until 2005
#
UTILITIES_STOP_WORDS_TINY = {'this': 1, 'that': 1, 'the': 1, 'be': 1, 'will': 1, 'or': 1, 'for': 1, 'in': 1, 'by': 1, 'a': 1, 'was': 1, 'what': 1, 'as': 1, 'how': 1, 'from': 1, 'where': 1, 'about': 1, 'is': 1, 'who': 1, 'of': 1, 'it': 1, 'at': 1, 'are': 1, 'i': 1, 'on': 1, 'with': 1, 'an': 1, 'to': 1, 'when': 1}
#
#   This was the "google" stop word list as claimed on the web around 2020
#
UTILITIES_STOP_WORDS_SHORT = {'his': 1, "don't": 1, "mustn't": 1, 'having': 1, "weren't": 1, "you're": 1, 'are': 1, 'them': 1, "i've": 1, 'have': 1, 'once': 1, 'when': 1, "that's": 1, "what's": 1, 'an': 1, 'is': 1, "i'd": 1, 'so': 1, 'all': 1, 'at': 1, 'that': 1, 'most': 1, "wouldn't": 1, 'above': 1, 'because': 1, 'few': 1, 'doing': 1, "they'll": 1, "we've": 1, "you'd": 1, 'where': 1, "they've": 1, "who's": 1, "hadn't": 1, 'then': 1, "you've": 1, 'had': 1, 'itself': 1, 'him': 1, "shouldn't": 1, 'not': 1, 'only': 1, "i'll": 1, 'between': 1, "you'll": 1, 'again': 1, 'after': 1, 'how': 1, "can't": 1, 'our': 1, 'under': 1, 'about': 1, 'a': 1, "we'd": 1, 'could': 1, 'until': 1, 'before': 1, 'some': 1, 'with': 1, 'which': 1, 'as': 1, "won't": 1, "they're": 1, "couldn't": 1, 'in': 1, "it's": 1, 'your': 1, 'very': 1, "aren't": 1, "i'm": 1, 'be': 1, 'yourselves': 1, 'being': 1, "we're": 1, 'their': 1, 'was': 1, 'if': 1, 'own': 1, 'my': 1, 'ours': 1, 'below': 1, 'ought': 1, 'by': 1, 'to': 1, 'cannot': 1, 'they': 1, "he'll": 1, 'over': 1, "she'll": 1, 'more': 1, 'what': 1, 'do': 1, 'on': 1, 'myself': 1, 'me': 1, 'himself': 1, 'yourself': 1, 'these': 1, 'any': 1, 'both': 1, 'and': 1, 'no': 1, 'we': 1, 'she': 1, 'such': 1, 'has': 1, 'too': 1, 'does': 1, "doesn't": 1, 'been': 1, 'into': 1, 'its': 1, 'while': 1, 'or': 1, 'who': 1, "hasn't": 1, 'each': 1, 'up': 1, 'hers': 1, "wasn't": 1, 'he': 1, 'but': 1, "isn't": 1, 'themselves': 1, 'here': 1, 'further': 1, "she'd": 1, 'down': 1, "we'll": 1, 'would': 1, "he'd": 1, "when's": 1, 'you': 1, "let's": 1, 'there': 1, 'for': 1, 'am': 1, 'other': 1, 'why': 1, 'i': 1, 'did': 1, "they'd": 1, "there's": 1, "she's": 1, 'it': 1, 'against': 1, 'were': 1, 'ourselves': 1, "why's": 1, "here's": 1, 'same': 1, 'off': 1, 'out': 1, 'through': 1, 'the': 1, "where's": 1, 'whom': 1, "shan't": 1, 'during': 1, 'herself': 1, "haven't": 1, "how's": 1, "didn't": 1, "he's": 1, 'theirs': 1, 'than': 1, 'yours': 1, 'should': 1, 'from': 1, 'this': 1, 'of': 1, 'nor': 1, 'her': 1, 'those': 1}
#
#   The set of stop words, 543 words, used by MySQL
#
UTILITIES_STOP_WORDS_MYSQL = {'however': 1, 'rather': 1, 'indeed': 1, 'corresponding': 1, 'now': 1, 'self': 1, 'placed': 1, 'truly': 1, 'merely': 1, 'say': 1, 're': 1, "what's": 1, 'onto': 1, 'her': 1, 'must': 1, 'whenever': 1, 'mostly': 1, 'some': 1, 'only': 1, 'shall': 1, 'concerning': 1, 'further': 1, 'nine': 1, 'regarding': 1, 'nevertheless': 1, 'others': 1, 'at': 1, 'yourself': 1, 'well': 1, 'everywhere': 1, 'something': 1, 'ex': 1, 'consider': 1, 'certain': 1, 'sensible': 1, 'six': 1, 'without': 1, 'his': 1, 'could': 1, 'ignored': 1, 'above': 1, 'between': 1, 'since': 1, 'zero': 1, 'like': 1, 'known': 1, 'provides': 1, 'various': 1, "you'd": 1, 'more': 1, 'gotten': 1, 'into': 1, 'almost': 1, 'within': 1, 'knows': 1, 'after': 1, 'before': 1, 'changes': 1, 'theirs': 1, 'away': 1, 'thanx': 1, 'brief': 1, 'down': 1, "it'd": 1, 'howbeit': 1, "don't": 1, 'seriously': 1, 'whereafter': 1, 'that': 1, 'might': 1, 'often': 1, 'should': 1, 'no': 1, 'because': 1, 'beside': 1, 'comes': 1, 'help': 1, 'several': 1, 'he': 1, 'which': 1, 'becoming': 1, 'somewhat': 1, 'sent': 1, 'hereupon': 1, 'thats': 1, 'nd': 1, 'unlikely': 1, 'greetings': 1, 'way': 1, 'instead': 1, "weren't": 1, 'using': 1, 'two': 1, "i'd": 1, 'un': 1, 'whatever': 1, 'co': 1, 'besides': 1, 'take': 1, 'theres': 1, 'lest': 1, 'may': 1, "you'll": 1, 'next': 1, 'furthermore': 1, 'sometimes': 1, 'anywhere': 1, 'liked': 1, 'having': 1, 'seem': 1, 'already': 1, 'and': 1, 'their': 1, 'you': 1, 'ought': 1, 'even': 1, 'really': 1, 'am': 1, 'apart': 1, 'sup': 1, 'had': 1, 'believe': 1, 'over': 1, 'quite': 1, 'off': 1, 'very': 1, 'came': 1, "i've": 1, 'although': 1, "t's": 1, 'until': 1, "hasn't": 1, 'therein': 1, 'cause': 1, 'there': 1, 'tends': 1, 'thorough': 1, 'downwards': 1, 'hi': 1, 'mean': 1, 'secondly': 1, 'alone': 1, 'viz': 1, 'those': 1, 'follows': 1, 'wants': 1, 'seeing': 1, 'lately': 1, 'able': 1, "we'll": 1, 'about': 1, 'somebody': 1, 'among': 1, 'themselves': 1, 'near': 1, "we're": 1, 'if': 1, 'better': 1, 'itself': 1, 'own': 1, 'currently': 1, 'sorry': 1, 'following': 1, 'to': 1, 'first': 1, 'specifying': 1, 'be': 1, 'whither': 1, 'despite': 1, "let's": 1, 'they': 1, "i'll": 1, 'specified': 1, 'him': 1, 'everyone': 1, 'oh': 1, 'amongst': 1, 'says': 1, "ain't": 1, 'indicate': 1, 'unto': 1, 'com': 1, 'relatively': 1, 'thereupon': 1, 'anybody': 1, "they've": 1, 'rd': 1, 'nor': 1, 'many': 1, 'few': 1, 'look': 1, "wouldn't": 1, 'regardless': 1, 'whereupon': 1, 'so': 1, 'most': 1, 'us': 1, 'tries': 1, 'why': 1, 'need': 1, 'in': 1, 'inasmuch': 1, 'accordingly': 1, 'taken': 1, "he's": 1, 'usually': 1, 'kept': 1, 'formerly': 1, 'was': 1, 'around': 1, "c'mon": 1, 'still': 1, 'non': 1, 'eg': 1, 'presumably': 1, 'appropriate': 1, 'on': 1, 'according': 1, 'think': 1, 'has': 1, 'willing': 1, 'right': 1, 'perhaps': 1, 'thank': 1, 'been': 1, 'my': 1, 'eight': 1, 'against': 1, 'moreover': 1, 'containing': 1, 'by': 1, 'she': 1, 'definitely': 1, 'both': 1, 'indicates': 1, 'go': 1, 'other': 1, 'new': 1, 'then': 1, 'third': 1, 'whence': 1, 'etc': 1, 'seeming': 1, 'know': 1, "it's": 1, 'last': 1, 'any': 1, 'least': 1, 'towards': 1, 'five': 1, "they'd": 1, 'course': 1, 'ourselves': 1, 'whereas': 1, 'else': 1, "wasn't": 1, 'your': 1, 'seems': 1, 'exactly': 1, 'via': 1, 'gets': 1, "haven't": 1, 'fifth': 1, 'different': 1, 'too': 1, "we've": 1, 'along': 1, 'respectively': 1, 'but': 1, 'yet': 1, 'especially': 1, 'seven': 1, 'throughout': 1, 'whoever': 1, 'available': 1, 'ask': 1, 'wonder': 1, 'across': 1, 'edu': 1, 'hereafter': 1, 'let': 1, "a's": 1, "there's": 1, 'its': 1, 'somewhere': 1, 'does': 1, 'needs': 1, 'just': 1, 'through': 1, 'will': 1, 'asking': 1, 'contains': 1, 'anyone': 1, 'together': 1, 'keeps': 1, 'nowhere': 1, 'contain': 1, 'than': 1, 'et': 1, 'would': 1, 'wherein': 1, 'latterly': 1, 'second': 1, 'anything': 1, 'ltd': 1, 'from': 1, 'one': 1, 'none': 1, 'toward': 1, 'became': 1, 'gone': 1, 'allow': 1, 'yourselves': 1, 'reasonably': 1, 'when': 1, 'it': 1, 'sometime': 1, 'anyways': 1, 'former': 1, 'thence': 1, 'except': 1, 'yes': 1, 'saw': 1, 'took': 1, 'thereafter': 1, 'unfortunately': 1, 'mainly': 1, 'gives': 1, 'elsewhere': 1, 'seemed': 1, 'for': 1, 'particular': 1, 'come': 1, 'neither': 1, 'the': 1, 'vs': 1, 'going': 1, 'actually': 1, 'thus': 1, 'become': 1, 'per': 1, 'doing': 1, 'anyway': 1, 'though': 1, 'wherever': 1, 'consequently': 1, 'ok': 1, 'anyhow': 1, "you've": 1, 'three': 1, 'somehow': 1, "you're": 1, 'below': 1, 'are': 1, 'herein': 1, 'forth': 1, 'these': 1, 'with': 1, 'each': 1, 'here': 1, 'immediate': 1, 'were': 1, 'can': 1, 'do': 1, 'afterwards': 1, "can't": 1, 'keep': 1, 'selves': 1, 'whereby': 1, 'twice': 1, 'how': 1, 'little': 1, 'certainly': 1, 'whose': 1, 'also': 1, 'necessary': 1, 'old': 1, 'cannot': 1, 'enough': 1, 'did': 1, 'hers': 1, 'th': 1, 'indicated': 1, "hadn't": 1, 'particularly': 1, 'of': 1, 'useful': 1, 'whether': 1, 'followed': 1, 'becomes': 1, 'every': 1, "it'll": 1, 'again': 1, 'said': 1, 'this': 1, "doesn't": 1, 'all': 1, "shouldn't": 1, 'another': 1, 'described': 1, "they'll": 1, 'considering': 1, 'try': 1, 'normally': 1, 'want': 1, 'got': 1, 'went': 1, 'best': 1, 'hence': 1, "who's": 1, 'beforehand': 1, 'obviously': 1, 'appear': 1, 'please': 1, 'once': 1, 'our': 1, 'noone': 1, 'inc': 1, 'someone': 1, 'such': 1, 'nothing': 1, 'okay': 1, 'hopefully': 1, 'ever': 1, 'value': 1, 'allows': 1, 'inward': 1, 'get': 1, 'myself': 1, 'less': 1, "we'd": 1, 'unless': 1, 'tell': 1, 'maybe': 1, 'we': 1, 'me': 1, "they're": 1, 'or': 1, 'otherwise': 1, 'under': 1, 'being': 1, 'sure': 1, 'thru': 1, 'thoroughly': 1, 'novel': 1, 'specify': 1, 'yours': 1, 'them': 1, 'hello': 1, 'cant': 1, 'inner': 1, 'himself': 1, 'plus': 1, "aren't": 1, 'have': 1, 'during': 1, 'soon': 1, 'always': 1, 'ones': 1, 'up': 1, 'far': 1, 'name': 1, 'used': 1, 'qv': 1, 'awfully': 1, 'done': 1, 'entirely': 1, 'goes': 1, 'example': 1, "i'm": 1, 'happens': 1, 'later': 1, 'associated': 1, "that's": 1, 'wish': 1, 'beyond': 1, 'serious': 1, 'use': 1, 'what': 1, 'much': 1, 'sub': 1, 'hither': 1, 'as': 1, 'same': 1, 'either': 1, 'behind': 1, "won't": 1, 'out': 1, 'getting': 1, 'insofar': 1, 'is': 1, 'therefore': 1, 'herself': 1, 'trying': 1, 'who': 1, 'possible': 1, "isn't": 1, 'causes': 1, 'not': 1, 'latter': 1, 'an': 1, 'probably': 1, 'thereby': 1, 'seen': 1, 'outside': 1, "here's": 1, 'ie': 1, 'likely': 1, 'never': 1, 'namely': 1, 'tried': 1, 'see': 1, 'looking': 1, 'hereby': 1, 'hardly': 1, "couldn't": 1, 'ours': 1, "didn't": 1, 'appreciate': 1, 'four': 1, 'while': 1, "where's": 1, 'everything': 1, "c's": 1, 'where': 1, 'aside': 1, 'looks': 1, 'whole': 1, 'given': 1, 'meanwhile': 1, 'upon': 1, 'whom': 1, 'nobody': 1, 'everybody': 1, 'regards': 1, 'nearly': 1, 'thanks': 1, 'saying': 1, 'uses': 1, 'que': 1, 'overall': 1, 'welcome': 1, 'clearly': 1}
#
#   This 'extensive' list came from the site https://www.ranks.nl/stopwords about 2020
#
UTILITIES_STOP_WORDS_EXTENSIVE = {'however': 1, 'rather': 1, "you've": 1, 'effect': 1, 'ran': 1, 'd': 1, 'when': 1, 'sufficiently': 1, 'self': 1, 'placed': 1, 'truly': 1, 'merely': 1, 'say': 1, 're': 1, 'a': 1, 'because': 1, 'indeed': 1, 'past': 1, 'must': 1, 'whenever': 1, 'w': 1, 'mr': 1, 'heres': 1, 'mostly': 1, 'hes': 1, 'only': 1, 'shall': 1, 'oh': 1, 'back': 1, 'nine': 1, 'recent': 1, 'found': 1, 'regarding': 1, 'nevertheless': 1, 'makes': 1, 'at': 1, 'yourself': 1, 'everywhere': 1, 'thru': 1, 'something': 1, 'ex': 1, 'whereas': 1, 'certain': 1, 'therein': 1, 'six': 1, 'without': 1, 'his': 1, 'could': 1, 'thoughh': 1, 'pp': 1, 'gave': 1, 'between': 1, 'since': 1, 'r': 1, 'readily': 1, 'like': 1, 'known': 1, 'provides': 1, 'various': 1, 'more': 1, 'gotten': 1, 'into': 1, 'almost': 1, 'b': 1, 'within': 1, 'knows': 1, 'after': 1, 'before': 1, 'yes': 1, 'briefly': 1, 'keepkeeps': 1, 'away': 1, 'thanx': 1, 'particular': 1, 'obtained': 1, 'brief': 1, 'widely': 1, 'down': 1, 'respectively': 1, 'aren': 1, 'u': 1, 'theyd': 1, 'howbeit': 1, 'abst': 1, "don't": 1, 'put': 1, 'whereafter': 1, 'that': 1, 'obtain': 1, 'might': 1, 'often': 1, 'should': 1, 'no': 1, 'onto': 1, 'theyre': 1, 'do': 1, 'beside': 1, 'k': 1, 'via': 1, 'comes': 1, 'several': 1, 'taking': 1, 'he': 1, 'which': 1, 'becoming': 1, 'somewhat': 1, 'mug': 1, 'wont': 1, 'hereupon': 1, 'otherwise': 1, 'thats': 1, 'shes': 1, 'nd': 1, 'unlikely': 1, 'vols': 1, 'further': 1, 'way': 1, 'instead': 1, 'there': 1, 'using': 1, 'some': 1, "'ve": 1, 'whether': 1, 'un': 1, 'werent': 1, 'co': 1, 'besides': 1, 'pages': 1, 'theres': 1, 'lest': 1, 'may': 1, "there've": 1, 'next': 1, 'furthermore': 1, 'sometimes': 1, 'anywhere': 1, 'id': 1, 'having': 1, 'seem': 1, 'already': 1, 'and': 1, 'their': 1, 'significant': 1, 'you': 1, 'following': 1, 'even': 1, 'really': 1, "what'll": 1, 'suret': 1, 'give': 1, 'apparently': 1, 'e': 1, 'believe': 1, 'herself': 1, 'over': 1, 'f': 1, 'ups': 1, 'ord': 1, 'liked': 1, 'looks': 1, 'very': 1, 'owing': 1, 'came': 1, 'til': 1, 'nos': 1, "i've": 1, 'although': 1, 'until': 1, "hasn't": 1, "that've": 1, 'nonetheless': 1, 'cause': 1, 'o': 1, 'tends': 1, 'million': 1, 'wouldnt': 1, 'downwards': 1, 'hi': 1, 'mean': 1, 'substantially': 1, 'uses': 1, 'necessary': 1, 'viz': 1, 'follows': 1, 'wants': 1, 'kg': 1, 'affected': 1, 'lately': 1, 'how': 1, "we'll": 1, 'resulting': 1, 'showns': 1, 'hed': 1, 'about': 1, 'somebody': 1, 'among': 1, 'whos': 1, 'themselves': 1, 'near': 1, 'whod': 1, 'if': 1, 'ltd': 1, 'itself': 1, 'own': 1, 'miss': 1, 'possibly': 1, 'others': 1, 'us': 1, 'to': 1, 'adj': 1, 'first': 1, 'specifying': 1, "she'll": 1, 'promptly': 1, 'be': 1, 'whither': 1, 'poorly': 1, 'arent': 1, 'everything': 1, 'they': 1, 'wherein': 1, "i'll": 1, 'your': 1, 'specified': 1, 'him': 1, 'everyone': 1, 'contain': 1, 'amongst': 1, 'took': 1, 'says': 1, 'usefulness': 1, 'take': 1, 'et-al': 1, 'accordance': 1, 'shows': 1, 'unto': 1, 'quickly': 1, 'com': 1, 'relatively': 1, 'anybody': 1, "they've": 1, 'rd': 1, 'zero': 1, 'invention': 1, 'z': 1, 'h': 1, 'nor': 1, 'many': 1, 'few': 1, 'together': 1, 'look': 1, 'information': 1, 'y': 1, 'regardless': 1, 'yet': 1, 'so': 1, 'most': 1, 'qv': 1, 'tries': 1, 'home': 1, 'need': 1, 'in': 1, 'hundred': 1, 'accordingly': 1, 'proud': 1, 'taken': 1, 'the': 1, 'eg': 1, 'usually': 1, 'kept': 1, 'formerly': 1, 'was': 1, 'ah': 1, 'around': 1, 'thereof': 1, 'still': 1, 'non': 1, 'quite': 1, 'eighty': 1, 'somewhere': 1, 'did': 1, 'on': 1, 'ending': 1, 'according': 1, 'has': 1, 'willing': 1, 'right': 1, 'perhaps': 1, 'thank': 1, 'been': 1, 'my': 1, 'p': 1, 'eight': 1, 'usefully': 1, 'against': 1, 'moreover': 1, 'either': 1, 'by': 1, 'she': 1, 'ed': 1, "who'll": 1, 'both': 1, 'go': 1, 'nay': 1, 'other': 1, 'new': 1, 'previously': 1, 'line': 1, 'whence': 1, 'etc': 1, 'seeming': 1, 'unlike': 1, 'know': 1, 'therere': 1, 'am': 1, 'last': 1, 'any': 1, 'least': 1, 'refs': 1, 'towards': 1, 'five': 1, 'omitted': 1, 'www': 1, 'her': 1, 'ourselves': 1, 'thered': 1, 'else': 1, 'whats': 1, 'therefore': 1, 'beginnings': 1, 'all': 1, 'now': 1, 'whim': 1, 'thereto': 1, 'gets': 1, "haven't": 1, 'potentially': 1, 'fifth': 1, 'couldnt': 1, 'different': 1, 'due': 1, 'too': 1, "we've": 1, 'along': 1, 'beginning': 1, 'but': 1, 'c': 1, 'mg': 1, 'especially': 1, 'na': 1, 'throug': 1, 'throughout': 1, 'available': 1, 'ask': 1, 'across': 1, 'edu': 1, 'hereafter': 1, 'youd': 1, 'let': 1, 'whereupon': 1, 'why': 1, 'its': 1, 'does': 1, 'needs': 1, 'just': 1, 'through': 1, 'present': 1, 'had': 1, 'contains': 1, 'showed': 1, 'significantly': 1, 'anyone': 1, 'recently': 1, 'nowhere': 1, 'x': 1, 'than': 1, 'immediately': 1, 'would': 1, 'ought': 1, 'latterly': 1, 'think': 1, "that'll": 1, 'want': 1, 'anything': 1, 'make': 1, 'from': 1, 'one': 1, 'none': 1, 'thou': 1, 'became': 1, 'gone': 1, 'approximately': 1, 'yourselves': 1, 'mrs': 1, 'useful': 1, 'im': 1, 'it': 1, 'off': 1, 'sometime': 1, 'anyways': 1, 'former': 1, 'thousand': 1, 'toward': 1, 'except': 1, 'slightly': 1, 'made': 1, 'similar': 1, 'saw': 1, 'arise': 1, 'thereafter': 1, 'unfortunately': 1, 'mainly': 1, 'outside': 1, 'someone': 1, 'elsewhere': 1, 'seemed': 1, 'for': 1, 'immediate': 1, 'come': 1, 'neither': 1, 's': 1, 'meantime': 1, 'two': 1, 'thereupon': 1, 'actually': 1, 'sec': 1, 'ff': 1, 'become': 1, 'per': 1, 'doing': 1, 'anyway': 1, 'though': 1, 'wherever': 1, 'ok': 1, 'anyhow': 1, 'whomever': 1, 'similarly': 1, 'somehow': 1, 'world': 1, 'ts': 1, 'below': 1, 'are': 1, 'herein': 1, 'forth': 1, 'these': 1, 'with': 1, 'each': 1, 'here': 1, 'end': 1, 'were': 1, 'can': 1, 'resulted': 1, 'i': 1, 'afterwards': 1, 'shown': 1, "can't": 1, 'seven': 1, 'selves': 1, 'whereby': 1, 'twice': 1, 'page': 1, 'able': 1, 'little': 1, 'certainly': 1, 'successfully': 1, "'ll": 1, 'theirs': 1, 'youre': 1, 'also': 1, 'alone': 1, 'old': 1, 'cannot': 1, 'enough': 1, 'wasnt': 1, 'importance': 1, 'seems': 1, 'l': 1, 'biol': 1, 'hers': 1, 'th': 1, 'seeing': 1, 'our': 1, 'particularly': 1, 'of': 1, "they'll": 1, 'noted': 1, 'followed': 1, 'becomes': 1, 'every': 1, "it'll": 1, 'again': 1, 'said': 1, 'this': 1, "doesn't": 1, 'four': 1, "shouldn't": 1, 'giving': 1, 'another': 1, 'vs': 1, 'ninety': 1, 'try': 1, 'normally': 1, 'added': 1, 'lets': 1, 'whatever': 1, 'v': 1, 'got': 1, 'went': 1, 'whose': 1, 'part': 1, 'hence': 1, 'strongly': 1, 'beforehand': 1, 'auth': 1, 'while': 1, 'wheres': 1, 'please': 1, 'once': 1, 'everybody': 1, 'noone': 1, 'inc': 1, 'announce': 1, 'specify': 1, 'such': 1, 'nothing': 1, 'okay': 1, 'obviously': 1, 'value': 1, 'shed': 1, 'ml': 1, 'anymore': 1, 'inward': 1, "there'll": 1, 'sup': 1, 'get': 1, 'myself': 1, 'less': 1, 'unless': 1, 'tell': 1, 'maybe': 1, 'we': 1, 'me': 1, 'act': 1, 'or': 1, 'itd': 1, 'vol': 1, 'under': 1, 'somethan': 1, 'ca': 1, 'show': 1, 'being': 1, 'suggest': 1, 'section': 1, 'thence': 1, 'primarily': 1, 'm': 1, 'yours': 1, 'date': 1, 'them': 1, 'tip': 1, 'above': 1, 'himself': 1, 'km': 1, 'plus': 1, 'have': 1, 'during': 1, 'soon': 1, 'always': 1, 'then': 1, 'ones': 1, 'up': 1, 'far': 1, 'name': 1, 'used': 1, 'et': 1, 'awfully': 1, 'done': 1, 'ref': 1, 'research': 1, 'goes': 1, 'thus': 1, 'happens': 1, 'begins': 1, 'later': 1, 'hid': 1, 'stop': 1, 'those': 1, 'asking': 1, 'wish': 1, 'beyond': 1, 'use': 1, 'wed': 1, 'what': 1, 'much': 1, 'possible': 1, 'hither': 1, 'as': 1, 'same': 1, 'containing': 1, 'behind': 1, 'out': 1, 'index': 1, 'getting': 1, 'is': 1, 'sorry': 1, 'largely': 1, 'affecting': 1, 'trying': 1, 'who': 1, 'words': 1, 'ever': 1, "isn't": 1, 'n': 1, 'causes': 1, 'not': 1, 'latter': 1, 'an': 1, 'probably': 1, 'thereby': 1, 'seen': 1, 'gives': 1, 'ie': 1, 'likely': 1, 'sub': 1, 'important': 1, 'results': 1, 'never': 1, 'namely': 1, 'run': 1, 'tried': 1, 'see': 1, 'g': 1, 'hereby': 1, 'hardly': 1, 'sent': 1, 'related': 1, 'ours': 1, "didn't": 1, 'whoever': 1, 'looking': 1, 'means': 1, "you'll": 1, 'j': 1, 'where': 1, 'predominantly': 1, 'overall': 1, 'aside': 1, 'begin': 1, 'whole': 1, 'given': 1, 'meanwhile': 1, 'upon': 1, 'fix': 1, 'whom': 1, 'nobody': 1, 'regards': 1, 'nearly': 1, 'thanks': 1, 'q': 1, 'saying': 1, 'specifically': 1, 'que': 1, 'affects': 1, 'welcome': 1, 'necessarily': 1}


if __name__ == '__main__':
    print("StopWords.py is a class with no main()")





