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
pip install -r requirements.txt
```

## Running
```
python music.py
```

This code will look at IPs you have saved in `ip.order.txt` and will change their color based on what is heard through the microphone.

---

Coded with ❤️ in Lausanne