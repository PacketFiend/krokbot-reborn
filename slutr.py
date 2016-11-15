#!/usr/bin/env python
#
# Name:    slutr.py
# Author:  ekim
# Date:    Apr 18th, 2016
# Summary: slutr: krokbot pr0n extension
#

from sopel import module, tools
import random
import time
from random import randint

import sys
import requests
import praw

import feedparser

# Define some memory dicts/lists for keeping track of users
def setup(bot):
    bot.memory["user_quotes"] = {}

# slutr extensions
# Reddit titty pic poster
@module.interval(3600)
def sluttosphere_setup(bot):
    r = praw.Reddit(user_agent='sopel_get_titty_pic')
    titty_subreddits = ['boobs', 'gonemild', 'tits', 'redheads', 'brunettes', 'tittydrop']
    clam_subreddits = ['pussy', 'rearpussy', 'pussy_girls', 'asianpussy', 'perfectpussies', 'ready_pussy', 'pussyjuices']
    sideboob_subreddits = ['sideboob', 'sideboobs', 'downblouse']
    global slut_links_tits
    global slut_links_clams
    global slut_links_sideboobs
    slut_links_tits = []
    slut_links_clams = []
    slut_links_sideboobs = []

    for sub in titty_subreddits:
        submissions1 = r.get_subreddit(sub).get_new(limit=15)
        slut_links_tits = ["[" + s.title + "] - " + s.url for s in submissions1]

    for sub in clam_subreddits:
        submissions2 = r.get_subreddit(sub).get_new(limit=15)
        slut_links_clams = ["[" + s.title + "] -" + s.url for s in submissions2]

    for sub in sideboob_subreddits:
        submissions3 = r.get_subreddit(sub).get_new(limit=15)
        slut_links_sideboobs = ["[" + s.title + "] - " + s.url for s in submissions3]

    print sluttosphere_setup.__name__ + " - Grabbed latest batch of slut pics"

    return (slut_links_tits, slut_links_clams, slut_links_sideboobs)

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

@module.rate(20)
@module.commands('sideboob')
def sluttosphere_sideboob(bot, trigger):
    try:
        rand_submission = "NSFW - " + random.choice(slut_links_sideboobs)
        print sluttosphere_sideboob.__name__ + " - " + rand_submission
        bot.say(rand_submission)
    except (KeyError, IndexError, NameError):
        errmsg = "Got no popping side boobs yet"
        bot.say(errmsg)
        dummy_arg = None
        sluttosphere_setup(dummy_arg)
