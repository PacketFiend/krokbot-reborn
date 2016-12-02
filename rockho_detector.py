#!/usr/bin/env python
#
# Name:    rockho_detector.py
# Author:  ekim
# Date:    Apr 18th, 2016
# Summary: krokbot rockho detector
#

from __future__ import print_function
from sopel import module, tools, config
from sopel.tools.target import User, Channel
from sopel.tools import Identifier, iteritems, events
from sopel.module import rule, event, commands
import random
import time
from random import randint
from pprint import pprint

import sys
import requests
import sqlalchemy

#engine = create_engine("mysql+pymysql://krok:kr0kl4bs@localhost/krokbot?host=localhost?port=3306")
engine = sqlalchemy.create_engine("mysql+pymysql://ken:hHq4C*CP3yx&tBe$CQbRj<k-2g{-vm!/@asgard.pure-defect.com:3306/krokbot")

#api = twitter.Api(consumer_key=creds.tw_consumer_key,
#       consumer_secret=creds.tw_consumer_secret,
#       access_token_key=creds.tw_access_token_key,
#       access_token_secret=creds.tw_access_token_secret)

'''
Define some memory dicts/lists for keeping track of users.
'''
def setup(bot):
    #bot.memory['tor_exit_nodes'] = {}
    global tor_exit_nodes
    tor_exit_nodes = []

@module.unblockable
@module.event('JOIN')
@module.rule('.*')
def check_for_rockhos(bot, trigger):

    match = False
    conn = engine.connect()
    query = "SELECT nick,hostmasks,greeting FROM coolkids"
    results = conn.execute(query)
    for item in results:
	hostmasklist = item[1]
	greeting = item[2]

	if match: break			# Or we end up printing multiple lines for joins if a user has more than one nick
	if not hostmasklist: continue	# This is really just for readability, there's too many indents...

	hostmasks = hostmasklist.split(',')
	for hostmask in hostmasks:
		if hostmask.strip() in trigger.hostmask and greeting:
			bot.msg(trigger.sender, greeting)
			match = True
				
    if trigger.admin:
        bot.say("A glorious leader has joined!")
    if trigger.nick == 'rockho' or "ct.charter.com" in trigger.hostmask:
        bot.say("A wild rockho appeared! Prepare the defenses!")


'''
Get TOR Exit nodes list and parse the IPs into a python list.
'''
@module.commands('get_tor')
@module.interval(3600)
def get_tor_exit_nodes(bot, trigger=None):
    num = 0
    r = requests.get('https://check.torproject.org/exit-addresses')
    pprint(str(r.text))
    text = str(r.text).split('\n')
    #for block in text:
    #    if "ExitAddress" in block: tor_exit_nodes.append(block.split()[1])
    tor_exit_nodes = [block.split()[1] for block in text.split('\n') if "ExitAddress" in block]
    print("Retrieved " + len(tor_exit_nodes) + " TOR nodes.")
