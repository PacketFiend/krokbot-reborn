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

	# Increment all counters, and set timers to decrement them at the appropriate times
	def newMessage(self):
		print self.messages
		self.messages[channelActivity.dictionary['tenseconds']] += 1

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

	# Calculates channel activity - newer messages are given more weight
	def calculateChannelActivity(self, bot, channel=None):

		if channel:
			self.channelActivity = self.messages[channelActivity.dictionary['tenseconds']] * 1000
			self.channelActivity += self.messages[channelActivity.dictionary['oneminute']] * 100
			self.channelActivity += self.messages[channelActivity.dictionary['tenminutes']] * 10
			self.channelActivity += self.messages[channelActivity.dictionary['onehour']]
		else:
			print "Oops! What the fuck did you do?!?!"

defaultTimer = {} # channelActivity('defaultTimer')

# Counts the number of messages per channel and calculate activity on every message
@module.rule('[^\.].*')
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

	channel = str(trigger.sender.lstrip('#'))
	numTimers = 0

	defaultTimer[channel].calculateChannelActivity(bot, trigger.sender)
	bot.msg(trigger.sender, trigger.nick + ", current channel activity level is " + str(defaultTimer[channel].channelActivity))

	for timer in defaultTimer[channel].timers:
		if not timer.finished.is_set(): numTimers += 1

	print str(numTimers) + " timers active, " + str(len(defaultTimer[channel].timers)) + " total"
