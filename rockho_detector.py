#!/usr/bin/env python
#
# Name:    rockho_detector.py
# Author:  ekim
# Date:    Apr 18th, 2016
# Summary: krokbot rockho detector
#

import config
from config import sql_connection_string
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

engine = sqlalchemy.create_engine(sql_connection_string)

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
    print "Retrieved " + len(tor_exit_nodes) + " TOR nodes."
