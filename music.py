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
    # of IPs like 192.168.1.1, with one IP per line. The file should start
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
    print (f"💡 Connected to {len(ips)} LED strips")

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
    '''Change the color of LEDs based on the peak value'''

    if peak < 255:
        # hack to accomodate for cray cray peak
        a_peak = peak*10
        if a_peak < 255:
            for bulb in bulbs:
                bulbs[bulb].setRgb(a_peak,a_peak,a_peak)

    else:
        print(peak)


def processMusic(sample):
    '''Process music with @BinaryBrain's filters'''

    # Filter only bass component
    value = bassFilter(sample)

    # Take signal amplitude and filter
    if value < 0:
        value = -value

    # Take signal amplitude and filter
    envelope = envelopeFilter(value)

    # Filter out repeating bass sounds 100 - 180bpm
    beat = beatFilter(envelope)

    return int(envelope)


def checkMode():
    '''Check mode of button pushed from redis'''

    p_mode = r.get('mode')
    mode = pickle.loads(p_mode)

    return mode['mode']


def easeOutCubic(x):
    '''Easing function'''

    return 1 - pow(1 - x, 3)


def setGeneral(bulbs):
    '''Set general lighting for when the music mode is disabled'''

    # use an easing function to smoothyl turn on the LEDs
    for i in range(255):
        brightness = int(easeOutCubic(i/254)*254)
        loop.run_until_complete(changeColor(bulbs, int(brightness/10)))
        time.sleep(0.01)


def respondToMusic(stream, bulbs):
    '''Respond to every chunk read by the audio input'''

    # listen to music
    data = np.frombuffer(stream.read(chunk, exception_on_overflow = False), dtype=np.int16)
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


def checkInternet():
    '''Check whether the internet is working before continuing with
    the application'''

    retry = True

    while retry:
        try:
            resp = requests.get('http://example.com')
            print('🌍 Connected to internet')
            time.sleep(1)
            if resp.status_code/10==20:
                retry = False
        except:
            time.sleep(1)
            print('🕐 Waiting for connection...')

    return True

def loadMicrophone():
    '''Load microphone by setting it up and creating a pyaudio
    stream that can be read.'''

    # Configure options for audio capture
    chunk = 2**10
    form_1 = pyaudio.paInt16 # 16-bit resolution
    chans = 1 # 1 channel
    samp_rate = 44100 # 44.1kHz sampling rate
    chunk = 256 # 2^12 samples for buffer
    dev_index = 0 # device index found by p.get_device_info_by_index(ii)

    # Create pyaudio instantiation
    audio = pyaudio.PyAudio() 

    # Create pyaudio stream
    stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                        input_device_index = dev_index,input = True, \
                        frames_per_buffer=chunk)

    return stream, chunk


if __name__ == "__main__":
    # Wait for there to be an internet connection
    checkInternet()

    # Set up the LEDs
    bulbs = loadLEDs()

    # Set up the microphone
    stream, chunk = loadMicrophone()

    # start responding to music
    loop = asyncio.get_event_loop()
    last_ten = [] # avg values across 10 samples
    changed = True
    last_mode = 'start'
    count = 0
    timestamp = 0

    while True:
        # check if music mode is on or off
        mode = checkMode()
        if mode != last_mode:
            changed = True
            last_mode = mode

        # if music mode is on, continue as normal
        if mode == "music":
            if changed == True:
                print('🥁 Setting music mode')
                changed = False

            respondToMusic(stream, bulbs)

        # if general mode, set general mode, and 
        # then check state again every second
        if mode == "general":
            if changed == True:
                print('🔦 Setting general lighting mode')
                setGeneral(bulbs)
                changed = False

            time.sleep(1) # sleep so that we don't ddos redis

        # do stuff every 100 steps
        count += 1

        if count > 100:
            time_elapsed = time.time()-timestamp
            print(f'   Current FPS: {int(100/time_elapsed)}', end='\r') # debug framerate
            timestamp = time.time()
            count = 0

# this is probably important TODO FIXME
#stream.stop_stream()
#stream.close()
#p.terminate()
