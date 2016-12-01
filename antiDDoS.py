#
# Name:    antiDDoS.py
# Author:  Striek
# Date:    November 2016
# Summary: krokbot module to manage channel limit automatically, based on the current number of users plus a margin
#	   used as an anti-DDoS measure.
#

from sopel import module, tools, bot
from sopel.tools.target import User, Channel
from random import randint
import sys, os
import threading
from pprint import pprint,pformat

global limitMargin
limitMargin = 2
global lockedChannels
lockedChannels = []
global maxUsers
maxUsers = 100

import sqlalchemy

#engine = sqlalchemy.create_engine("mysql+pymysql://krok:kr0kl4bs@localhost/krokbot?host=localhost?port=3306")
engine = sqlalchemy.create_engine("mysql+pymysql://ken:bwK9VnGxtCdd@asgard.pure-defect.com:3306/krokbot")

@module.require_admin
@module.commands('channel_limit')
def channel_limit(bot, trigger):

	newLimit = trigger.group(2)
	bot.msg(trigger.sender, trigger.nick + ", setting channel limit to " + newLimit)

	bot.write(['MODE', trigger.sender , "+l" , newLimit])


@module.commands('show_users')
def show_users(bot, trigger):

	bot.msg(trigger.sender, trigger.nick + ", here's a list of everyone in here:")

	for user in bot.users:
		bot.msg(trigger.sender, user)


@module.event('PART')
@module.event('JOIN')
@module.event('KICK')
@module.event('QUIT')
@module.event('KILL')
@module.priority('low')
@module.unblockable
@module.rule('.*')
def userJoin(bot, trigger):
	# Sets a new channel user limit on specific channel or server events in channels where the bot is at least a halfop
	# The new limit will be equal to the number of users in the channel, plus a margin which can be changed in setLimitMargin
	# Is called on every part, join, kick, quit, and kill evemt

	global limitMargin
	global lockedChannels

	# If this was a JOIN, PART, or KICK event , we know which channel it occured in.
	# On KILL and QUIT events, we don't so we reset the channel limit on /every/ channel.
	if trigger.event == 'KICK' or trigger.event == 'JOIN' or trigger.event == 'PART':
		print "PART/KICK/JOIN event triggered!"
		setChannelLimit(bot, trigger.sender)
	else:
		# We don't know which channel this was sent from, so we'll just cycle through every channel we're in...
		print "KILL or QUIT event triggered!"
		for channel in bot.channels:
			setChannelLimit(bot, channel)

@module.require_admin
@module.commands('set_limit_margin')
@module.unblockable
def setLimitMargin(bot, trigger):
	'''Sets the margin by which the channel limit is greater than the number of users'''

	global limitMargin
	limitMargin = int(trigger.group(2))
	bot.msg(trigger.sender, trigger.nick + ", limit margin is now " + str(limitMargin))

@module.require_admin
@module.commands('lock_channel_limit')
@module.unblockable
@module.priority('high')
def lockChannelLimit(bot, trigger):
	'''Locks down the channel limit it is called in. This is to be used in the case of DDoS attacks'''

	global lockedChannels
	global limitMargin
	if not trigger.sender in lockedChannels:
		lockedChannels.append(trigger.sender)
		bot.msg(trigger.sender, trigger.nick + ", channel limit for " + trigger.sender + " is locked down at " + str(len(bot.channels[trigger.sender].users) + limitMargin))
	else:
		bot.msg(trigger.sender, trigger.nick + ", this channel limit is already locked, dumbass.")

@module.require_admin
@module.commands('unlock_channel_limit')
@module.unblockable
def unlockChannelLimit(bot, trigger):
	'''Unlocks the channel limit for the channel it is called in. Takes no arguments.'''

	global lockedChannels
	if trigger.sender in lockedChannels:
		lockedChannels.remove(trigger.sender)
		bot.msg(trigger.sender, trigger.nick + ", channel limit for " + trigger.sender + " has been unlocked")
		# Reset the channel limit
		userJoin(bot, trigger)
	else:
		bot.msg(trigger.sender, trigger.nick + ", this channel limit is already unlocked, dumbass.")

@module.commands('max_users')
@module.require_admin
def maxUsers(bot, trigger):
	'''Sets the maximum number of users that can be in any channel where this bot is at least a halfop'''

	global maxUsers
	maxUsers = int(trigger.group(2))
	bot.msg(trigger.sender, trigger.nick + ", maximum users in any channel I'm a halfop in is now " + str(maxUsers))

def setChannelLimit(bot, channel):
	# Sets a new channel limit on the given channel based on the number of users in the channel and an operator-defined margin
	global limitMargin
	global lockedChannels
	global maxUsers

	if bot.privileges[channel][bot.nick] < module.HALFOP:
		print "Can't set the channel limit, as I'm not at leaft a halfop in " + channel
		return
	if channel in lockedChannels:
		print channel + " has a locked down channel limit. We're probably being DDoS'ed"
		bot.msg(channel, "Not changing the channel limit. We are locked down for now.")
		return
	# Calculate the new channel limit to be the number of users plus the margin we specified, tracked as limitMargin
	# Or, to the maximum number of users specified by maxUsers
	if len(bot.channels[channel].users) + limitMargin <= maxUsers:
		newLimit = len(bot.channels[channel].users.keys()) + limitMargin
	else:
		newLimit = maxUsers
	#bot.msg(channel, "Setting channel limit to " + str(newLimit))

	# Set the new channel limit
	bot.write(['MODE', channel , "+l" , str(newLimit)])

@module.commands('show_channel_users')
@module.require_admin
def showChannelUsers(bot, trigger):
	''' Prints out a list of every user in the channel - for debugging purposes'''

	channel = trigger.group(2)
	bot.msg(trigger.nick, trigger.nick + ", this is the state of bot.privileges[" + str(channel) + "]:")
	bot.msg(trigger.nick, pformat(bot.privileges[channel]))

	bot.msg(trigger.nick, "And here's all of bot.privileges:")
	bot.msg(trigger.nick, pformat(bot.privileges))

@module.commands('hush_channel')
@module.require_admin
@module.priority('high')
@module.unblockable
def hushChannel(bot, trigger):
	'''Sets the channel +m, and gives everyone on a predefined list voice. Used for bot parties'''

	bot.msg(trigger.sender, trigger.nick + ", setting " + trigger.sender + " +m and giving all the cool kids +v")

	# Set the channel +m, with exptra protection agains KNOCK flood attacks
	bot.write(['MODE', trigger.sender, "+mKi"])

	# Now read in a list of the cool kids, and give them all voice
	conn = engine.connect()
	query = "SELECT nick FROM coolkids WHERE trusted = 1"
	items = conn.execute(query)
	for entry in items:
		# Results are returned as a tuple with an empty second element
		nick = entry[0]
		if nick in bot.privileges[trigger.sender].keys():
			bot.write(['MODE', trigger.sender, "+v", nick])


@module.commands('unhush_channel')
@module.require_admin
@module.priority('high')
@module.unblockable
def unHushChannel(bot, trigger):
	'''Sets the channel -m, and removes +v from everyone on a predefined list. Used for bot parties'''

	bot.msg(trigger.sender, trigger.nick + ", setting " + trigger.sender + " -m and taking +v from all the cool kids")

	# Read in a list of the cool kids, and take voice from them
	conn = engine.connect()
	query = "SELECT nick FROM coolkids WHERE trusted = 1"
	items = conn.execute(query)
	for entry in items:
		# Results are returned as a tuple with an empty second element
		nick = entry[0]
		if nick in bot.privileges[trigger.sender].keys():
			bot.write(['MODE', trigger.sender, "-v", nick])


	# Set the channel -m and remove no-KNOCK and invite
	bot.write(['MODE', trigger.sender, "-mKi"])
