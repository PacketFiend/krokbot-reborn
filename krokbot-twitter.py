#!/usr/bin/env python
#
# Name:    krokbot-twitter.py
# Author:  Striek
# Date:    Dec 2016
# Summary: krokbot Twitter module
#


import config
import time, re, twitter
from sopel import module, tools
from sopel.tools import events
from pprint import pprint
import threading

from sqlalchemy import (create_engine, Table, Column, Text, Integer, String, MetaData, ForeignKey, exc)
from sqlalchemy.sql import (select, exists)
from sqlalchemy.exc import OperationalError

api = twitter.Api(consumer_key=config.tw_consumer_key,
    consumer_secret=config.tw_consumer_secret,
    access_token_key=config.tw_access_token_key,
    access_token_secret=config.tw_access_token_secret)

metadata = MetaData()

loggedInUsers = []
whoisReceived = False
displayUpdates = True

engine = create_engine(config.sql_connection_string, pool_recycle = 14400)

coolkids = Table('coolkids', metadata, autoload=True, autoload_with=engine)

global twitter_updates
global debug
debug = False

def setup(bot):
    tw_init(bot)
    
@module.commands('tweet')
def postStatusUpdate(bot, trigger):
    """Posts a twitter status update with krokbot's twitter account. URLs will be automatically shortened. Use !tweetpic for multimedia tweets.
usage: !tweet <update>
"""
    message = str(trigger.group(2))
    nick = trigger.nick
    print "Message is " + message + "; nick is " + str(nick)
    
    error = can_tweet(bot, nick)
    if error == 0:
        status = api.PostUpdate(message)
        bot.msg(trigger.sender, trigger.nick + ", you just tweeted: " + " " + status.text)
    else:
        bot.say(trigger.sender, error)

@module.commands('tweetpic')
def postStatusUpdatePic(bot, trigger):
    """Posts a multimedia twitter status update with krokbot's twitter account. URLs will be removed and the remainder tweeted.
usage: !tweet <update> <url> [<more update>]
"""
    nick = trigger.nick
    regex = re.compile("(https?|ftp)://([^\s/?\.#]+\.?)+(/[^\s]*)?")
    match = regex.search(trigger.group(2))
    message = str(trigger.group(2))

    error = can_tweet(bot,nick)
    if error == 0:
        if match:
            url = match.group()
            message = message.replace(url,"").replace("  ", " ")        # Remove the URL from the message, and collapse any douple spaces
            bot.msg(trigger.sender, "The message is: " + message)
        else:
            bot.msg(trigger.sender, "You need to include a URL, asshole.")
            return
        status = api.PostMedia(message, url)
        bot.msg(trigger.sender, trigger.nick + ", you just tweeted: " + " " + status.text)
    else:
        bot.say(trigger.sender, error)

@module.commands('tw_status')
def tw_status(bot, trigger):

    print "Checking Twitter status..."
    global displayUpdates
    if tw_stream_control(bot, "check") == True:
        bot.say("The Twitter stream is active", trigger.sender)
    else:
        bot.say("The Twitter stream is inactive", trigger.sender)
        
    if displayUpdates == True:
        bot.say("I *should* be displaying Twitter status updates...", trigger.sender)
    else:
        bot.say("I should *not* be displaying Twitter status updates...", trigger.sender)

@module.require_admin
@module.commands('tw_showupdates')
def showUpdates(bot, trigger):
    global displayUpdates
    displayUpdates = True
    bot.msg(trigger.sender, trigger.nick + ", now showing Twitter status updates")

@module.require_admin
@module.commands('tw_hideupdates')
def hideUpdates(bot, trigger):
    global displayUpdates
    displayUpdates = False
    bot.msg(trigger.sender, trigger.nick + ", now hiding Twitter status updates")

def tw_init(bot):

    global twitter_updates
    global displayUpdates
    displayUpdates = True
    
    tw_stream_control(bot, "start")
    
def tw_stream_control(bot, command = None):

    global twitter_updates
    global debug
    global userStream

    if command == "start":
        if tw_stream_control(bot, "check") == False:
            # Set up the user stream - returns a generator object
            userStream = api.GetUserStream(withuser='followings')
            if debug: print userStream
            twitter_updates = threading.Thread(target=tw_get_updates, args=(bot, userStream))
            twitter_updates.start()
            if debug: print "twitter_updates.is_alive(): " + str(twitter_updates.is_alive())
    elif command == "check":
        try:
            twitter_updates
        except NameError:
            return False
        if twitter_updates.is_alive():
            return True
        else:
            return False
    elif command == "stop":
        # Stop the user stream
        if tw_stream_control(bot, "check") == True:
            del userStream

def tw_get_updates(bot, userStream):

    # Run this loop looking for new tweets
    for datum in userStream:
        if "text" in datum:
            for channel in bot.channels:
                if displayUpdates:
                    bot.msg(channel, "Incoming tweet from @" + datum['user']['screen_name'] + "(" + datum['user']['name'] + "): " + datum['text'])
        print datum
    

@module.require_admin
@module.commands('tw_reinit')
def tw_reinit(bot, trigger):
    
    global displayUpdates
    displayUpdates = True
    tw_stream_control(bot, "stop")
    tw_stream_control(bot, "start")

    bot.msg(trigger.sender, "Twitter Stream Reactivated")


@module.rule('.*')
@module.event('319', '330') # 307 is returned if a user is logged in. 319 is the list of channels it's in, and should be received first.
def parseWhois(bot, trigger):

    global whoisReceived
    triggerParts = trigger.raw.split(' ')
    # The server will return a response such as
    # :irc.unerror.com 330 AlsoStriek Syini666 Syini666 :is logged in as
    # We need to check the nick it's referring to, and whether it's registered or not.
    nick = triggerParts[3]
    # Now add it to the list, if the user is logged in
    print trigger.raw
    if "is logged in as" in trigger:
        loggedInUsers.append(nick)
    whoisReceived = True

@module.commands('loggedin')
def checkLoginStatus(bot, trigger):
    nick = trigger.group(2)
    loggedIn = isLoggedIn(bot, nick)

def isLoggedIn(bot, nick):

    global whoisReceived

    # First, remove the nick from the list of logged in users, if it's there
    # This is to ensure the nick is removed if a user has logged out
    if nick in loggedInUsers:
        loggedInUsers.remove(nick)
    bot.write(['WHOIS', nick])

    # Now wait for the server command to be returned and parseWhois() to be triggered
    whoisReceived = False
    while not whoisReceived: time.sleep(0.1)
    if nick in loggedInUsers:
        whoisReceived = False
        return True
    else:
        whoisReceived = False
        return False

def can_tweet(bot, nick):

    loginStatus = False
    message = ""

    conn = engine.connect()
    q = select([coolkids.c.cantweet]).where(coolkids.c.nick == nick)
    try:
        items = conn.execute(q)
    except OperationalError:
        bot.msg(trigger.sender, nick + ", you broke the fucking SQL server. Gimme a minute and try again")
        return
    row = items.fetchone()
    try:
        canTweet = row[0]
    except TypeError:
        canTweet = 0

    loginStatus = isLoggedIn(bot, nick)

    if canTweet and loginStatus:
        return 0
    else:
        if not loginStatus:
            message = "Don't be a fucking tool. I don't let just anybody tweet. Register with Nickserv."
        elif not canTweet:
            message = "Hey there pipo, I just don't like you enough. Get one of my admins to vouch for you."
        else:
            message = "Sorry " + nick + ", you cannot send tweets. I'm so high I can't really figure out why."

        return message
        
@module.require_admin
@module.commands('tw_debug')
def tw_debug(bot, trigger):

   global debug
   if debug == True:
       debug = False
       bot.say(trigger.nick + ", debug flag is now off. Thanks!", trigger.sender)
   else:
       debug = True
       bot.say(trigger.nick + ", debug flag is now on. Go fuck a pig.", trigger.sender)

'''
Search for periscope.tv tweets. For more information on how tweets are
constructed, please see https://dev.twitter.com/overview/api/tweets. If you want
to browse the tweet's structure, run api.GetStatus(id) where id = tweet's id and
pipe it via jq or jsonlint.

Actual tweets can be directly queries for attributes. RT tweets will typically be
truncated. To get around this, we need to query RT's tweet.retweeted_status.id to
get original tweet's id. This id can then be queried for full text/attributes.

Args:
    scope  (str):   command to be acted on
    param1 (str):   search string for twitter query, part of trigger.group()

Returns:
    query (obj):    query object with a list of results; parse this to get
                    individual tweets
    tweet (obj):    tweet object with various attributes of a tweet
'''
@module.commands('scope')
@module.rate(20)
def get_periscope(bot, trigger):
    channel = trigger.sender
    # make sure that we actually have a search term, shitbird
    if trigger.group(2) is not None:
        # we're doing America a favor...
        search_term = "#periscope " + str(trigger.group(2))
        query = api.GetSearch(term=search_term, result_type="recent", count="3")
        for q in query:
            id = q.id
            # get each tweet's extended attributes; each tweet is an object with
            # various attributes
            tweet = api.GetStatus(id)
            # check if the tweet was retweeted and if so, get the original
            # untruncated tweet
            try:
                text = tweet.retweeted_status.text
                # clean up the tweet text so we're not displaying urls twice
                text = re.sub('https?:\/\/.[^\s].*$', '', text)
                url = tweet.retweeted_status.urls[0].url
                created_at = tweet.retweeted_status.created_at
            except AttributeError:
                text = tweet.text
                text = re.sub('https?:\/\/.[^\s].*$', '', text)
                url = tweet.urls[0].url
                created_at = tweet.created_at
            else:
                bot.say("Incoming scope: " + created_at + " - [" + text + "] - " + url)
    else:
        bot.say("Don't be a mental midget, enter a search string")

@module.require_admin
@module.commands('showscopes')
def show_new_scopes(bot, trigger):
    global displayScopes
    displayScopes = True

    # Set up the user stream - returns a generator object
    userStream = api.GetUserStream(withuser='followings')
    bot.msg(trigger.sender, "Scope Stream Activated")
    # Run this loop looking for new tweets
    for datum in userStream:
        if "text" in datum and "#periscope" in datum['text']:
            for channel in bot.channels:
                if displayScopes:
                    bot.msg(channel, "Incoming scope from @" + datum['user']['screen_name'] + "(" + datum['user']['name'] + "): " + datum['text'])
