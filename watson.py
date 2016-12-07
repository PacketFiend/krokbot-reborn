#!/usr/bin/env python
#
# Name:    watson.py
# Author:  Striek	
# Date:    December 2016
# Summary: krokbot natural language processing module
#

import config
from sopel import module, tools
import json
from watson_developer_cloud import AlchemyLanguageV1, WatsonException
from pprint import pprint

from sqlalchemy import (create_engine, Table, Column, Text, Integer, String, MetaData, ForeignKey, exc)
from sqlalchemy.sql import (select, exists, update)
from sqlalchemy.exc import OperationalError

engine = create_engine(config.sql_connection_string, pool_recycle = 14400)
metadata = MetaData()
watson_apikeys = Table('watson_apikeys', metadata, autoload=True, autoload_with=engine)


class APIKey:

	def __init__(self):
		self.currentAPIKey = 0
		self.api_keys = []
		self.queryCount = 1000
		#api_keys.append("1c9d6cd926fc7bff7488f0a4d6597f98ab8ca2de")	# Striek API key #1 - CC# attached
		#self.api_keys.append("f5a2025a517f32fc272844e0ddeb36ccdb117336") # Striek
		#self.api_keys.append("7719aa5300998a90464e4cb36a6858c072d2096a") # Syini666
		#self.api_keys.append("39f58aeb7f09742f80fbebbe1bdc43ac80318b93") # ekim

		# Load API keys from the database
		query = select([watson_apikeys.c.key, watson_apikeys.c.queries, watson_apikeys.c.owner])
		print query
		conn = engine.connect()
		keys = conn.execute(query)
		for key in keys:
			self.api_keys.append(key.key)
		self.name = self.api_keys[self.currentAPIKey]
		# Get the current query count for this key
		self.queryCount = self.getQueryCount()

	def next(self):
		self.currentAPIKey += 1
		print "currentApiKey: " + str(self.currentAPIKey) + "; len(self.api_keys): " + str(len(self.api_keys))
		if self.currentAPIKey > len(self.api_keys)-1:
			return False
		else:
			self.name = self.api_keys[self.currentAPIKey]
			alchemy_language = AlchemyLanguageV1(api_key = self.name)
			self.queryCount = self.getQueryCount()
			return True

	def first(self):
		self.currentAPIKey = 0

	def updateQueryCount(self):
		self.queryCount += 1
		query = update(watson_apikeys).where(watson_apikeys.c.key == self.name).values(queries = self.queryCount)
		conn = engine.connect()
		conn.execute(query)
		return self.queryCount

	def getQueryCount(self):
		# Pull the current number of queries the key has used
		query = select([watson_apikeys.c.queries]).where(watson_apikeys.c.key == self.name)
		conn = engine.connect()
		result = conn.execute(query)
		self.queryCount = result.fetchone()
		self.queryCount = self.queryCount[0]
		return self.queryCount

	def getCurrentKey(self):
		query = select([watson_apikeys.c.key, watson_apikeys.c.queries, watson_apikeys.c.owner]).where(watson_apikeys.c.key == self.name)
		conn = engine.connect()
		result = conn.execute(query)
		keyInfo = result.fetchone()
		return keyInfo

class TextAnalyzer:

	def __init__(self, name):
		self.APIKey = APIKey()
		self.threshold = 0.6
		self.nlp_enabled = False
		self.emotionDetected = False
		self.alchemy_language = AlchemyLanguageV1(api_key = self.APIKey.name)

	def analyzeEmotion(self, bot, trigger):
		if not self.nlp_enabled: return
		self.emotionDetected = False
		emotion = ""
		print trigger
		# This block sucks ass. Need a better way to store multiple API keys and switch between them,
		if self.APIKey.queryCount >= 100:
			bot.msg(trigger.sender, "Cycling to next API key!")
			if not self.APIKey.next():
				self.nlp_enabled = False
				bot.msg(trigger.sender, "API query limit exhausted with current set of keys. Disabling NLP subsystem.")
				return
			else:
				# Start this function from the beginning
				self.analyzeEmotion(bot, trigger)
				return			
	        try:
	                result = json.dumps(
	                        self.alchemy_language.combined(
	                                text=trigger,
	                                extract='doc-emotion',
	                                max_items=1)
	                        )
			self.APIKey.updateQueryCount()
	        except WatsonException, message:
	                if "daily-transaction-limit-exceeded" in str(message):
	                        bot.msg(trigger.sender, "API daily transaction limit exceeded. Switching to next key :D")
				self.APIKey.next(bot, trigger)
				bot.msg(trigger.sender, "API Key is now: " + self.APIKey)
	                return

	        print result
	        json_data = json.loads(result)

	        if float(json_data['docEmotions']['anger']) > self.threshold:
	                self.emotionDetected = True
	                emotion += "angry, "
	        if float(json_data['docEmotions']['joy']) > self.threshold:
	                self.emotionDetected = True
	                emotion += "joyous, "
	        if float(json_data['docEmotions']['fear']) > self.threshold:
	                self.emotionDetected = True
	                emotion += "afraid, "
	        if float(json_data['docEmotions']['sadness']) > self.threshold:
	                self.emotionDetected = True
	                emotion += "sad, "
	        if float(json_data['docEmotions']['disgust']) > self.threshold:
	                self.emotionDetected = True
	                emotion += "disgusted, "

	        # Say something cute if we think we've detected some kind of sentiment...
	        if self.emotionDetected:
	                # These next few lines construct a grammatically correct list of emotions
	                # We need to replace the last ", " with " and "
	                emotion = emotion.rstrip(", ")
	                lastEmotion = emotion.rsplit(",", 1)
	                if len(lastEmotion) > 1:
	                        lastEmotion[1] = lastEmotion[1].replace(" ", "and ")
	                        emotion = " ".join(lastEmotion)
	                else:
	                        emotion = "".join(lastEmotion)
	                bot.msg(trigger.sender, "Why so " + emotion + ", " + trigger.nick + "?")


emotionAnalyzer = TextAnalyzer('emotionAnalyzer')

# Match a line not starting with ".", "!", "krokbot", "krokpot", "kdev", or "krokwhore"
@module.rule('^(?!krokbot|krokwhore|krokpot|kdev)^[^\.!].*')
def analyzeText(bot, trigger):

	emotionAnalyzer.analyzeEmotion(bot, trigger)


@module.commands('nlp_emotion_threshold')
def setEmotionThreshold(bot, trigger):
	'''Sets a new threshold for emotion detection, or shows current threshold if no argument is given. Defaults to 0.6. Must be 0 <= threshold <= 1
Usage: !nlp_emotion_threshold [0 <= <new value> <= 1]'''
	if emotionAnalyzer.nlp_enabled:
		if trigger.group(2):
			args = trigger.group(2).split()
			newThreshold = float(args[0])
			if not 0 <= newThreshold <= 1:
				bot.msg(trigger.sender, "The new value must be between 0 and 1 inclusive. RTFM, mothafucka!")
				return
			else:
				emotionAnalyzer.threshold = float(trigger.group(2))
				bot.msg(trigger.sender, trigger.nick + ", new emotion detection threshold is " + str(emotionAnalyzer.threshold))
		else:
			bot.msg(trigger.sender, trigger.nick + ", current emotion detection threshold is " + str(emotionAnalyzer.threshold))
	else:
		bot.msg(trigger.sender, "Enable the NLP subsystem first, fuckwad.")

@module.require_admin
@module.commands('nlp_enable')
def enableNlp(bot, trigger):
	'''Enables the natural language processing subsystem. Requires admin access.'''
	if emotionAnalyzer.nlp_enabled:
		bot.msg(trigger.sender, "Natural language processing is already enabled, fucktard.")
	else:
		emotionAnalyzer.nlp_enabled = True
		emotionAnalyzer.APIKey.first()
		bot.msg(trigger.sender, "Natural language processing susbsystems enabled.")

@module.require_admin
@module.commands('nlp_disable')
def disableNlp(bot, trigger):
	'''Disables the natural language processing subsystem. Requires admin access.'''
	if not emotionAnalyzer.nlp_enabled:
		bot.msg(trigger.sender, "Natural language processing is already disabled, fucktard.")
	else:
		emotionAnalyzer.nlp_enabled = False
		bot.msg(trigger.sender, "Natural language processing susbsystems disabled.")

@module.commands('nlp_status')
def getNlpStatus(bot, trigger):
	'''Displays the current status of the NLP subsystem.'''
	if emotionAnalyzer.nlp_enabled:
		bot.msg(trigger.sender, "NLP subsystem is active!")
	else:
		bot.msg(trigger.sender, "Sorry, NLP subsystem is offline.")

@module.require_admin
@module.commands('nlp_current_key')
def showKeyInfo(bot, trigger):
	'''Shows the key currently in use via PRIVMSG to the requester. Requires admin access.'''
	if emotionAnalyzer.nlp_enabled:
		keyInfo = emotionAnalyzer.APIKey.getCurrentKey()
		bot.msg(trigger.nick, "Current API key: " + keyInfo['key'])
		bot.msg(trigger.nick, "Current query count: " + str(keyInfo['queries']))
		bot.msg(trigger.nick, "Key owner: " + keyInfo['owner'])
		bot.msg(trigger.nick, "Thank you, " + trigger.nick + ", and have an awesome day!")
	else:
		bot.msg(trigger.sender, "Enable the NLP subsystem first, fuckwad.")
