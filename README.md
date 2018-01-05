# TweetSentimentParallelization

Multiple python multiprocessing library techniques were experimented with, including Multiprocesses and Multiprocessing pools and were paired with message passing strategies, such as using ZeroMQ PUSH/PULL protocol, in order to try and achieve the best speedup.

Environment used was DigitalOcean quad-core high-CPU VM.

** Instruction **

Tests can be run by running the run_tweets_test.sh bash script in /ParallelProcessing.

** Results **

Average Fetch Time of 500 Tweets:

Serial: 48.424s
Parallel: 12.691s

Average Sentiment Analysis Time:

Serial:0.596s
Parallel:0.183s

Total Program Time:

Serial: 49.959s
Parallel: 14.414s

Speedup Achieved: 3.466

