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
from effects.easings import generateEasings

next_vals = []

async def changeColor(bulbs, peak):
    # Set initial values
    global next_vals
    everyOther = True
    global_hue = 150
    every60k = 0
    minimum_threshold = 80

    # Make sure that we never get out of bounds data
    if peak < 255:
        a_peak = peak*10
        thresh = 200

        # Briefly change the hue when there is a high peak
        if (everyOther == True and a_peak > thresh):
            everyOther = False
            global_hue += 20
        elif (everyOther == False and a_peak > thresh):
            everyOther = True
            global_hue -= 20

        # Shift hue roughly every 10 seconds
        every60k += 1
        if every60k > 600:
            every60k = 1
            global_hue += 10

        threshold = minimum_threshold
        iterations = 3

        # If value is above the threshold, compute a set of ease values
        if (a_peak > threshold):
            next_vals = generateEasings(a_peak, threshold, iterations)

        # If not, check if there are ease values and return those
        elif (a_peak < threshold and len(next_vals) > 0):
            a_peak = next_vals.pop()

        # Finally, if there are no values, return threshold value
        else:
            a_peak = threshold

        # If value is legit, proceed
        if a_peak < 255:

            # Set a minimum brightness
            if a_peak < minimum_threshold:
                a_peak = minimum_threshold

            # Set a iterable so that each bulb has its own hue
            i = 1

            for bulb in bulbs:
                # Normalize peak to convert to hsv 
                normalized_peak = a_peak/255
                
                # Change hue for each individual bulb
                i += 50

                # Convert hue to rgb values
                r, g, b = hsv2rgb(global_hue+i, 1, normalized_peak)

                # Set rgb values on lights
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
    # Wait for there to be an internet connection
    checkInternet()

    # Set up redis connection
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

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
