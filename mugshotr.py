#!/usr/bin/env python
#
# Name:    mugshotr.py
# Author:  Syini666/ekim
# Date:    May 28th, 2016
# Summary: Display latest Ranson mugshots and arrest records
#

from sopel import module, tools
import random
import time
from random import randint

import requests
import re
from sqlalchemy import (create_engine, Table, Column, Integer, String, MetaData, ForeignKey, exc)
from sqlalchemy.sql import (select, exists)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import config

#import kgen
#import creds

Base = declarative_base()

class Jailbird(Base):
    __tablename__ = 'jailbirds'
    id = Column(Integer, primary_key=True, autoincrement=True)
    arrestid = Column(String)
    name = Column(String)


'''
Find details of the jailbird such as name, arrest location, data
'''
def find_jailbird_name(url):
    r = requests.get(url)
    pattern = re.compile(r"<TITLE>(.+?)  </TITLE>", flags=re.DOTALL)
    jailbird_name = pattern.findall(r.text)

    return jailbird_name

'''
Get arrest information
'''
def get_arrests():
    r = requests.get('http://arre.st/Mugshots/WestVirginia/ERJ')
    found = re.findall(r"WV\-[0-9]{10}", r.text)
    #found2 = re.findall(r"http://cdn\.arre\.st/Jails/WVJails\.info/tb\.php\?file=images2/[A-Za-z0-9\-]{1,}\.jpg&size=200", r.text)

    return found

def start_db():
    engine = create_engine("mysql+pymysql://krok:kr0kl4bs@localhost/krokbot?host=localhost?port=3306", pool_recycle = 14400)
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    Base.metadata.reflect(engine)

    return session

'''
Gather latest jailbirds and dump them into a database
'''
@module.interval(1800)
def latest_jailbirds(bot):
# find out if we have a new arrestee; if we do, add them to the db
    session = start_db()
    found = get_arrests()
    jailbirds = []

    def add_new_jailbirds(arrestid):
        rs = session.query(exists().where(Jailbird.arrestid == arrestid)).scalar()
        if rs is False:
            url = "http://arre.st/" + arrestid
            jailbird_name = find_jailbird_name(url)
            arrestid = str(arrestid)
            jailbird_name = str(jailbird_name)
            new_jailbird = Jailbird(arrestid=arrestid, name=jailbird_name)
            try:
                session.add(new_jailbird)
                session.commit()
                print "Adding new jailbird to the database: " + jailbird_name + " " + arrestid
            finally:
                session.close()
    map(add_new_jailbirds, found)

'''
Print latest jailbirds
'''
@module.rate(20)
@module.commands('jailbirds')
def last_five_jailbirds(bot, trigger):
# Get channel we're connected to
    conn_channels = bot.privileges
    channel_list = []
    channel_list = [ch for ch in conn_channels if ch not in channel_list]

    session = start_db()
    rs = session.query(Jailbird).order_by(Jailbird.id.desc()).limit(5)
    if rs:
        bot.say("Latest Ranson jailbirds:")
        for jailbird in rs:
            jailbird = jailbird.name + " http://arre.st/" + jailbird.arrestid
            bot.say(jailbird)
    else:
        bot.say("No new arrests in Ranson!")
    session.close()

'''
Print a random jailbird
'''
@module.rate(20)
@module.commands('jailbird')
def random_jailbird(bot, trigger):
    # grab a list of IDs from db
    session = start_db()
    id_count = session.query(Jailbird.id).count()

    rnd = randint(0,id_count)

    # grab a random jailbird
    rnd_jailbird = session.query(Jailbird).get(rnd)
    jlbrd_msg = rnd_jailbird.name + " http://arre.st/" + rnd_jailbird.arrestid
    bot.say(jlbrd_msg)
    session.close()

if __name__ == "__main__":
    latest_jailbirds()
