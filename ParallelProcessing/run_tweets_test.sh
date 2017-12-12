
##### Functions #####
function start_server {
	python3 parallelTweetSentiment_Strategies.py &
	while true; do
	    nc 127.0.0.1 3333 < /dev/null
	    if [ $? -eq 0 ]; then
	        break
	    fi
	    sleep 1
	done
	sleep 1
	echo "server is up"
}

function kill_server {
	ps aux  |  grep -i python  |  awk '{print $2}'  |  xargs sudo kill -9
	sleep 1
	echo "server is shutdown"
}

##### Run tests #####
kill_server
echo "starting tests"

### Test 1 ###
start_server

test1_date=`date '+%Y_%m_%dT%H_%M_%S'`

curl -X GET "http://127.0.0.1:3333/?max_tweets=5000&parallel=true&processes=4&assign_core=true&test=pipe" -m 45 > test1_$test1_date.log

### Test 2 ### Uncomment curl command to try pool test
#start_server

#curl -X GET "http://127.0.0.1:3333/?max_tweets=5000&parallel=true&processes=4&assign_core=true&test=pool" -m 45 > test2_$test1_date.log

#kill_server

### Test 3 ### Uncomment curl command to try ZeroMQ test
#start_server

#curl -X GET "http://127.0.0.1:3333/?max_tweets=5000&parallel=true&processes=4&assign_core=true&test=zeromq" -m 45 > test3_$test1_date.log

#Baseline
curl -X GET "http://127.0.0.1:3333/?max_tweets=5000&parallel=false&processes=1&assign_core=False&test=default" -m 60 > test4_$test1_date.log

kill_server