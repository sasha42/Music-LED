import numpy as np
import pyaudio
import time
import librosa
import os
import pickle
import redis

# Set up redis
r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

def sendBpmRedis(bpm):
    """Sends bpm value to redis. First it pulls the existing list,
    pops the oldest value, and appends the latest bpm value"""

    # Get value from redis
    try:
        p_mode = r.get('params')
        params = pickle.loads(p_mode)
    except:
        params = {}
        params['bpmList'] = [0]

    # Append value
    try:
        params['bpmList'].append(bpm)
    except:
        params['bpmList'] = [0]
        params['bpmList'].append(bpm)

    # Pop last value if more than 10
    if len(params['bpmList']) > 10:
        params['bpmList'].pop(0)

    # Send updated list back to redis
    p_mode = pickle.dumps(params)
    r.set('params', p_mode)


class AudioHandler(object):
    def __init__(self):
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024 * 200
        self.p = None
        self.stream = None

    def start(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.FORMAT,
                                  channels=self.CHANNELS,
                                  rate=self.RATE,
                                  input=True,
                                  output=False,
                                  stream_callback=self.callback,
                                  frames_per_buffer=self.CHUNK)

    def stop(self):
        self.stream.close()
        self.p.terminate()

    def callback(self, in_data, frame_count, time_info, flag):
        numpy_array = np.frombuffer(in_data, dtype=np.float32)
        bpm = librosa.beat.tempo(numpy_array)
        print('yes')
        sendBpmRedis(int(bpm[0]))
        return None, pyaudio.paContinue

    def mainloop(self):
        while (self.stream.is_active()): # if using button you can set self.stream to 0 (self.stream = 0), otherwise you can use a stop condition
            time.sleep(2.0)


print('audio handler')
audio = AudioHandler()
print('start')
audio.start()     # open the the stream
print('main loop')
audio.mainloop()  # main operations with librosa
