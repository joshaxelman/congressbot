__author__ = 'jaxelman'
import yaml
import tweepy
import json
import time
import sqlite3

class CongressBot:

    def __init__(self):
        with open('env.yaml', 'r') as f:
            config = yaml.load(f)
        self.db = sqlite3.connect('data/congress.db', isolation_level=None)
        self.twitter_replies(config)
        self.db.close()

    def get_state(self, zipcode):
        cur = self.db.cursor()
        t = (zipcode,)
        try:
            cur.execute('SELECT state FROM zipcodes WHERE zip=?', t)
            return cur.fetchone()[0]
        except Exception, e:
            print " - zipcode not found %s" % e

    def get_senators(self, state):
        cur = self.db.cursor()
        t = (state,)
        try:
            cur.execute('SELECT * FROM congress WHERE state_short=?', t)
            return cur.fetchall()
        except Exception, e:
            print " - state not found %s" % e

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

            time.sleep(15)

CongressBot()

