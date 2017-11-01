import re
import tweepy
from tweepy import OAuthHandler
from textblob import TextBlob
from flask import Flask
app = Flask(__name__)
 
class TwitterClient(object):
    '''
    Generic Twitter Class for sentiment analysis.
    '''
    def __init__(self):
        '''
        Class constructor or initialization method.
        '''
        # keys and tokens from the Twitter Dev Console
        consumer_key = 'hfwpuUy8AbfQEWop6SmtLu0Vo'
        consumer_secret = 'EOcwVK6IGxd1NWAqdzVuOygcXdMHWbG7AZREg2uVwkd8a55c8e'
        access_token = '578964539-Z8YzO0mx022PoKpD49GPgsqvOjEYSqsxP0GS5yaY'
        access_token_secret = 'mMNBzr6GCFzeCjEDyTbquxChi2qg0vvc3xL6Yov0IVsOl'
 
        # attempt authentication
        try:
            # create OAuthHandler object
            self.auth = OAuthHandler(consumer_key, consumer_secret)
            # set access token and secret
            self.auth.set_access_token(access_token, access_token_secret)
            # create tweepy API object to fetch tweets
            self.api = tweepy.API(self.auth)
        except:
            print("Error: Authentication Failed")
 
    def clean_tweet(self, tweet):
        '''
        Utility function to clean tweet text by removing links, special characters
        using simple regex statements.
        '''
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())
 
    def get_tweet_sentiment(self, tweet):
        '''
        Utility function to classify sentiment of passed tweet
        using textblob's sentiment method
        '''
        # create TextBlob object of passed tweet text
        analysis = TextBlob(self.clean_tweet(tweet))
        # set sentiment
        if analysis.sentiment.polarity > 0:
            return 'positive'
        elif analysis.sentiment.polarity == 0:
            return 'neutral'
        else:
            return 'negative'
 
    ###############################################################################################
    # parse_tweets can be the "worker" method for the processes
    ###############################################################################################
    def parse_tweets(self, fetched_tweets):
        tweets = []
        numPtweets = 0
        numNtweets = 0
        # parsing tweets one by one
        for tweet in fetched_tweets:
            # empty dictionary to store required params of a tweet
            parsed_tweet = {}

            # saving text of tweet
            parsed_tweet['text'] = tweet.text
            # saving sentiment of tweet
            parsed_tweet['sentiment'] = self.get_tweet_sentiment(tweet.text)
            
            if parsed_tweet['sentiment'] == 'positive':
                numPtweets += 1
            elif parsed_tweet['sentiment'] == 'negative':
                numNtweets += 1

            tweets.append(parsed_tweet)

        print(numPtweets)
        return tweets, numPtweets, numNtweets

    def get_tweets(self, query, count):
        '''
        Main function to fetch tweets and parse them.
        '''
 
        try:
            max_tweets = 1000
            fetched_tweets = []
            last_id = -1
            while len(fetched_tweets) < max_tweets:
                count = max_tweets - len(fetched_tweets)
                # call twitter api to fetch tweets
                new_tweets = self.api.search(q=query, count=count, max_id=str(last_id - 1))
                if not new_tweets:
                    break

                for tweet in new_tweets:
                    #remove tweet if retweet count is greater than 0
                    if tweet.retweet_count > 0:
                        new_tweets.remove(tweet)

                fetched_tweets.extend(new_tweets)
                last_id = new_tweets[-1].id
 
            # return parsed tweets, number of posistive and negative tweets
            tweets, numPtweets, numNtweets = self.parse_tweets(fetched_tweets)
            return tweets, numPtweets, numNtweets
 
        except tweepy.TweepError as e:
            # print error (if any)
            print("Error : " + str(e))

respMain=""
def addline(aLine):
    global respMain
    respMain=respMain+"\r\n<br />"+aLine
    return
 
def main():
    # creating object of TwitterClient Class
    api = TwitterClient()
    # calling function to get tweets
    tweets, numPtweets, numNtweets = api.get_tweets(query = 'Engineer', count = 5000)
    addline("total "+str(len(tweets)))
    # percentage of positive tweets
    addline("positive "+str(float(numPtweets)/float(len(tweets))))    
    addline("Positive tweets percentage: {}".format(100*numPtweets/len(tweets)))
    # percentage of negative tweets
    addline("negative "+str(float(numNtweets)/float(len(tweets))))    
    addline("Negative tweets percentage: {}".format(100*numNtweets/len(tweets)))

    addline("========================================================================")
    for tweet in tweets:
        addline(tweet['text'])
    addline("========================================================================")
    global respMain
    genRank = respMain
    respMain = ""
    return genRank
@app.route('/')
def hello_world():
    return main()
if __name__ == "__main__":
    # calling main function
    app.run(host='0.0.0.0', port=3333)