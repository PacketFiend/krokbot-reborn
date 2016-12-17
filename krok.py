#!/usr/bin/env python
#
# Name:    krok.py
# Author:  Syini666, ekim
# Date:    Various dates in 2015/2016
# Summary: krokbot: evil AI
#

import config
from sopel import module, tools
import sqlite3
import pymysql
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

from pprint import pprint

from sqlalchemy import (create_engine, Table, Column, Text, Integer, String, MetaData, ForeignKey, exc)
from sqlalchemy.sql import (select, exists)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
metadata = MetaData()

from watson import KrokHandler

#engine = create_engine("mysql+pymysql://krok:kr0kl4bs@localhost/krokbot?host=localhost?port=3306")
engine = create_engine(config.sql_connection_string)
Session = sessionmaker(bind=engine)

bestkrok = Table('bestkrok', metadata, autoload=True, autoload_with=engine)
watson_krok = Table('watson_krok', metadata, autoload=True, autoload_with=engine)
watson_krokemotions = Table('watson_krokemotions', metadata, autoload=True, autoload_with=engine)

api = twitter.Api(consumer_key=config.tw_consumer_key,
	consumer_secret=config.tw_consumer_secret,
	access_token_key=config.tw_access_token_key,
	access_token_secret=config.tw_access_token_secret)

geolocator = Nominatim()

# Define some memory dicts/lists for keeping track of users
def setup(bot):
    bot.memory["user_quotes"] = {}

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
    session = Session()
    imp = trigger.group(2)
    conn = engine.connect()

    if imp is not None:
        shard = imp.split(" ")
        if int(shard[0]) > 5:
            bot.say(trigger.nick + ": quit being a chomo, chomo")   
        else:
            limit = int(shard[0])
    else:
        limit = 1
    if len(imp) > 1:
        emotion = str(shard[1])
        if emotion not in KrokHandler.emotionList:
            bot.say("Don't be a chomo. I don't recognize that emotion. Valid emotions are: "\
                    + ", ".join(KrokHandler.emotionList))
            return
        items = session.query(watson_krok).join(watson_krokemotions)\
            .filter(watson_krokemotions.c.emotion == emotion)\
            .order_by('RAND()')\
            .limit(limit)
    else:
        items = session.query(watson_krok).join(watson_krokemotions)\
            .order_by('RAND()')\
            .limit(limit)
        
    #q = select([bestkrok.c.quote]).order_by('RAND()').limit(limit)
    pprint(items)
    #items = conn.execute(q)
    for i in items:
        pprint(i[1])
        bot.say(i[1])

# this gets a random quote from the database
@module.commands('krokquote')
def krokquote(bot, trigger):
    """ usage: !krokquote """
    conn = engine.connect()
    q = select([bestkrok.c.id, bestkrok.c.quote]).where(bestkrok.c.quote != '')
    items = conn.execute(q)
    i = 0
    for row in items:
        i += 1
	
    rnd = randint(0,i)
    x = 0
    q = select([bestkrok.c.id, bestkrok.c.quote]).where(bestkrok.c.quote != '')
    items = conn.execute(q)
    for q in items:
        if q[0] == rnd:
            quote = str(q[1])
            q_id = str(q[0])
            x += 1
    try: 
	    return_quote = "("+q_id+") "+quote
    except:
	    return_quote = "Nice going asshole, way to fuck it up"

    rq_clean = return_quote.replace("\\'",",")
    bot.say(rq_clean)

# this listens for when someone talks about it
@module.rule(r'.*krokbot.*')
def talk_shit(bot, trigger):
	#response = "Hey "+trigger.nick+", go fuck yourself!"
	#bot.say(response)
	conn = engine.connect()
	name = str(trigger.nick)
	query = select([bestkrok.c.id, bestkrok.c.quote]).where(bestkrok.c.quote.like('%'+name+'%'))
	items = conn.execute(query)

	cnt = 0 
	for i in items:
		cnt += 1
	if cnt == 0:
		ret_quote = "you look like an asshole I've never seen before"
		clean_quote = ret_quote # fix for bug found on 2016-06-28 when nick s0b addressed the bot
	else:
		quote = randint(0,cnt)

		items = conn.execute(query)

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
	#full = trigger.nick + ": " + ret_quote
	bot.say(ret_quote)

# deeplove - target another nick with insults
@module.rate(20) # we may need to adjust this, but we dont need people spamming the command
@module.commands('deeplove')
def deeplove(bot, trigger):
    """ usage: !deeplove <nick> """
    clean_quote = ''
    ret_quote = ''
    conn = engine.connect()
    if trigger.group(2):
        name = str(trigger.group(2))
    else:
	bot.action("makes sweet android love to itself.", trigger.sender)
	return
    try:
        query = select([bestkrok.c.id, bestkrok.c.quote]).where(bestkrok.c.quote.like('%'+name+'%'))
	items = conn.execute(query)

        cnt = 0
        for i in items:
            cnt += 1
        if cnt == 0:
            ret_quote = "that looks like an asshole I've never seen before"
        else:
            quote = randint(0,cnt)

	    query = select([bestkrok.c.id, bestkrok.c.quote]).where(bestkrok.c.quote.like('%'+name+'%'))
            items = conn.execute(query)

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
    conn = engine.connect()
    q = select([bestkrok.c.id, bestkrok.c.quote]).where(bestkrok.c.quote != '')
    items = conn.execute(q)
    i = 0
    for row in items:
        i += 1

    rnd = randint(0,i)
    x = 0
    items = conn.execute(q)
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
    nicks = []
    conn_channels = bot.privileges
    channel_list = [channel for channel in conn_channels]
    channel_list = sorted(set(channel_list))
    for channel in channel_list:
        #print channel
        if random.random() < 0.3:
            channel.encode('utf-8')
            names = bot.privileges[channel]
            blocked_nicks = ('krokbot', 'krokpot', 'krokwhore')
            for nick in names.keys():
                if nick not in blocked_nicks:
                        nicks.append(nick)
            rand_nick = random.choice(list(nicks))

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
    blocked_nicks = ('krokbot', 'krokpot', 'krokwhore')
    nicks = [nick for nick in names.keys() if nick not in blocked_nicks]
    rand_nick = random.choice(list(nicks))

    rand_krok = random_krok() 
    rand_yo = "yo " + rand_nick 
    bot.msg(channel, rand_yo, 1)
    bot.msg(channel, rand_krok, 1)

