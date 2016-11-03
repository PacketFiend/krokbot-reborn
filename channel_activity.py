#!/usr/bin/env python
#
# Name:    channel_activity.py
# Author:  Syini666, ekim, Striek
# Date:    Various dates in 2015/2016
# Summary: krokbot: evil AI
#

from sopel import module, tools
import random	# We might decide to only sample 1 in 10 messages or something
from random import randint
import sys
import threading
import math

class channelActivity:

	dictionary = {}		# Yeah, stupid name, I know
	dictionary = {'tenseconds':0, 'oneminute':1, 'tenminutes':2, 'onehour':3}

	def __init__(self, name):
		self.channelActivity = 0
		self.name = name
		self.messages = [0,0,0,0]
		self.messages[channelActivity.dictionary['tenseconds']] = 0	# Messages in last 10 seconds
		self.messages[channelActivity.dictionary['oneminute']] = 0	# Messages in last minute
		self.messages[channelActivity.dictionary['tenminutes']] = 0	# Messages in last 10 minutes
		self.messages[channelActivity.dictionary['onehour']] = 0	# Messages in last hour
		self.timers = []						# List of all timers we will use
		self.channelActivityCounterSum = 0				# Boil it all down to a single number, the sum of lograthmic and exponential functions
		self.channelActivityCounterExp = 0
		self.channelActivityCounterLog = 0
		self.channelActivityExp = 0
		self.channelActivityLog = 0
		self.logFactor = 20						# The multiple used in the logarithmic decay function
		self.expFactor = 0.01						# The multiple used in the exponential decay funciton
		self.powFactor = 3						# channelActivityCounterExp is raised to this power

	# Increment all counters, and set timers to decrement them at the appropriate times
	def newMessage(self):
		print self.messages
		self.messages[channelActivity.dictionary['tenseconds']] += 1
		self.channelActivityCounterExp += 1
		self.channelActivityCounterLog += 1

		t = threading.Timer(10, self.decrementMessageCount, args=[channelActivity.dictionary['tenseconds']])
		t.start()
		self.timers.append(t)

	# Decrement the message count, place that message in the next queue, and start a new timer for it
	def decrementMessageCount(self, counter):
		print "Decrementing..."
		print counter

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

		print "Log counter: " + str(self.channelActivityCounterLog) + "; exp counter: " + str(self.channelActivityCounterExp)

		self.channelActivityExp = math.pow(self.channelActivityCounterExp,self.powFactor) * self.expFactor
		if self.channelActivityCounterLog == 0: self.channelActivityLog = 0 	# log(0) is undefined
		else: self.channelActivityLog = self.logFactor * math.log(self.channelActivityCounterLog)
		self.channelActivitySum = self.channelActivityExp + self.channelActivityLog

defaultTimer = {} # channelActivity('defaultTimer')

# Counts the number of messages per channel and calculate activity on every message
@module.rule('[^\.!].*')
def countMessages(bot, trigger):

	channel = str(trigger.sender.lstrip('#'))

	print "Channel: " + channel + "; trigger.sender: " + trigger.sender
	if not channel in defaultTimer:
		defaultTimer[channel] = channelActivity(channel)

	defaultTimer[channel].newMessage()
	defaultTimer[channel].calculateChannelActivity(bot, trigger.sender)

# Calculates channel activity once per minute if the channel is dead - newer messages are given more weight
@module.interval(60)
def calculateChannelActivity(bot):

	for channel in defaultTimer:
		defaultTimer[channel].calculateChannelActivity(bot, channel)
		# At least -try- to delete the old timers. Dumbass Python.
		for timer in defaultTimer[channel].timers:
			if timer.finished.is_set():
				print timer.name + " is stopped. Deleting it."
				defaultTimer[channel].timers.remove(timer)
				del timer


@module.commands('show_channel_activity')
def show_channel_activity(bot, trigger):
	'''Prints the current channel activity level to the channel it's called in'''

	arg = trigger.group(2)
	channel = str(trigger.sender.lstrip('#'))
	numTimers = 0

	defaultTimer[channel].calculateChannelActivity(bot, trigger.sender)
	if not arg:
		bot.msg(trigger.sender, trigger.nick + ", current channel activity level is " + str(defaultTimer[channel].channelActivity) 
		        + " and sum of exp,log is " + str(defaultTimer[channel].channelActivitySum) + " (" + str(defaultTimer[channel].channelActivityExp) + "+" + str(defaultTimer[channel].channelActivityLog) + ")" 
			+ " based on " + str(defaultTimer[channel].channelActivityCounterExp) + "," + str(defaultTimer[channel].channelActivityCounterLog))
	else:
		print "Showing stats for " + arg
		bot.msg(trigger.sender, trigger.nick + ", current channel activity level is " + str(defaultTimer[arg].channelActivity) 
		        + " and sum of exp,log is " + str(defaultTimer[arg].channelActivitySum) + " (" + str(defaultTimer[arg].channelActivityExp) + "+" + str(defaultTimer[arg].channelActivityLog) + ")" 
			+ " based on " + str(defaultTimer[arg].channelActivityCounterExp) + "," + str(defaultTimer[arg].channelActivityCounterLog))


	for timer in defaultTimer[channel].timers:
		if not timer.finished.is_set(): numTimers += 1

	print str(numTimers) + " timers active, " + str(len(defaultTimer[channel].timers)) + " total"

@module.thread(True)
@module.interval(30)
def decay_counter_exp(bot):
	'''Runs every 30 seconds and decays the activity counter'''
	print "Decaying exp counter..."

	for channel in defaultTimer:
		if defaultTimer[channel].channelActivityCounterExp > 0:
			defaultTimer[channel].channelActivityCounterExp -= 1

@module.thread(True)
@module.interval(5)
def decay_counter_log(bot):
	''' Runs every 5 seconds and decays the logarithmic activity counter'''
	print "Decaying log counter..."

	for channel in defaultTimer:
		if defaultTimer[channel].channelActivityCounterLog > 0:
			defaultTimer[channel].channelActivityCounterLog -= 1

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
