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
from math import sqrt
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


# set up redis connection
r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

avg_last_ten = []
last_ten_ts = 0
global_hue = 150
settingTime = 0
everyOther = True
every60k = 0
originalColors = []
offset_values = []

def printLog(log):
    '''Generates standard time string and prints out'''

    # Generate time string
    st = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f'[{st}] {log}')


def loadLEDs():
    '''Loads IPs from ip.order.txt into memory, and attemps to connect
    to them.'''

    # Open ip.order.txt and read the IPs of the bulbs. It expects a list
    # of IPs like 192.168.1.1, with one IP per line. The file should end
    # with one empty line.
    filepath = os.getenv("IP_ORDER", "ip.order.txt")

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
    printLog(f"💡 Connected to {len(ips)} LED strips")

    for ip in ips:
        try:
            bulb = flux_led.WifiLedBulb(ip)
            #print(vars(bulb))
            #print(bulb._WifiLedBulb__state_str)
            bulbs[cnt] = bulb
            lastOrder[cnt] = ""
            cnt = cnt + 1

        except Exception as e:
            print ("Unable to connect to bulb at [{}]: {}".format(ip,e))
            continue
    
    #for bulb in bulbs:
    #    bulbs[bulb].getBulbInfo()
    # Return the bulbs that were successfully innitiated
    return bulbs


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


async def simpleChangeColor(bulbs, peak):

    if peak < 255:
        a_peak = peak*10

        if a_peak < 255:
            for bulb in bulbs:

                r = int(a_peak)
                g = int(a_peak)
                b = int(a_peak)
                # set color on lights
                bulbs[bulb].setRgb(r, g, b)

    else:
        print(peak)


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
                if offset_values[0] < 50:
                    a_peak = 20
                else:
                    a_peak = offset_values[0]

                # normalize peak 
                normalized_peak = a_peak/255
                global_hue = 0
                r, g, b = hsv2rgb(global_hue, 1, normalized_peak)

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
    #beat = beatFilter(envelope)

    #print(beat)

    return int(envelope)


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




from scipy import fft, arange
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import os


def frequency_spectrum(x, sf):
    """
    Derive frequency spectrum of a signal from time domain
    :param x: signal in the time domain
    :param sf: sampling frequency
    :returns frequencies and their content distribution
    """
    x = x - np.average(x)  # zero-centering

    n = len(x)
    #print(n)
    k = arange(n)
    tarr = n / float(sf)
    frqarr = k / float(tarr)  # two sides frequency range

    frqarr = frqarr[range(n // 2)]  # one side frequency range

    x = fft(x) / n  # fft computing and normalization
    x = x[range(n // 2)]

    return frqarr, abs(x)


list_bulb_values = []

def respondToMusic(stream, bulbs):
    global avg_last_ten
    global last_ten_ts
    global list_bulb_values

    # listen to music
    data = np.fromstring(stream.read(chunk, exception_on_overflow = False),dtype=np.int16)

    #plt.plot(data)
    #plt.savefig("data.png")

    frequencies, distribution = frequency_spectrum(data, stream._rate)

    #plt.figure()
    #plt.plot(frequencies)
    #plt.savefig("freq.png")

    #plt.figure()
    #plt.plot(distribution)
    #plt.savefig("distr.png")

    #print(f'Shape: {data.shape}')
    #print(f'Frequencies: {frequencies}')
    #print(f'Distribution: {distribution}')
    #print("Freq shape", len(frequencies))

    #print('😇 after')
    FREQ_MIN = 20
    FREQ_MAX = 50
    #AVERAGE_OVER_LAST = 20 # samples
    AVERAGE_OVER_LAST = 10 # samples
    new_value = np.average(np.abs(distribution[FREQ_MIN:FREQ_MAX]))


    # volume multiplier
    volumeFactor = 0.5
    multiplier = pow(2, (sqrt(sqrt(sqrt(volumeFactor))) * 192 - 192)/6)
    new_value *= multiplier #np.multiply(new_value, volumeFactor, out=new_value, casting="unsafe")

    list_bulb_values.append(new_value)
    list_bulb_values = list_bulb_values[-100:]
    value = np.average(list_bulb_values[-AVERAGE_OVER_LAST:])

    value -= np.min(list_bulb_values)
    value *= 255/(np.max(list_bulb_values)-np.min(list_bulb_values))
    #value -= np.median(list_bulb_values)
    #value *= 250/(np.max(list_bulb_values)-np.median(list_bulb_values)))

    try:
        loop.run_until_complete(changeColor(bulbs, int(value/20)))
    except:
        pass
    return

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


if __name__ == "__main__":
    # wait for there to be an internet connection
    checkInternet()

    # set up the LEDs
    bulbs = loadLEDs()

    # set up the microphone
    #chunk = 2**10
    form_1 = pyaudio.paInt16 # 16-bit resolution
    chans = 1 # 1 channel
    #samp_rate = 44100 # 44.1kHz sampling rate
    samp_rate = 16000
    #chunk = int(0.2*samp_rate)
    chunk = int(730/3.5)
    #chunk = 730# 2^12 samples for buffer
    #chunk = int(144000/4) # 2^12 samples for buffer
    dev_index = 0 # device index found by p.get_device_info_by_index(ii)

    # Hide all the alsa warnings and instantiate pyaudio
    #with noalsaerr():
    #with nostdout():
    #os.close(sys.stderr.fileno())

    audio = pyaudio.PyAudio() # create pyaudio instantiation

    # create pyaudio stream
    stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                        input_device_index = dev_index,input = True, \
                        frames_per_buffer=chunk)


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
        #if mode != last_mode:
        #    changed = True
        #    last_mode = mode

        # if music mode is on, continue as normal
        #if mode == "music":
        #    if changed == True:
        #printLog('🥁 Setting music mode')
        changed = False

        respondToMusic(stream, bulbs)

        # if general mode, set general mode, and 
        # then check state again every second
        #if mode == "general":
        #    if changed == True:
        #        printLog('🔦 Setting general lighting mode')
        #        setGeneral(bulbs)
        #    changed = False

            #getBulbState(bulbs)

        #    time.sleep(1) # sleep so that we don't ddos redis

        # do stuff every 100 steps
        count += 1
    
        if count > 100:
            time_elapsed = time.time()-timestamp
            fps = 100/time_elapsed
            print(f'FPS: {fps}\r', end="\r") # debug framerate
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
