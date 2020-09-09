# music
import pyaudio
import numpy as np
from filters import bassFilter, envelopeFilter, beatFilter

# leds
import time
import math
import asyncio
import datetime
import copy
import flux_led_v3 as flux_led

# connection check
import requests
import time

# redis
import redis
import os
import pickle


# set up redis connection
r = redis.from_url(os.environ.get("REDIS_URL"))


def loadLEDs():
    '''Loads IPs from ip.order.txt into memory, and attemps to connect
    to them.'''

    # Open ip.order.txt and read the IPs of the bulbs. It expects a list
    # of IPs like 192.168.1.1, with one IP per line. The file should end
    # with one empty line.
    filepath = 'ip.order.txt'

    # Define variables
    ips = []
    bulbs = {}
    lastOrder = {}

    with open(filepath) as fp:
        line = fp.readline()
        cnt = 1
        while line:
            line = fp.readline()
            if line.strip() == "":
                continue
            ip = line.strip()

            ips.append(ip)

    # Once the file has been read, the script will attempt to create
    # objects for each bulb.
    print ("Connecting to {}".format(ips))

    for ip in ips:
        try:
            bulb = flux_led.WifiLedBulb(ip)
            bulbs[cnt] = bulb
            lastOrder[cnt] = ""
            cnt = cnt + 1

        except Exception as e:
            print ("Unable to connect to bulb at [{}]: {}".format(ip,e))
            continue
    
    # Return the bulbs that were successfully innitiated
    return bulbs


async def changeColor(bulbs, peak):
    if peak < 255:
        # hack to accomodate for cray cray peak
        a_peak = peak*10
        if a_peak < 255:
            for bulb in bulbs:
                if bulb in [1, 7]:
                    bulbs[bulb].setRgb(a_peak,a_peak,a_peak)
                elif bulb in [5, 6, 3]:
                    bulbs[bulb].setRgb(a_peak,a_peak,a_peak)
                else:
                    bulbs[bulb].setRgb(a_peak,a_peak,a_peak)

    else:
        print(peak)


def processMusic(sample):
    """Process music with @BinaryBrain's filters"""
    # Filter only bass component
    value = bassFilter(sample)

    # Take signal amplitude and filter
    if value < 0:
        value = -value

    # Take signal amplitude and filter
    envelope = envelopeFilter(value)

    # Filter out repeating bass sounds 100 - 180bpm
    beat = beatFilter(envelope)

    #print(beat)

    return int(envelope)


def checkMode():
    '''Check mode of button pushed from redis'''

    p_mode = r.get('mode')
    mode = pickle.loads(p_mode)

    return mode['mode']


def easeInBack(x):
    # actually easeInQuart
    #c1 = 1.70158
    #c3 = c1 + 1

    #return c3 * x * x * x - c1 * x * x
    return x * x * x * x


def setGeneral(bulbs):
    for i in range(254):
        brightness = int(easeInBack(i/254)*254)
        print(brightness)
        loop.run_until_complete(changeColor(bulbs, int(brightness/10)))
        time.sleep(0.01)



def respondToMusic(stream, bulbs):
    # listen to music
    data = np.fromstring(stream.read(CHUNK, exception_on_overflow = False),dtype=np.int16)
    peak=np.average(np.abs(data))*2

    # process value
    value = processMusic(peak)

    last_ten.append(value)
    if len(last_ten) > 1:
        last_ten.pop(0)
    else:
        pass
    avg_last_ten = int(sum(last_ten) / 1)

    # change the color of LEDs
    loop.run_until_complete(changeColor(bulbs, avg_last_ten))


if __name__ == "__main__":
    # wait for there to be an internet connection
    retry = True
    while retry:
        try:
            resp = requests.get('http://example.com')
            print('Connected to internet')
            print(resp.status_code)
            time.sleep(1)
            if resp.status_code/10==20:
                retry = False
        except:
            time.sleep(1)
            print('Waiting for connection...')

    # set up the LEDs
    bulbs = loadLEDs()

    # set up the microphone
    CHUNK = 2**10
    #RATE = 44100

    #p=pyaudio.PyAudio()
    #stream=p.open(format=pyaudio.paInt16,channels=128,rate=RATE,input=True,
    #            frames_per_buffer=CHUNK)

    form_1 = pyaudio.paInt16 # 16-bit resolution
    chans = 1 # 1 channel
    samp_rate = 44100 # 44.1kHz sampling rate
    chunk = 256 # 2^12 samples for buffer
    dev_index = 0 # device index found by p.get_device_info_by_index(ii)

    audio = pyaudio.PyAudio() # create pyaudio instantiation

    # create pyaudio stream
    stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                        input_device_index = dev_index,input = True, \
                        frames_per_buffer=CHUNK)

    # start responding to music
    loop = asyncio.get_event_loop()
    last_ten = [] # avg values across 10 samples
    changed = False

    print('about to start magic')

    while True:
        # check if music mode is on or off
        mode = checkMode()

        # if music mode is on, continue as normal
        if mode == "music":
            changed = False
            respondToMusic(stream, bulbs)

        # if general mode, set general mode, and 
        # then check state again every second
        if mode == "general":
            if changed == False:
                setGeneral(bulbs)
                print('setGeneral placeholders')
                changed = True

            time.sleep(1) # sleep so that we don't ddos redis

        #check_running
        #if running = False
        #    if running_state == 'music':
        #        set_to_general
        #        running_state = 'general'
        #    time.sleep(1) # sleep to avoid going crazy on redis

        #else:
        #    if running_state == 'general':
        #        running_state = 'music'



# this is probably important TODO FIXME
#stream.stop_stream()
#stream.close()
#p.terminate()
