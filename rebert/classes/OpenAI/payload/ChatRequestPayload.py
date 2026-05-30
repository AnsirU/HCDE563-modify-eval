#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: ChatRequestPayload.py
#   REVISION: December, 2024
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   A payload class based on a DictionaryValidatorFromTemplate. The class implements the
#   payload contents necessary for an OpenAI chat completion request. The CHAT_REQUEST_TEMPLATE
#   provides a template for the fields of a chat completion request.
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#

import sys, copy, collections, json
from rebert.classes.data.DictionaryValidatorFromTemplate import DictionaryValidatorFromTemplate
from rebert.classes.OpenAI.payload.ChatMessage import ChatMessage


#####
#   
#   CONSTANTS
#   
#####
#   
#   Selected a model that is similar to the web based ChatGPT
#   We don't really need a 'reasoning' model, but the non-reasoning models are slowly going away
#
MODEL_DEFAULT = 'gpt-5.3-chat-latest'
#
#   A list of common models that could be used for chat
#
MODEL_OPTIONS = ['gpt-5.4', 'gpt-5.4-mini', 'gpt-5', 'gpt-5.4-nano', 'gpt-5-nano', 'gpt-5-mini', 
                 'gpt-5.3-chat-latest', 'gpt-5.2-chat-latest', 'gpt-5.1-chat-latest', 'gpt-5-chat-latest',
                 'gpt-4.1', 'gpt-4.1-mini',  'gpt-4.1-nano']
#
#   A list of possible constraints on reasoning models
#
REASONING_OPTIONS = ['low', 'medium', 'high']
#
#   The basic chat template. See the documentation of the DictionaryValidatorFromTemplate
#   for an explanation of the dictionary specifications. The documentation for the
#   API call is: https://platform.openai.com/docs/api-reference/chat
#
#   This template does not contain all of the possible fields that have been added to
#   chat. These are a number of fields that cover a large number of common use cases.
#
#   The transition to the "responses" API will require a change to this template spec. That
#   will be handled in a different revision.
#
CHAT_REQUEST_TEMPLATE = {
    'messages'              : { 'required'  : True,
                                'type'      : list },
    'model'                 : { 'required'  : True,
                                'type'      : str, 
                                'options'   : MODEL_OPTIONS,
                                'default'   : MODEL_DEFAULT },
    'store'                 : { 'required'  : False,
                                'type'      : bool },
    'reasoning_effort'      : { 'required'  : False,
                                'type'      : str, 
                                'options'   : REASONING_OPTIONS},
    'frequency_penalty'     : { 'required'  : False,
                                'type'      : float,
                                'range'     : [-2.0, 2.0] },
    'logprobs'              : { 'required'  : False,
                                'type'      : bool },
    'top_logprobs'          : { 'required'  : False,
                                'type'      : int,
                                'range'     : [0, 20] },
    'max_completion_tokens' : { 'required'  : False,
                                'type'      : int },
    'n'                     : { 'required'  : False,
                                'type'      : int },
    'presence_penalty'      : { 'required'  : False,
                                'type'      : float,
                                'range'     : [-2.0, 2.0] },
    'stop'                  : { 'required'  : False,
                                'type'      : list },
    'temperature'           : { 'required'  : False,
                                'type'      : float,
                                'range'     : [0.0, 2.0] },
    'top_p'                 : { 'required'  : False,
                                'type'      : float,
                                'range'     : [0.0, 1.0] },
    'user'                  : { 'required'  : False,
                                'type'      : str }
}
#
#
#   October 2024
#   The 'max_tokens' parameter is now deprecated and should be removed. It was
#   still working Dec of 2024, but OpenAI basically ignores it. There is a
#   replacement field max_completion_tokens that should be implemented instead.
#
#   When using setMaxTokens the code will use these constants to try and keep
#   the model within some reasonable bounds - to control costs. Naturally, if you
#   know what you're doing then you can change the ranges for these. 
#
#   There is no specific range set for this value in the DictionaryValidator
#
#   The MINIMUM - so we make sure we get something back
MAX_TOKEN_MINIMUM = 256
#MAX_TOKEN_MINIMUM = 512
#
#   The MAXIMUM - control for over response
#MAX_TOKEN_MAXIMUM = 2048
MAX_TOKEN_MAXIMUM = 4096
#MAX_TOKEN_MAXIMUM = 8192
#
#   Lower temperatures result in less randomness and more predictable responses   
#
TEMPERATURE_DEFAULT = 0.6
#
#
#
#####
#   
#   START class ChatRequestPayload definition
#   
#####

class ChatRequestPayload(DictionaryValidatorFromTemplate):
    '''
    This class implements a chat request body that conforms to the OpenAI chat
    completion request. This is a subclass of DictionaryValidatorFromTemplate.
    The template, CHAT_REQUEST_TEMPLATE, is the specification for what is allowed
    in the body of a chat request.
    
    Attributes:
        There are no new attributes, all are inhereited from the super class
    
    Methods:
        setModel()              - set the model that should be used for this response
        setMaxTokens()          - set the maximum number of tokens to generate in response
        setTemperature()        - set the temperature of the token generation 
        setTopP()               - set the threshold for the probability of the token generated
        setLogprobs()           - set the number of log probabilities to return
        setPresencePenalty()    - set a value for presence penalty
        setFrequencyPenalty()   - set a value for frequency penalty
        setN()                  - set the number of responses to generate for this request
        setUser()               - set a user ID value for this request
        
        getLastMessage()        - get the last message from the message list
        newMessage()            - create a new chat message thing using supplied parameters
        addMessage()            - add a single message to the message list
        setMessages()           - use a list of message like things to set the message list
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
            kwargs["template"] = CHAT_REQUEST_TEMPLATE
        super().__init__(*args, **kwargs)
        
        #   Potentially, set some defaults for a request
        #   the CHAT_REQUEST_TEMPLATE can also be used to set
        #   default values
        #self.setModel()
        #self.setTemperature()
        #self.setMaxTokens(MAX_TOKEN_MINIMUM)
        return

    #
    #   A method to set the model to use for this request
    #   
    def setModel(self, model=MODEL_DEFAULT):
        '''
        Set the model to be used for this request.
        
        Optional Parameters:
        model       : one of the OpenAI models that works for chat completions
        '''
        if model:
            self.__data__["model"] = model
        else:
            self.__data__["model"] = ""
        return
    

    #
    #   A method to set the max_tokens - the maximum number of tokens to generate in
    #   a completion. Some early models only limit to 2048 tokens
    #
    #   This actually sets the 'max_completion_tokens' request field and ignores the
    #   old max_token field. While the underlying data is slightly different the
    #   assumed semantics for the use of this is basically the same - to control the
    #   amount of effort the API spends on computing a result
    #   
    def setMaxTokens(self, mt=MAX_TOKEN_MINIMUM):
        '''
        Set the maximum number of tokens to generate for this request.
        
        Optional Parameters:
        mt          : an integer number of tokens, this is thresholded by the value of
                      the constant MAX_TOKEN_MAXIMUM set for this object
        '''
        if mt < 0: mt = MAX_TOKEN_MINIMUM
        if mt > MAX_TOKEN_MAXIMUM: mt = MAX_TOKEN_MAXIMUM
        self.__data__["max_completion_tokens"] = mt
        return
    

    #
    #   A method to set the temperature - the 'sampling temperature' with higher values 
    #   providing more randomness and lower values being much more deterministic. Range 
    #   is 0.0 .. 2.0
    #   
    #   This is an alternative to 'top_p'. It is recommended that temperature and top_p 
    #   not be used together.
    #
    def setTemperature(self, temp=TEMPERATURE_DEFAULT):
        '''
        Set the top_p value for this request.
        
        Optional Parameters:
        temp        : a float between 0.0 and 2.0
        '''
        if temp < 0.0: temp = 0.0
        if temp > 2.0: temp = 2.0
        self.__data__["temperature"] = temp
        return
    

    #
    #   A method to set the top_p - a sampling technique based on the probability of 
    #   a given token. Top_p is a threshold with the probablility of a token needing 
    #   to be in the top p probability rank. That is, top_p of 0.1 means only tokens 
    #   in the top 10% (over 90% probability) will be considered.
    #
    #   This is an alternative to 'temperature'. It is recommended that top_p and 
    #   temperature not be used together.
    #   
    def setTopP(self, tp=0.20):
        '''
        Set the top_p value for this request.
        
        Optional Parameters:
        tp          : a float between 0.0 and 1.0
        '''
        if tp <= 0.0: tp = 0.0
        if tp > 1.0: tp = 1.0
        self.__data__["top_p"] = tp
        return
    

    #
    #   Set the log probabilities of the tokens returned. There is always a default 
    #   returned this allows you to set a higher value. The max is currently 5
    #   
    def setLogprobs(self, lp=None):
        '''
        Set the number of log probabilities to return.
        
        Optional Parameters:
        lp          : an int, current max is 5
        '''
        if lp: 
            self.__data__["logprobs"] = lp
        else:
            self.__data__["logprobs"] = None
        return
    

    #
    #   Allows specifying a string or a list of up to 4 termination strings
    #   
    def setStop(self, s=[]):
        '''
        Set a termination string, or a list of up to 4 termination strings.
        
        This allows the setting of termination strings. If the parameter is a
        single string then it prepends that string to a growing list of 
        termination strings that is a max of 4 items. Otherwise if it is a
        list then it sets the termination strings to the list and trims that
        to a maximum of 4 items
        
        Optional Parameters:
        s           : string or a list of strings
        '''
        if isinstance(s, list):
            #   Empty list clears this field
            if not s:
                self.__data__["stop"] = None
                return
            #   Otherwise, we take the first four items
            self.__data__["stop"] = s[:4].copy()
            return
        #   Add string to the front of a list of termination strings
        elif isinstance(s, str):
            stops = list()
            stops.append(s)
            if self.__data__["stop"]:
                stops.extend(self.__data__["stop"])
                self.__data__["stop"] = stops[:4]
            else:
                self.__data__["stop"] = stops
        return
    

    #
    #   Set a presence penalty - whether a token appears in the completion already. 
    #   Positive values are penalties, so negative values must be a bonus. Ranges 
    #   from -2.0 to 2.0.
    #   
    def setPresencePenalty(self, p=0.0):
        '''
        Set the presence penalty for this request.
        
        Optional Parameters:
        p           : a float value for the presence penalty
        '''
        if p < -2.0: p = -2.0
        if p > 2.0: p = 2.0
        self.__data__["presence_penalty"] = p
        return
    

    #
    #   Set a frequency penalty - whether the frequency of a token should be penalized. 
    #   Positive values are penalties, so negative values must be a bonus. Ranges 
    #   from -2.0 to 2.0.
    #   
    def setFrequencyPenalty(self, p=0.0):
        '''
        Set the frequency penalty for this request.
        
        Optional Parameters:
        p           : a float value for the frequency penalty
        '''
        if p < -2.0: p = -2.0
        if p > 2.0: p = 2.0
        self.__data__["frequency_penalty"] = p
        return
     
    
    #
    #   The number of completions to generate in one response. This is dangerous because 
    #   it can burn LOTS of tokens.
    #   
    #   It is probably not necessary to use this at all. Just make another request - with
    #   slightly varied parameters of other request fields.
    #
    #   As a safety measure this function currently only allows the values 1, 2 or 3 completions. 
    #   
    def setN(self, n=1):
        '''
        Set 'n', the number of responses to generate in response to this chat request.
        
        OpenAI will allow you to generate more than one response at a time. The idea is that
        you might want to generate options in a single request.
        
        Optional Parameters:
        n           : an int, number of responses you want
        '''
        if n < 0: n = 1
        if n > 3: n = 3
        self.__data__["n"] = n
        return
    
    
    #
    #   A method to set a user ID. The user ID is useful when managing multiple requests
    #   and responses. It can be used to link a given request with a response.
    #   
    def setUser(self, user=None):
        '''
        Set a user ID value for this chat.
        
        The idea here is that by tracking user interactions we might learn who is abusing
        the system. OpenAI might be helpful if we use this field systematically
        
        Optional Parameters:
        user        : a string that is a unique ID for a given user
        '''
        if 'user':
            self.__data__["user"] = user
        else:
            self.__data__["user"] = None
        return
    

    #
    #   A method to return the last item in the message list
    #   
    def getLastMessage(self):
        '''
        Returns the last ChatMessage object in the message list.
        
        Often, we will probably want to know the last item because that is where the
        chat is happening. The newest contribution to the chat by the user or the
        assistant (system) is the last item.
                
        Returns:
        ChatMessage : the last message in the message list
        '''
        if len(self.__data__["messages"])>0:
            return self.__data__["messages"][-1]
        return None
    

    #
    #   A method to create and initialize a new message for a chat
    #   
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
        ChatMessage : a new ChatMessage object, using any values supplied
        '''
        self.log(f"entering", level="DEBUG")
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
        self.log(f"returning", level="DEBUG")
        return m
    
    
    #
    #   A method to add or append a message to the 'messages' field of a chat
    #   
    def addMessage(self, *args, **kwargs):
        '''
        Adds a ChatMessage to the message list of this chat request body
        
        This method will take parameters in different ways and do its best to
        infer how they should be used.
        
        If it's supplied an unnnamed argument - and that argument is a dictionary
        type thing, then it looks in that dictionary to try to set values. If the
        argument is a ChatMessage() then it just appends it to the message list
        
        If the method is  supplied named kwargs (key word arguments) then it looks
        for 'role', 'content', and 'name' as parameters to set the respective
        values on a newly created ChatMessage
        
        Optional Parameters:
        m           : An optional dictionary parameter with 'role', 'content', 'name'
        message     : An optional dictionary parameter with 'role', 'content', 'name'
        role        : A single key word argument for role
        content     : A single key word argument for content
        name        : A single key word argument for name
        '''
        self.log(f"entering", level="DEBUG")
        #   Make sure that the messages field is a list
        if not isinstance(self.__data__["messages"], list):
            self.__data__["messages"] = list()
        #
        #   Just adding a Chat message object - append it
        if args and isinstance(args[0], ChatMessage):
            self.__data__["messages"].append(args[0])
            self.log(f"returning", level="DEBUG")
            return
        #
        #   If the parameter is just a dict then see if we can convert it to
        #   a ChatMessage type thing   
        if args and isinstance(args[0], dict):
            m = ChatMessage()
            m.setMessage(args[0])
            #   Try a validation, if there is no message returned then
            #   then it was iniitalized correctly and we can append it
            if not m.validate():
                self.__data__["messages"].append(m)
            self.log(f"returning", level="DEBUG")
            return
        #
        #   Using parameter keys to create and add a message - this can only
        #   be a valid message if it has 'role' and 'content' fields
        #   otherwise we just have to skip it
        if ('role' in kwargs) and ('content' in kwargs):
            m = self.newMessage(role=kwargs['role'],content=kwargs['content'])
            if 'name' in kwargs:
                m.setName(kwargs['name'])
            #   Validate the ChatMessage before appending
            if not m.validate():
                self.__data__["messages"].append(m)
        self.log(f"returning", level="DEBUG")
        return
    

    #
    #   A method to set the messages field as a list of message dictionary items
    #   
    def setMessages(self, message_list=None):
        '''
        Add a whole list of chat message like items to the list.
        
        The method checks that the message_list is a list, and then processes each item
        in the list using self.addMessage() to add each message to the object.
        
        Optional Parameters:
        message_list    : a list of chat message like dictionaries or ChatMessage objects
        '''
        self.log(f"entering", level="DEBUG")
        count = 0
        #   This sets a whole list of messages
        if isinstance(message_list, list):
            #   Add each item, either dict or ChatMessage object
            for item in message_list:
                self.addMessage(item)
                count += 1
        self.log(f"returning, added {count} messages to message list", level="DEBUG")
        return
    
    
    #
    #   A method to shorten the message list. This will change the trajectory of the
    #   conversation by removing some of the chat context. This will attempt to keep
    #   the 'system' message if that is the first message - and make it the first
    #   message of the resulting messages list
    #   
    def trimMessages(self, trim=2):
        '''
        Trims the front - first part of the messages list by the specified number of
        messages.
        
        The method considers the 'role' of the first message and if it is a system role then
        it saves that message as the new first item.
        
        Optional Parameters:
        trim        : an integer, number of messages to remove
        '''
        self.log(f"entering, message list has {len(self.__data__['messages'])} items", 
                 level="DEBUG")
        new_messages = list()
        #   Make sure we are going to trim something
        if trim <= 0:
            self.log(f"trim must be a positive value", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return
        #   Make sure we are trimming less than the total
        if trim >= len(self.__data__['messages']):
            self.log(f"trim should be less than the number of messages", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return
        #   Now, try to trim by running through the list
        for m in self.__data__['messages']:
            #   Keep system messages - probably the first message in the list
            if m['role'] == 'system':
                new_messages.append(m)
            else:
                #   When we've trimmed, ignored, the right number of items 
                #   begin adding the remaining items to the new list
                if trim == 0:
                    new_messages.append(m)
                else:
                    #   Ignore this item, one less item to trim
                    trim -= 1
        #
        #   Save the resulting set of messages back to the message list
        self.__data__['messages'] = new_messages
        self.log(f"returning, message list is now {len(self.__data__['messages'])}", 
                 level="DEBUG")
        return
    

    #
    # A method to return a string JSON representation of the object
    #
    def json(self, r=None, clean=True, indent=0, sort_keys=False):
        '''
        Produce a JSON version of the underlying dictionary.
        
        The method provides a number of options to produce JSON. The main point of this
        override is to change the defalult value of the 'clean' option to True. We
        will use this class to send data - and we don't want to send extraneous, unused
        key:value pairs.
        
        Optional Parameters:
        r           : A dictionary to work with
        clean       : Perform a cleaning, to remove unused fields
        indent      : Create a formatted version of the JSON output
        sort_keys   : Sort the keys when producing the JSON
        
        Returns:
        A string of the dictionary in JSON format
        '''
        self.log(f"entering", level="DEBUG")
        #   The main point here is to make 'clean' default to True
        result = super().json(r,clean,indent,sort_keys)
        self.log(f"returning", level="DEBUG")
        return result


    #
    #   The main class DictionaryValidatorFromTemplate, performs a cleaning, but does not
    #   know how to clean a nested structure. This will handle cleaning the nested
    #   set of messages
    def __clean_dict__(self):
        #   This handles the default object
        req_data = super().__clean_dict__()
        #   If there are no nested messages, then don't clean that
        if len(req_data['messages']) == 0:
            self.log(f"cleaning, 0 messages", level="DEBUG")
            return req_data
        #
        #   Have nested messages
        new_messages = list()
        for m in req_data['messages']:
            #   Make sure the nested message is something we know hot to clean
            if isinstance(m, DictionaryValidatorFromTemplate):
                converted = m.__clean_dict__()
            else:
                #   Not something we know about, just keep it as-is
                converted = m
            new_messages.append(converted)
        #
        #   This should never happen, but maybe produce a warning just in case
        if not new_messages:
            self.log(f"cleaning nested 'messages' field, removed all messages", level="WARN")
        #
        #
        req_data['messages'] = new_messages
        #print("Cleaned Request Payload:\n",json.dumps(req_data,indent=4))
        #print(f"Has {len(req_data['messages'])} messages.")
        self.log(f"cleaning, {len(req_data['messages'])} messages", level="DEBUG")
        return req_data

#####
#   
#   END class ChatRequestPayload definition
#   
#####

if __name__ == '__main__':
    print("ChatRequestPayload.py is a class with no main()")



