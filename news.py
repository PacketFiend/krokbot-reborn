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

	maxSearchTerms = 25 # Shared by all instances of this class
	maxSearchTermLength = 25 # Maximum length of any one searh term - again, shared by all instances

	def __init__(self, name):
		self.searchList = ['terror','gun','attack','seige','shooting']
		self.headlines = []
		self.name = name
		self.wordlist = ""	# This is just a string built from searchList - so we can print it in a message easily
		for term in self.searchList:
			self.wordlist = self.wordlist + " " + term
		self.rejectedTerms = ""
	
	def add_searchTerm(self,newTerms,nick,channel,bot):

		# Make sure the list of terms to search for doesn't grow too big
		newTerms = newTerms.split(" ")	# Shard the passed terms into a list
		self.rejectedTerms = ""
		if len(self.searchList) + len(newTerms) > headlineList.maxSearchTerms:
			bot.msg(channel, nick + ", I can't add that many search terms - the limit is " + str(headlineList.maxSearchTerms))
		else:	# Add all the terms we received to the search term list
			for searchTerm in newTerms:
				if searchTerm in self.searchList:
					self.rejectedTerms += searchTerm + ": already present; "
				elif len(searchTerm) > headlineList.maxSearchTermLength:
					self.rejectedTerms += searchTerm + ": >" + str(headlineList.maxSearchTermLength) + " chars; "
				else:
					self.searchList.append(searchTerm)

		# Construct a string conatining all the search terms
		self.wordlist = ""	
		for term in self.searchList:
			self.wordlist = self.wordlist + " " + term

		# Clean up the strings we constructed
		self.wordlist = self.wordlist.rstrip()
		self.rejectedTerms = self.rejectedTerms.rstrip('; ');
		print self.searchList
	
	def remove_searchTerm(self,terms2Remove,nick,channel,bot):

		terms2Remove = terms2Remove.split(" ")	# Shard the passed string of terms into a list
		self.rejectedTerms = ""
		for searchTerm in terms2Remove:		# Remove the list of terms from the search list
			if searchTerm in self.searchList:
				self.searchList.remove(searchTerm)
			else:
				self.rejectedTerms += searchTerm + " "

		# Construct a string containing all the search terms
		self.wordlist = ""
		for term in self.searchList:
			self.wordlist = self.wordlist + " " + term

		# Clean up the strings we constructed
		self.wordlist = self.wordlist.rstrip()
		self.rejectedTerms = self.rejectedTerms.rstrip()
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

@module.rate(30)
@module.commands('addtoheadlines')
def addtoheadlines(bot, trigger):
	"""Adds a new search term to the headline search. Multiple terms can be added at once."""
	if news == False: return

	imp = trigger.group(2)
	defaultHeadlines.add_searchTerm(imp,trigger.nick,trigger.sender,bot)

	bot.msg(trigger.sender, trigger.nick + ", now searching for these words: " + defaultHeadlines.wordlist)
	# If we rejected any search terms, let someone know
	if defaultHeadlines.rejectedTerms:
		bot.msg(trigger.sender, trigger.nick + ", could not add these terms: " + defaultHeadlines.rejectedTerms)

@module.rate(30)
@module.commands('removefromheadlines')
def removefromheadlines(bot, trigger):
	""" Removes a term from the headline search. Multiple terms may be removed at once."""
	if news == False: return

	imp = trigger.group(2)
	defaultHeadlines.remove_searchTerm(imp,trigger.nick,trigger.sender,bot)

	# If we couldn't remove any terms, let someone know
	if defaultHeadlines.rejectedTerms:
		bot.msg(trigger.sender, trigger.nick + ", you suck. These terms are not in the list: " + defaultHeadlines.rejectedTerms)

	bot.msg(trigger.sender, trigger.nick + ", now searching for these words: " + defaultHeadlines.wordlist)

# Function to fetch the rss feed and return the parsed RSS
def parseRSS( rss_url ):
    try:
	parsedRSS = feedparser.parse( rss_url )
    except:
	print "Unhandled excpetion: ",sys.exc_info()[0]
	raise
    return parsedRSS

# Function grabs the rss feed headlines (titles) and returns them as a list
def getHeadlines( rss_url ):
    headlines = []

    try:
	feed = parseRSS( rss_url )
    except:
	print "Unhandled exception: ",sys.exec_info()[0]
	raise
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
@module.rate(30)
@module.commands('news_announce')
def news_announce(bot, trigger):
	"""Search the provided news feeds for news matching the current search term list. Results are printed to the channel with tinuyrl links."""
	# when using module.interval() you dont need to pass trigger to the function, just bot
	#defaultHeadlines = headlineList('default')
	global news
	if news == True:
		# A list to hold all headlines
		allheadlines = []

		# List of RSS feeds that we will fetch and combine
		newsurls = {
		    'googlenews':       'https://news.google.com/news?cf=all&hl=en&pz=1&ned=us&num=15&output=rss'
		}

		# Iterate over the feed urls
		for key,url in newsurls.items():
		    # Call getHeadlines() and combine the returned headlines with allheadlines
		    allheadlines.extend( getHeadlines( url ) )
		print "NEWS: "
		print allheadlines
		print "*****"
		defaultHeadlines.headlines = allheadlines
		things = defaultHeadlines.find_hits()
		for t in things:
			bot.msg(trigger.sender,t,1)	
		#message = "The Krokbot News System: keeping you informed of up-to-the-minute jihad jihad"
		#bot.msg("#lounge",message, 1)

# End News System
