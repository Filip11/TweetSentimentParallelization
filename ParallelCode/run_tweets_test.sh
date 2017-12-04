
##### Functions #####
function start_server {
	python3 twitterSentiment_parallel.py &
	while true; do
	    nc 127.0.0.1 3333 < /dev/null
	    if [ $? -eq 0 ]; then
	        break
	    fi
	    sleep 1
	done
	echo "server is up"
}

function kill_server {
	ps aux  |  grep -i python  |  awk '{print $2}'  |  xargs sudo kill -9
	echo "server is shutdown"
}

##### Run tests #####
echo "starting tests"

### Test 1 ###
start_server

curl -X GET http://127.0.0.1:3333/?max_tweets=1000&parallel=true&processes=4&assign_core=false&test=pipe -m 25

kill_server

### Test 2 ###
start_server

curl -X GET http://127.0.0.1:3333/?max_tweets=1000 -m 25

kill_server

### Test 3 ###
start_server

curl -X GET http://127.0.0.1:3333/?max_tweets=1000 -m 25

kill_server