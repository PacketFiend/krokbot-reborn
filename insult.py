#!/usr/bin/env python
#
# Name:    insult.py
# Author:  Syini666, ekim
# Date:    November 2016	
# Summary: shakesperian insult generator
#

import config
from sopel import module, tools
import random
from random import randint
import sqlalchemy

#engine = sqlalchemy.create_engine("mysql+pymysql://krok:kr0kl4bs@localhost/krokbot?host=localhost?port=3306")
engine = sqlalchemy.create_engine(config.sql_connection_string, pool_recycle = 14400)

@module.commands('insult')
def getInsult(bot, trigger):
	'''Constructs a random shakesperian insult from the MySQL database'''
	randint = 0
	target = trigger.group(2)
	if not target:
		target = trigger.nick
	target = target.strip()
	insult = target + ", thou "

	random.seed()
	
	conn = engine.connect()
	# returning random results from MySQL is horribly inefficient. count the rows and do the randomization with python
	for position in {1,2,3}:
		# Count the rows
		query = "SELECT COUNT(*) AS cnt FROM insults WHERE place=" + str(position)
		items = conn.execute(query)
		item = items.fetchone()

		# Select a random insult from each section
		randint = random.randint(1,int(item[0]-1))
		query = "SELECT insult FROM insults WHERE place = " + str(position) + " LIMIT " + str(randint) + ", 1"
		result = conn.execute(query)
		item = result.fetchone()
		insult = insult + str(item[0])
		if not position == 3: insult = insult + ", "

	insult = insult + "!"

	bot.msg(trigger.sender, insult)
