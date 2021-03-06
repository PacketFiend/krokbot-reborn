#!/usr/bin/env python
#
# Name:    channel_activity.py
# Author:  Syini666, ekim, Striek
# Date:    Various dates in 2015/2016
# Summary: krokbot: evil AI
#

from sopel import module, tools
import random   # We might decide to only sample 1 in 10 messages or something
from random import randint
import sys
import threading
import math
from pprint import pprint

def setup(bot):
    bot.memory['activity'] = {}

class channelActivity:

    dictionary = {}     # Yeah, stupid name, I know
    dictionary = {'tenseconds':0, 'oneminute':1, 'tenminutes':2, 'onehour':3}

    def __init__(self, name):
        self.channelActivity = 0
        self.name = name
        self.messages = [0,0,0,0]
        self.messages[channelActivity.dictionary['tenseconds']] = 0 # Messages in last 10 seconds
        self.messages[channelActivity.dictionary['oneminute']] = 0  # Messages in last minute
        self.messages[channelActivity.dictionary['tenminutes']] = 0 # Messages in last 10 minutes
        self.messages[channelActivity.dictionary['onehour']] = 0    # Messages in last hour
        self.timers = []                        # List of all timers we will use
        self.channelActivityCounterSum = 0              # Boil it all down to a single number, the sum of lograthmic and exponential functions
        self.channelActivityCounterExp = 0
        self.channelActivityCounterLog = 0
        self.channelActivityExp = 0
        self.channelActivityLog = 0
        self.logFactor = 50                     # The multiple used in the logarithmic decay function
        self.expFactor = 0.002                      # The multiple used in the exponential decay funciton
        self.powFactor = 3                      # channelActivityCounterExp is raised to this power
        self.expDecayFactor = 200.0                 # Default setting will cause the exponential counter to decay to 0 in one hour
        self.logDecayFactor = 5.0                   # Default setting will cause the logarithmic counter to decay to 0 in five minutes
        self.channelActivitySum = 0

    # Increment all counters, and set timers to decrement them at the appropriate times
    def newMessage(self):
        #print self.messages
        self.messages[channelActivity.dictionary['tenseconds']] += 1
        self.channelActivityCounterExp += 1
        self.channelActivityCounterLog += 1

        t = threading.Timer(10, self.decrementMessageCount, args=[channelActivity.dictionary['tenseconds']])
        t.start()
        self.timers.append(t)

    # Decrement the message count, place that message in the next queue, and start a new timer for it
    def decrementMessageCount(self, counter):
        #print "Decrementing..."
        #print counter

        self.messages[counter] = self.messages[counter] - 1

        # Previous timers are subtracted explicity (600-60) for readability
        if counter == channelActivity.dictionary['onehour']:
            pass
        elif counter == channelActivity.dictionary['tenseconds']:
            self.messages[counter+1] += 1
            t = threading.Timer(60-10, self.decrementMessageCount, args=[channelActivity.dictionary['oneminute']])
            t.start()
            self.timers.append(t)
        elif counter == channelActivity.dictionary['oneminute']:
            self.messages[counter+1] += 1
            t = threading.Timer(600-60, self.decrementMessageCount, args=[channelActivity.dictionary['tenminutes']])
            t.start()
            self.timers.append(t)
        elif counter == channelActivity.dictionary['tenminutes']:
            self.messages[counter+1] += 1
            t = threading.Timer(3600-600, self.decrementMessageCount, args=[channelActivity.dictionary['onehour']])
            t.start()
            self.timers.append(t)

    def decayLogarithmic():
        self.channelActivity = 0

    def decayExp(bot):
        self.channelActivityExp = 0

    # Calculates channel activity - newer messages are given more weight
    def calculateChannelActivity(self, bot, channel=None):

        if channel:
            self.channelActivity = self.messages[channelActivity.dictionary['tenseconds']] * 1000
            self.channelActivity += self.messages[channelActivity.dictionary['oneminute']] * 100
            self.channelActivity += self.messages[channelActivity.dictionary['tenminutes']] * 10
            self.channelActivity += self.messages[channelActivity.dictionary['onehour']]
        else:
            print "Oops! What the fuck did you do?!?!"

        #print "Log counter: " + str(self.channelActivityCounterLog) + "; exp counter: " + str(self.channelActivityCounterExp)

        self.channelActivityExp = math.pow(self.channelActivityCounterExp,self.powFactor) * self.expFactor
        if self.channelActivityCounterLog < 1: self.channelActivityLog = 0  # log(0) is undefined, and we don't want negative numbers here
        else: self.channelActivityLog = self.logFactor * math.log(self.channelActivityCounterLog)
        self.channelActivitySum = self.channelActivityExp + self.channelActivityLog
        bot.memory['activity'][channel] = self.channelActivitySum

defaultTimer = {} # channelActivity('defaultTimer')

# Counts the number of messages per channel and calculate activity on every message
@module.rule('[^\.!].*')
def countMessages(bot, trigger):

    channel = str(trigger.sender.lstrip('#'))

    #print "Channel: " + channel + "; trigger.sender: " + trigger.sender
    if not channel in defaultTimer:
        defaultTimer[channel] = channelActivity(channel)
        bot.memory['activity'][channel] = defaultTimer[channel].channelActivitySum

    defaultTimer[channel].newMessage()
    defaultTimer[channel].calculateChannelActivity(bot, channel)

# Calculates channel activity once per minute if the channel is dead - newer messages are given more weight
@module.interval(60)
def calculateChannelActivity(bot):

    for channel in defaultTimer:
        defaultTimer[channel].calculateChannelActivity(bot, channel)
        # At least -try- to delete the old timers. Dumbass Python.
        for timer in defaultTimer[channel].timers:
            if timer.finished.is_set():
                #print timer.name + " is stopped. Deleting it."
                defaultTimer[channel].timers.remove(timer)
                del timer

@module.commands('activity')
def show_channel_activity(bot, trigger):
    '''Prints the current channel activity level to the channel it's called in'''

    arg = None
    if trigger.group(2): arg = str(trigger.group(2).lstrip('#'))
    channel = str(trigger.sender.lstrip('#'))
    numTimers = 0

    defaultTimer[channel].calculateChannelActivity(bot, channel)
    
    if arg:
        print "Showing stats for " + arg
        bot.msg(trigger.sender, trigger.nick + ", current channel activity level is " + str(defaultTimer[arg].channelActivity) 
                + ", but the better metric is " + str(defaultTimer[arg].channelActivitySum))
    else:
        bot.msg(trigger.sender, trigger.nick + ", current channel activity level is " + str(defaultTimer[channel].channelActivity) 
                + ", but the better metric is " + str(defaultTimer[channel].channelActivitySum))


    for timer in defaultTimer[channel].timers:
        if not timer.finished.is_set(): numTimers += 1

    print str(numTimers) + " timers active, " + str(len(defaultTimer[channel].timers)) + " total"

@module.thread(True)
@module.interval(5)
def decay_counter_exp(bot):
    '''Runs every 5 seconds and decays the activity counter'''

    for channel in defaultTimer:
        if defaultTimer[channel].channelActivityCounterExp > 0:
            # Will decay completely in one hour unless expDecayFactor is changed
            #print "Exponential decay factor for #" + channel + " is " + str(defaultTimer[channel].expDecayFactor) + ". Decaying by " + str(defaultTimer[channel].channelActivityCounterExp / defaultTimer[channel].expDecayFactor) + " every 5 seconds."
            #print "channelActivityCounterExp is " + str(defaultTimer[channel].channelActivityCounterExp)
            defaultTimer[channel].channelActivityCounterExp -= (defaultTimer[channel].channelActivityCounterExp / defaultTimer[channel].expDecayFactor)

    for channel in defaultTimer:
        if defaultTimer[channel].channelActivityCounterLog > 0:
            # Will decay completely in five minutes unless logDecayFactor is changed
            #print "Logarithmic decay factor for #" + channel + " is " + str(defaultTimer[channel].logDecayFactor) + ". Decaying by " + str(defaultTimer[channel].channelActivityCounterLog / defaultTimer[channel].logDecayFactor) + " every 5 seconds."
            #print "channelActivityCounterLog is " + str(defaultTimer[channel].channelActivityCounterLog)
            defaultTimer[channel].channelActivityCounterLog -= defaultTimer[channel].channelActivityCounterLog / defaultTimer[channel].logDecayFactor

# Changes the factors used in the logarithmic decay function
@module.commands('logfactor')
@module.require_admin
def log_factor(bot, trigger):
    ''' Changes the multiple used in the logarithmic decay function'''

    factor = float(trigger.group(2))
    for channel in defaultTimer:
        defaultTimer[channel].logFactor = factor

# Changes the power we raise activityCounterExp to
@module.commands('powfactor')
@module.require_admin
def pow_factor(bot, trigger):
    ''' Changes the power we raise activityCounterExp to '''

    factor = float(trigger.group(2))
    print "Setting powFactor to " + str(factor)
    for channel in defaultTimer:
        defaultTimer[channel].powFactor = factor

# Changes the multiple used in the exponential decay function
@module.commands('expFactor')
@module.require_admin
def exp_factor(bot, trigger):
    '''Changes the multiple used in the exponential decay function'''

    factor = float(trigger.group(2))
    print "Setting expFactor to " + str(factor)
    for channel in defaultTimer:
        defaultTimer[channel].expFactor = factor

# Changes the exponential decay factor, affecting how long the counter takes to approach 0
@module.commands('expdecay')
@module.require_admin
def exp_decay(bot, trigger):
    '''Changes the exponential decay factor, affecting how long the counter takes to approach 0'''

    factor = float(trigger.group(2))
    for channel in defaultTimer:
        print "Changing exponential decay factor for " + channel + " to " + str(factor)
        defaultTimer[channel].expDecayFactor = factor

# Changes the logarithmic decay factor, affecting how long the counter takes to approach
@module.commands('logdecay')
@module.require_admin
def log_decay(bot, trigger):
    '''Changes the logarithmic decay factor, affecting how long the counter takes to approach 0'''

    factor = float(trigger.group(2))
    for channel in defaultTimer:
        print "Changing logarithmic decay factor for " + channel + " to " + str(factor)
        defaultTimer[channel].logDecayFactor = factor
