#!/usr/bin/env python

import time
import math
import flux_led_v3 as flux_led

filepath = 'ip.order.txt'
bulbs = {}

with open(filepath) as fp:
    line = fp.readline()
    cnt = 1
    while line:
        line = fp.readline()
        if line.strip() == "":
            continue
        ip = line.strip()
        print ("Handle IP [{}]:".format(ip))

        try:

            bulb = flux_led.WifiLedBulb(ip)
            bulb.setPresetPattern(0x25, 100)
            time.sleep(0.1)

        except Exception as e:
            print ("Unable to connect to bulb at [{}]: {}".format(ip,e))
            continue


