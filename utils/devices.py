# coding: utf-8
import pyaudio
import utils.alsaerror
from utils.flux_led_v4 import BulbScanner
from utils.general import printLog
from utils.timeout import timeout
import utils.flux_led_v4 as flux_led


# Instantiate PyAudio
p = pyaudio.PyAudio()


def getDevices():
    """Gets all the suitable devices which have input channels
    and are not the default dummy device. Returns a list."""

    # Create a list
    suitable_devices = []
            
    # Iterate over each device
    for i in range(p.get_device_count()):
        # Extract device metadata (note: there is more available)
        d = {}
        d['name'] = p.get_device_info_by_index(i)['name'].split(':')[0]
        d['dev_index'] = i
        d['rate'] = int(p.get_device_info_by_index(i)['defaultSampleRate'])
        d['channels'] = p.get_device_info_by_index(i)['maxInputChannels']
        
        # Check if device has input channels and isn't the default fake device
        if (d['channels'] >= 1 and d['name'] != 'default'):
            # Save it to list
            suitable_devices.append(d)

    return suitable_devices


def simpleList(devices):
    """Print a simple list of devices"""

    # Create an empty string
    device_str = f'🔌 Found {len(devices)} input devices: '

    # Append each device name to string
    for i in range(len(devices)):
        device_str += devices[i]['name'] 
        device_str += ' (' 
        device_str += str(devices[i]['dev_index'])
        device_str += ', ' 
        device_str += str(devices[i]['channels'])
        device_str +=' channels)'
        if i+1 < len(devices):
            device_str += ', '

    return device_str


def loadLEDs():
    '''Loads IPs from ip.order.txt into memory, and attemps to connect
    to them.'''

    # Open ip.order.txt and read the IPs of the bulbs. It expects a list
    # of IPs like 192.168.1.1, with one IP per line. The file should end
    # with one empty line.
    filepath = '/home/pi/Music-LED/ip.order.txt'

    # Define variables
    ips = []
    bulbs = {}
    lastOrder = {}
    cnt = 1

    # Try to open local list of IPs, if not, scan the network for list
    try:
        with open(filepath) as fp:
            line = fp.readline()
            while line:
                line = fp.readline()
                if line.strip() == "":
                    continue
                ip = line.strip()

                ips.append(ip)
    except:
        ips = getBulbs()

    # Once the file has been read, the script will attempt to create
    # objects for each bulb.
    printLog(f"💡 Connected to {len(ips)} LED strips")

    for ip in ips:
        with timeout(1):
            try:
                bulb = flux_led.WifiLedBulb(ip, timeout=0.1)
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


def getBulbs():
    """Gets bulbs from the local network using a scan"""

    # Initialize bulb scanner
    s = BulbScanner()
    
    # Scan the local network with timeout of 1
    result = s.scan(timeout=1)

    # Return just the IPs
    ips = []
    for i in result:
        ips.append(i['ipaddr'])

    return ips


def simpleBulbList(bulbs):
    """Pretty prints a list of bulbs"""

    return f"💡 found {len(bulbs)} bulbs"


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
    

def setGeneral(bulbs):
    #for i in range(255):
    #    brightness = int(easeOutCubic(i/254)*254)
    #    loop.run_until_complete(changeColor(bulbs, int(brightness/10)))
    #    time.sleep(0.01)

    for bulb in bulbs:
        bulbs[bulb].setRgb(30, 10, 1)


def createStream():
    """Creates a PulseAudio stream and handles choosing the
    right input device to capture sound"""

    # Get all input devices
    _devices = devices.getDevices()
    d = _devices[0] # Change device id here for now
    printLog(f'🎙  Found {len(_devices)} input devices')
    printLog(f'🎙  Connected to {d["name"]}')

    # set up the microphone
    form_1 = pyaudio.paInt16 # 16-bit resolution
    chans = d['channels'] # 1 channel
    samp_rate = d['rate'] # 44.1kHz sampling rate
    chunk = 730 # 2^12 samples for buffer
    #/chunk = int(730*0.43) # 2^12 samples for buffer
    dev_index = d['dev_index'] # device index found by p.get_device_info_by_index(ii)

    audio = pyaudio.PyAudio() # create pyaudio instantiation

    # create pyaudio stream
    stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                        input_device_index = dev_index,input = True, \
                        frames_per_buffer=chunk)

    return stream, chunk


if __name__ == "__main__":
    devices = getDevices()
    simple_devices = simpleList(devices)

    bulbs = getBulbs()
    simple_bulbs = simpleBulbList(bulbs)   

    print(simple_devices)
    print(simple_bulbs)
