#!/usr/bin/env python
#
# Name:    stats.py
# Author:  Syini666, ekim
# Date:    Various dates in 2015/2016
# Summary: krokbot: evil AI stats of lathers, lures, and baits. Not safe for human
#          consumption.
#

from __future__ import print_function
from sopel import module, tools
import random
import time
from random import randint
from sqlalchemy import (create_engine, Table, Column, Integer, String, MetaData, ForeignKey, exc)
from sqlalchemy.sql import (select, exists)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
import config
import re
from pprint import pprint

'''
Setup database ORM stuff. Database location is fed in via config module.
'''
Base = declarative_base()

class Lathers(Base):
    __tablename__ = 'lathers'
    channel = Column(String, primary_key=True, autoincrement=False)
    count = Column(Integer)
    name = Column(String)

class Lures(Base):
    __tablename__ = 'lures'
    channel = Column(String, primary_key=True, autoincrement=False)
    count = Column(Integer)
    name = Column(String)

class Baits(Base):
    __tablename__ = 'baits'
    channel = Column(String, primary_key=True, autoincrement=False)
    count = Column(Integer)
    name = Column(String)

class Words(Base):
    __tablename__ = 'words'
    channel = Column(String, primary_key=True, autoincrement=False)
    count = Column(Integer)
    name = Column(String)

def start_db():
    #engine = create_engine('sqlite:///' + config.stats_db, connect_args={'check_same_thread': False}, pool_recycle = 14400)
    engine = create_engine(config.sql_connection_string, pool_recycle = 14400)
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    Base.metadata.reflect(engine)

    return session

'''
Define some memory dicts/lists for keeping track of users and their word counts.
'''
def setup(bot):

    session = start_db()
    results = session.query(Words, Words.channel)
    session.close()
    for result in results:
        channel = result[1]
        channel = channel.encode('ascii')
        bot.memory['word_counts'] = {}
        bot.memory['word_counts'][channel] = {}

'''
Insert top lather stats; Start by matching on ACTION lathers; if match found
check if nickname is in the lathers table and get his current count. Increment and
add latest score. If the nickname is not present, add a new row for them with a
count of 1.
'''
@module.rule(r'\blathers\b|\blures\b|\bbaits\b (\w+)')
@module.rate(20)
def insert_top_action(bot, trigger):
    if trigger.match and 'sopel' not in trigger.nick:
        nickname = trigger.nick
        channel = trigger.sender
        channel = channel.encode('ascii')
        actions = []

        if 'lather' in trigger.group(0):
            table = Lathers
            actions.append(table)
        if 'lure' in trigger.group(0):
            table = Lures
            actions.append(table)
        if 'bait' in trigger.group(0):
            table = Baits
            actions.append(table)

        for table in actions:
            session = start_db()
            rs = session.query(exists().where((table.channel == channel) & (table.name == nickname))).scalar()

            if rs is True:
                try:
                    session.query(table).filter_by(channel=channel).filter_by(name=nickname).update({'count': table.count + 1})
                    session.commit()
                except NameError:
                    print("{} not found in the table.".format(nickname))
                except:
                    print("Could not increment user's {} count in the table.".format(table))
                finally:
                    session.close()
            elif rs is False:
                print("Adding new nickname to the {} stats table : {}".format(table, nickname))
                try:
                    rs = table(channel=channel, name=nickname, count=1)
                    session.add(rs)
                    session.commit()
                except:
                    table = 'words'
                    print("Failed adding {} to the {} stats table".format(nickname, table))
                finally:
                    print("What you talkin' about chamo?")
                session.close()

'''
Get top stats for lather, lure, and bait. We start off with defining 3 commands.
Then we check for those commands in the trigger.group(1) (1 being the first
command specified in the line from the server). Based on that, we decide which
database table we'll be querying.
'''
@module.rate(20)
@module.commands('toplather', 'toplure', 'topbait', 'words')
def get_top_stats(bot, trigger):
    channel = trigger.sender
    channel = channel.encode('ascii')

    if 'lather' in trigger.group(1):
        reply = "Top Lather Action"
        table = Lathers
    elif 'lure' in trigger.group(1):
        reply = "Lure Leaderboard"
        table = Lures
    elif 'bait' in trigger.group(1):
        reply = "Fine Baiting"
        table = Baits
    elif 'words' in trigger.group(1):
        reply = "Top Blabbermouths"
        table = Words

    session = start_db()
    top_stats = {nickname.name: nickname.count for nickname in session.query(table.name, table.count).filter_by(channel=channel)}

    session.close()

    stats = {k.encode('ascii'): v for k, v in top_stats.items()}
    bot.msg(channel, reply + ": " + str(stats))

'''
!words command that tracks channel's top talkers with word counts for a given timespan.

This command is setup in get_top_stats() but requires word_stats() to build a dictionary
with word counts for every user in the channel. Currently, this tracks all channels for each user.
In the future we probably should track word counts for each user per individual channel.

Algorithm description:
We need to setup bot.memory for each user in the channel. If the user is not in bot.memory['word_counts']
dictionary, set up a new key for them with value == '0'.

On each line that the bot sees from each user, count the words and put them in bot.memory
dict for that user. For more lines, update the value for the username key with newer word count.
Periodically dump the bot.memory['word_counts'] dict into a database table and set the
value for the username key to 0.

Current database schema:
nickname, count
'''
@module.rule(r'.*')
def words_stats(bot, trigger):
    nickname = trigger.user
    nickname = nickname.encode('ascii')
    channel = trigger.sender
    channel = channel.encode('ascii')
    line = trigger.args[1:]
    line =  map(str, line)
    #line = line.encode('ascii')
    word_count = len(str(line).split(" "))

    if re.match(r'\#', trigger.sender):
        try:
            pprint(bot.memory)
            if channel not in bot.memory['word_counts']:
                bot.memory['word_counts'][channel] = {}
            if 'sopel' not in trigger.user:
                if nickname not in bot.memory['word_counts'][channel]: # or bot.memory['word_counts'][channel].get(nickname, None) == 0:
                    bot.memory['word_counts'][channel][nickname] = word_count
                else:
                    bot.memory['word_counts'][channel][nickname] += word_count
                    #print(bot.memory['word_counts'])
        except KeyError:
            bot.say("Well something just went terribly wrong...")
    else:
        print("Private message it seems...")

    # instead of using a forloop, count the "line" list elements and
    # add that number to the bot.memory['word_counts'] dict.
    #for word in str(line).split(" "):
    #    bot.memory['word_counts'][nickname] += 1

'''
Dump bot.memory['word_counts'] into a database table
'''
@module.interval(900)
@module.require_admin
@module.commands('stats_dump_words')
def dump_word_stats(bot, trigger=None):
    session = start_db()
    table = Words

    for channel in bot.memory['word_counts'].keys():
        for nickname, word_count in bot.memory['word_counts'][channel].items():
            rs = session.query(exists().where((table.channel == channel) & (table.name == nickname))).scalar()

            if rs is True:
                try:
                    session.query(table).filter_by(channel=channel).filter_by(name=nickname).update({'count': table.count + word_count})
                    session.commit()
                except NameError:
                    print("{} not found in the table.".format(nickname))
                except:
                    print("Could not increment user's {} count in the table.".format(table))
                finally:
                    session.close()
            elif rs is False:
                print("Adding new nickname to the {} stats table : {}".format(table, nickname))
                try:
                    rs = table(channel=channel, name=nickname, count=word_count)
                    session.add(rs)
                    session.commit()
                except:
                    table = 'words'
                    print("Failed adding {} to the {} stats table".format(nickname, table))
                finally:
                    print("What you talkin' about chamo?")
                    session.close()

            # Clear the memory before starting again
            bot.memory['word_counts'][channel][nickname] = 0
