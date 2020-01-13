#!/usr/bin/env python

import time
import math
import flux_led_v3 as flux_led
from multiprocessing import Pool

filepath = 'ip.order.txt'
bulbs = []

def setPattern(ip):
    print("ip: {}".format(ip))

    try:
        bulbs.append(ip)
        bulb = flux_led.WifiLedBulb(ip)
        return bulb.setRgb(0,0,255)

    except Exception as e:
        print("Unable to connect to bulb at [{}]: {}".format(ip,e))
        return

if __name__ == '__main__':

    with open(filepath) as fp:
        line = fp.readline()
        cnt = 1
        while line:
            line = fp.readline()
            if line.strip() == "":
                continue
            ip = line.strip()
            print ("Handle IP [{}]:".format(ip))

            bulbs.append(ip)


        try:
            print ("Ips: {}".format(bulbs))
            with Pool(processes = 40) as pool:
                result = pool.map(setPattern, bulbs, 3)

        except Exception as e:
            print ("error: {}".format(e))


