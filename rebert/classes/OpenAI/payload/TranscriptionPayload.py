#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: TranscriptionPayload.py
#   REVISION: December, 2024
#   CREATION DATE: June, 2024
#   AUTHOR: David W. McDonald
#
#   A payload class based on a DictionaryValidatorFromTemplate. The class implements the
#   payload contents necessary for an OpenAI transcription request. The TRANSCRIPT_REQUEST_TEMPLATE
#   provides a template for the fields for a transcription request. This class is interesting
#   because it illustrates a file upload to the OpenAI server - or almost any server using a
#   multi-part MIME encoded form.
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#

import sys, os, copy, io, collections, json
from rebert.classes.data.DictionaryValidatorFromTemplate import DictionaryValidatorFromTemplate
#
#   This should come with the requests module
from requests_toolbelt import MultipartEncoder

#
#   This is one of the MIME type form things that this code can use. This is sometimes installed
#   with the installation of Flask. If your python does not have it you might want to install it.
HAS_WERKZEUG_IMPORT = False
try:
    #   This is part of Flask and is not absolutely required
    #   This class is used to wrapper MIME file uploads in Flask
    from werkzeug.datastructures import FileStorage
    HAS_WERKZEUG_IMPORT = True
except:
    pass


#####
#   
#   CONSTANTS
#   
#####
#
#   There are several different transcription models MODEL_OPTIONS lists the ones that are
#   available through the API. The 'whisper-1' model is the 'old reliable' model. This 
#   currently defaults to gpt-4o-mini-transcribe because it is supposedly "faster and better"
#
#MODEL_DEFAULT = 'whisper-1'
MODEL_DEFAULT = 'gpt-4o-mini-transcribe'
#
#   A list of three models that are now available for transcriptions
#
MODEL_OPTIONS = ['gpt-4o-transcribe', 'gpt-4o-mini-transcribe', 'whisper-1']
#
#   This is a subset of the codes that are some very common languages.
#   If you really want to transcribe something other than one of the common 
#   languages, you will need to add it to this options list and test, test, test.
#
ISO_639_1_LANGS = [ '', 'ar','de','en','es','fr','he','ja','ko','pt','ru','yi','zh']
#   
#   This is a list of the potential response formats supported by transcription
#
RESPONSE_FORMATS = ['json','text','srt','verbose_json','vtt']
#   
#   Lower temperatures result in less randomness and more predictable transcription   
#
TEMPERATURE_DEFAULT = 0.0
#
#   A template for a transcription request. This template is a DictionaryValidatorFromTemplate
#   compliant dictionary. See that class definition for an explanation of the template
#   specification. The OpenAI transcription documentation is at:
#   https://platform.openai.com/docs/api-reference/audio/createTranscription
#
TRANSCRIPTION_REQUEST_TEMPLATE = {
    'file'                      : True,         # there is no validation of this field
    
    'model'                     : { 'required'  : True,
                                    'type'      : str, 
                                    'options'   : MODEL_OPTIONS,
                                    'default'   : MODEL_DEFAULT },
    'language'                  : { 'required'  : False,
                                    'type'      : str,
                                    'options'   : ISO_639_1_LANGS,
                                    'default'   : 'en' },
    'prompt'                    : { 'required'  : False,
                                    'type'      : str },
    'response_format'           : { 'required'  : False,
                                    'type'      : str,
                                    'options'   : RESPONSE_FORMATS,
                                    'default'   : 'json' },
    'temperature'               : { 'required'  : False,
                                    'type'      : float,
                                    'range'     : [0.0, 2.0],
                                    'default'   : TEMPERATURE_DEFAULT },
    'timestamp_granularities'   : { 'required'  : False,
                                    'type'      : list }
}
#
#   This class allows loading a file from disk. The standard assumption is that
#   the file is an audio file. The file extension is used to determine a MIME type that
#   will be used when encoding the data that is sent to the OpenAI server. If you know
#   the file is actually a video file, then you can also specify that when setting the
#   'file' data field with the setFile() method.
#
OAI_TRANSCRIPTION_EXT_TO_MIME = {
    'video': {   
        '.mpeg' : 'video/mpeg',
        '.ogg'  : 'video/ogg',
        '.m4a'  : 'video/m4a',
        '.mpga' : 'video/mpga',
        '.mp4'  : 'video/mp4',
        '.mpeg' : 'video/mpeg',
        '.webm' : 'video/webm'
    },
    'audio': {
        '.flac' : 'audio/flac',
        '.mp3'  : 'audio/mpeg',
        '.mp4'  : 'audio/mp4',
        '.mpeg' : 'audio/mpeg',
        '.ogg'  : 'audio/ogg',
        '.wav'  : 'audio/wav',
        '.m4a'  : 'audio/m4a',
        '.mpga' : 'audio/mpga',
        '.webm' : 'audio/webm',
        '.weba' : 'audio/webm'
    }
}
#
#   A set of text MIME types that is supported by the transcription service as keys
#   and the likely file type extension as the values
#
OAI_TRANSCRIPTION_MIME_TO_EXT = {
    'audio/flac' :  '.flac', 
    'audio/mpeg' :  '.mpeg',
    'audio/mp4'  :  '.mp4',
    'audio/ogg'  :  '.ogg',
    'audio/wav'  :  '.wav',
    'audio/m4a'  :  '.m4a',
    'audio/mpga' :  '.mpga',
    'audio/webm' :  '.webm',
    'video/mpeg' :  '.mpeg', 
    'video/ogg'  :  '.ogg',
    'video/m4a'  :  '.m4a',
    'video/mpga' :  '.mpga', 
    'video/mp4'  :  '.mp4',
    'video/mpeg' :  '.mpeg',
    'video/webm' :  '.webm'
}
#
#   A set of file extensions that we use as a helper to figure out the MIME type
#   of the data loaded from a file
#
OAI_TRANSCRIPTION_MIME_FILE_EXT = ['.flac', '.mp3', '.mp4', '.mpeg', '.mpga', 
                                    '.m4a', '.ogg', '.wav', '.weba', '.webm']
#
#
#
#####
#   
#   START class TranscriptionPayload definition
#   
#####

class TranscriptionPayload(DictionaryValidatorFromTemplate):
    '''
    This class implements a chat request body that conforms to the OpenAI chat
    completion request. This is a subclass of DictionaryValidatorFromTemplate.
    The template, CHAT_REQUEST_TEMPLATE, is the specification for what is allowed
    in the body of a chat request.
    
    Attributes:
        __full_name__           - the full path to the file
        __short_name__          - the leaf/file name
        __extension__           - the extension of the file name
        __mime_type__           - the assumed mime type for encoding
        __file_handle__         - a file/stream handle of the data 
    
    Methods:
        setFile()                   - sets the file field of the request
        getFormMultiPartEncoded()   - get a multi-part MIME encoded form to send
        setModel()                  - set the model that should be used for this response
        setTemperature()            - set the temperature of the token generation 
        setResponseFormat()         - set the response format for the transcript
        setLanguage()               - set the language of the audio (and transcript)
        setPrompt()                 - set a prompt for the transcription
        close()                     - close the file/stream that had the data
        __get_tuple__()             - get a MIME tuple - for MIME encoding

    '''
    def __init__(self, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        template    : A template dictionary for the data structure
        extensions  : A list of the acceptable file extensions for this class/object
        '''
        if "template" not in kwargs:
            kwargs["template"] = TRANSCRIPTION_REQUEST_TEMPLATE.copy()
        super().__init__(*args, **kwargs)

        self.__extensions__ = OAI_TRANSCRIPTION_MIME_FILE_EXT.copy()
        #
        #   We need to have a list of file extensions that this can accept
        if ("extensions" in kwargs):
            self.__extensions__ = kwargs['extensions']
        #
        #   Local attributes for managing the file data
        self.__full_name__ = ""
        self.__short_name__ = ""
        self.__extension__ = ""
        self.__mime_type__ = ""
        self.__file_handle__ = None     # an open file or stream
        #
        return

    #
    #   A method set the file to upload 
    #   
    def setFile(self, *args, **kwargs):
        '''
        Set the 'file' field for the transcription request. 
        
        This should either be the name of a data file on disk, or some kind of existing
        data stream. If the data stream is a MIME type thing then this will try to fill out
        the necessary fields using what it knows about the MIME type thing.
        
        Opional Parameters:
        filename            : An optional description or name for the object
        stream              : A MIME stream or file stream type thing
        mimetype            : A string MIME type for the stream
        is_video            : A template dictionary for the data structure
        '''
        if args:
            if isinstance(args[0],str):
                is_video = False
                filename = args[0]
                if (len(args) > 1) and isinstance(args[1],bool):
                    is_video = args[1]
                self.__set_file_filename__(filename,is_video)
                return
        elif ('filename' in kwargs) and ('stream' not in kwargs):
            filename = kwargs['filename']
            is_video = False
            if 'is_video' in kwargs:
                is_video = kwargs['filename']
            self.__set_file_filename__(filename,is_video)
            return
        elif 'stream' in kwargs:
            stream = None
            filename = ""
            mimetype = ""
            is_video = False
            temp_stream = kwargs['stream']
            #   
            #   This case handles a 'files' MIME type thing in Flask
            if HAS_WERKZEUG_IMPORT and isinstance(temp_stream,FileStorage):
                stream = temp_stream.stream
                mimetype = temp_stream.mimetype.lower()
                #   Should assume this is an unsafe filename  - but we're going to
                #   send it somewhere else - not save it
                filename = os.path.basename(temp_stream.filename)
            #
            #   This case handles a basic file from the file system
            elif isinstance(temp_stream,io.IOBase):
                stream = temp_stream
                if 'filename' in kwargs:
                    filename = kwargs['filename']
                if 'mimetype' in kwargs:
                    mimetype = kwargs['mimetype']
            if 'is_video' in kwargs:
                is_video = kwargs['is_video']
            
            self.__set_file_stream__(stream, mimetype, filename, is_video)
            return
        else:
            raise Exception("Must provide a 'filename' or a 'stream' for setFile() method.")

        return

    #
    #   The simple filename version of this - just open the file and use that
    #
    def __set_file_filename__(self, filename="", is_video=False):
        '''
        A low level method to set the 'file' field of a transcription request 
        
        This low leve method handles the disk/file version which requires opening
        a file
        
        Parameters:
        filename            : An optional description or name for the object
        is_video            : A template dictionary for the data structure
        '''
        #
        #   Make sure there is a filename
        if not filename:
            raise Exception(f"Empty 'filename'. Need to set the 'filename' parameter for SetFile()")
        #
        self.__full_name__ = filename
        # pick off the leaf - as the short name
        path = os.path.split(filename)
        self.__short_name__ = path[1]
        #
        #   Make sure there is a file - not just a directory
        if not self.__short_name__:
            raise Exception(f"Need a file. Looks like '{self.__full_name__}' is just a directory.")

        # pick of the extension - a guess for the file type
        pair = os.path.splitext(filename)
        self.__extension__ = pair[1].lower()

        #
        #   Now check the file type based on the extension
        if (not self.__extension__) or (not self.__extension__ in self.__extensions__):
            accept = f"Acceptable audio data types are: {str(self.__extensions__)}"
            raise Exception(f"Wrong file type or wrong file type extension. {accept}")
        #
        #   Make sure we have a matching MIME type
        type_key = "audio"
        if is_video: type_key = "video"
        if not self.__extension__ in OAI_TRANSCRIPTION_EXT_TO_MIME[type_key]:
            types_list = OAI_TRANSCRIPTION_EXT_TO_MIME[type_key].values()
            accept = f"The acceptable '{type_key}' MIME types are: {str(types_list)}"
            raise Exception(f"Cannot find matching MIME type. {accept}")
        #
        self.__mime_type__ = OAI_TRANSCRIPTION_EXT_TO_MIME[type_key][self.__extension__]
        
        #
        #   Ok, looks like we can open the file
        try:
            self.__file_handle__ = open(self.__full_name__,"rb")
        except:
            self.__file_handle__ = None
            raise
        
        #   If we get to this point then the file will be the full name of the file
        #   This field is *replaced* by a __get_tuple__() when this is converted
        #   to a form that can be sent to the OpenAI server
        self.__data__['file'] = self.__full_name__
        return
    
    
    #
    #   The stream version - uses an open stream as the source of the data
    #
    def __set_file_stream__(self, stream="", mimetype="", filename="", is_video=False):
        #
        #   Make sure there is a filename
        if not filename:
            raise Exception(f"Empty 'filename'. Need to set the 'filename' parameter for SetFile()")
        self.__full_name__ = filename
        # pick off the leaf - as the short name
        path = os.path.split(filename)
        self.__short_name__ = path[1]
        #
        #   Make sure there is a file - not just a directory
        if not self.__short_name__:
            raise Exception(f"Need a file. Looks like '{self.__full_name__}' is just a directory.")
        #
        #   Validate the MIME type
        if mimetype in OAI_TRANSCRIPTION_MIME_TO_EXT:
            self.__mime_type__ = mimetype
            self.__extension__ = OAI_TRANSCRIPTION_MIME_TO_EXT[mimetype]
        else:
            raise Exception(f"MIME type '{mimetype}' is is not one of the allowable audio types.")
        
        #
        #   Make sure there is a stream
        if not stream:
            raise Exception(f"Empty 'stream'. Need to supply an open 'stream' parameter for SetFile()")

        self.__file_handle__ = stream

        self.__data__['file'] = self.__full_name__
        return



    #
    #   Get a multi-part mime encoded version of this data.
    #   
    def getFormMultiPartEncoded(self):
        '''
        Before a file (raw data) can be sent, it has to be encoded. This returns a MIME encoded form
        so that the raw data can be sent to the remote server using the HTTP prototcol. For this
        class - this should be an audio file that will be transcribed.
        '''
        #   Create a copy of our data
        data = self.__clean_dict__()
        #
        #   The file needs to be expressed as a specific tuple structure
        #
        file_tuple = self.__get_tuple__()
        
        if not file_tuple:
            raise Exception(f"The field 'file' looks corrupted. Looks like '{self.__data__['file']}'")        

        if not isinstance(file_tuple,tuple):
            raise Exception(f"The file tuple looks corrupted. Looks like '{str(file_tuple)}'")        
        #
        #   The file_tuple is a descriptor of what the data is and is placed in the file
        #   field for the encoder to work
        data['file'] = file_tuple

        #
        #   Have to fix a few of the fields ... It turns out there is a problem with the
        #   MultipartEncoder from requests_toolbelt. It uses the string encode method and
        #   content that is not a string - like a float or int - cause it trouble. So, to
        #   make this work we have to convert the 'temperature' field to a string
        #
        #   /requests_toolbelt/multipart/encoder.py", line 416, in encode_with
        #   return string.encode(encoding)
        #   AttributeError: 'float' object has no attribute 'encode'
        #
        if 'temperature' in data:
            data['temperature'] = str(data['temperature'])
        #
        #   Might have to 'fix' other fields but this works for a basic transcription
        #   of an audio file
        #
        #   Now, get the encoded form and return that
        form = MultipartEncoder(fields=data)
        return form


    #
    #   A method to set the model to use for this request
    #   
    def setModel(self, model=MODEL_DEFAULT):
        '''
        Set the model to be used for this request.
        
        Optional Parameters:
        model           : one of the OpenAI models that works for chat completions
        '''
        if model:
            self.__data__["model"] = model
        else:
            self.__data__["model"] = ""
        return
        

    #
    #   A method to set the temperature - the 'sampling temperature' with higher values 
    #   providing more randomness and lower values being much more deterministic. Range 
    #   is 0.0 .. 2.0
    #   
    def setTemperature(self, temp=TEMPERATURE_DEFAULT):
        '''
        Set the top_p value for this request.
        
        Optional Parameters:
        temp            : a float between 0.0 and 2.0
        '''
        if temp < 0.0: temp = 0.0
        if temp > 2.0: temp = 2.0
        self.__data__["temperature"] = temp
        return
    
    
    #
    #   A method to set the format for the response 
    #   
    def setResponseFormat(self, format='json'):
        '''
        Set the format of the resulting transcription.
        
        Parameters:
        format          : a string, one of the acceptable response formats
        '''
        if format:
            self.__data__["response_format"] = format
        else:
            self.__data__["response_format"] = ""
        return
    
    
    
    #
    #   A method to set the language of the audio recordiing. This can improve accuracy 
    #   
    def setLanguage(self, lang='en'):
        '''
        Set the language for the audio file and the resulting transcription.
        
        Parameters:
        lang            : a string 2 letter language code
        '''
        if lang:
            self.__data__["language"] = lang
        else:
            self.__data__["language"] = ""
        return
    
    
    
    #
    #   Set a prompt to instruct to guide the model, or continue a prior audio transcription
    #   A prompt should be in the same language as the audio being transcribed
    #   
    def setPrompt(self, prompt=""):
        '''
        Set a prompt to help the transcription.
        
        Parameters:
        prompt          : a string, prompt instructions
        '''
        if prompt:
            self.__data__["prompt"] = prompt
        else:
            self.__data__["prompt"] = ""
        return
    
    
    #
    #   if we have a file - just try to close it
    def close(self):
        '''
        Close the open file/stream, to make sure we don't keep these handles around
        when an object no longer needs it.
        
        '''
        if self.__file_handle__:
            try:
                self.__file_handle__.close()
                self.__file_handle__ = None
            except:
                pass
        return
    
    #
    #   return a tuple of the short filename and the open file handle
    #
    #   The tuple is expected to be in this format:
    #       ('filename', fileobj, 'content_type')
    #
    #   The tuple should be the *value* of a key:value dictionary where the key is
    #   the form field name to be uploaded.
    #
    def __get_tuple__(self):
        if self.__file_handle__:
            if self.__file_handle__.closed:
                return None
            else:
                return (self.__short_name__, self.__file_handle__, self.__mime_type__)
        return None
    
    
    
    #
    #   The main class DictionaryValidatorFromTemplate, performs a cleaning, but does not
    #   know how to clean a nested structure. Is there something extra to clean here?
    #
    #def __clean_dict__(self):
    #    #   This handles the default object
    #    req_data = super().__clean_dict__()
    #    #   Here we would clean anything nested in req_data
    #    return req_data

    
    #
    #   Just in case, we'll try to close any open file handles when this object is being
    #   disposed.
    #
    def __del__(self):
        self.close()
        return

#####
#   
#   END class TranscriptionPayload definition
#   
#####

if __name__ == '__main__':
    print("TranscriptionPayload.py is a class with no main()")



