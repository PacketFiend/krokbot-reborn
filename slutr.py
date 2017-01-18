#!/usr/bin/env python
#
# Name:    slutr.py
# Author:  ekim
# Date:    Apr 18th, 2016
# Summary: slutr: krokbot pr0n extension
#

from sopel import module, tools
import random
from random import randint
import praw

# Define some memory dicts/lists for keeping track of pics that were already used
def setup(bot):
    bot.memory["used_pics"] = []

# slutr extensions
# Reddit titty pic poster
@module.interval(3600)
def sluttosphere_setup(bot):
    r = praw.Reddit(user_agent='sopel_get_titty_pic')
    titty_subreddits = ['boobs', 'gonemild', 'tits', 'redheads', 'brunettes', 'tittydrop', 'downblouse', 'titties']
    clam_subreddits = ['pussy', 'rearpussy', 'pussy_girls', 'asianpussy', 'perfectpussies', 'ready_pussy', 'pussyjuices']
    sideboob_subreddits = ['sideboob', 'sideboobs']
    sharpies_subreddits = ['buttsharpies']
    global slut_links_tits
    global slut_links_clams
    global slut_links_sideboobs
    global slut_links_buttsharpies
    slut_links_tits = []
    slut_links_clams = []
    slut_links_sideboobs = []
    slut_links_buttsharpies = []

    for sub in titty_subreddits:
        r_posts = r.get_subreddit(sub).get_new(limit=15)
        slut_links_tits = ["[" + s.title + "] - " + s.url for s in r_posts]

    for sub in clam_subreddits:
        r_posts = r.get_subreddit(sub).get_new(limit=15)
        slut_links_clams = ["[" + s.title + "] -" + s.url for s in r_posts]

    for sub in sideboob_subreddits:
        r_posts = r.get_subreddit(sub).get_new(limit=15)
        slut_links_sideboobs = ["[" + s.title + "] - " + s.url for s in r_posts]

    for sub in sharpies_subreddits:
        r_posts = r.get_subreddit(sub).get_new(limit=15)
        slut_links_buttsharpies = ["[" + s.title + "] - " + s.url for s in r_posts]

    print(sluttosphere_setup.__name__ + " - Grabbed latest batch of slut pics")

    return (slut_links_tits, slut_links_clams, slut_links_sideboobs, slut_links_buttsharpies)

@module.rate(20)
@module.commands('tittypic')
def sluttosphere_tits(bot, trigger):
    try:
        rand_submission = "NSFW - " + random.choice(slut_links_tits)
        print(sluttosphere_tits.__name__ + " - " + rand_submission)
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
        print(sluttosphere_clams.__name__ + " - " + rand_submission)
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
        print(sluttosphere_sideboob.__name__ + " - " + rand_submission)
        bot.say(rand_submission)
    except (KeyError, IndexError, NameError):
        errmsg = "Got no poppin' side boobs yet"
        bot.say(errmsg)
        dummy_arg = None
        sluttosphere_setup(dummy_arg)

@module.rate(20)
@module.commands('sharpie')
def sluttosphere_sharpie(bot, trigger):
    try:
        rand_submission = "NSFW - " + random.choice(slut_links_buttsharpies)
        print(sluttosphere_sharpie.__name__ + " - " + rand_submission)
        bot.say(rand_submission)
    except (KeyError, IndexError, NameError):
        errmsg = "Let's see how many sharpies I can fit up my asshole"
        bot.say(errmsg)
        dummy_arg = None
        sluttosphere_setup(dummy_arg)
