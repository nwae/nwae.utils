# -*- coding: utf-8 -*-

# To get audio from microphone
#  > brew install portaudio
#  > pip install PyAudio
import pyaudio
import wave
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
from nwae.utils.audio.AudioFormats import AudioFormats


class AudioPlay:

    def __init__(
            self,
            audio_filepath
    ):
        self.audio_filepath = audio_filepath
        return

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
    audio_filepath_wav = AudioFormats().convert_format(
        filepath = audio_filepath_mp3
    )

    print('Playing audio from "' + str(audio_filepath_wav) + '"')
    AudioPlay(
        audio_filepath = audio_filepath_wav
    ).play(
        n_chunks = 0
    )
    exit(0)
