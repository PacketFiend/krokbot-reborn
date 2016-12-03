#!/usr/bin/env python
#
# Name:    krokbot-twitter.py
# Author:  Striek
# Date:    Dec 2016
# Summary: krokbot Twitter module
#


import config
from sopel import module, tools
from sopel.tools import events
import pymysql
import random
import time
from random import randint
import re
from pprint import pprint

import sys, os, getopt, twitter, requests, tweepy

from sqlalchemy import (create_engine, Table, Column, Text, Integer, String, MetaData, ForeignKey, exc)
from sqlalchemy.sql import (select, exists)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

api = twitter.Api(consumer_key=config.tw_consumer_key,
	consumer_secret=config.tw_consumer_secret,
	access_token_key=config.tw_access_token_key,
	access_token_secret=config.tw_access_token_secret)

metadata = MetaData()

loggedInUsers = []
whoisReceived = False
displayUpdates = False

engine = create_engine(config.sql_connection_string)

coolkids = Table('coolkids', metadata, autoload=True, autoload_with=engine)

@module.commands('tweet')
def postStatusUpdate(bot, trigger):
	"""Posts a twitter status update with krokbot's twitter account. URLs will be automatically shortened. Use !tweetpic for multimedia tweets.
usage: !tweet <update>
"""
	loginStatus = False

	message = str(trigger.group(2))
	nick = trigger.nick
	conn = engine.connect()
	q = select([coolkids.c.cantweet]).where(coolkids.c.nick == nick)
	try:
		items = conn.execute(q)
	except OperationalError:
		bot.msg(trigger.sender, nick + ", you broke the fucking SQL server. Gimme a minute and try again")
	row = items.fetchone()
	try:
		canTweet = row[0]
	except TypeError:
		canTweet = 0

	pprint(bot)
	loginStatus = isLoggedIn(bot, nick)
	if loginStatus and canTweet:
		status = api.PostUpdate(message)
		bot.msg(trigger.sender, trigger.nick + ", you just tweeted: " + " " + status.text)
	else:
		if not loginStatus:
			bot.msg(trigger.sender, "Don't be a fucking tool. I don't let just anybody tweet. Register with Nickserv.")
		elif not canTweet:
			bot.msg(trigger.sender, "Hey there pipo, I just don't like you enough. Get one of my admins to vouch for you.")
		else:
			bot.msg(trigger.sender, "Sorry " + nick + ", you cannot send tweets. I'm so high I can't really figure out why.")

@module.commands('tweetpic')
def postStatusUpdatePic(bot, trigger):
	"""Posts a twitter status update with krokbot's twitter account. URLs will be removed and the remainder tweeted.
usage: !tweet <update> <url> [<more update>]
"""
	nick = trigger.nick
	loginStatus = False
	#regex = re.compile(r"https?://[^\s]*")
	regex = re.compile("(https?|ftp)://([^\s/?\.#]+\.?)+(/[^\s]*)?")
	match = regex.search(trigger.group(2))
	message = str(trigger.group(2))

	if match:
		url = match.group()
		message = message.replace(url,"").replace("  ", " ")		# Remove the URL from the message, and collapse any douple spaces
		bot.msg(trigger.sender, "The message is: " + message)
	else:
		bot.msg(trigger.sender, "You need to include a URL, asshole.")
		return

	conn = engine.connect()
	q = select([coolkids.c.cantweet]).where(coolkids.c.nick == nick)
	try:
		items = conn.execute(q)
	except OperationalError:
		bot.msg(trigger.sender, nick + ", you broke the fucking SQL server. Gimme a minute and try again")
		return
	row = items.fetchone()
	try:
		canTweet = row[0]
	except TypeError:
		canTweet = 0

	loginStatus = isLoggedIn(bot, nick)
	if loginStatus and canTweet:
		status = api.PostMedia(message, url)
		bot.msg(trigger.sender, trigger.nick + ", you just tweeted: " + " " + status.text)
	else:
		if not loginStatus:
			bot.msg(trigger.sender, "Don't be a fucking tool. I don't let just anybody tweet. Register with Nickserv.")
		elif not canTweet:
			bot.msg(trigger.sender, "Hey there pipo, I just don't like you enough. Get one of my admins to vouch for you.")
		else:
			bot.msg(trigger.sender, "Sorry " + nick + ", you cannot send tweets. I'm so high I can't really figure out why.")

@module.require_admin
@module.commands('hideupdates')
def hideUpdates(bot, trigger):
	global displayUpdates
	displayUpdates = False
	bot.msg(trigger.sender, trigger.nick + ", now hiding Twitter status updates")

@module.require_admin
@module.commands('displayupdates')
def displayUpdates(bot, trigger):
	global displayUpdates
	displayUpdates = True
	bot.msg(trigger.sender, trigger.nick + ", now showing Twitter status updates")

@module.require_admin
@module.commands('showupdates')
def showUpdates(bot, trigger):
	
	global displayUpdates
	displayUpdates = True

	# Set up the user stream - returns a generator object
	userStream = api.GetUserStream(withuser='followings')
	print userStream
	bot.msg(trigger.sender, "Twitter Stream Activated")

	# Run this loop looking for new tweets
	for datum in userStream:
		if "text" in datum:
			for channel in bot.channels:
				if displayUpdates:
					bot.msg(channel, "Incoming tweet from @" + datum['user']['screen_name'] + ": " + datum['text'])
		print datum

@module.rule('.*')
@module.event('319', '330')	# 307 is returned if a user is logged in. 319 is the list of channels it's in, and should be received first.
def parseWhois(bot, trigger):

	global whoisReceived
	triggerParts = trigger.raw.split(' ')
	# The server will return a response such as
	# :irc.unerror.com 330 AlsoStriek Syini666 Syini666 :is logged in as
	# We need to check the nick it's referring to, and whether it's registered or not.
	nick = triggerParts[3]
	# Now add it to the list, if the user is logged in
	print trigger.raw
	if "is logged in as" in trigger:
		loggedInUsers.append(nick)
	whoisReceived = True

@module.commands('loggedin')
def checkLoginStatus(bot, trigger):
	pprint(bot.users)
	nick = trigger.group(2)
	loggedIn = isLoggedIn(bot, nick)
	print loggedIn

def isLoggedIn(bot, nick):

	global whoisReceived

	# First, remove the nick from the list of logged in users, if it's there
	# This is to ensure the nick is removed if a user has logged out
	if nick in loggedInUsers:
		loggedInUsers.remove(nick)
	bot.write(['WHOIS', nick])

	# Now wait for the server command to be returned and parseWhois() to be triggered
	whoisReceived = False
	while not whoisReceived: time.sleep(0.1)
	if nick in loggedInUsers:
		whoisReceived = False
		return True
	else:
		whoisReceived = False
		return False
