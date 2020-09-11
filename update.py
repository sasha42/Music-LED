# sasha 2020
import redis
from redis import ConnectionError
import pickle
import os
import time
from Adafruit_IO import *


# connect to redis
try:
    r = redis.from_url(os.environ.get("REDIS_URL"))
    r.ping()
except ConnectionError:
    print('Unable to connect to redis')
    exit()


# connect to adafruit
try:
    # initiate connection
    aio = Client('Sasha_', 'aio_EuTH19hE3tprYuaRdtcS7Nk5JYaI')
    digital = aio.feeds('music-mode')

    # print timestamp for debug
    timestamp = aio.receive_time()

except Exception as error:
    #print(error)
    print('Unable to connect to adafruit')
    exit(0)


if __name__ == "__main__":

    print('Connection successful, running updater')

    while True:
        # pull data from adafruit
        data = aio.receive(digital.key)
        mode = data.value

        # update redis
        mode = {'mode': mode}
        p_mode = pickle.dumps(mode)
        r.set('mode', p_mode)

        #set mode
        time.sleep(1)
