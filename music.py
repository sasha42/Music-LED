import numpy as np
from utils.filters import bassFilter, envelopeFilter
import time
import asyncio
import redis
import os
from utils.devices import createStream, loadLEDs, setGeneral
from utils.timeout import timeout
from utils.general import printLog, checkMode, checkInternet
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


def respondToMusic(stream, bulbs):
    """Takes in chunks from the audio stream, applies some filters
    to clean up the output, and then triggers lights based on amplitude
    on the main asyncio loop."""

    # Listen to music
    data = np.frombuffer(stream.read(chunk, exception_on_overflow = False),dtype=np.int16)

    # Get peak value
    peak=np.average(np.abs(data))*2

    # Filter only the bass 
    value = bassFilter(peak)

    # Make sure that the value will always be positive
    if value < 0:
        value = -value

    # Run through an envelope filter
    envelope = envelopeFilter(value)

    # Change the color of LEDs
    loop.run_until_complete(changeColor(bulbs, int(envelope)))


if __name__ == "__main__":
    # wait for there to be an internet connection
    checkInternet()

    # Set up audio input
    stream, chunk = createStream()

    while True:
        try:
            # set up the LEDs
            with timeout(1): # 10 s timeout
                bulbs = loadLEDs()

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
                mode = checkMode(r)
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
