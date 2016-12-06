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

nlp_enabled = False

api_keys = []
api_keys.append("1c9d6cd926fc7bff7488f0a4d6597f98ab8ca2de")
api_keys.append("f5a2025a517f32fc272844e0ddeb36ccdb117336")
global currentApiKey
global threshold
threshold = 0.5
currentApiKey = 0

# Match a line not starting with ".", "!", "krokbot", "krokpot", "kdev", or "krokwhore"
@module.rule('^(?!krokbot|krokwhore|krokpot|kdev)^[^\.!].*')
def analyzeText(bot, trigger):
	global nlp_enabled
	if not nlp_enabled: return
	global currentApiKey
	global threshold

	alchemy_language = AlchemyLanguageV1(api_key = api_keys[currentApiKey])

	emotionDetected = False
	emotion = ""
	print trigger
	# This block sucks ass. Need a better way to store multiple API keys and switch between them,
	try:
		result = json.dumps(
			alchemy_language.combined(
				text=trigger,
				extract='doc-emotion',
				max_items=1)
			)
	except WatsonException, message:
		if "daily-transaction-limit-exceeded" in str(message):
			bot.msg(trigger.sender, "API daily transaction limit exceeded. Switching to next key :D")
			try:
				currentApiKey += 1
				print "currentApiKey: " + str(currentApiKey) + "; len(api_keys): " + str(len(api_keys))
				if currentApiKey > len(api_keys)-1:
					bot.msg(trigger.sender, "API query limit exhausted with current set of keys. Disabling NLP subsystem:")
					nlp_enabled = False
					return
				bot.msg(trigger.sender, "Old API key: " + api_keys[currentApiKey-1])
				bot.msg(trigger.sender, "New API key: " + api_keys[currentApiKey])
				alchemy_language = AlchemyLanguageV1(api_key = api_keys[currentApiKey])
			except WatsonException, message:
				bot.msg(trigger.sender, "API key no workie!: "+ api_key)
		return

	print result

	json_data = json.loads(result)

	if float(json_data['docEmotions']['anger']) > threshold:
		emotionDetected = True
		emotion += "angry, "
	if float(json_data['docEmotions']['joy']) > threshold:
		emotionDetected = True
		emotion += "joyous, "
	if float(json_data['docEmotions']['fear']) > threshold:
		emotionDetected = True
		emotion += "afraid, "
	if float(json_data['docEmotions']['sadness']) > threshold:
		emotionDetected = True
		emotion += "sad, "
	if float(json_data['docEmotions']['disgust']) > threshold:
		emotionDetected = True
		emotion += "disgusted, "

	# Say something cute if we think we've detected some kind of sentiment...
	if emotionDetected:
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

@module.require_admin
@module.commands('set_emotion_threshold')
def setEmotionThreshold(bot, trigger):
	'''Sets a new threshold for emotion detection. Defaults to 0.5. Value must be 0 <= threshold <= 1.'''
	global threshold
	threshold = float(trigger.group(2))
	bot.msg(trigger.sender, trigger.nick + ", new emotion detection threshold is " + str(threshold))

@module.commands('enable_nlp')
def enableNlp(bot, trigger):
	global nlp_enabled
	if nlp_enabled:
		bot.msg(trigger.sender, "Natural language processing is already enabled, fucktard.")
	else:
		nlp_enabled = True
		bot.msg(trigger.sender, "Natural language processing susbsystems enabled.")

@module.commands('disable_nlp')
def disableNlp(bot, trigger):
	global nlp_enabled
	if not nlp_enabled:
		bot.msg(trigger.sender, "Natural language processing is already disabled, fucktard.")
	else:
		nlp_enabled = False
		bot.msg(trigger.sender, "Natural language processing susbsystems disabled.")

