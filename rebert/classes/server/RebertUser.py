#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: RebertUser.py
#   REVISION: March, 2024
#   CREATION DATE: December, 2024
#   Author: David W. McDonald
#
#   This is the rebert specific implementation of the flask_login 'user'. This allows the
#   rebert system to maintain login authentication
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
import flask_login


REBERT_USER_PROFILE_TEMPLATE = {
    'account_id':               '',  
    'username':                 '',
    'email':                    '',
    'password':                 '',
    'zipcode':                  '',
    'creation_ts':              '',
    'active':                   True,
    'allow_audio_logging':      True
}

#
#   A generic user with some fields that we might use   
#
class RebertUser(flask_login.UserMixin):
    #
    #
    def __init__(self, *args, **kwargs):
        '''
        The base class
        '''
        super().__init__(*args, **kwargs)
        #   The 'id' attribute is required
        id = ""
        account_id = ""
        record = None
        ratings = None
        return

 

if __name__ == '__main__':
    print("RebertUser.py is a class with no main()")

