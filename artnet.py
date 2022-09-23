from utils.devices import createStream, loadLEDs, setGeneral
from utils.timeout import timeout
from utils.general import checkLastActive, printLog, checkMode, checkInternet, setLastActive
from stupidArtnet import StupidArtnetServer
import asyncio

async def change(bulb, r, g, b):
    bulb.setRgb(r, g, b)

if __name__ == "__main__":
    # Wait for there to be an internet connection
    checkInternet()

    # Connect artnet
    server = StupidArtnetServer()
    u1_listener = server.register_listener(0)

    # Connect to bulbs
    bulbs = loadLEDs()

    # Create loop
    loop = asyncio.get_event_loop()

    while True:
        data = server.get_buffer(listener_id=u1_listener)
        if len(data) > 0:
            i = 0
            for bulb in bulbs:
                loop.run_until_complete(change(bulbs[bulb], data[i], data[i+1], data[i+2]))
                i += 3

