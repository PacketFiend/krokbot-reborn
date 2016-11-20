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
import sqlite3
import random
import time
from random import randint
from sqlalchemy import (create_engine, Table, Column, Integer, String, MetaData, ForeignKey, exc)
from sqlalchemy.sql import (select, exists)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import config

'''
Setup database ORM stuff. Database location is fed in via config module.
'''
Base = declarative_base()

class Lathers(Base):
    __tablename__ = 'lathers'
    name = Column(String, primary_key=True, autoincrement=False)
    count = Column(Integer)

class Lures(Base):
    __tablename__ = 'lures'
    name = Column(String, primary_key=True, autoincrement=False)
    count = Column(Integer)

class Baits(Base):
    __tablename__ = 'baits'
    name = Column(String, primary_key=True, autoincrement=False)
    count = Column(Integer)

def start_db():
    engine = create_engine('sqlite:///' + config.stats_db)
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    Base.metadata.reflect(engine)

    return session

'''
Insert top lather stats; Start by matching on ACTION lathers; if match found
check if nickname is in the lathers table and get his current count. Increment and
add latest score. If the nickname is not present, add a new row for them with a
count of 1.
'''
@module.rule(r'\blathers\b|\blures\b|\bbaits\b (\w+)')
@module.rate(20)
def insert_top_action(bot, trigger):
    if trigger.match:
        nickname = trigger.nick
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
        #count = session.query(Lathers).filter_by(name=nickname).first()

        for table in actions:
            session = start_db()
            rs = session.query(exists().where(table.name == nickname)).scalar()
            if rs is True:
                try:
                    session.query(table).filter_by(name=nickname).update({'count': table.count + 1})
                    session.commit()
                except NameError:
                    print("{} not found in the table.".format(nickname))
                except:
                    print("Could not increment user's {} count in the table.").format(table)
                finally:
                    session.close()
            elif rs is False:
                print("Adding new nickname to the {} stats table : {}".format(table, nickname))
                try:
                    rs = table(name=nickname, count=1)
                    session.add(rs)
                    session.commit()
                except:
                    print("Failed adding {} to the {} stats table".format(nickname, table))
                finally:
                    session.close()

'''
Get top stats for lather, lure, and bait. We start off with defining 3 commands.
Then we check for those commands in the trigger.group(1) (1 being the first
command specified in the line from the server). Based on that, we decide which
database table we'll be querying.
'''
@module.rate(20)
@module.commands('toplather', 'toplure', 'topbait')
def get_top_stats(bot, trigger):
    if 'lather' in trigger.group(1):
        print("got a lather")
        table = Lathers
    elif 'lure' in trigger.group(1):
        print("got a lure")
        table = Lures
    elif 'bait' in trigger.group(1):
        print("got a bait")
        table = Baits

    session = start_db()
    top_stats = {}
    for nickname in session.query(table):
        top_stats[nickname.name] = nickname.count

    stats = {k.encode('ascii'): v for k, v in top_stats.items()}
    print(stats)
    bot.reply("Top Lather Action: " + str(stats))
