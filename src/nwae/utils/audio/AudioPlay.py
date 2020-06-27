# -*- coding: utf-8 -*-

# To get audio from microphone
#  > brew install portaudio
#  > pip install PyAudio
import pyaudio
import wave


class AudioPlay:

    def __init__(
            self,
            audio_filepath
    ):
        self.audio_filepath = audio_filepath
        return

    def play(self):
        # define stream chunk
        chunk = 1024

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
        while data:
            stream.write(data)
            data = f.readframes(chunk)

            # stop stream
        stream.stop_stream()
        stream.close()

        # close PyAudio
        p.terminate()


if __name__ == '__main__':
    audio_filepath = '/usr/local/git/nwae/nwae.lang/app.data/voice-recordings/hi.wav'

    AudioPlay(
        audio_filepath = audio_filepath
    ).play()
    exit(0)
