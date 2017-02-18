#!/usr/bin/env python
#
# Name:    slutr.py
# Author:  ekim
# Date:    Apr 18th, 2016
# Summary: slutr: krokbot pr0n extension
#

from sopel import module, tools
import random
from random import randint
import praw
from sqlalchemy import (create_engine, Table, Column, Integer, String, MetaData, ForeignKey, exc, desc)
from sqlalchemy.sql import (select, exists)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
import config

'''
Setup database ORM stuff. Database location is fed in via config module.
'''
Base = declarative_base()

class Sluts(Base):
    __tablename__ = 'sluts'
    sluts_id = Column(Integer, primary_key=True, autoincrement=True)
    sluts_vote = Column(Integer)
    sluts_name = Column(String)

def start_db():
    #engine = create_engine('sqlite:///' + config.stats_db, connect_args={'check_same_thread': False}, pool_recycle = 14400)
    engine = create_engine(config.sql_connection_string, pool_recycle = 14400)
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    Base.metadata.reflect(engine)

    return session

'''
Define some memory dicts/lists for keeping track of pics that were already used
'''
def setup(bot):
    bot.memory["used_pics"] = {}
    bot.memory["used_pics"]['tittypic'] = []
    bot.memory["used_pics"]['clamshot'] = []
    bot.memory["used_pics"]['sideboob'] = []
    bot.memory["used_pics"]['sharpie'] = []
    bot.memory["used_pics"]['last_pic'] = None

# slutr extensions
# Reddit titty pic poster
@module.interval(3600)
def sluttosphere_setup(bot):
    r = praw.Reddit(user_agent='sopel_get_titty_pic')
    titty_subreddits = ['boobs', 'gonemild', 'tits', 'redheads', 'brunettes', 'tittydrop', 'downblouse', 'titties']
    clam_subreddits = ['pussy', 'rearpussy', 'pussy_girls', 'asianpussy', 'perfectpussies', 'ready_pussy', 'pussyjuices']
    sideboob_subreddits = ['sideboob', 'sideboobs']
    sharpies_subreddits = ['buttsharpies']
    global slut_links_tits
    global slut_links_clams
    global slut_links_sideboobs
    global slut_links_sharpie
    slut_links_tits = {}
    slut_links_clams = {}
    slut_links_sideboobs = {}
    slut_links_sharpie = {}

    for sub in titty_subreddits:
        r_posts = r.get_subreddit(sub).get_new(limit=15)
        # each picture has an id, title, and a url; the id is the key and
        # title and url are values
        slut_links_tits = {s.id: [s.title, s.url] for s in r_posts}

    for sub in clam_subreddits:
        r_posts = r.get_subreddit(sub).get_new(limit=15)
        slut_links_clams = {s.id: [s.title, s.url] for s in r_posts}

    for sub in sideboob_subreddits:
        r_posts = r.get_subreddit(sub).get_new(limit=15)
        slut_links_sideboobs = {s.id: [s.title, s.url] for s in r_posts}

    for sub in sharpies_subreddits:
        r_posts = r.get_subreddit(sub).get_new(limit=15)
        slut_links_sharpie = {s.id: [s.title, s.url] for s in r_posts}

    print(sluttosphere_setup.__name__ + " - Grabbed latest batch of slut pics")

    return (slut_links_tits, slut_links_clams, slut_links_sideboobs, slut_links_sharpie)

@module.rate(20)
@module.commands(r'tittypic\b|clamshot\b|sideboob\b|sharpie\b')
def sluttosphere_get_pic(bot, trigger):
    try:
        if 'tittypic' in trigger.group(0):
            pic_type = 'tittypic'
            pics = slut_links_tits
        elif 'clamshot' in trigger.group(0):
            pic_type = 'clamshot'
            pics = slut_links_clams
        elif 'sideboob' in trigger.group(0):
            pic_type = 'sideboob'
            pics = slut_links_sideboobs
        elif 'sharpie' in trigger.group(0):
            pic_type = 'sharpie'
            pics = slut_links_sharpie
        else:
            pics = "can't find the dict"

        # first we pick a random pic, then we check if it is in the memory and if
        # the memory is full for each type of pics.
        while True:
            pic = random.choice(pics.keys())
            if pic in bot.memory['used_pics'][pic_type]:
                pass
            elif len(bot.memory['used_pics'][pic_type]) >= 15:
                bot.say("Hold on, the sluts are coming!")
                break
            else:
                rand_submission = "NSFW - [" + pics[pic][0] + "] " + pics[pic][1]
                print(sluttosphere_get_pic.__name__ + " - " + rand_submission)
                bot.say(rand_submission)
                bot.memory['used_pics'][pic_type].append(pic)
                bot.memory['used_pics']['last_pic'] = rand_submission
                break
    except (KeyError, IndexError, NameError):
        if 'tittypic' in trigger.group(0):
            errmsg = "Got no sluts yet"
        elif 'clamshot' in trigger.group(0):
            errmsg = "Got no pink tacos yet"
        elif 'sideboob' in trigger.group(0):
            errmsg = "Got no poppin' side boobs yet"
        elif 'sharpie' in trigger.group(0):
            errmsg = "Let's see how many sharpies I can fit up my asshole"
        else:
            print(trigger.group(0))
            errmsg = "Hold on, the sluts are coming!"
        bot.say(errmsg)
        dummy_arg = None
        sluttosphere_setup(dummy_arg)

'''
!upvote command
Here we upvote the last pasted pic that is kept in the bot.memory['used_pics']['last_pic'].
If the pic is not found, we add it to the database table with a vote count of 1.
If the upvote command references an ID, we upvote that specific ID.

:param1 (str):  id of the pic to be upvote, optional; part of trigger.group()
'''
@module.rate(20)
@module.commands('upvote')
def sluttosphere_upvote(bot, trigger):
    last_pic = bot.memory['used_pics']['last_pic']
    table = Sluts
    vote_id = trigger.group(2)
    vote = 1

    session = start_db()
    if vote_id is None:
        print("Searching for the slut in the table")
        rs = session.query(exists().where((table.sluts_name == last_pic))).scalar()
        if rs is True:
            rs = session.query(table).filter_by(sluts_name=last_pic).scalar()
            try:
                print("Found the pic in the table. Updating slut's vote count")
                session.query(table).filter_by(sluts_name=last_pic).update({'sluts_vote': table.sluts_vote + vote})
                session.commit()
            except:
                print("Could not increment vote for {} in the Sluts table.".format(last_pic))
            finally:
                session.close()
        elif rs is False:
            print("Adding a new slut to vote on to the Sluts table.")
            try:
                rs = table(sluts_name=last_pic, sluts_vote=vote)
                session.add(rs)
                session.commit()
            except:
                print("Failed adding {} to the Sluts table".format(last_pic))
            finally:
                session.close()
    else:
        # Search for the pic based on the vote_id (which is really the slut_idand
        # then update the pic's vote count.
        rs = session.query(exists().where((table.sluts_id == vote_id))).scalar()
        if rs is True:
            try:
                print("Foudn the ID in the table. Updating slut's vote count")
                session.query(table).filter_by(sluts_id=vote_id).update({'sluts_vote': table.sluts_vote + vote})
                session.commit()
            except:
                print("Could not increment vote for {} in the Sluts table.".format(last_pic))
            finally:
                session.close()
        elif rs is False:
            bot.say("Could not find the id of the titty pic, pipo")

'''
!topbabes command
Print top voted pics.
'''
@module.rate(20)
@module.commands('topsluts')
def sluttosphere_topbabes(bot, trigger):
    session = start_db()
    table = Sluts
    rs = session.query(table).order_by(desc(table.sluts_vote)).limit(5)
    for slut in rs:
        bot.say(str(slut.sluts_vote) + " votes: #" + str(slut.sluts_id) + " - " + slut.sluts_name)
    bot.say("To upvote, either call !upvote after pic post or !upvote <#ID>")
    session.close()
