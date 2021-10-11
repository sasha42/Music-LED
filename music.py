# music
import pyaudio
import numpy as np
from utils.filters import bassFilter, envelopeFilter, beatFilter
import time
import math
import asyncio
import redis
import os
from utils.devices import devices, createStream
from utils.timeout import timeout
from utils.general import printLog, checkMode, checkInternet, setGeneral
from utils.color import hsv2rgb

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

            i = 1

            # When a peak surpasses threshold, create an easeOutQuint from peak value to threshold 

            # SET THRESHOLD TODO FIXME
            threshold = 120

            #if a_peak < threshold:
            #    for i in range(10):

            #  # set next 10 values with easing
            #  for i in range(10)
            #    next_ten[i] = easing(a_peak)

            for bulb in bulbs:
                # set minimum brightness
                if offset_values[0] < 120:
                    a_peak = 120
                else:
                    a_peak = offset_values[0]

                # normalize peak 
                i += 50
                normalized_peak = a_peak/255
                r, g, b = hsv2rgb(global_hue+i, 1, normalized_peak)
                #r, g, b = hsv2rgb(1, 1, normalized_peak)

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


if __name__ == "__main__":
    # wait for there to be an internet connection
    checkInternet()

    # Set up audio input
    stream, chunk = createStream()

    while True:
        try:
            # set up the LEDs
            with timeout(1): # 10 s timeout
                bulbs = devices.loadLEDs()

            if len(bulbs) == 0:
                printLog("No lights connected!")
                raise RuntimeError

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
                mode = checkMode()
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

                    time.sleep(0.01) # sleep so that we don't ddos redis

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
        except RuntimeError:
            printLog('Timed out, retrying in 5 seconds')
            time.sleep(5)

# this is probably important TODO FIXME
#stream.stop_stream()
#stream.close()
#p.terminate()
