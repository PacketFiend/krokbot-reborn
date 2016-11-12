#!/usr/bin/env python
#
# Name:    stats.py
# Author:  Syini666
# Date:    Various dates in 2015/2016
# Summary: krokbot: evil AI
#

from sopel import module, tools
import sqlite3
import random
import time
from random import randint

import sys

# the only place that the stats.db file needs to be is /home/krokbot/.sopel/
# we can reference the sqlitefile with ../stats.db

# get lather stats
@module.rate(20)
@module.commands('toplather')
def get_top_lather_stats(bot, trigger):
        conn = sqlite3.connect('/home/krokbot/.sopel/modules/stats.db')
        lather_stats = []
        items = conn.execute("SELECT * FROM lathers ORDER BY count DESC limit 5;")
        for i in items:
                t = str(i[0]) + ": " + str(i[1])
                lather_stats.append(t)
        bot.reply("Top Lather Action: "+str(lather_stats))


# get lure stats
@module.rate(20)
@module.commands('toplure')
def get_top_lure_stats(bot, trigger):
        conn = sqlite3.connect('../stats.db')
        lure_stats = []
        items = conn.execute("SELECT * FROM lures ORDER BY count DESC limit 5;")
        for i in items:
                t = str(i[0]) + ": " + str(i[1])
                lure_stats.append(t)
        bot.reply("Lure Leaderboard: "+str(lure_stats))

# get baits stats
@module.rate(20)
@module.commands('topbait')
def get_top_bait_stats(bot, trigger):
        conn = sqlite3.connect('../stats.db')
        bait_stats = []
        items = conn.execute("SELECT * FROM baits ORDER BY count DESC limit 5;")
        for i in items:
                t = str(i[0]) + ": " + str(i[1])
                bait_stats.append(t)
        bot.reply("Fine Baiting: "+str(bait_stats))

