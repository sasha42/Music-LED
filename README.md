# Music LED
### Experimental LED music visualizer

This repo uses the flux_led library and allows you to visualize music. You will need `numpy` and `pyaudio` for this to work.

Inspired by:
* [this blog](https://www.swharden.com/wp/2016-07-19-realtime-audio-visualization-in-python/)
* [this project](https://github.com/jorticus/audiovis/blob/master/audiovis.py)
* [and this project](https://github.com/BinaryBrain/Arduino-Beat-Detection-LED/)

# Setup
You can run this on Mac or Linux. In order for this to work, you'll need:
* Microphone or line in (built in to many devices)
* Python installed on your device
* The IP addresses of your *magic home* LED controllers

The installation varies based on the device, but you run the code in the same way after installation is finished.

## LED configuration
You will need a list of IPs to place into `ip.order.txt`. An example configuration has been provided. The list should contain 1 IP per line. The file should end with a blank line. 

## Mac setup
You will need to install the portaudio plugin through brew:
```
brew install portaudio
pip install -r requirements.txt
```

## Linux (Raspberry Pi) setup
There are several steps involved in getting this code to run on linux. You will need to install several additional packages and set up some environment variables, then edit some configurations.

**Install packages**
You will need some 
```
sudo apt-get update
sudo apt-get install libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev libatlas-base-dev libffi-dev redis
```

**Set up environment variables**
```
echo "PA_ALSA_PLUGHW=1" >> ~/.bashrc
``` 

**Edit some configurations**
Inside of `~/.asoundrc`
```
pcm.!default { type hw card 1 }
ctl.!default { type hw card 1 }
```

Inside of `/usr/share/alsa/alsa.conf` (you will need to edit this with sudo), you will need to comment out lines `127` through `142`

**Install dependencies with Python**
```
# install virtual environment
# optional but highly recommended
sudo pip3 install virtualenv
virtualenv venv
source venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

**Configure audio device**
Inside of your virtual enviromnent, you will need to run `python -m sounddevice` to figure out what device you're using to capture audio, and how many channels it has:
```
(venv) pi@music-led:~/Music-LED $ python -m sounddevice
  0 RODE AI-1: USB Audio (hw:1,0), ALSA (1 in, 2 out)
* 1 default, ALSA (1 in, 2 out)
```

You will then need to take the above information, and plug it into `music.py`, on lines `18` and `19`. 
* The `device` should equal to the number which is to the left of your input device (in this case it's `0`, as part of `0 RODE AI-1: US...`)
* The `channel` should equal to the number of inputs, which is at the end of the line (in this case it's `1`, as part of `(1 in, 2 out)`)

Once you have everything set up, you can run it.

**Run on boot**

Inside of `/lib/systemd/system/musicled.service`, you will need to add the following:
```
[Unit]
Description=Music LED experience
After=multi-user.target

[Service]
Environment="REDIS_URL=redis://localhost:6379"
ExecStartPre=/bin/bash -c 'source /home/pi/Music-LED/venv/bin/activate && /home/pi/Music-LED/venv/bin/python /home/pi/Music-LED/server.py > /home/pi/serverled.log 2>&1 &'
ExecStart=/bin/bash -c 'source /home/pi/Music-LED/venv/bin/activate && /home/pi/Music-LED/venv/bin/python /home/pi/Music-LED/music.py > /home/pi/musicled.log 2>&1'

[Install]
WantedBy=multi-user.target
```

You will then need to enable the service with `sudo systemctl enable musicled.service`. This should run when you reboot the Pi every time.

## Running
You will need to have `redis-server` installed and running on your computer.

```
export REDIS_URL='redis://localhost:6379'
python music.py
```

This code will look at IPs you have saved in `ip.order.txt` and will change their color based on what is heard through the microphone.

---

Coded with ❤️ in Lausanne
