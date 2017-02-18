#
# Name:    censor.py
# Author:  Striek
# Date:    November 2016
#

import config
from sopel import module, tools, bot
from sopel.tools.target import User, Channel
from random import randint
import sys, os
import threading
from pprint import pprint,pformat

global banned_words
global censor_enabled
censor_enabled = False
banned_words = ["trump", "vote"]

@module.rule('.*')
def autoban(bot, trigger):

    global censor_enabled
    if not censor_enabled: return
    global banned_words
    channel = trigger.sender
    nick = trigger.nick

    for banned_word in banned_words:
        if banned_word.lower() in trigger.lower():
            bot.write(['MODE', channel , "+b" , trigger.hostmask])
            bot.write(['KICK', channel, nick], "You said a bad word!")

@module.require_admin
@module.commands('censor_addword')
def censor_addword(bot, trigger):

    global banned_words

    banned_words.append(trigger.group(2))

@module.require_admin
@module.commands('censor_removeword')
def censor_removeword(bot, trigger):

    global banned_words

    banned_words.remove(trigger.group(2))
    
@module.commands('censor_showbanned')
def censor_showbanned(bot, trigger):

    global banned_words

    bot.msg(trigger.sender, "You can't say these in #offtopic: " + " ".join(banned_words))

@module.require_admin
@module.commands('censor_enable')
def censor_enable(bot, trigger):

    global censor_enabled
    censor_enabled = True
    bot.msg(trigger.sender, "Censor module enabled")

@module.require_admin
@module.commands('censor_disable')
def censor_disable(bot, trigger):

    global censor_enabled
    censor_enabled = False
    bot.msg(trigger.sender, "Censor module disabled.")

@module.commands('censor_status')
def censor_status(bot, trigger):

    global censor_enabled
    if censor_enabled:
        bot.msg(trigger.sender, "Censor module is active")
    else:
        bot.msg(trigger.sender, "Censor module is inactive")
