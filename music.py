# music
import pyaudio
import alsaerror
import sys
import io
import numpy as np
from filters import bassFilter, envelopeFilter, beatFilter

# leds
import time
import math
import asyncio
import datetime
import copy
import flux_led_v4 as flux_led

# connection check
import requests
import time
import datetime

# redis
import redis
import os
import pickle

# experimental
from bpm_detection import bpm_detector
#from devices import getDevices, simpleList
import devices


# set up redis connection
r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# pls don't judge my global variables
avg_last_ten = []
last_ten_ts = 0
global_hue = 150
settingTime = 0
everyOther = True
every60k = 0
originalColors = []
offset_values = []

def printLog(log, end=None):
    '''Generates standard time string and prints out'''

    # Generate time string
    st = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f'[{st}] {log}', end=end)


def getBulbState(bulbs):
    """Gets bulb state"""
    for bulb in bulbs:
        bulbs[bulb].refreshState()
        #print(vars(bulbs[bulb]))
        bulb_ip = bulbs[bulb].ipaddr

        bulb_state_raw = bulbs[bulb]._WifiLedBulb__state_str

        #bulb_state = bulb_state_raw.split('(')[1].split(')')[0]

        #bulb_colors = bulb_state.split(', ')
        print(vars(bulbs[bulb]))
        #print(bulb_ip, bulb_state_raw)
    printLog('-----')
    

def hsv2rgb(h, s, v):
    h = float(h)
    s = float(s)
    v = float(v)
    h60 = h / 60.0
    h60f = math.floor(h60)
    hi = int(h60f) % 6
    f = h60 - h60f
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r, g, b = 0, 0, 0
    if hi == 0: r, g, b = v, t, p
    elif hi == 1: r, g, b = q, v, p
    elif hi == 2: r, g, b = p, v, t
    elif hi == 3: r, g, b = p, q, v
    elif hi == 4: r, g, b = t, p, v
    elif hi == 5: r, g, b = v, p, q
    r, g, b = int(r * 255), int(g * 255), int(b * 255)
    return r, g, b


async def changeColor(bulbs, peak):
    global global_hue
    global settingTime
    global everyOther
    global every60k
    global offset_values

    if peak < 255:
        # hack to accomodate for cray cray peak
        a_peak = peak*10
        #if a_peak > 120:
            #print(global_hue)
            #global_hue += 30

        thresh = 200

        if (everyOther == True and a_peak > thresh):
            everyOther = False
            global_hue += 20
        elif (everyOther == False and a_peak > thresh):
            everyOther = True
            global_hue -= 20

        every60k += 1

        if every60k > 600:
            every60k = 1
            #print(f'change hue {global_hue}\n')
            global_hue += 10

        if a_peak < 255:
            # set up offset
            offset_length = 1
            offset_values.append(a_peak)
            if len(offset_values) > offset_length:
                del offset_values[0]
            else:
                pass

            for bulb in bulbs:
                # set minimum brightness
                if offset_values[0] < 80:
                    a_peak = 20
                else:
                    a_peak = offset_values[0]

                # normalize peak 
                normalized_peak = a_peak/255
                #r, g, b = hsv2rgb(global_hue, 1, normalized_peak)
                r, g, b = hsv2rgb(1, 1, normalized_peak)

                settingTime = time.time()
                if settingTime > time.time()+1:
                    print(settingTime)
                    print(time.time()+1)
                    print('-----------------')
                    print('bug')

                # set color on lights
                bulbs[bulb].setRgb(r, g, b)

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
    #return int(beat)


def checkMode():
    '''Check mode of button pushed from redis'''

    p_mode = r.get('mode')
    mode = pickle.loads(p_mode)

    return mode['mode']


def easeOutCubic(x):
    return 1 - pow(1 - x, 3)


def setGeneral(bulbs):
    #for i in range(255):
    #    brightness = int(easeOutCubic(i/254)*254)
    #    loop.run_until_complete(changeColor(bulbs, int(brightness/10)))
    #    time.sleep(0.01)

    for bulb in bulbs:
        bulbs[bulb].setRgb(3, 1, 0)


def respondToMusic(stream, bulbs):
    global avg_last_ten
    global last_ten_ts

    # listen to music
    data = np.frombuffer(stream.read(chunk, exception_on_overflow = False),dtype=np.int16)
    #arr = data
    #print(data.shape)
    
    # Printing type of arr object
    #print("Array is of type: ", type(arr))
    # 
    ## Printing array dimensions (axes)
    #print("No. of dimensions: ", arr.ndim)
    # 
    ## Printing shape of array
    #print("Shape of array: ", arr.shape)
    # 
    ## Printing size (total number of elements) of array
    #print("Size of array: ", arr.size)
    # 
    ## Printing type of elements in array
    #print("Array stores elements of type: ", arr.dtype)

    peak=np.average(np.abs(data))*2

    # test bpm
    #bpm, fs = bpm_detector(data, 44100)
    #print(bpm)

    # process value
    value = processMusic(peak)

    last_ten.append(value)
    if len(last_ten) > 100:
        last_ten.pop(0)
    else:
        pass
    avg_last_ten = int(sum(last_ten) / 100)
    if value+3 < avg_last_ten:
        time_delta = time.time()-last_ten_ts
        last_ten_ts = time.time()
        #print(time_delta)
        #print('beat')

    # change the color of LEDs
    #loop.run_until_complete(changeColor(bulbs, avg_last_ten))
    loop.run_until_complete(changeColor(bulbs, value))


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


def createStream():
    """Creates a PulseAudio stream and handles choosing the
    right input device to capture sound"""

    # Get all input devices
    _devices = devices.getDevices()
    d = _devices[0] # Change device id here for now
    printLog(f'🎙  Found {len(_devices)} input devices')
    printLog(f'🎙  Connected to {d["name"]}')

    # set up the microphone
    form_1 = pyaudio.paInt16 # 16-bit resolution
    chans = d['channels'] # 1 channel
    samp_rate = d['rate'] # 44.1kHz sampling rate
    chunk = 730 # 2^12 samples for buffer
    #/chunk = int(730*0.43) # 2^12 samples for buffer
    dev_index = d['dev_index'] # device index found by p.get_device_info_by_index(ii)

    audio = pyaudio.PyAudio() # create pyaudio instantiation

    # create pyaudio stream
    stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                        input_device_index = dev_index,input = True, \
                        frames_per_buffer=chunk)

    return stream, chunk


if __name__ == "__main__":
    # wait for there to be an internet connection
    checkInternet()

    # set up the LEDs
    bulbs = devices.loadLEDs()

    # Set up audio input
    stream, chunk = createStream()

    # start responding to music
    loop = asyncio.get_event_loop()
    last_ten = [] # avg values across 10 samples
    changed = True
    last_mode = 'start'
    count = 0
    timestamp_bug = 0
    timestamp = 0

    while True:
        # check if music mode is on or off
        mode = 'music'
        #mode = checkMode()
        if mode != last_mode:
            changed = True
            last_mode = mode

        # if music mode is on, continue as normal
        if mode == "music":
            if changed == True:
                printLog('🥁 Setting music mode')
                changed = False
            respondToMusic(stream, bulbs)

        # if general mode, set general mode, and 
        # then check state again every second
        if mode == "general":
            if changed == True:
                printLog('🔦 Setting general lighting mode')
                setGeneral(bulbs)
                changed = False

            #getBulbState(bulbs)

            time.sleep(1) # sleep so that we don't ddos redis

        # do stuff every 100 steps
        count += 1
    
        if count > 100:
            time_elapsed = time.time()-timestamp
            fps = 100/time_elapsed
            printLog(f'🔥 FPS: {int(fps)}', end='\r')
            #print(avg_last_ten)
            #getBulbState(bulbs)
            if (fps < 50 and mode != "general"):
                time_bug = time.time()-timestamp_bug
                timestamp_bug = time.time()
                
                if time_bug < 100000: # ignore the first error message on boot
                    printLog(f'🔥 BUG at {round(time_bug,2)}s from last fail, {round(fps,2)} FPS')
            timestamp = time.time()

            count = 0

        #if timestamp_bug == 0:
        #    print(chr(27) + "[2J")
        #    printLog('asdf')

# this is probably important TODO FIXME
#stream.stop_stream()
#stream.close()
#p.terminate()
