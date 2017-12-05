import re
import tweepy
from tweepy import OAuthHandler
from textblob import TextBlob
from flask import Flask, request
import multiprocessing as mp
import time
import os
import pickle
from datetime import datetime, timedelta
import argparse
import zmq

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
    def parse_tweets(self, fetched_tweets, output,test,core):
        # print("parse_tweets")
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


        if test == "zeromq":
            context = zmq.Context()
            zmq_pushsocket1 = context.socket(zmq.PUSH)
            port = str(5557+core)
            zmq_pushsocket1.connect("tcp://0.0.0.0:"+port)
            zmq_pushsocket1.send_json({"tweets" : tweets})
            zmq_pushsocket1.send_json({"numPtweets" : numPtweets})
            zmq_pushsocket1.send_json({"numNtweets" : numNtweets})

        else:
            #return tweets, numPtweets, numNtweets
            temp_results = []
            temp_results.append({"tweets" : tweets})
            temp_results.append({"numPtweets" : numPtweets})
            temp_results.append({"numNtweets" : numNtweets})
            output.send(temp_results)


        '''output.put({"tweets" : tweets})
        output.put({"numPtweets" : numPtweets})
        output.put({"numNtweets" : numNtweets})'''

    def get_tweets(self, query, max_tweets, date = None):
        '''
        Main function to fetch tweets.
        '''
        count = 100
        try:
            fetched_tweets = []
            last_id = -1
            while len(fetched_tweets) < max_tweets:
                # call twitter api to fetch tweets
                new_tweets = self.api.search(q=query, count=count, max_id=str(last_id), until=date)
                #time.sleep(1)
                if not new_tweets:
                    break

                for tweet in new_tweets:
                    #remove tweet if retweet count is greater than 0
                    if tweet.retweet_count > 0:
                        new_tweets.remove(tweet)

                fetched_tweets.extend(new_tweets)
                # print("fetched " + str(len(fetched_tweets)))
                if len(new_tweets) > 0:
                    last_id = new_tweets[-1].id
 
            return fetched_tweets
 
        except tweepy.TweepError as e:
            print("Error : " + str(e))

##############################################
# End of TwitterClient
##############################################


respMain=""
def addline(aLine):
    global respMain
    respMain=respMain+"\r\n<br />"+aLine
    return

###########################################
# worker method for processes to get/parse tweets
###########################################
def worker(core, tweet_limit, fetched_tweets, output, assign_core,test):
    #set process to use specific core, does not work on Windows
    if assign_core:
        os.sched_setaffinity(0, {core})
    if not fetched_tweets:
        fetched_tweets = []
    if len(fetched_tweets) <= 0:
        start = time.time()
        query = 'Engineer'
        date = datetime.now() - timedelta(days=(core*2))
        date = date.strftime("%Y-%m-%d")
        #print("date: " + date)
        fetched_tweets = TwitterClient().get_tweets(query, tweet_limit, date)
        end = time.time()
        print("fetching " + str(core) + ": " + str(end-start))
    if len(fetched_tweets) > tweet_limit:
        fetched_tweets = fetched_tweets[:int(tweet_limit)]
    start = time.time()
    TwitterClient().parse_tweets(fetched_tweets, output,test,core)
    end = time.time()
    print("processing " + str(core) + ": " + str(end-start))

# starts the processes and times them
def run_processes(processes, parent_recv,test):

    results = []
    #start timer
    start = time.time()
    '''
    if test == "pool":
        pool = mp.Pool(processes =processes)
        for x in range(processes):
            pool.apply_async(worker,args=(x,parent_recv,[],None,None,test)) 

        pool.close()
    '''

    # Run processes
    for p in processes:
        p.start()

    if test == "zeromq":
        for i in range(3):
            results.append(parent_recv.recv_json())

    else:
        # Get process results from output pipe
        for i in range(len(processes)):
            results.extend(parent_recv.recv())

    # Exit the completed processes
    for p in processes:
        # print("joining")
        p.join()

    #end time
    end = time.time()
    print('total processing time: ' + str(end - start))

    return results

# start pool processing
def run_pool(processes,tweets_per_process,assign_core):
    print("testing pool")
    results = []

    start = time.time()
    # Define pipe to send data from parent and child processes
    parent_recv, child_send = mp.Pipe()


    pool = mp.Pool(processes =processes)
    for x in range(processes):
        pool.apply_async(worker,args=(x,tweets_per_process,[],child_send,assign_core,"pool")) 
    for i in range(processes):
        results.extend(parent_recv.recv())
    
    pool.close()

    end = time.time()
    print('total processing time: ' + str(end - start))

    return results

# add lines of results to the webpage
def display_results(results):
    tweets = []
    numPtweets = 0
    numNtweets = 0
    #get number of positive and negative tweets
    for item in results:
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

def main(test, parallel_get_tweets, num_processes, max_tweets, use_saved, save_tweets, filename, query, assign_core):

    results = []
    fetched_tweets = None

    #start total application timer
    start_app_timer = time.time()

    # get all of the tweets before processing
    if not parallel_get_tweets:
        fetch_start_timer = time.time()
        if use_saved:
                with open(tweet_file, 'rb') as f:
                    fetched_tweets = pickle.load(f)
        elif save_tweets: # fetch and save tweets to text file
            api = TwitterClient()
            fetched_tweets = api.get_tweets(query = query, max_tweets = max_tweets)
            with open(tweet_file, 'wb') as f:
                pickle.dump(fetched_tweets,f)
        else: # fetch tweets from online
            api = TwitterClient()
            fetched_tweets = api.get_tweets(query = query, max_tweets = max_tweets)
            # print("done fetching")

        fetch_end_timer = time.time()
        print("Total fetching: " + str(fetch_end_timer - fetch_start_timer))

        #process the pre fetched tweets from saved or query
        if fetched_tweets:

            if len(fetched_tweets) > max_tweets:
                fetched_tweets = fetched_tweets[:max_tweets-1]

            # Define pipe to send data from parent and cild processes
            parent_recv, child_send = mp.Pipe()

            # number of tweets per process
            tweets_per_process = len(fetched_tweets)/num_processes
            print("tweets per process " + str(tweets_per_process))

            # Setup a list of processes
            processes = []
            for x in range(num_processes):
                lower_limit = int(x*tweets_per_process)
                upper_limit = int(((x+1)*tweets_per_process) - 1)
                #print("limit " + str(lower_limit) + "," + str(upper_limit))
                tweets_subset = []
                if x == num_processes-1:
                    tweets_subset = fetched_tweets[lower_limit:]
                else:
                    tweets_subset = fetched_tweets[lower_limit:upper_limit]
                processes.append(mp.Process(target=worker, args=(x, tweets_per_process, tweets_subset, child_send, assign_core,test)))

            results = run_processes(processes, parent_recv,test)

    # get tweets in parallel processes
    elif parallel_get_tweets:

        if test == 'pipe':
            # Define pipe to send data from parent and child processes
            parent_recv, child_send = mp.Pipe()

            # number of tweets per process
            tweets_per_process = max_tweets/num_processes
            print("tweets per process " + str(tweets_per_process))

            # Setup a list of processes
            processes = []
            for x in range(num_processes):
                tweets_subset = []
                processes.append(mp.Process(target=worker, args=(x, tweets_per_process, tweets_subset, child_send, assign_core,test)))

            results = run_processes(processes, parent_recv,test)

        elif test == 'pool':

            # number of tweets per process
            tweets_per_process = max_tweets/num_processes
            print("tweets per process " + str(tweets_per_process))

            results = run_pool(num_processes, tweets_per_process,assign_core)


        elif test == 'zeromq':
            context = zmq.Context()
            zmq_pullsocket1 = context.socket(zmq.PULL)
            zmq_pullsocket1.bind("tcp://0.0.0.0:5557")
            zmq_pullsocket1.bind("tcp://0.0.0.0:5558")
            zmq_pullsocket1.bind("tcp://0.0.0.0:5559")
            zmq_pullsocket1.bind("tcp://0.0.0.0:5560")

            # number of tweets per process
            tweets_per_process = max_tweets/num_processes
            print("tweets per process " + str(tweets_per_process))

            # Setup a list of processes
            processes = []
            for x in range(num_processes):
                tweets_subset = []
                processes.append(mp.Process(target=worker, args=(x, tweets_per_process, tweets_subset,None,assign_core,test)))



            results = run_processes(processes, zmq_pullsocket1,test)


    display_results(results)

    #end total application timer
    end_app_timer = time.time()
    print('total time: ' + str(end_app_timer - start_app_timer))

    global respMain
    genRank = respMain
    respMain = ""
    return genRank

# convert string to boolean
def strToBool(value):
  return value.lower() in ("yes", "true", "t", "1")

@app.route('/', methods=('get', 'post'))
def hello_world():
    #default test values
    test = None
    parallel = False
    num_processes = 1
    max_tweets = 5000
    use_saved = False
    save_tweets = False
    filename = 'tweets.txt'
    query = 'Engineer'
    assign_core = False

    if 'test' in request.args:
        test = request.args.get('test')
    if 'parallel' in request.args:
        parallel = strToBool(request.args.get('parallel'))
    if 'processes' in request.args:
        num_processes = int(request.args.get('processes'))
    if 'max_tweets' in request.args:
        max_tweets = int(request.args.get('max_tweets'))
    if 'use_saved' in request.args:
        use_saved = strToBool(request.args.get('use_saved'))
    if 'save_tweets' in request.args:
        save_tweets = strToBool(request.args.get('save_tweets'))
    if 'filename' in request.args:
        filename = request.args.get('filename')
    if 'query' in request.args:
        query = request.args.get('query')
    if 'assign_core' in request.args:
        assign_core = strToBool(request.args.get('assign_core'))

    return main(test,parallel,num_processes,max_tweets,use_saved,save_tweets, filename, query, assign_core)

if __name__ == "__main__":
    # calling main function
    app.run(host='0.0.0.0', port=3333)