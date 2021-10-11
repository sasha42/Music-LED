import datetime
import requests
import time

def printLog(log, end=None):
    '''Generates standard time string and prints out'''

    # Generate time string
    st = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f'[{st}] {log}', end=end)


def checkMode():
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

