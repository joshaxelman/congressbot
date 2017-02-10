__author__ = 'jaxelman'
import yaml
import tweepy
import json
import time
import os
import sqlite3

class CongressBot:

    def __init__(self):
        path = os.path.dirname(os.path.abspath(__file__))
        with open(path + '/env.yaml', 'r') as f:
            config = yaml.load(f)
        self.db = sqlite3.connect(path + '/data/congress.db', isolation_level=None)
        self.twitter_replies(config)
        #self.get_house_rep('90048')
        self.db.close()

    def get_state(self, zipcode):
        cur = self.db.cursor()
        t = (zipcode,)
        try:
            cur.execute("SELECT state FROM zipcodes WHERE zip=?", t)
            return cur.fetchone()[0]
        except Exception, e:
            print " - zipcode not found %s" % e

    def get_senators(self, state):
        cur = self.db.cursor()
        t = (state,)
        try:
            cur.execute("SELECT * FROM congress WHERE state_short=?", t)
            return cur.fetchall()
        except Exception, e:
            print " - state not found %s" % e

    def get_house_rep(self, zip):
        cur = self.db.cursor()
        twitter_handles = []
        t = (zip,)
        cur.execute("SELECT * FROM house_rep WHERE zip=?", t)
        reps = cur.fetchall()
        for rep in reps:
            #print(rep[1])
            split_name = rep[1].split()
            firstname = split_name[0]
            lastname = split_name[len(split_name)-1]
            search_name = "%" + firstname + ' ' + lastname + "%"
            cur.execute("SELECT name, twitter_handle FROM house_twitter WHERE name like ?", (search_name, ))
            twitter_handles.append(cur.fetchone())
        return twitter_handles

    def twitter_replies(self, config):
        print (config)
        auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
        auth.set_access_token(config['access_token'], config['token_secret'])
        api = tweepy.API(auth)
        sentTweets = []
        #on first start find the last sent tweet
        me = api.me()
        last_sent = me._json['status']['in_reply_to_status_id']
        sentTweets.append(last_sent)
        print json.dumps(me._json, sort_keys=True, indent=4, separators=(',', ': '))

        while True:
            replies = api.mentions_timeline(wait_on_rate_limit=True, since_id=last_sent)
            for tweet in replies:
                if tweet.id not in set(sentTweets):
                    user = tweet._json['user']['screen_name']
                    sentTweets.append(tweet.id)
                    zipcode = tweet.text.lower().replace('@congress_bot ', '')
                    if not zipcode.isdigit():
                        try:
                            message = '@' + user + ' please use 5 digit zip code only'
                            #api.update_status(message, tweet.id)
                            print(message)
                        except Exception, e:
                            print " - failed (maybe a duplicate?): %s" % e
                    else:
                        print (zipcode)
                        print('tweet id: ' + str(tweet.id))
                        print(tweet._json['user']['screen_name'])
                        results = self.get_senators(self.get_state(zipcode))
                        reply = 'Demand action from '
                        for row in results:
                            reply = reply + row[3]
                            if row[4]:
                                reply = reply + ' ' + row[4]
                            if row[5]:
                                reply = reply + ' ' + row[5]
                            if row[6]:
                                reply = reply + ' ' + row[6]
                            reply = reply + ' '
                        message = '@' + user + ' ' + reply
                        if len(results) > 0:
                            try:
                                api.update_status(message, tweet.id)
                                print(message)
                            except Exception, e:
                                print " - failed (maybe a duplicate?): %s" % e
                        else:
                            print('Not Found')

                        # get the House Reps, send a second tweet
                        twitter_handles = self.get_house_rep(zipcode)
                        reply = 'Demand action from your Reps '
                        for rep in twitter_handles:
                            if rep:
                                has_rep = True
                                print(rep[0] + ' ' + rep[1])
                                reply = reply + rep[0] + ' ' + rep[1]
                        message = '@' + user + ' ' + reply
                        if has_rep:
                            try:
                                api.update_status(message, tweet.id)
                                print(message)
                            except Exception, e:
                                print " - failed (maybe a duplicate?): %s" % e
                        else:
                            print('Not Found')

            time.sleep(15)

CongressBot()

