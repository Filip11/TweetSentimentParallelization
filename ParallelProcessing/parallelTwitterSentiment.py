import re
import tweepy
from tweepy import OAuthHandler
from textblob import TextBlob
from flask import Flask
import multiprocessing as mp
from multiprocessing import Pool
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
 
    def parse_tweets(self,fetched_tweets):

        tweets = []
        numPtweets = 0
        numNtweets = 0
        print("parsed_tweet",len(fetched_tweets))
        # parsing tweets one by one
        for tweet in fetched_tweets:
            # empty dictionary to store required params of a tweet
            parsed_tweet = {}

            # saving text of tweet
            parsed_tweet['text'] = tweet.text
            # saving sentiment of tweet
            parsed_tweet['sentiment'] = self.get_tweet_sentiment(tweet.text)
            # appending parsed tweet to tweets list
            '''
            if tweet.retweet_count > 0:
                # if tweet has retweets, ensure that it is appended only once
                if parsed_tweet not in tweets:
                    tweets.append(parsed_tweet)
            else:
                '''

            if parsed_tweet['sentiment'] == 'positive':
                numPtweets += 1
            elif parsed_tweet['sentiment'] == 'negative':
                numNtweets += 1
            tweets.append(parsed_tweet)

        # return parsed tweets
        return [tweets,numPtweets,numNtweets]

    def get_tweets(self, query, max_tweets):
        '''
        Main function to fetch tweets.
        '''
        count = 100
        try:
            fetched_tweets = []
            last_id = -1
            while len(fetched_tweets) < max_tweets:
                print(len(fetched_tweets))
                # call twitter api to fetch tweets
                new_tweets = self.api.search(q=query, count=count, max_id=str(last_id))
                #time.sleep(1)
                if not new_tweets:
                    break

                for tweet in new_tweets:
                    #remove tweet if retweet count is greater than 0
                    if tweet.retweet_count > 0:
                        new_tweets.remove(tweet)

                if (len(fetched_tweets) + len(new_tweets) > max_tweets):
                    fetched_tweets.extend(new_tweets[:max_tweets-len(fetched_tweets)])
                else:
                    fetched_tweets.extend(new_tweets)
                print("fetched " + str(len(fetched_tweets)))
                if len(new_tweets) > 0:
                    last_id = new_tweets[-1].id
 
            return fetched_tweets
 
        except tweepy.TweepError as e:
            # print error (if any)
            print("Error : " + str(e))

            #print("len fetched: " + str(len(fetched_tweets)))

respMain=""
def addline(aLine):
    global respMain
    respMain=respMain+"\r\n<br />"+aLine
    return
def worker(core, fetched_tweets):
    #set process to use specific core, does not work on Windows
    #os.sched_setaffinity(0, {core})
    print("process: " + str(core) + " done")
    return TwitterClient().parse_tweets(fetched_tweets)
    

def appendTweets(tweets):
    global results
    global ptweets
    global ntweets
    results.extend(tweets[0])
    ptweets +=tweets[1]
    ntweets +=tweets[2]
 
def main():
    fetched_tweets = None
    global results
    global ptweets
    global ntweets
    results = []
    ptweets = 0
    ntweets = 0
    # creating object of TwitterClient Class
    api = TwitterClient()
    # calling function to get tweets
    fetched_tweets = api.get_tweets(query = 'Engineer', max_tweets = 200)

    pool = mp.Pool(processes =4)
    for x in range(4):
        pool.apply_async(worker,args=(x,fetched_tweets[x*50:(x+1)*50]),callback=appendTweets) 

    pool.close()
    pool.join()
    
    
    #tweets = api.parse_tweets(fetched_tweets = fetched_tweets)

    addline("total: "+str(len(results)))
    #ptweets = [tweet for tweet in tweets if tweet['sentiment'] == 'positive']
    addline("positive: "+str(float(ptweets)/float(len(results))))
    # percentage of positive tweets
    addline("Positive tweets percentage: "+ str(100*(ptweets)/len(results)))
    # picking negative tweets from tweets
    #ntweets = [tweet for tweet in tweets if tweet['sentiment'] == 'negative']
    # percentage of negative tweets
    addline("negative: "+str(float(ntweets)/float(len(results))))    
    addline("Negative tweets percentage: "+str(100*(ntweets)/len(results)))
    #percentage of neutral tweets
    addline("Neutral tweets percentage: "+str(100*(len(results) - ntweets - ptweets)/len(results)))
    addline("========================================================================")
    for tweet in results:
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