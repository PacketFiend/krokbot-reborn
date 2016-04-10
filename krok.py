#!/usr/bin/env python

from sopel import module, tools
import sqlite3
import random
import time
from random import randint

import sys
import twitter
import requests
from geopy.geocoders import Nominatim
import praw

import kgen
import creds
import feedparser
"""
@module.commands('echo','repeat')
def echo(bot, trigger):
	bot.reply(trigger.group(2))
"""

api = twitter.Api(consumer_key=creds.tw_consumer_key,
	consumer_secret=creds.tw_consumer_secret,
	access_token_key=creds.tw_access_token_key,
	access_token_secret=creds.tw_access_token_secret)

geolocator = Nominatim()

# Define some memory dicts/lists for keeping track of users
def setup(bot):
    bot.memory["user_quotes"] = {}

# Begin News System
global news
news = False

def find_hits(headlines):
    words = ['terror','gun','attack','seige','shooting']
    hits = []
    for s in headlines:
        for w in words:
            if w in s:
                hits.append(s)
            else:
                pass
            goats = list(set(hits))
            return goats
    
# Function to fetch the rss feed and return the parsed RSS
def parseRSS( rss_url ):
    return feedparser.parse( rss_url )

# Function grabs the rss feed headlines (titles) and returns them as a list
def getHeadlines( rss_url ):
    headlines = []

    feed = parseRSS( rss_url )
    for newsitem in feed['items']:
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

@module.interval(120)
def news_announce(bot):
	# when using module.interval() you dont need to pass trigger to the function, just bot
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
		things = find_hits(allheadlines)
		for t in things:
			bot.msg("#lounge",t,1)	
		#message = "The Krokbot News System: keeping you informed of up-to-the-minute jihad jihad"
		#bot.msg("#lounge",message, 1)

# End News System

@module.commands('sauce')
def sauce(bot, trigger):
    bot.memory["who"] = {}
    bot.write(["WHO", "#OFFTOPIC"])
    for w in bot.memory["who"]:
        print w	
		
@module.rate(20) # we may need to adjust this, but we dont need people spamming the command
@module.commands('newkrok')
def newkrok(bot, trigger):
    """ usage: !newkrok """
    file_ = open('rockho-improved.log')
    markov = kgen.Markov(file_)
    new_krok = markov.generate_markov_text()
    bot.say(new_krok)

@module.commands('tsearch')
def tsearch(bot, trigger):
    """ usage: !tsearch <search string> """
    if trigger.group(2):
        criteria = trigger.group(2)
        query = api.GetSearch(term=criteria,result_type="recent", count="10")
        tweets = []
        for q in query:
            info = q.user.screen_name + "("+q.created_at+") >> " +q.text
            tweets.append(info)
            bot.msg(trigger.nick,info,1)
    else:
        bot.reply("usage: !tsearch jihad jihad")

@module.commands('gsearch')
def gsearch(bot, trigger):
    """ usage: !gsearch <location> | <search string> """
    if trigger.group(2):
        # we can work with this
        find = trigger.group(2)
        (locate, criteria) = find.split("|")

        location = geolocator.geocode(locate)

        lat = location.latitude
        lng = location.longitude

        query = api.GetSearch(term=criteria, geocode=(lat, lng, "20mi"),
				      result_type="recent", count="10")
        tweets = []
        for q in query:
            info = q.user.screen_name + "("+q.created_at+") >> " +q.text
            tweets.append(info)
            bot.msg(trigger.nick, info, 1)
    else:
        bot.reply("usage: !gsearch location | jihaid jihad")

# shootout time for the virtual 2 peso thug!
@module.rate(20) # we may need to adjust this, but we dont need people spamming the command
@module.commands('shootout')
def shootout(bot, trigger):
    """ usage: !shootout <num> (between 1 and 5) """
    imp = trigger.group(2)
    shard = imp.split(" ")

    if int(shard[0]) > 5:
        bot.say(trigger.nick + ": quit being a chomo, chomo")	
    else:
        file = 'rockho-improved.log'
        num_lines = sum(1 for line in open(file))

        f = open(file)
        lines = f.readlines()
        f.close()

        max =  num_lines - 1

        #line = randint(0,max)

        limit = int(shard[0])
        if limit > 5:
            limit = int(5)
            i = 1
            while i <= limit:
                line = randint(0,max)
                reply = str(lines[line].decode('utf8'))
                bot.say(reply)
                i += 1
        else:
            i = 1
            while i <= limit:
                line = randint(0,max)
                #print str(lines[line])
                reply = str(lines[line].decode('utf8'))
                bot.say(reply)
                i += 1

# this gets a random quote from the database
@module.commands('krokquote')
def krokquote(bot, trigger):
    """ usage: !krokquote """
    conn = sqlite3.connect('krokquotes.db')
    items = conn.execute("SELECT id, quote FROM bestkrok WHERE quote != '';")
    i = 0
    for row in items:
        i += 1
	
    rnd = randint(0,i)
    x = 0
    items = conn.execute("SELECT id, quote FROM bestkrok WHERE quote != '';")
    for q in items:
        if x == rnd:
            quote = str(q[1])
            q_id = str(q[0])
            x += 1

    return_quote = "("+q_id+") "+quote

    rq_clean = return_quote.replace("\\'",",")
    bot.say(rq_clean)

# this listens for when someone talks about it
@module.rule(r'.*krokbot.*')
def talk_shit(bot, trigger):
	#response = "Hey "+trigger.nick+", go fuck yourself!"
	#bot.say(response)
	conn = sqlite3.connect('krokquotes.db')
	name = trigger.nick
	items = conn.execute("SELECT id, quote FROM bestkrok WHERE quote LIKE '%"+str(name)+"%';")

	cnt = 0 
	for i in items:
		cnt += 1
	if cnt == 0:
		ret_quote = "you look like an asshole I've never seen before"
	else:
		quote = randint(0,cnt)

		items = conn.execute("SELECT id, quote FROM bestkrok WHERE quote LIKE '%"+str(name)+"%';")

		cnt = 0
		clean_quote = ''
		for q in items:
			if cnt == quote:
				clean_quote = q[1].replace("\\'","'")	
			else:
				pass
			cnt += 1
		if clean_quote == '':
			clean_quote = "another red coat I don't recognize"
		else:
			pass

	ret_quote = clean_quote
	full = trigger.nick + ": " + ret_quote
	bot.say(full)

# deeplove - target another nick with insults
@module.rate(20) # we may need to adjust this, but we dont need people spamming the command
@module.commands('deeplove')
def deeplove(bot, trigger):
    """ usage: !deeplove <nick> """
    clean_quote = ''
    ret_quote = ''
    conn = sqlite3.connect('krokquotes.db')
    nickarg = trigger.args[1].split()
    try:
        name = nickarg[1]
        items = conn.execute("SELECT id, quote FROM bestkrok WHERE quote LIKE '%"+str(name)+"%';")

        cnt = 0
        for i in items:
            cnt += 1
        if cnt == 0:
            ret_quote = "that looks like an asshole I've never seen before"
        else:
            quote = randint(0,cnt)

            items = conn.execute("SELECT id, quote FROM bestkrok WHERE quote LIKE '%"+str(name)+"%';")

            cnt = 0
            clean_quote = ''
            for q in items:
                if cnt == quote:
		            clean_quote = q[1].replace("\\'","'")	
                else:
                    pass
                cnt += 1
            print deeplove.__name__ + " - " + trigger.nick + "@" + trigger.sender + " is insulting: " + name
    except IndexError:
        ret_quote = "you didn't type the name asshole"
    #except:
    #    ret_quite = "so high I completely forgot what I was doing"

    if clean_quote:
        full = clean_quote
        bot.memory["user_quotes"].setdefault(name, [])
        bot.memory["user_quotes"][name].append(clean_quote)
    elif ret_quote:
        full = ret_quote
    else:
        full = "so high I completely forgot what I was doing"
    bot.say(full)
    print deeplove.__name__ + " - Other quotes in memory:"
    for user, quotes in bot.memory["user_quotes"].items():
        print user + ": " + str(quotes)


# grab a random quote
def random_krok():
    conn = sqlite3.connect('krokquotes.db')
    items = conn.execute("SELECT id, quote FROM bestkrok WHERE quote != '';")
    i = 0
    for row in items:
        i += 1

    rnd = randint(0,i)
    x = 0
    items = conn.execute("SELECT id, quote FROM bestkrok WHERE quote != '';")
    for q in items:
        if x == rnd:
            rand_quote = str(q[1])
            rand_q_id = str(q[0])
        x += 1
    rand_krok = rand_quote.replace("\\'","'")

    return rand_krok

# print a random 'yo <nick>' and random krokquote
@module.interval(5400)
def random_yo(bot):
# for each channel that we're in, pick a random nick out of privileges dict,
# remove krok{b,p}ot and other blocked nicks
    channel_list = []
    conn_channels = bot.privileges
    for channel in conn_channels:
        if channel not in channel_list:
            channel_list.append(channel)
    for channel in channel_list:
        #print channel
        if random.random() < 0.3:
            channel.encode('utf-8')
            names = bot.privileges[channel]
            blocked_nicks = ('krokbot', 'krokpot')
            for bnick in blocked_nicks:
                if bnick in names.keys():
                    del names[bnick]
            rand_nick = random.choice(list(names.keys()))

            rand_krok = random_krok() 
            rand_yo = "yo " + rand_nick 
            bot.msg(channel, rand_yo, 1)
            bot.msg(channel, rand_krok, 1)
        else:
            pass

# call a 'random yo'
@module.rate(20)
@module.commands('yo')
def random_yo_callable(bot, trigger):
    """ usage: !yo  """
    channel = trigger.sender
    names = bot.privileges[channel]
    blocked_nicks = ('krokbot', 'krokpot')
    for bnick in blocked_nicks:
        if bnick in names.keys():
            del names[bnick]
    rand_nick = random.choice(list(names.keys()))

    rand_krok = random_krok() 
    rand_yo = "yo " + rand_nick 
    bot.msg(channel, rand_yo, 1)
    bot.msg(channel, rand_krok, 1)

# Reddit titty pic poster
@module.interval(3600)
def sluttosphere_setup(bot):
    r = praw.Reddit(user_agent='sopel_get_titty_pic')
    subreddits = ['boobs', 'gonemild', 'tits', 'redheads', 'brunettes']
    global slut_links
    slut_links = []

    for sub in subreddits:
        submissions = r.get_subreddit(sub).get_new(limit=15)
        for s in submissions:
            latest_submission = "[" + s.title + "] - " + s.url
            slut_links.append(latest_submission)

    print sluttosphere_setup.__name__ + " - Grabbed latest batch of slut pics"

    return slut_links
  
@module.rate(20)
@module.commands('tittypic')
def sluttosphere(bot, trigger):
    try:
        rand_submission = "NSFW - " + random.choice(slut_links)
        print sluttosphere.__name__ + " - " + rand_submission
        bot.say(rand_submission)
    except (KeyError, NameError):
        errmsg = "Got no sluts yet" 
        bot.say(errmsg)
        dummy_arg = None
        sluttosphere_setup(dummy_arg)
