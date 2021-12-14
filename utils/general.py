import datetime
import requests
import time
import pickle

def printLog(log, end=None):
    '''Generates standard time string and prints out'''

    # Generate time string
    st = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f'[{st}] {log}', end=end)


def checkMode(r):
    '''Check mode of button pushed from redis'''

    p_mode = r.get('mode')
    mode = pickle.loads(p_mode)

    return mode['mode']


def checkInternet():
    '''Check whether the internet is working before continuing with
    the application'''

    retry = True

    while retry:
        try:
            resp = requests.get('http://example.com')
            printLog('🌍 Connected to internet')
            time.sleep(1)
            if resp.status_code/10==20:
                retry = False
        except:
            time.sleep(1)
            printLog('🕐 Waiting for connection...')

    return True


def setLastActive(r):
    '''Set the timestamp of the last time the lights were online
    and active, so that we can turn on the lights intelligently.'''

    # Get current timestamp
    timestamp = int(time.time())

    # printLog('⏰ Setting inactive timestamp')

    # Set it in redis
    r.set('active', timestamp)


def checkLastActive(r):
    '''Checks the time when the lights were last active and return
    a true or false whether they should be turned on.'''

    # Get current timestamp
    timestamp = int(time.time())

    # Get timestamp from redis
    try:
        prev_timestamp = int(r.get('active'))
    except:
        prev_timestamp = int(0)

    # Define the time delta for when we should forcefully turn
    # on the lights
    delta = int(30) # 30s in ms for testing

    if (timestamp-prev_timestamp) > delta:
        printLog('⏰ Previously inactive for a long time, turning on')
        return True
    else:
        printLog('⏰ Not inactive for long period')
        return False
