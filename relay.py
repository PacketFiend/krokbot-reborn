#!/usr/bin/env python
#
# Name:    relay.py
# Author:  Striek
# Date:    2016-11-04
# Summary: relays messages from some channels to other channels. Mostly useful for
#          channel_activiy.py testing, as that module needs an active channel to test
#

from sopel import module, tools
from random import randint
import sys
import threading
import math
from collections import defaultdict

global relayChannels
relayChannels = defaultdict(list)

@module.require_admin
@module.commands('relayon')
def relayOn(bot, trigger):
	'''Turns off relaying to the current channel from the named channel. Usage: .relayon <channel>'''
	global relayChannels
	print relayChannels
	channelString = ""
	channelToRelay = str(trigger.group(2).lstrip('#'))
	currentChannel = str(trigger.sender)

	if not channelToRelay in relayChannels: relayChannels[channelToRelay] = []
	relayChannels[channelToRelay].append(currentChannel)
	print relayChannels
	channelString = ""
	for foo in relayChannels: print foo
	channelString = ' '.join(relayChannels[channelToRelay])
	bot.msg(trigger.sender, trigger.nick + ", now relaying " + channelToRelay + " to the following channels: " + channelString)

@module.require_admin
@module.commands('relayoff')
def relayOff(bot, trigger):
	'''Turns off relaying to the current channel from the named channel. Usage: .relayoff <channel>'''

	global relayChannels
	imp = trigger.group(2)
	channelToRelay = str(trigger.group(2).lstrip('#'))
	currentChannel = str(trigger.sender)

	relayChannels[channelToRelay].remove(currentChannel)
	channelString = ""
	channelString = ' '.join(relayChannels[channelToRelay])
	bot.msg(trigger.sender, trigger.nick + ", now relaying " + channelToRelay + " to the following channels: " + channelString)


@module.rule('[^.!].*')		# Don't relay bot commands. This might result in a feedback loop.
def relayMessages(bot, trigger):
	'''Relays messages from every channel the bot is in to all appropriate channels'''

	global relayChannels
	currentChannel = str(trigger.sender.lstrip('#'))

	print relayChannels
	print currentChannel
	# Are we relaying FROM the current channel?
	if currentChannel in relayChannels:
		# Yes, and we're relaying To these channels
		for relayTo in relayChannels[currentChannel]:
			bot.msg(relayTo, trigger.nick + "> " + trigger)
