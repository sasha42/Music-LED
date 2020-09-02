# Music LED
### Experimental LED music visualizer

This repo uses the flux_led library and allows you to visualize music. You will need `numpy` and `pyaudio` for this to work.

Inspired by:
* [this blog](https://www.swharden.com/wp/2016-07-19-realtime-audio-visualization-in-python/)
* [this project](https://github.com/jorticus/audiovis/blob/master/audiovis.py)
* [and this project](https://github.com/BinaryBrain/Arduino-Beat-Detection-LED/)

## Mac setup
You will need to install the portaudio plugin through brew:
```
brew install portaudio
```

## Running
```
python music.py
```

***

### Descriptions of files
* `audiovis.py` cool audio visualization in console
* `blue.py` sets all your LEDs to blue
* `blueBlink.py` and `blueFlashing.py` various methods of blinking LEDs
* `dark.py` makes all your LEDs go dark (without turning them off)
* `filters.py` used by music.py, transcoded from @binarybrain
* `flux_led_v3.py` library for controlling the leds
* `ip.order.txt` example ip order file (required to control LEDs)
* `music.py` **use this** to controll lights from music
* `pong.py` example code for high frequency LED updates
* `rainbow[Blink,Smooth,Tunnel].py` rainbow effects on LEDs

Have fun!