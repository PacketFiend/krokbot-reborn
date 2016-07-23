#!/usr/bin/env python
#
# Name:    slutr.py
# Author:  ekim
# Date:    Apr 18th, 2016
# Summary: slutr: krokbot pr0n extension
#

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

# slutr extensions
# Reddit titty pic poster
@module.interval(3600)
def sluttosphere_setup(bot):
    r = praw.Reddit(user_agent='sopel_get_titty_pic')
    titty_subreddits = ['boobs', 'gonemild', 'tits', 'redheads', 'brunettes', 'sideboob', 'tittydrop']
    clam_subreddits = ['pussy', 'rearpussy', 'pussy_girls', 'asianpussy', 'perfectpussies', 'ready_pussy', 'pussyjuices']
    global slut_links_tits
    global slut_links_clams
    slut_links_tits = []
    slut_links_clams = []

    for sub in titty_subreddits:
        submissions1 = r.get_subreddit(sub).get_new(limit=15)
        for s in submissions1:
            latest_submission = "[" + s.title + "] - " + s.url
            slut_links_tits.append(latest_submission)
        
    for sub in clam_subreddits:
        submissions2 = r.get_subreddit(sub).get_new(limit=15)
        for s in submissions2:
            latest_submission = "[" + s.title + "] - " + s.url
            slut_links_clams.append(latest_submission)

    print sluttosphere_setup.__name__ + " - Grabbed latest batch of slut pics"
    for clams in slut_links_clams:
        print clams
    for titties in slut_links_tits:
        print titties

    return (slut_links_tits, slut_links_clams)
  
@module.rate(20)
@module.commands('tittypic')
def sluttosphere_tits(bot, trigger):
    try:
        rand_submission = "NSFW - " + random.choice(slut_links_tits)
        print sluttosphere_tits.__name__ + " - " + rand_submission
        bot.say(rand_submission)
    except (KeyError, IndexError, NameError):
        errmsg = "Got no sluts yet" 
        bot.say(errmsg)
        dummy_arg = None
        sluttosphere_setup(dummy_arg)

@module.rate(20)
@module.commands('clamshot')
def sluttosphere_clams(bot, trigger):
    try:
        rand_submission = "NSFW - " + random.choice(slut_links_clams)
        print sluttosphere_clams.__name__ + " - " + rand_submission
        bot.say(rand_submission)
    except (KeyError, IndexError, NameError):
        errmsg = "Got no pink tacos yet" 
        bot.say(errmsg)
        dummy_arg = None
        sluttosphere_setup(dummy_arg)
