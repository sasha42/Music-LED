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

    tempIps = copy.copy(ips)
    tempIps.reverse()

    # Once the file has been read, the script will attempt to create
    # objects for each bulb.
    print ("Connecting to {}".format(tempIps))
    for ip in tempIps:
        ips.append(ip)

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


def respondToMusic(stream, bulbs):
    # listen to music
    data = np.fromstring(stream.read(CHUNK),dtype=np.int16)
    peak=np.average(np.abs(data))*2

    # process value
    value = processMusic(peak)

    last_ten.append(value)
    if len(last_ten) > 10:
        last_ten.pop(0)
    else:
        pass
    avg_last_ten = int(sum(last_ten) / 10)

    # change the color of LEDs
    loop.run_until_complete(changeColor(bulbs, avg_last_ten))


if __name__ == "__main__":
    # set up the LEDs
    bulbs = loadLEDs()

    # set up the microphone
    CHUNK = 2**10
    RATE = 44100

    p=pyaudio.PyAudio()
    stream=p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input=True,
                frames_per_buffer=CHUNK)

    # start responding to music
    loop = asyncio.get_event_loop()
    last_ten = [] # avg values across 10 samples

    while True:
        respondToMusic(stream, bulbs)


# this is probably important TODO FIXME
#stream.stop_stream()
#stream.close()
#p.terminate()
