#!/usr/bin/env python
#
# Name:    twitter.py
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
from pprint import pprint

import sys, os, getopt, twitter, requests

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

engine = create_engine(config.sql_connection_string)

coolkids = Table('coolkids', metadata, autoload=True, autoload_with=engine)


#@module.require_admin
@module.commands('tweet')
def postStatusUpdate(bot, trigger):
	'''Posts a twitter status update with krokbot's twitter account'''

	message = str(trigger.group(2))
	nick = trigger.nick
	conn = engine.connect()
	q = select([coolkids.c.cantweet]).where(coolkids.c.nick == nick)
	items = conn.execute(q)
	row = items.fetchone()
	if row[0]:
		canTweet = row[0]
	else:
		canTweet = 0
	bot.write(['WHOIS ', trigger.nick])
	time.sleep(1)	# Wait for the server response
	# If the nick is logged in, it should be in loggedInUsers now...
	if nick in loggedInUsers and canTweet:
		status = api.PostUpdate(message)
		bot.msg(trigger.sender, trigger.nick + ", you just tweeted: " + " " + status.text)
	else:
		if nick not in loggedInUsers:
			bot.msg(trigger.sender, "Don't be a fucking tool. I don't let just anybody tweet. Register with Nickserv.")
		elif not canTweet:
			bot.msg(trigger.sender, "Hey there pipo, I just don't like you enough. Get one of my admins to vouch for you.")
		else:
			bot.msg(trigger.sender, "Sorry " + nick + ", you cannot send tweets. I'm so high I can't really figure out why.")

@module.rule('.*')
@module.event('319', '330')	# 307 is returned if a user is logged in. 319 is the list of channels it's in, and should be received first.
def parseWhois(bot, trigger):

	triggerParts = trigger.raw.split(' ')
	# The server will return a response such as
	# :irc.unerror.com 330 AlsoStriek Syini666 Syini666 :is logged in as
	# We need to check the nick it's referring to, and whether it's registered or not.
	nick = triggerParts[3]
	# First, remove the nick from the list of logged in users, if it's there
	# This is to ensure the nick is removed if a user has logged out
	if nick in loggedInUsers:
		loggedInUsers.remove(nick)
	# Now add it to the list, if the user is logged in
	print trigger.raw
	if "is logged in as" in trigger:
		loggedInUsers.append(nick)
