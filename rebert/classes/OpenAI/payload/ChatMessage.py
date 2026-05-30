#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: ChatMessage.py
#   REVISION: January, 2025
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   This class implemnts the underlying message construct for an OpenAI chat completion
#   request. 
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#

import sys, copy, re, collections, json
from rebert.classes.data.DictionaryValidatorFromTemplate import DictionaryValidatorFromTemplate


#####
#   
#   CONSTANTS
#   
#####
#
#   This validation template provides support for most of the message types that would
#   be part of a chat completion interation. The API is updated constantly, so some you
#   might need to review the API documentation to use some of the fields correctly
#
#   Technically, according to the specification, the 'content' field is not required in all
#   cases. Therefore it has been marked as an optional field. However, for most standard
#   chat completion conditions, the content is the body of the message that the LLM will
#   act upon - and is required.
#
CHAT_MESSAGE_TEMPLATE = {
    'role'          : { 'required'  : True,
                        'type'      : str,
                        'options'   : ['system', 'developer', 'assistant', 'tool', 'user'] },
    'content'       : { 'required'  : False,
                        'type'      : str },
    'name'          : { 'required'  : False,    #   Can be used for tracking
                        'type'      : str },
    'tool_call_id'  : { 'required'  : False,    #   Only used with 'tool' messages
                        'type'      : str }
}
#
#
#####
#   
#   START class ChatMessage definition
#   
#####
#
#
class ChatMessage(DictionaryValidatorFromTemplate):
    '''
    This class implements a single chat message record as described by the OpenAI 
    documentation. This is a subclass of DictionaryValidatorFromTemplate. The
    template CHAT_MESSAGE_TEMPLATE specifies what is allowed in the individual
    chat messages.
    
    Attributes:
        There are no new attributes, all are inhereited from the super class
    
    Methods:
        newMessage()    - like a factory method, returns a new initialzed object
        setMessage()    - sets this object fields with the supplied values
        setRole()       - set the role field 
        setContent()    - set the content field 
        setName()       - set the name field
    '''
    def __init__(self, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        template    : A template dictionary for the data structure
        '''
        if "template" not in kwargs:
            kwargs["template"] = CHAT_MESSAGE_TEMPLATE
        super().__init__(*args, **kwargs)
        return

    #
    #   This method behaves like a 'factory' to make new message objects that 
    #   are initialized with supplied parameters. It can be called with just
    #   one parameter, a dict of a message, or by named parameters of 'role'
    #   'content', and 'name'
    def newMessage(self, *args, **kwargs):
        '''
        Returns a new ChatMessage object initialized with the supplied values.
        
        This method will take parameters in different ways and do its best to
        infer how they should be used.
        
        If it's supplied an unnnamed argument - and that argument is a dictionary
        type thing, then it looks in that dictionary to try and initialze the new
        ChatMessage.
        
        If it is supplied named parameters, 'm' or 'message' and those are a
        dictionary type of thing, then it tries to use the fields to initialize
        the new ChatMessage
        
        Lastly, if it is just supplied named kwargs (key word arguments) then it
        looks for 'role', 'content', and 'name' as parameters to initialize the
        new ChatMessage.
        
        Optional Parameters:
        m           : An optional dictionary parameter with 'role', 'content', 'name'
        message     : An optional dictionary parameter with 'role', 'content', 'name'
        role        : A single key word argument for role
        content     : A single key word argument for content
        name        : A single key word argument for name
        
        Returns:
        ChatMessage : a new ChatMessage object, using the values supplied
        '''
        mdict = None
        if args:
            if isinstance(args[0],dict):
                mdict = args[0] 
        elif 'm' in kwargs:
            if isinstance(kwargs['m'],dict):
                mdict = kwargs['m']
        elif 'message' in kwargs:
            if isinstance(kwargs['message'],dict):
                mdict = kwargs['message']
        else:
            mdict = kwargs
        
        m = ChatMessage()
        if not mdict: return m
        if 'role' in mdict:
            m.setRole(mdict['role'])
        if 'content' in mdict:
            m.setContent(mdict['content'])
        if 'name' in mdict:
            m.setName(mdict['name'])
        return m
    
    
    #
    #   Try to set the message using whatever we got as parameters.
    def setMessage(self, *args, **kwargs):
        '''
        Sets the values on this ChatMessage object depening on values provided.
        
        This method will take parameters in different ways and do its best to
        infer how they should be used.
        
        If it's supplied an unnnamed argument - and that argument is a dictionary
        type thing, then it looks in that dictionary to try to set values.
        
        If it is supplied named parameters, 'm' or 'message' and those are a
        dictionary type of thing, then it tries to use the fields of the dictionary
        to set the values on this object.
        
        Lastly, if it is just supplied named kwargs (key word arguments) then it
        looks for 'role', 'content', and 'name' as parameters to set the
        respective value on this ChatMessage object
        
        Optional Parameters:
        m           : An optional dictionary parameter with 'role', 'content', 'name'
        message     : An optional dictionary parameter with 'role', 'content', 'name'
        role        : A single key word argument for role
        content     : A single key word argument for content
        name        : A single key word argument for name
        '''
        mdict = None
        if args:
            if isinstance(args[0],dict):
                mdict = args[0] 
        elif 'm' in kwargs:
            if isinstance(kwargs['m'],dict):
                mdict = kwargs['m']
        elif 'message' in kwargs:
            if isinstance(kwargs['message'],dict):
                mdict = kwargs['message']
        else:
            mdict = kwargs
        if 'role' in mdict:
            self.setRole(mdict['role'])
        if 'content' in mdict:
            self.setContent(mdict['content'])
        if 'name' in mdict:
            self.setName(mdict['name'])
        return
    
    
    #
    #   Set the role field on this ChatMessage.
    def setRole(self, role=None):
        '''
        Sets the role field for this ChatMessage object.
        
        Parameters:
        role        : the string role that created the content
        '''
        if role:
            self.__data__['role'] = role
        else:
            self.__data__['role'] = None
        return
    
    #
    #   Set the content field on this ChatMessage.
    def setContent(self, content=None):
        '''
        Sets the content field for this ChatMessage object.
        
        Parameters:
        content     : the string content
        '''
        if content:
            self.__data__['content'] = content
        else:
            self.__data__['content'] = None
        return
    
    #
    #   Set the name field on this ChatMessage.
    def setName(self, name=None):
        '''
        Sets the name field for this ChatMessage object.
        
        Parameters:
        name        : a string name to associate with this content
        '''
        if name:
            # docs say "string" but it turns out this field has restrictions
            name = name.replace(" ","_")
            name_fixed = re.sub(r'[^a-zA-Z0-9_]', '-', name)
            self.__data__['name'] = name_fixed
        else:
            self.__data__['name'] = None
        return
    
#####
#   
#   END class ChatMessage definition
#   
#####

if __name__ == '__main__':
    print("ChatMessage.py is a class with no main()")
