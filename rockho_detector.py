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
import random
import time
from random import randint

import sys
import requests

'''
Define some memory dicts/lists for keeping track of users.
'''
def setup(bot):
    #bot.memory['tor_exit_nodes'] = {}
    global tor_exit_nodes
    tor_exit_nodes = []

@module.event('JOIN')
@module.rule(r'.*')
def check_for_rockhos(bot, trigger):
    if trigger.admin:
        bot.say("A glorious leader has joined!")
    if trigger.nick == 'rockho' or "ct.charter.com" in trigger.hostmask:
        bot.say("A wild rockho appeared! Prepare the defenses!")

'''
Get TOR exit node list and parse the IPs into a python list.
'''
#@module.interval(3600)
#def get_tor_exit_nodes(bot):
#    num = 0
#    r = requests.get('https://check.torproject.org/exit-addresses')
#    text = r.split('\n')
#    #for block in text:
#    #    if "ExitAddress" in block: tor_exit_nodes.append(block.split()[1])
#    tor_exit_nodes = [block.split()[1] for block in text.split('\n') if "ExitAddress" in block]
#    print("Retrieved " + len(tor_exit_nodes) + " TOR nodes.")
#
