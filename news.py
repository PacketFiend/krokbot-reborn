#!/usr/bin/env python
#
# Name:    news.py
# Author:  Syini666, ekim, Striek
# Date:    Various dates in 2015/2016
# Summary: krokbot: evil AI
#

from sopel import module, tools
import random
import time
from random import randint

import sys
import requests
import tinyurl

import creds
import feedparser
"""
@module.commands('echo','repeat')
def echo(bot, trigger):
	bot.reply(trigger.group(2))
"""

# Begin News System
global news
news = False

class headlineList:

	def __init__(self, name):
		self.searchList = ['terror','gun','attack','seige','shooting']
		self.headlines = []
		self.name = name
		self.wordlist = ""
	
	def add_searchTerm(self,searchTerm,nick,channel,bot):
		if searchTerm in self.searchList:
			bot.msg(channel,nick + ", " + searchTerm + " is already in the search list.")
		else:
			self.searchList.append(searchTerm)
		self.wordlist = ""
		for term in self.searchList:
			self.wordlist = self.wordlist + " " + term

		print self.searchList
	
	def remove_searchTerm(self,searchTerm,nick,channel,bot):
		if searchTerm in self.searchList:
			self.searchList.remove(searchTerm)
		else:
			bot.msg(channel,nick + ", " + searchTerm + " is not in the search list, so I can't remove it.")

		self.wordlist = ""
		for term in self.searchList:
			self.wordlist = self.wordlist + " " + term

		print self.searchList
	
	# Find any headlines with matching keywords. Search is case sensitive, so we convert to lowercase before searching.
	def find_hits(self):
	    hits = []
	    for headline in self.headlines:
	        for term in self.searchList:
	            if term.lower() in headline.lower():
	                hits.append(headline)
	            else:
	                pass
            goats = list(set(hits))
	    print self.searchList
            return goats

defaultHeadlines = headlineList('default')

@module.commands('addtoheadlines')
def addtoheadlines(bot, trigger):
	imp = trigger.group(2)
	shard = imp.split(" ")
	for term in shard:
		defaultHeadlines.add_searchTerm(term,trigger.nick,trigger.sender,bot)

	bot.msg(trigger.sender, trigger.nick + ", now searchnig for these words: " + defaultHeadlines.wordlist)

@module.commands('removefromheadlines')
def removefromheadlines(bot, trigger):
	imp = trigger.group(2)
	shard = imp.split(" ")
	for term in shard:
		defaultHeadlines.remove_searchTerm(term,trigger.nick,trigger.sender,bot)

	bot.msg(trigger.sender, trigger.nick + ", now searchnig for these words: " + defaultHeadlines.wordlist)

# Function to fetch the rss feed and return the parsed RSS
def parseRSS( rss_url ):
    return feedparser.parse( rss_url )

# Function grabs the rss feed headlines (titles) and returns them as a list
def getHeadlines( rss_url ):
    headlines = []

    feed = parseRSS( rss_url )
    for newsitem in feed['items']:
	newsitem['title'] += " - " + tinyurl.create_one(newsitem['link'])
        headlines.append(newsitem['title'])

    return headlines

@module.require_admin
@module.commands('news_status')
def news_status(bot, trigger):
	global news
	if news == False:
		message = "News Systems: Disabled"
	else:
		message = "News Systems: Active"
	bot.say(message)

@module.require_admin
@module.commands('news_enable')
def news_enable(bot, trigger):

	defaultHeadlines = headlineList('defaultHeadlines')
	global news
	if news == False:
		news = True
		message = "News System has been Activated"
	else:
		message = "News System is already active"
	bot.say(message)

@module.require_admin
@module.commands('news_disable')
def news_disable(bot, trigger):
	global news
	if news == True:
		news = False
		message = "News System has been Deactivated"
	else:
		message = "News System is already deactivated"
	bot.say(message)

#@module.interval(120)
@module.commands('news_announce')
def news_announce(bot, trigger):
	# when using module.interval() you dont need to pass trigger to the function, just bot
	#defaultHeadlines = headlineList('default')
	global news
	if news == True:
		# A list to hold all headlines
		allheadlines = []

		# List of RSS feeds that we will fetch and combine
		newsurls = {
		    'googlenews':       'http://news.google.com/news?cf=all&hl=en&pz=1&ned=us&output=rss'
		}

		# Iterate over the feed urls
		for key,url in newsurls.items():
		    # Call getHeadlines() and combine the returned headlines with allheadlines
		    allheadlines.extend( getHeadlines( url ) )
		print allheadlines
		defaultHeadlines.headlines = allheadlines
		things = defaultHeadlines.find_hits()
		for t in things:
			bot.msg("#safespace",t,1)	
		#message = "The Krokbot News System: keeping you informed of up-to-the-minute jihad jihad"
		#bot.msg("#lounge",message, 1)

# End News System
