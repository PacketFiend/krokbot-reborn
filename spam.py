#!/usr/bin/env python
#
# Name:    spam.py
# Author:  Striek
# Date:    Various dates in 2015/2016
# Summary: evil spam module
#

from sopel import module, tools
import random
import time
import sys
import requests
import krok

global usersToSpam
usersToSpam = []

@module.require_admin
@module.commands('spam')
def spam(bot, trigger):
    '''Sends all part/join/quit messages from all channels the bot is in the specificed nick'''

    global usersToSpam
    imp = trigger.group(2)
    nick = imp.split(" ")
    nick = nick[0]

    if nick not in usersToSpam:
        usersToSpam.append(nick)
    else:
        if nick in usersToSpam:
            bot.msg(trigger.sender, trigger.nick + ", I'm already spamming " + nick\
                    + ". You're a fucking fucktard, fucker. Fuck the fuck off. FUCK!")

@module.require_admin
@module.commands('unspam')
def unSpam(bot, trigger):
    '''Stops spamming the specified user'''

    global usersToSpam
    imp = trigger.group(2)
    nick = imp.split(" ")
    nick = nick[0]

    if nick in usersToSpam:
        usersToSpam.remove(nick)
    else:
        bot.msg(trigger.sender, trigger.nick + ", you're such a fucktard. I wasn't spamming that dude yet.")

@module.event('JOIN')
@module.event('PART')
@module.event('QUIT')
@module.rule('.*')
def snedSpamMessage(bot, trigger):
    '''Relays PART/JOIN/QUIT messages to users we intend to spam'''
    if trigger.event == 'JOIN':
        event = "joined "
    elif trigger.event == 'QUIT':
        event = "quit "
    elif trigger.event == 'PART':
        event = "left "

    global usersToSpam
    message = ""
    for nick in usersToSpam:
        message = trigger.nick + " (" + trigger.hostmask + ") has " + event + trigger.sender
        bot.msg(nick, message)
    print trigger.hostmask

@module.interval(10)
def messageSpam(bot):
    '''Spams every user on the list. Interval can be any multiple of 10 seconds'''

    global usersToSpam
    for nick in usersToSpam:
        rand_krok = krok.random_krok()
        bot.msg(nick, rand_krok)
