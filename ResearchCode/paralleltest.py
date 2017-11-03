import multiprocessing as mp
import random
import string
import time
import os

# define a example function
def rand_string(core, length, output):
    """ Generates a random string of numbers, lower- and uppercase chars. """
    #set process to use specific core
    os.sched_setaffinity(0, {core})
    rand_str = ''.join(random.choice(
                        string.ascii_lowercase
                        + string.ascii_uppercase
                        + string.digits)
                   for i in range(length))
    #print the curernt core of the process
    print(open("/proc/{pid}/stat".format(pid=os.getpid()), 'rb').read().split()[-14])
    for j in range(1):
        loop = 1000000
        for x in range(loop):
            temp = (x*x)*(x*x) + (x*x)


    output.put(rand_str)

if __name__ == '__main__':
    mp.freeze_support()

    random.seed(123)

	# Define an output queue
    output = mp.Queue()

	# Setup a list of processes that we want to run
    processes = [mp.Process(target=rand_string, args=(x, 5, output)) for x in range(4)]


    start = time.time()

	# Run processes
    for p in processes:
        p.start()

	# Exit the completed processes
    for p in processes:
        p.join()

    end = time.time()
    print(end - start)

	# Get process results from the output queue
    results = [output.get() for p in processes]

    print(results)
