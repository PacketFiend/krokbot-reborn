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

from sqlalchemy import (create_engine, Table, Column, Text, Integer, 
                        String, MetaData, ForeignKey, exc)
from sqlalchemy.sql import (select, exists, update, insert)
from sqlalchemy.exc import OperationalError

import traceback

engine = create_engine(config.sql_connection_string, pool_recycle = 14400)
metadata = MetaData()
watson_apikeys = Table('watson_apikeys', metadata, autoload=True, autoload_with=engine)
watson_krok = Table('watson_krok', metadata, autoload=True, autoload_with=engine)
watson_kroksubjects = Table('watson_kroksubjects', metadata, autoload=True, autoload_with=engine)
watson_krokemotions = Table('watson_krokemotions', metadata, autoload=True, autoload_with=engine)

global debug
debug = False

class APIKeyClass:
    '''A class to contain a list of all API keys in use, and cycle through them when we
    reach a specified number of API calls'''

    def __init__(self):
        self.currentAPIKey = 0
        self.api_keys = []
        self.queryCount = 1000
        #self.api_keys.append("1c9d6cd926fc7bff7488f0a4d6597f98ab8ca2de")   # Striek API key #1 - CC# attached

        # Load API keys from the database
        query = select([watson_apikeys.c.key, watson_apikeys.c.queries, watson_apikeys.c.owner])
        conn = engine.connect()
        keys = conn.execute(query)
        for key in keys:
            self.api_keys.append(key.key)
        self.name = self.api_keys[self.currentAPIKey]
        # Get the current query count for this key
        self.queryCount = self.getQueryCount()

    class exc:
        '''A subclass which holds any exceptions raised by this class. Currently, just
        used for NoMoreKeysException.'''
        class NoMoreKeysException(Exception):
            pass
    
    def next(self):
        '''Cycles to the next API key in the list. Return False if we've exhausted the
        available keys. Returns the key we've switched to.'''
        self.currentAPIKey += 1
        if self.currentAPIKey > len(self.api_keys)-1:
            raise APIKey.exc.NoMoreKeysException("No more API keys available!")
            return False
        else:
            self.name = self.api_keys[self.currentAPIKey]
            self.queryCount = self.getQueryCount()
            return self.name

    def first(self):
        '''Resets us back to the first key in the list. Generally called from
        !nlp_enable.'''
        self.currentAPIKey = 0
        self.name = self.api_keys[self.currentAPIKey]
        self.getQueryCount()

    def updateQueryCount(self):
        '''Updates the in-memory record of the current query count, and writes that value
        to the DB'''
        self.queryCount = self.getQueryCount()
        self.queryCount += 1
        query = update(watson_apikeys).where(watson_apikeys.c.key == self.name)\
                .values(queries = self.queryCount)
        conn = engine.connect()
        conn.execute(query)
        return self.queryCount

    def getQueryCount(self):
        '''Returns the number of queries that the currently in use API key has performed'''
        query = select([watson_apikeys.c.queries]).where(watson_apikeys.c.key == self.name)
        conn = engine.connect()
        result = conn.execute(query)
        self.queryCount = result.fetchone()
        self.queryCount = self.queryCount[0]
        return self.queryCount

    def getCurrentKey(self):
        '''Returns a dict containing information on the currently in use API key'''
        query = select([watson_apikeys.c.key, watson_apikeys.c.queries,
                        watson_apikeys.c.owner]).where(watson_apikeys.c.key == self.name)
        conn = engine.connect()
        result = conn.execute(query)
        keyInfo = result.fetchone()
        return keyInfo

APIKey = APIKeyClass()

class TextAnalyzer:
    ''' A class to analyze text messages from an IRC channel and make cutesy-tutesy
    comments about what we think the state of the commenter is.'''

    master_nlp_enabled = False

    def __init__(self, name):
        '''Opens a dialogue with Watson and sets up sane defaults. Also sets up our API
        keys by calling instantiating am APIKey object'''
        self.threshold = config.watson_emotion_detection_threshold
        self.emotionDetected = False
        self.alchemy_language = AlchemyLanguageV1(api_key = APIKey.name)

    def analyzeEmotion(self, bot, trigger):
        '''Runs IRC messages through Watson's Alchemy API, attempting to identify
        emotional context.'''
        if debug: print "Entering analyzeEmotion()"
        if not krok_handler.nlp_master_enabled or not krok_handler.nlp_emotion_enabled:
            print "Early return from analyzeEmotion()!"
            return
        self.emotionDetected = False
        emotions = {}
        channel = trigger.sender
        channel = "#test1"
        print trigger
        if APIKey.queryCount >= 990:
            bot.msg(channel, "Cycling to next API key!")
            # If there's no more API keys we can use, disable the NLP subsystem and exit.
            # Otherwise, move to the next key.
            try:
                self.alchemy_language = AlchemyLanguageV1(api_key = APIKey.next())
                emotions = self.analyzeEmotion(bot, trigger)  # Start over w/new key.
                return emotions
            except APIKey.exc.NoMoreKeysException:
                TextAnalyzer.master_nlp_enabled = False
                raise APIKey.exc.NoMoreKeysException("This class is entirelely "
                +" uncontaminated with API keys! "
                +" (https://www.youtube.com/watch?v=B3KBuQHHKx0). Disabling NLP subsystem.")

        try:
            # This is the block that actually sends messages off to Alchemy for processing.
            if debug: print "In analyzeEmotion(): Analyzing emotion"
            json_dump = self.alchemy_language.combined(
                            text=trigger,
                            extract='doc-emotion',
                            max_items=1,
                            language='english')
            result = json.dumps(json_dump)
            pprint(result)
                # Make sure we keep track of how many API queries we've used
            APIKey.updateQueryCount()
            print result

        except WatsonException, message:
            # This really shouldn't happen if we set the max query count correctly.
            # This means this block is untestable :(
            if "daily-transaction-limit-exceeded" in str(message):
                bot.msg(channel, "API daily transaction limit exceeded. "
                                 +"Switching to next key :D (" + str(message))
                self.alchemy_language = AlchemyLanguageV1(api_key = APIKey.next())
                print "API Key is now: " + APIKey.name
            else:
                bot.msg(channel, "Unhandled Watson Exception: " + str(message))
                return
        except Exception, message:
            print "Unhandled exception! " + str(message)

        if result:
            json_data = json.loads(result)

        if float(json_data['docEmotions']['anger']) > self.threshold:
            emotions["anger"] = float(json_data['docEmotions']['anger'])
            self.emotionDetected = True
        if float(json_data['docEmotions']['joy']) > self.threshold:
            emotions["joy"] = float(json_data['docEmotions']['joy'])
            self.emotionDetected = True
        if float(json_data['docEmotions']['fear']) > self.threshold:
            emotions["fear"] = float(json_data['docEmotions']['fear'])
            self.emotionDetected = True
        if float(json_data['docEmotions']['sadness']) > self.threshold:
            emotions["sadness"] = float(json_data['docEmotions']['sadness'])
            self.emotionDetected = True
        if float(json_data['docEmotions']['disgust']) > self.threshold:
            emotions["disgust"] = float(json_data['docEmotions']['disgust'])
            self.emotionDetected = True


        if self.emotionDetected == True:
            if debug: pprint("About to return... " + str(emotions))
            return emotions
        else:
            return False

    def analyzeSubject(self, bot, trigger):
        '''Runs messages through Watson's Alchemy API, attempting to identify
        topical context.'''
        if not krok_handler.nlp_master_enabled or not krok_handler.nlp_subject_enabled:
            if debug: print "TextAnalyzer.analyzeSubject(): early return!"
            return
        subjects = []
        channel = trigger.sender
        channel = "#test1"
        print trigger
        if APIKey.queryCount >= 990:
            bot.msg(channel, "Cycling to next API key!")
            # If there's no more API keys we can use, disable the NLP subsystem and exit.
            # Otherwise, move to the next key.
            try:
                self.alchemy_language = AlchemyLanguageV1(api_key = APIKey.next())
                concepts = self.analyzeSubject(bot, trigger)   # Start over with new key.
                return concepts
            except APIKey.exc.NoMoreKeysException:
                TextAnalyzer.master_nlp_enabled = False
                raise APIKey.exc.NoMoreKeysException("This class is entirelely"
                    +" uncontaminated with API keys! "
                    +" (https://www.youtube.com/watch?v=B3KBuQHHKx0). Disabling NLP subsystem.")

        try:
            # This is the block that actually sends messages off to Alchemy for processing.
            result = json.dumps(
                    self.alchemy_language.concepts(text=trigger,
                                                   show_source_text = 1,
                                                   linked_data = 0,
                                                   language='english')
                    )
            # Make sure we keep track of how many API queries we've used
            APIKey.updateQueryCount()
        except WatsonException, message:
            # This really shouldn't happen if we set the max query count correctly.
            # This means this block is untestable :(
            if "daily-transaction-limit-exceeded" in str(message):
                bot.msg(channel, "API daily transaction limit exceeded. \
                Switching to next key :D (" + str(message))
                self.alchemy_language = AlchemyLanguageV1(api_key = APIKey.next())
                print "API Key is now: " + APIKey.name
                return
            else:
                bot.msg(channel, "Unhandled Watson Exception: " + str(message))

	print result
        json_data = json.loads(result)
	concepts = json_data['concepts']
        if json_data['concepts']:
            return concepts
        else:
            return False

        
class DataHandler:
    '''A class to handle messages and identified context'''

    master_nlp_enabled = False

    def __init__(self, name):
        self.name = name
        self.nlp_enabled = False

    def recordSubjects(self, trigger, concepts):
        '''Tags krok already present in the database with associated subjects'''

        # Pull the key ID for the krok we just inserted.
        # (Can a ResultProxy object give us this info?)
        conn = engine.connect()
        query = select([watson_krok.c.krokid]).where(watson_krok.c.text == trigger)
        result = conn.execute(query)
        if result.rowcount != 0:
            krokID = result.first()[0]

            # Now, update kroksubjects with a list of every subject identified for
            # that krok, and its relevance.
            for datum in concepts:
                subject = datum['text']
                query = watson_kroksubjects.insert().values(krokid = krokID,
                                                     subject = subject,
                                                     relevance = datum['relevance'])
                try:
                    result = conn.execute(query)
                except Exception, message:
                    print "Exception in recordSubjects() writing " + subject \
                        + " to database for krok " + trigger + ": " + str(message)
                    return False
            return True
        else:
            return False

    def recordEmotions(self, trigger, emotions):
        '''Tags krok already present in the database with associated subjects'''

        # Pull the key ID for the krok we just inserted.
        # (Can a ResultProxy object give us this info?)
        conn = engine.connect()
        query = select([watson_krok.c.krokid]).where(watson_krok.c.text == trigger)
        result = conn.execute(query)
        if result.rowcount != 0:
            krokID = result.first()[0]

            # Now, update kroksubjects with a list of every subject identified for
            # that krok, and its relevance.
            for emotion in emotions:
                confidence = emotions[emotion]
                query = watson_krokemotions.insert().values(krokid = krokID,
                                                     emotion = emotion,
                                                     confidence = confidence)
                result = conn.execute(query)
            return True
        else:
            return False

class KrokHandler:
    '''Handles the processing, analysis, and db insertion of krok.'''

    def __init__(self, name):
        concepts = []
        emotions = []
        self.nlp_master_enabled = True
        self.nlp_emotion_enabled = True
        self.nlp_subject_enabled = True
        self.emotionAnalyzer = TextAnalyzer('emotionAnalyzer')
        self.emotionHandler = DataHandler('emotionHandler')
        self.subjectAnalyzer = TextAnalyzer('subjectAnalyzer')
        self.subjectHandler = DataHandler('subjectHandler')
    
    def record_krok(self, bot, trigger, force=False):
        '''Inserts krok in the database, first checking that it's unique'''
        # If force is true, this function will insert the krok regardless of whether
        # or not any context was identified. Otherwise, one of the subclasses
        # must return some context before the krok will be inserted.

        if not self.nlp_master_enabled:
            if debug: print "In record_krok(): early return, nlp_master_enabled is False"
            return

        channel = trigger.sender
        try:
            conn = engine.connect()
            query = select([watson_krok.c.text]).where(watson_krok.c.text == trigger)
            result = conn.execute(query)
            
            # Is this krok already present in the database? If so, exit now.
            if result.rowcount != 0:
                if debug: print "Found " + str(result.rowcount) + " matching entries."
                return
            if self.nlp_emotion_enabled:
                if debug: print "About to analyze emotions"
                emotions = self.emotionAnalyzer.analyzeEmotion(bot, trigger)
                if debug: print "Analyzed emotions"; print emotions
            if self.nlp_subject_enabled:
                if debug: print "About to analyze subjects"
                concepts = self.subjectAnalyzer.analyzeSubject(bot, trigger)
                if debug: print "Analyzed subjects"; print concepts

            # Record the krok, if there's any context identified, or we forced it
            if concepts or emotions or force:
                query = watson_krok.insert().values(text = trigger).prefix_with("IGNORE")
                result = conn.execute(query)
            else:
                if debug: print "In record_krok(): early return - no context identified."
                return False

            # Now, if we identified any context, enter that into the DB as well
            try:
                if emotions:
                    self.emotionHandler.recordEmotions(trigger,emotions)
                if concepts:
                    self.subjectHandler.recordSubjects(trigger, concepts)
            except APIKey.exc.NoMoreKeysException:
			    bot.msg(trigger.sender, "NoMoreKeysException: " + str(message))

        except OperationalError, message:
            if "has gone away" in message:
                print "MariaDB server has gone away: " + str(message)
            else:
                print "Unhandled OperationalError in recordKrok() writing to database: "\
                      + str(message)
        # Disable the NLP subsystem if we catch any other exception, to prevent flooding
        except Exception, message:
            self.nlp_master_enabled = False
            traceback.print_exc()
            raise

krok_handler = KrokHandler('krokHandler')

# Match a line not starting with ".", "!", "krokbot", "krokpot", "kdev", or "krokwhore"
@module.unblockable
@module.rule('^(?!krokbot|krokwhore|krokpot|kdev)^[^\.!].*')
def analyzeText(bot, trigger):
    '''Passes messages to the TextAnalyzer class for analysis by the Big Blue'''
    global debug
    channel = trigger.sender

    # Ignore this rule if it's not rockho
    if not debug:
        if "ct.charter.com" not in trigger.hostmask:
            return
    try:
        krok_handler.record_krok(bot, trigger)
    except Exception, message:
        bot.msg(channel, "Unhandled exception in record_krok(): " + str(message) \
                         +"; NLP subsystem disabled.")


@module.commands('nlp_emotion_threshold')
def setEmotionThreshold(bot, trigger):
    '''Sets a new threshold for emotion detection, or shows current threshold if no
argument is given. Defaults to 0.6. Must be 0 <= threshold <= 1 Usage: !nlp_emotion_threshold [0 <= <new value> <= 1]'''
    if krok_handler.nlp_master_enabled:
        if trigger.group(2):
            args = trigger.group(2).split()
            newThreshold = float(args[0])
            if not 0 <= newThreshold <= 1:
                bot.msg(trigger.sender, "The new value must be between 0 and 1 "
                    +" inclusive. RTFM, mothafucka!")
                return
            else:
                krok_handler.emotionAnalyzer.threshold = float(trigger.group(2))
                bot.msg(trigger.sender, trigger.nick 
                    + ", new emotion detection threshold is "
                    + str(krok_handler.emotionAnalyzer.threshold))
        else:
            bot.msg(trigger.sender, trigger.nick 
                + ", current emotion detection threshold is "
                + str(krok_handler.emotionAnalyzer.threshold))
    else:
        bot.msg(trigger.sender, "Enable the NLP subsystem first, fuckwad.")

@module.require_admin
@module.commands('nlp_enable')
def enableNlp(bot, trigger):
    '''Enables the natural language processing subsystems. Requires admin access.'''
    channel = trigger.sender
    if trigger.group(2) == "emotion":
        if krok_handler.nlp_emotion_enabled:
            bot.msg(channel, "Emotional analysis is already enabled, fucktard.")
        else:
            krok_handler.nlp_emotion_enabled = True
            bot.msg(channel, "Emotional analysis enabled")
        return
    elif trigger.group(2) == "subject":
        if krok_handler.nlp_subject_enabled:
            bot.msg(channel, "Subject analysis is already enabled, fucktard.")
        else:
            krok_handler.nlp_subject_enabled = True
            bot.msg(channel, "Subject analysis enabled.")
        return
    else:
        if krok_handler.nlp_master_enabled:
            bot.msg(trigger.sender, "Natural language processing is already enabled, fucktard.")
        else:
            krok_handler.nlp_master_enabled = True
            APIKey.first()
            bot.msg(trigger.sender, "Natural language processing susbsystems enabled.")

@module.require_admin
@module.commands('nlp_disable')
def disbleNlp(bot, trigger):
    '''Disables the natural language processing subsystems. Requires admin access.'''
    channel = trigger.sender
    if trigger.group(2) == "emotion":
        if not krok_handler.nlp_emotion_enabled:
            bot.msg(channel, "Emotional analysis is already disabled, fucktard.")
        else:
            krok_handler.nlp_emotion_enabled = False
            bot.msg(channel, "Emotional analysis disabled")
        return
    elif trigger.group(2) == "subject":
        if not krok_handler.nlp_subject_enabled:
            bot.msg(channel, "Subject analysis is already disabled, fucktard.")
        else:
            krok_handler.nlp_subject_enabled = False
            bot.msg(channel, "Subject analysis disabled.")
        return
    else:
        if not krok_handler.nlp_master_enabled:
            bot.msg(trigger.sender, "Natural language processing is already disabled, fucktard.")
        else:
            krok_handler.nlp_master_enabled = False
            bot.msg(trigger.sender, "Natural language processing susbsystems disabled.")

@module.commands('nlp_status')
def getNlpStatus(bot, trigger):
    '''Displays the current status of the NLP subsystem.'''
    channel = trigger.sender
    if krok_handler.nlp_master_enabled: bot.msg(channel, "NLP subsystem is active!")
    else: bot.msg(channel, "Sorry, NLP subsystem is offline.")

    if krok_handler.nlp_emotion_enabled: bot.msg(channel, "Emotional analysis: Online")
    else: bot.msg(channel, "Emotional analysis: Offline")
        
    if krok_handler.nlp_subject_enabled: bot.msg(channel, "Subject analysis: Online")
    else: bot.msg(channel, "Subject analysis: Offline")

@module.require_admin
@module.commands('nlp_current_key')
def showKeyInfo(bot, trigger):
    '''Shows the key currently in use via PRIVMSG to the requester. Requires admin access.'''
    if krok_handler.nlp_master_enabled:
        keyInfo = APIKey.getCurrentKey()
        bot.msg(trigger.nick, "Current API key: " + keyInfo['key'])
        bot.msg(trigger.nick, "Current query count: " + str(keyInfo['queries']))
        bot.msg(trigger.nick, "Key owner: " + keyInfo['owner'])
        bot.msg(trigger.nick, "Thank you, " + trigger.nick + ", and have an awesome day!")
    else:
        bot.msg(trigger.sender, "Enable the NLP subsystem first, fuckwad.")

@module.require_admin
@module.commands('nlp_debug')
def nlp_debug(bot, trigger):
    '''Toggles the state of the debug global.'''
    global debug
    if debug:
        debug = False
        bot.msg(trigger.sender, trigger.nick + ", debug flag is now off. Thanks!")
    else:
        debug = True
        bot.msg(trigger.sender, trigger.nick + ", debug flag is now on. Go fuck a pig.")