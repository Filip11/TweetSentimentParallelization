import re
import tweepy
from tweepy import OAuthHandler
from textblob import TextBlob
from flask import Flask
import multiprocessing as mp
import time
import os

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
    def parse_tweets(self, fetched_tweets, output):
        print("parse_tweets")
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

        #return tweets, numPtweets, numNtweets
        output.put({"tweets" : tweets})
        output.put({"numPtweets" : numPtweets})
        output.put({"numNtweets" : numNtweets})

    def get_tweets(self, query, max_tweets):
        '''
        Main function to fetch tweets.
        '''
        count = 100
        try:
            fetched_tweets = []
            last_id = -1
            while len(fetched_tweets) < max_tweets:
                # call twitter api to fetch tweets
                new_tweets = self.api.search(q=query, count=count, max_id=str(last_id - 1))
                time.sleep(1)
                if not new_tweets:
                    break

                for tweet in new_tweets:
                    #remove tweet if retweet count is greater than 0
                    if tweet.retweet_count > 0:
                        new_tweets.remove(tweet)

                fetched_tweets.extend(new_tweets)
                print("fetched " + str(len(fetched_tweets)))
                if len(new_tweets) > 0:
                    last_id = new_tweets[-1].id
 
            return fetched_tweets
 
        except tweepy.TweepError as e:
            # print error (if any)
            print("Error : " + str(e))

##############################################
# End of TwitterClient
##############################################


respMain=""
def addline(aLine):
    global respMain
    respMain=respMain+"\r\n<br />"+aLine
    return

def worker(core, fetched_tweets, output):
    #set process to use specific core, does not work on Windows
    #os.sched_setaffinity(0, {core})
    TwitterClient().parse_tweets(fetched_tweets, output)
    print("process: " + str(core) + " done")

def main():

    tweets = []
    fetched_tweets = None
    numPtweets = 0
    numNtweets = 0
    max_tweets = 100
    num_processes = 4

    use_saved_tweets = False
    save_tweets = True
    tweet_file = "tweets.txt"

    # calling function to get tweets
    if use_saved_tweets:
            with open(tweet_file, 'r') as f:
                fetched_tweets = list(f.read())
        elif save_tweets:
            # creating object of TwitterClient Class
            api = TwitterClient()
            fetched_tweets = api.get_tweets(query = 'Engineer', max_tweets = max_tweets)
            with open(tweet_file, 'w') as f:
                f.write(str(str(fetched_tweets).encode("utf-8")))

    if fetched_tweets:

        if len(fetched_tweets) > max_tweets:
            fetched_tweets = fetched_tweets[:max_tweets-1]

        # Define an output queue
        output = mp.Queue()

        # number of tweets per process
        tweets_per_process = len(fetched_tweets)/num_processes
        print("tweets per process " + str(tweets_per_process))

        # Setup a list of processes
        processes = []
        for x in range(num_processes):
            lower_limit = int(x*tweets_per_process)
            upper_limit = int(((x+1)*tweets_per_process) - 1)
            #print("limit " + str(lower_limit) + "," + str(upper_limit))
            if x == num_processes-1:
                tweets_subset = fetched_tweets[lower_limit:]
            else:
                tweets_subset = fetched_tweets[lower_limit:upper_limit]
            processes.append(mp.Process(target=worker, args=(x, tweets_subset, output)))

        #start timer
        start = time.time()

        # Run processes
        for p in processes:
            p.start()

        # Exit the completed processes
        for p in processes:
            print("joining")
            p.join()

        #end time
        end = time.time()
        print(end - start)

    # Get process results from the output queue
        while not output.empty():
            item = output.get()
            if "tweets" in item:
                tweets.extend(item["tweets"])
            elif "numPtweets" in item:
                numPtweets += item["numPtweets"]
            elif "numNtweets" in item:
                numNtweets += item["numNtweets"]

    # parse tweets, and get number of positive and negative tweets
    # tweets, numPtweets, numNtweets = api.parse_tweets(fetched_tweets)

    addline("total "+str(len(tweets)))
    # percentage of positive tweets
    if len(tweets) > 0:
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