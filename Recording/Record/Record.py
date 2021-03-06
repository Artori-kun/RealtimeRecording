import os
import os.path
import queue
import struct
import sys
import wave
from array import array
from sys import byteorder

import matplotlib.pyplot as plt
import numpy as np
import pyaudio
import sounddevice as sd

# number of audio frame will be processed and displayed at a time

CHUNK = 1024 * 3

THRESHOLD = 400
FORMAT = pyaudio.paInt16
CHANNELS = 1
# sample per second
RATE = 44100

# INSERT YOUR PATH HERE
PATH = "../../Records"
is_recording = False
end = True


def is_silent(record_data):
    return max(record_data) < THRESHOLD


def normalize(record_data):
    """Average the volume out"""
    MAX = 16384
    times = float(MAX) / max(abs(i) for i in record_data)

    r = array('h')
    for i in record_data:
        r.append(int(i * times))
    return r


def trim(record_data):
    def _trim(rc_data):
        record_start = False
        r = array('h')

        for i in rc_data:
            if not record_start and abs(i) > THRESHOLD + 450:
                record_start = True
                r.append(i)
            elif record_start:
                r.append(i)
        return r

    record_data = _trim(record_data)

    record_data.reverse()
    record_data = _trim(record_data)
    record_data.reverse()
    return record_data


def add_silence(record_data, seconds):
    """Add some seconds of silence to the start and end of
    the processed command so that it won't get chopped off"""
    silence = [0] * int(seconds * RATE)
    r = array('h', silence)
    r.extend(record_data)
    r.extend(silence)
    return r


def record():
    """Record a word or words from the microphone and
    return the data as an array of signed shorts.

    Normalizes the audio, trims silence from the
    start and end, and pads with 0.5 seconds of
    blank sound to make sure it won't get chopped off."""
    global is_recording
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        output=True,
        frames_per_buffer=CHUNK
    )

    num_silent = 0
    r = array('h')
    prev = array('h')

    plt.ion()
    fig, ax = plt.subplots()

    x = np.arange(0, CHUNK)
    line, = ax.plot(x, np.random.rand(CHUNK))
    ax.set_ylim([-2 ** 9, (2 ** 9 - 1)])
    buffer = array('h')

    while True:
        if end:
            stream.stop_stream()
            stream.close()
            p.terminate()
            plt.close(fig)
            break
        record_data = array('h', stream.read(CHUNK))
        size_buffer = 7
        if byteorder == 'big':
            record_data.byteswap()
        # data = struct.unpack(str(CHUNK) + 'h', stream.read(CHUNK))
        line.set_ydata(record_data)
        fig.canvas.draw()
        fig.canvas.flush_events()

        # r.extend(record_data)

        silent = is_silent(record_data)

        if silent and is_recording:
            num_silent += 1
            r.extend(record_data)
            if num_silent > 3:
                is_recording = False
                num_silent = 0
                print('Stop')
                sample_width = p.get_sample_size(FORMAT)
                r = normalize(r)
                # r = trim(r)
                # r = add_silence(r, 0.2)
                record_to_file(r, sample_width)

                # r = buffer + r
                r = array('h')
        elif not silent:
            if not is_recording:
                is_recording = True
                r.extend(prev)
                print('Recording')
                # print(os.getcwd())
                # print(os.path.relpath(PATH))

            r.extend(record_data)
        prev = record_data


def record_to_file(data, sample_width):
    # sample_width, data = record()

    data = struct.pack('<' + ('h' * len(data)), *data)
    file_num = len([name for name in os.listdir(PATH) if name.endswith('.wav')])

    wf = wave.open(PATH + '/' + 'rec' + str(file_num) + '.wav', 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)

    # for i in data:
    #     i = struct.pack('<h', i)
    #     wf.writeframes(i)
    wf.writeframes(data)

    wf.close()


if __name__ == '__main__':
    print("Say something")
    record()
    print("Done")
