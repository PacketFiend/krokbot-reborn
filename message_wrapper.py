#!/usr/bin/env python
#
# Name:    messagewrapper.py
# Author:  Striek
# Date:    March 2017
# Summary: Places a wrapper around the say() and msg() methods so we can add our own logic to them
#

import config
import sopel

from pprint import pprint

from sqlalchemy import (create_engine, Table, Column, Text, Integer, String, MetaData, ForeignKey, exc)
from sqlalchemy.sql import (select, exists)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
metadata = MetaData()

engine = create_engine(config.sql_connection_string, pool_recycle = 14400)
coolkids = Table('coolkids', metadata, autoload=True, autoload_with=engine)

sopel.bot.Sopel._say = sopel.bot.Sopel.say
sopel.bot.Sopel._msg = sopel.bot.Sopel.msg

def say(self, text, recipient, max_messages=1):

    send_message = True
    conn = engine.connect()
    q = select([coolkids.c.highlight, coolkids.c.nick])
    items = conn.execute(q)

    # Check the list of nicks we have, and see if they've requested to not be highlighted    
    for item in items:
        if item.nick in text and item.highlight == 0:
            # No highlight. Change the nick to put a space between every character.
            nick = " ".join(list(item.nick))
            text = text.replace(item.nick, nick)
            #send_message = False
            break

    if send_message:
        sopel.bot.Sopel._say(self, text, recipient, max_messages)
    else:
        sopel.bot.Sopel._say(self, "Newp. " + nick + " doesn't want to be highlighted", recipient, max_messages)

def msg(self, recipient, text, max_messages=1):

    sopel.bot.Sopel._msg(self, recipient, text, max_messages)

sopel.bot.Sopel.say = say
sopel.bot.Sopel.msg = msg

@sopel.module.commands('donthighlightme')
def no_highight(bot, trigger):

    '''Instructs the krokbot to noght highlight you. Your nick will mangled in future messages
    to avoid highlighting you'''

    conn = engine.connect()
    query = coolkids.update().values(highlight=0).where(coolkids.c.nick == trigger.nick)
    conn.execute(query)
    
@sopel.module.commands('dohighlightme')
def do_highight(bot, trigger):

    '''Instructs the krokbot to highlight you once again'''
    
    conn = engine.connect()
    query = coolkids.update().values(highlight=1).where(coolkids.c.nick == trigger.nick)
    conn.execute(query)
