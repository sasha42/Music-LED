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

##############
#### LEDS ####
##############
filepath = 'ip.order.txt'
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

print ("foo {}".format(tempIps))
for ip in tempIps:
    ips.append(ip)

print ("List: {}".format(ips))

for ip in ips:
    try:
        bulb = flux_led.WifiLedBulb(ip)
        bulbs[cnt] = bulb
        lastOrder[cnt] = ""
        cnt = cnt + 1

    except Exception as e:
        print ("Unable to connect to bulb at [{}]: {}".format(ip,e))
        continue

async def respondToMusic(peak):
    #print(peak)
    if peak < 256:
        for bulb in bulbs:
            bulbs[bulb].setRgb(0,0,peak)
    else:
        print(peak)
    #print("set bulb {} to green ".format(peak))

loop = asyncio.get_event_loop()

###############
#### MUSIC ####
###############
CHUNK = 2**3
RATE = 44100

p=pyaudio.PyAudio()
stream=p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input=True,
              frames_per_buffer=CHUNK)

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

    print(beat)

    return int(envelope)

#for i in range(int(10*44100/1024)): #go for a few seconds

i = 0
prev_time = time.time()

while True:
    data = np.fromstring(stream.read(CHUNK),dtype=np.int16)
    peak=np.average(np.abs(data))*2

    i += 1
    if i > 200:
        i = 0
        #print(start_time)
        new_time = time.time()
        hz = int(1/((new_time-prev_time)/200))
        #print(f'{hz} hz')
        prev_time = new_time
        #print('yes')
        # process music
        value = processMusic(peak)
        #print(value)

        loop.run_until_complete(respondToMusic(value))
        #print(int(peak/128))


    #bars="#"*int(50*peak/2**16)
    #print("%04d %05d %s"%(i,int(peak/128),bars))
    
    

stream.stop_stream()
stream.close()
p.terminate()