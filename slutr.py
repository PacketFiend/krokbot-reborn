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
    bot.memory["used_pics"] = {}
    bot.memory["used_pics"]['tits'] = []
    bot.memory["used_pics"]['clams'] = []
    bot.memory["used_pics"]['sideboobs'] = []
    bot.memory["used_pics"]['sharpies'] = []

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
        # each picture has an id, title, and a url; the id is the key and
        # title and url are values
        slut_links_tits = {s.id: [s.title, s.url] for s in r_posts}

    for sub in clam_subreddits:
        r_posts = r.get_subreddit(sub).get_new(limit=15)
        slut_links_clams = {s.id: [s.title, s.url] for s in r_posts}

    for sub in sideboob_subreddits:
        r_posts = r.get_subreddit(sub).get_new(limit=15)
        slut_links_sideboobs = {s.id: [s.title, s.url] for s in r_posts}

    for sub in sharpies_subreddits:
        r_posts = r.get_subreddit(sub).get_new(limit=15)
        slut_links_buttsharpies = {s.id: [s.title, s.url] for s in r_posts}

    print(sluttosphere_setup.__name__ + " - Grabbed latest batch of slut pics")

    return (slut_links_tits, slut_links_clams, slut_links_sideboobs, slut_links_buttsharpies)

@module.rate(20)
@module.commands('tittypic')
def sluttosphere_tits(bot, trigger):
    try:
        # first we pick a random pic, then we check if it is in the memory and if
        # the memory is full for each type of pics.
        while True:
            pic = random.choice(slut_links_tits.keys())
            if pic in bot.memory['used_pics']['tits']:
                pass
            elif len(bot.memory['used_pics']['tits']) >= 15:
                bot.say("Hold on, the sluts are coming!")
                break
            else:
                rand_submission = "NSFW - [" + slut_links_tits[pic][0] + "] " + slut_links_tits[pic][1]
                print(sluttosphere_clams.__name__ + " - " + rand_submission)
                bot.say(rand_submission)
                bot.memory['used_pics']['tits'].append(pic)
                break
    except (KeyError, IndexError, NameError):
        errmsg = "Got no sluts yet"
        bot.say(errmsg)
        dummy_arg = None
        sluttosphere_setup(dummy_arg)

@module.rate(20)
@module.commands('clamshot')
def sluttosphere_clams(bot, trigger):
    try:
        while True:
            pic = random.choice(slut_links_clams.keys())
            if pic in bot.memory['used_pics']['clams']:
                pass
            elif len(bot.memory['used_pics']['clams']) >= 15:
                bot.say("Hold on, the sluts are coming!")
                break
            else:
                rand_submission = "NSFW - [" + slut_links_clams[pic][0] + "] " + slut_links_clams[pic][1]
                print(sluttosphere_clams.__name__ + " - " + rand_submission)
                bot.say(rand_submission)
                bot.memory['used_pics']['clams'].append(pic)
                break
    except (KeyError, IndexError, NameError):
        errmsg = "Got no pink tacos yet"
        bot.say(errmsg)
        dummy_arg = None
        sluttosphere_setup(dummy_arg)

@module.rate(20)
@module.commands('sideboob')
def sluttosphere_sideboob(bot, trigger):
    try:
        while True:
            pic = random.choice(slut_links_sideboobs.keys())
            if pic in bot.memory['used_pics']['sideboobs']:
                pass
            elif len(bot.memory['used_pics']['sideboobs']) >= 15:
                bot.say("Hold on, the sluts are coming!")
                break
            else:
                rand_submission = "NSFW - [" + slut_links_sideboobs[pic][0] + "] " + slut_links_sideboobs[pic][1]
                print(sluttosphere_clams.__name__ + " - " + rand_submission)
                bot.say(rand_submission)
                bot.memory['used_pics']['sideboobs'].append(pic)
                break
    except (KeyError, IndexError, NameError):
        errmsg = "Got no poppin' side boobs yet"
        bot.say(errmsg)
        dummy_arg = None
        sluttosphere_setup(dummy_arg)

@module.rate(20)
@module.commands('sharpie')
def sluttosphere_sharpie(bot, trigger):
    try:
        while True:
            pic = random.choice(slut_links_sharpies.keys())
            if pic in bot.memory['used_pics']['sharpies']:
                pass
            elif len(bot.memory['used_pics']['sharpies']) >= 15:
                bot.say("Hold on, the sluts are coming!")
                break
            else:
                rand_submission = "NSFW - [" + slut_links_sharpies[pic][0] + "] " + slut_links_sharpies[pic][1]
                print(sluttosphere_clams.__name__ + " - " + rand_submission)
                bot.say(rand_submission)
                bot.memory['used_pics']['sharpies'].append(pic)
                break
    except (KeyError, IndexError, NameError):
        errmsg = "Let's see how many sharpies I can fit up my asshole"
        bot.say(errmsg)
        dummy_arg = None
        sluttosphere_setup(dummy_arg)
