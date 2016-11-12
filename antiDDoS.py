#
# Name:    antiDDoS.py
# Author:  Striek
# Date:    November 2016
# Summary: krokbot module to manage channel limit automatically, based on the current number of users plus a margin
#	   used as an anti-DDoS measure.
#

from sopel import module, tools, bot
from sopel.tools.target import User, Channel
import random	# We might decide to only sample 1 in 10 messages or something
from random import randint
import sys
import threading

global limitMargin
limitMargin = 2
global lockedChannels
lockedChannels = []

@module.require_admin
@module.commands('channel_limit')
def channel_limit(bot, trigger):

	newLimit = trigger.group(2)
	bot.msg(trigger.sender, trigger.nick + ", setting channel limit to " + newLimit)

	#try:
	bot.write(['MODE', trigger.sender , "+l" , newLimit])
	#except:
	#bot.msg(trigger.sender, trigger.nick + " , unhandled exception occured :`(")


@module.commands('show_users')
def show_users(bot, trigger):

	bot.msg(trigger.sender, trigger.nick + ", here's a list of everyone in here:")

	for user in bot.users:
		bot.msg(trigger.sender, user)


@module.event('PART')
@module.unblockable
@module.rule('.*')
def userPart(bot, trigger):
	# Sets a new channel user limit every time a user parts a channel in which the bot is at least a halfop
	# The new limit will be equal to the number of users in the channel, plus a margin which can be changed in setLimitMargin

	global limitMargin
	global lockedChannels
	if bot.privileges[trigger.sender][bot.nick] < module.HALFOP:
		print "Can't set the channel limit, as I'm not at leaft a halfop in " + trigger.sender
		return
	if trigger.sender in lockedChannels:
		print trigger.sender + " has a locked down channel limit. We're probably being DDoS'ed"
		bot.msg(trigger.sender, "Not changing the channel limit. We are locked down for now.")
		return

	# Calculate the new channel limit to be the number of users plus the margin we specified, tracked as limitMargin
	newLimit = len(bot.channels[trigger.sender].users) + limitMargin

	bot.msg(trigger.sender, "Setting channel limit to " + str(newLimit))
	# Set the new channel limit
	bot.write(['MODE', trigger.sender , "+l" , str(newLimit)])

@module.event('JOIN')
@module.unblockable
@module.rule('.*')
def userJoin(bot, trigger):
	# Sets a new channel user limit every time a user joins a channel in which the bot is at least a halfop
	# The new limit will be equal to the number of users in the channel, plus a margin which can be changed in setLimitMargin

	global limitMargin
	global lockedChannels
	if bot.privileges[trigger.sender][bot.nick] < module.HALFOP:
		print "Can't set the channel limit, as I'm not at leaft a halfop in " + trigger.sender
		return
	if trigger.sender in lockedChannels:
		print trigger.sender + " has a locked down channel limit. We're probably being DDoS'ed"
		bot.msg(trigger.sender, "Not changing the channel limit. We are locked down for now.")
		return

	# Calculate the new channel limit to be the number of users plus the margin we specified, tracked as limitMargin
	newLimit = len(bot.channels[trigger.sender].users) + limitMargin

	bot.msg(trigger.sender, "Setting channel limit to " + str(newLimit))
	# Set the new channel limit
	bot.write(['MODE', trigger.sender , "+l" , str(newLimit)])

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
