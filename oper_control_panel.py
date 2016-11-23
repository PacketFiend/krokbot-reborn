#!/usr/bin/env python
#
# Name:    oper.py
# Author:  ekim
# Date:    Nov 23rd, 2016
# Summary: OPER mode command control panel
#

from __future__ import print_function
from sopel import module, tools, config
from sopel.tools.target import User, Channel
from sopel.tools import Identifier, iteritems, events

'''
Define some memory dicts/lists for keeping track of users who become OPs.
'''
def setup(bot):
    bot.memory['opers'] = {}

'''
Allow bot admins to gain channel OPs mode.
'''
#@module.require_privmsg
#@module.require_admin
@module.commands('opme')
@module.priority('low')
@module.rate('300')
def opme(bot, trigger):
    nickname = trigger.nick
    channel = trigger.sender

    if trigger.admin:
        if bot.memory['opers'].get(nickname, None) == None:
            mode = "+o"
            bot.write(['MODE ', channel, mode, nickname])
            bot.memory['opers'][nickname] = 1
            print("Current Opers:", bot.memory['opers'])
        elif bot.memory['opers'].get(nickname, None) == 1:
            mode = "-o"
            bot.write(['MODE ', channel, mode, nickname])
            del bot.memory['opers'][nickname]
            print("Current Opers:", bot.memory['opers'])
    else:
        bot.reply("No ops for you chamo, your mama don't love you")

'''
Functionality for bot admins to admin other users regardless of the fact whether
they have channel OPs or not.

NOTE: this could prove to be dangerous thus requires a bit more testing. This is
equivalent to having global server ops.
'''
#@module.require_admin
@module.commands('op')
@module.priority('low')
@module.rate('300')
def op_user(bot, trigger):
    if trigger.admin:
        nickname = trigger.group(2)
        channel = trigger.sender

        if bot.memory['opers'].get(nickname, None) == None:
            mode = "+o"
            bot.write(['MODE ', channel, mode, nickname])
            bot.memory['opers'][nickname] = 1
            print("Current Opers:", bot.memory['opers'])
        elif bot.memory['opers'].get(nickname, None) == 1:
            mode = "-o"
            bot.write(['MODE ', channel, mode, nickname])
            del bot.memory['opers'][nickname]
            print("Current Opers:", bot.memory['opers'])
    else:
        bot.reply("No ops for that chamo, go chop bongs")
