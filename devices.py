# coding: utf-8
import pyaudio
import alsaerror
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


if __name__ == "__main__":
    devices = getDevices()
    simple_devices = simpleList(devices)

    print(simple_devices)
