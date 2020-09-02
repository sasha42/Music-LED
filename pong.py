#!/usr/bin/env python

import time
import math
import asyncio
import datetime
import copy
import flux_led_v3 as flux_led

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


async def sendOrderBlue(bulb, id):
    if lastOrder[id] != "blue":
        lastOrder[id] = "blue"
        #bulb.setPresetPattern(0x33, 100)
        bulb.setRgb(0,0,1)
        print("set bulb {} to blue ".format(id))

async def sendOrderGreen(bulb, id):
    if lastOrder[id] != "green":
        lastOrder[id] = "green"
        bulb.setRgb(255,255,255)
        print("set bulb {} to green ".format(id))

FPS = 20
speedFactor = 1
lastFrameTime = 0
frameCounter = 0
loop = asyncio.get_event_loop()

while True:
    # dt is the time delta in seconds (float).
    currentTime = time.time()
    dt = currentTime - lastFrameTime
    lastFrameTime = currentTime
    sleepTime = 1./FPS - (currentTime - lastFrameTime)
    if sleepTime > 0:
        time.sleep(sleepTime)

    frameCounter = frameCounter + 1
    max = len(bulbs) + 1
    for key, bulb in bulbs.items():
        if(frameCounter -1 % max == key
                or frameCounter % max == key
                or frameCounter +1 % max == key):
            # sendOrderGreen(bulb, key)
            print(bulbs[1])
            loop.run_until_complete(sendOrderGreen(bulb, key))

        else:
            #sendOrderBlue(bulb, key)
            loop.run_until_complete(sendOrderBlue(bulb, key))


loop.close()
