#!/usr/bin/env python
#
# Name:    jihadjihad.py
# Author:  Syini666
# Date:    Various dates in 2015/2016
# Summary: krokbot: evil AI
#

from sopel import module, tools
import sopel
from sopel.bot import _CapReq
from sopel.tools import Identifier, iteritems, events
from sopel.tools.target import User, Channel
from sopel.module import rule, event, commands
import sqlite3
import random
import time
from random import randint

import sys
import twitter
import requests
from bs4 import BeautifulSoup
import arrow
from geopy.geocoders import Nominatim
import praw

import kgen
import feedparser
import re
# note - need to see which of these are even necessary

"""
@module.commands('echo','repeat')
def echo(bot, trigger):
	bot.reply(trigger.group(2))
"""

@module.commands('goat')
def goat(bot, trigger):
	channel = '#t3st';
	t = 'goatfuckers';
	channel_list = []
	conn_channels = bot.privileges
	for channel in conn_channels:
		if channel not in channel_list:
			channel_list.append(channel)

	for chan in channel_list:
		if chan == '#t3st':
			#bot.reply(bot.channels[chan].topic);
			last_topic = bot.channels[chan].topic
	new_topic = "jihad jihad information | " + last_topic
	bot.reply("last topic: "+last_topic)
	bot.write(('TOPIC', channel + ' :' + new_topic))

@module.commands('lasttopic')
def last_topic(bot, trigger):
	"""
	channel_list = []
	conn_channels = bot.privileges
	for channel in conn_channels:
		if channel not in channel_list:
			channel_list.append(channel)

	for chan in channel_list:
		if chan == '#t3st':
			#bot.reply(bot.channels[chan].topic);
			last_topic = bot.channels[chan].topic
	"""
	last_topic = bot.channels['#t3st'].topic
	bot.reply("last topic:" +last_topic)
@module.commands('jihadstats')
def jihad_monthly(bot, trigger):
	bot.reply(get_jihad_monthly_dead());
def get_jihad_monthly_dead():
	utc = arrow.utcnow()

	month = utc.format('MMMM');
	year = utc.format('YYYY');
	day = utc.format('DD');
	url = 'http://en.wikipedia.org/wiki/List_of_terrorist_incidents_in_'+str(month)+'_'+str(year)

	r = requests.get(url)
	html = r.text
	soup = BeautifulSoup(html, "html.parser")
	table = soup.find("table", attrs={"class":"wikitable sortable"})

	headings = [th.get_text() for th in table.find("tr").find_all("th")]

	datasets = []

	for row in table.find_all("tr")[1:]:
		dataset = zip(headings, (td.get_text() for td in row.find_all("td")))
		datasets.append(dataset)

	l = len(datasets)

	total_dead = 0
	for d in datasets:
		regex_pattern = r"^[0-9]{1,}"
		unfiltered_kills = d[2][1]
		
		if re.search(regex_pattern, unfiltered_kills):
			# matches found
			match = re.search(regex_pattern, unfiltered_kills)
			d_dead = int(match.group(0))
			total_dead = total_dead + d_dead
	msg = str(total_dead) + " people have been killed by the jihad-jihad to date this month"
	return msg
	
@module.commands('jihadinfo')
def jihadinfo(bot, trigger):
	bot.reply(get_jihad_info());

def get_jihad_info():
	utc = arrow.utcnow()
	month = utc.format('MMMM');
	year = utc.format('YYYY');
	day = utc.format('DD');
	url = 'http://en.wikipedia.org/wiki/List_of_terrorist_incidents_in_'+str(month)+'_'+str(year)

	r = requests.get(url)
	html = r.text
	soup = BeautifulSoup(html, "html.parser")
	table = soup.find("table", attrs={"class":"wikitable sortable"})

	headings = [th.get_text() for th in table.find("tr").find_all("th")]
	datasets = []

	for row in table.find_all("tr")[1:]:
		dataset = zip(headings, (td.get_text() for td in row.find_all("td")))
		datasets.append(dataset)
	l = len(datasets)
	date = datasets[l-1][0][1]
	dead = datasets[l-1][2][1]
	location = datasets[l-1][4][1]
	full_date = month + " " + date + " " + year
	perpetrator = datasets[l-1][6][1]
	attack_type = datasets[l-1][1][1]
	
	msg = dead + " people were killed on " + full_date + " in " + location + " in a " + attack_type
	return msg

@module.commands('lastjihad')
def lastjihad(bot, trigger):
	bot.reply(get_last_jihad());

def get_last_jihad():
	utc = arrow.utcnow()

	month = utc.format('MMMM');
	year = utc.format('YYYY');
	day = utc.format('DD');
	url = 'http://en.wikipedia.org/wiki/List_of_terrorist_incidents_in_'+str(month)+'_'+str(year)

	r = requests.get(url)
	html = r.text
	soup = BeautifulSoup(html, "html.parser")
	table = soup.find("table", attrs={"class":"wikitable sortable"})

	headings = [th.get_text() for th in table.find("tr").find_all("th")]

	datasets = []

	for row in table.find_all("tr")[1:]:
		dataset = zip(headings, (td.get_text() for td in row.find_all("td")))
		datasets.append(dataset)
	l = len(datasets)
	last_attack_day = int(datasets[l-1][0][1])

	diff = int(day)- last_attack_day
	
	if diff == 0:
		return_quote = "jihad-jihad detected today!"
	elif diff == 1:
		return_quote = "it is has been %s day since the last jihad-jihad incident" % str(diff)
	else:
		return_quote = "it is has been %s days since the last jihad-jihad incident" % str(diff)

	return return_quote

