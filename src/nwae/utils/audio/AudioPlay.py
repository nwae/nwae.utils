# -*- coding: utf-8 -*-

# To get audio from microphone
#  > brew install portaudio
#  > pip install PyAudio
import pyaudio
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
from nwae.utils.audio.AudioUtils import AudioUtils
import numpy as np
import wave


class AudioPlay:

    def __init__(
            self,
            audio_filepath
    ):
        self.audio_filepath = audio_filepath
        return

    def load_as_array(self):
        ifile = wave.open(self.audio_filepath)
        samples = ifile.getnframes()
        audio = ifile.readframes(samples)

        # Convert buffer to float32 using NumPy
        audio_as_np_int16 = np.frombuffer(audio, dtype=np.int16)
        audio_as_np_float32 = audio_as_np_int16.astype(np.float32)

        # Normalise float32 array so that values are between -1.0 and +1.0
        max_int16 = 2 ** 15
        audio_normalised = audio_as_np_float32 / max_int16
        return audio_normalised

    def play(
            self,
            # Stream chunk
            chunk = 1024,
            n_chunks = 0
    ):
        # open a wav format music
        f = wave.open(self.audio_filepath, "rb")
        # instantiate PyAudio
        p = pyaudio.PyAudio()
        # open stream
        stream = p.open(format=p.get_format_from_width(f.getsampwidth()),
                        channels=f.getnchannels(),
                        rate=f.getframerate(),
                        output=True)
        # read data
        data = f.readframes(chunk)

        # play stream
        i = 0
        while data:
            stream.write(data)
            data = f.readframes(chunk)
            i += 1
            Log.debug('Chunk #' + str(i))
            if n_chunks and i >= n_chunks:
                Log.info(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Done playing ' + str(n_chunks) + ' chunks.'
                )
                break

            # stop stream
        stream.stop_stream()
        stream.close()

        # close PyAudio
        p.terminate()


if __name__ == '__main__':
    Log.LOGLEVEL = Log.LOG_LEVEL_DEBUG_1
    audio_filepath_mp3 = '/usr/local/git/nwae/nwae.lang/app.data/voice-recordings/Lenin_-_In_Memory_Of_Sverdlov.ogg.mp3'
    audio_filepath_wav = AudioUtils().convert_format(
        filepath = audio_filepath_mp3
    )

    print('Playing audio from "' + str(audio_filepath_wav) + '"')
    obj = AudioPlay(
        audio_filepath = audio_filepath_wav
    )
    obj.play(
        n_chunks = 100
    )

    arr = obj.load_as_array()
    print(arr.tolist()[0:10000])

    l = min(len(arr), 20000)
    x = np.array(list(range(l)))
    y = arr[0:l]

    import matplotlib.pyplot as plt
    # plt.style.use('seaborn-whitegrid')
    # fig = plt.figure()
    # ax = plt.axes()
    # ax.plot(x, y)
    plt.plot(x, y)
    plt.show()

    exit(0)
