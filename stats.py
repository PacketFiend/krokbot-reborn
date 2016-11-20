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
from sqlalchemy import (create_engine, Table, Column, Integer, String, MetaData, ForeignKey, exc)
from sqlalchemy.sql import (select, exists)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

'''
The only place that the stats.db file needs to be is /home/krokbot/.sopel/
we can reference the sqlitefile with ../stats.db
'''
Base = declarative_base()

class Lathers(Base):
    __tablename__ = 'lathers'
    name = Column(String, primary_key=True, autoincrement=False)
    count = Column(Integer)

def start_db():
    engine = create_engine('sqlite:////home/mike/.sopel/modules/stats.db')
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    Base.metadata.reflect(engine)

    return session

'''
Insert top lather stats; Start by matching on ACTION lathers; if match found
check if user is in the lathers table and get his current count. Increment and add
latest score.
'''
@module.rule('lathers (\w+)')
@module.rate(20)
def insert_top_lather(bot, trigger):
    if trigger.match:
        nickname = trigger.nick
        #count = session.query(Lathers).filter_by(name=nickname).first()
        session = start_db()
        rs = session.query(exists().where(Lathers.name == nickname)).scalar()
        if rs is True:
            try:
                session.query(Lathers).filter_by(name=nickname).update({'count': Lathers.count + 1})
                session.commit()
            except NameError:
                print nickname + " not found in the database."
            except:
                print "Could not increment user's lather count in the database."
            finally:
                session.close()
        elif rs is False:
            print "Adding new nickname to the lather stats database: " + nickname
            rs = Lathers(name=nickname, count=1)
            try:
                session.add(rs)
                session.commit()
            finally:
                session.close()

# get lather stats
@module.rate(20)
@module.commands('toplather')
def get_top_lather_stats(bot, trigger):
    session = start_db()
    lather_stats = {}
    for nickname in session.query(Lathers):
        lather_stats[nickname.name] = nickname.count

    bot.reply("Top Lather Action: " + str(lather_stats))

#        conn = sqlite3.connect('/home/mike/.sopel/modules/stats.db')
#        lather_stats = []
#        items = conn.execute("SELECT * FROM lathers ORDER BY count DESC limit 5;")
#        for i in items:
#                t = str(i[0]) + ": " + str(i[1])
#                lather_stats.append(t)
#        bot.reply("Top Lather Action: "+str(lather_stats))

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
