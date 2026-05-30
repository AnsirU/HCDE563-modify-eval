#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: AsyncTimer.py
#   REVISION: July, 2024
#   PYTHON 3 CONVERSION: November, 2019
#   CREATION DATE: April, 2012
#   Author: David W. McDonald
#
#   An asynchronous timer. The idea is to make some action happen at different
#   intervals. The action could happen at regular intervals, like every 42 seconds or
#   it can be set up to happen with some randomness, such as every
#
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
import sys, time, random
from rebert.classes.base.ThreadedObject import Object

class AsyncTimer(Object):
    def __init__(self, *args, **kwargs):
        '''
        Initializes the object.
        
        Optional Parameters:
        name        : An optional description or name for the object
        logger      : An optional Logger object (rebert.classes.base.Logger)
        '''
        super().__init__(*args, **kwargs)       
        self.ticks = 0
        self.secs = 0.0
        self.mins = 0.0
        self.randsecs = 0.0
        self.timed_object = None
        return

    ##
    #   The timer is designed to activate the timed object on the specified intervals
    #
    #   The timed_object should have a specific method called intervalAction() that 
    #   takes zero parameters. This method will be called each time the timer expires.
    #
    def setTimedObject(self, to=None):
        self.timed_object = to

    ##
    #   Return the object that is supposed to be timed
    #
    def getTimedObject(self):
        return self.timed_object

    ##
    #   Set the amount/range of randomness in the intervals
    #   if this is zero (default) then the timer activates on
    #   the specified interval. 
    #
    def setRandomness(self, r=0):
        tot = float(60.0*self.mins)+float(self.secs)
        maxrandsecs = int(tot)
        if( r>=0 ):
            if( r<=maxrandsecs ):
                self.randsecs=r
            else:
                self.randsecs=0
        else:
            self.randsecs=0

    ##
    #   Set the number of minutes and seconds 
    #
    def setTimer(self, m=0.0, s=10.0):
        if( s >= 0.0 ):
            self.secs=s
        else:
            self.secs=10.0
        if( m >= 0.0 ):
            self.mins=m
        else:
            self.mins=0.0

    ##
    #
    def run(self):
        t = float(60.0*self.mins)+float(self.secs)
        self.debug("%s Thread starting"%(self.name))
        while( self.running ):
            # should there be some randomness in the timer
            if( self.randsecs > 0.0 ):
                sign = random.randint(0,1)
                if( sign > 0 ):
                    d = -1.0*random.randint(0,self.randsecs)
                    #print("decrease",d)
                else:
                    d = random.randint(0,self.randsecs)
                    #print("increase",d)
                wt = t+d
            else:
                wt = t
            if( self.running ):
                time.sleep(wt)
            self.ticks += 1
            if( self.timed_object ):
                if( self.running ):
                	self.timed_object.intervalAction()
            else:
	            self.debug("<%s-%d:%f>"%(self.name,self.ticks,wt))

        self.debug("<%s-%d:%f> Thread terminated"%(self.name,self.ticks,wt))
        return

    ##
    #
    def startThread(self, d=True):
        self.daemon = d
        self.running = True
        self.start()
        return

    ##
    #
    def terminateThread(self):
        self.running = False
        return


if __name__ == '__main__':
    print("AsyncTimer.py is a class with no main()")
    #timer = AsyncTimer(name="testTimer")
    #timer.setTimer(m=0,s=5)
    #timer.setRandomness(r=3)
    #timer.showDebug(True)
    #timer.startThread(d=False)
    #
    # Alternate approach as a daemon, but not supposed to have output!
    #timer.debug = False
    #timer.startThread(d=True)
    #time.sleep(6000)

