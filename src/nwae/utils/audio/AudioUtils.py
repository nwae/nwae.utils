# Need ffmpeg
# > brew install ffmpeg
from pydub import AudioSegment
import re
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
import numpy as np
import wave
import audioop
# To get audio from microphone for Mac
#  > brew install portaudio
#  > pip install PyAudio
import pyaudio


class AudioUtils:

    def __init__(
            self
    ):
        return

    def get_audio_filepath_extension(
            self,
            filepath
    ):
        return re.sub(pattern='(.*[.])([a-zA-Z0-9]+$)', repl='\\2', string=filepath)

    def get_audio_file_properties(
            self,
            wav_filepath
    ):
        assert self.get_audio_filepath_extension(filepath=wav_filepath) == 'wav',\
            'Audio file "' + str(wav_filepath) + '" must be wav file'

        try:
            p = pyaudio.PyAudio()

            with wave.open(wav_filepath, "rb") as wave_file:
                format = p.get_format_from_width(wave_file.getsampwidth())
                n_channels = wave_file.getnchannels()
                frame_rate = wave_file.getframerate()
                n_frames = wave_file.getnframes()

                return format, n_channels, frame_rate, n_frames
        except Exception as ex:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Could not get frame rate from "' + str(wav_filepath) + '". Exception: ' + str(ex)
            )

    def play_wav(
            self,
            wav_filepath,
            # Stream chunk
            chunk = 1024,
            n_chunks = 0
    ):
        assert self.get_audio_filepath_extension(filepath=wav_filepath) == 'wav',\
            'Audio file "' + str(wav_filepath) + '" must be wav file'

        # open a wav format music
        f = wave.open(wav_filepath, "rb")
        # instantiate PyAudio
        p = pyaudio.PyAudio()
        # open stream
        stream = p.open(
            format   = p.get_format_from_width(f.getsampwidth()),
            channels = f.getnchannels(),
            rate     = f.getframerate(),
            output   = True
        )
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
        return

    def load_as_array(
            self,
            audio_filepath
    ):
        ifile = wave.open(audio_filepath)
        samples = ifile.getnframes()
        audio = ifile.readframes(samples)

        # Convert buffer to float32 using NumPy
        audio_as_np_int16 = np.frombuffer(audio, dtype=np.int16)
        audio_as_np_float32 = audio_as_np_int16.astype(np.float32)

        # Normalise float32 array so that values are between -1.0 and +1.0
        max_int16 = 2 ** 15
        audio_normalised = audio_as_np_float32 / max_int16
        return audio_normalised

    def downsample(
            self,
            src_filepath,
            dst_filepath,
            outrate     = 16000,
            outchannels = 1
    ):
        try:
            s_read = wave.open(src_filepath, 'r')
            s_write = wave.open(dst_filepath, 'w')
        except Exception as ex_file:
            Log.error(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': File error: ' + str(ex_file)
            )
            return False

        n_frames = s_read.getnframes()
        n_channels = s_read.getnchannels()
        sampling_rate = s_read.getframerate()
        data = s_read.readframes(n_frames)

        try:
            converted = audioop.ratecv(
                data, 2, n_channels, sampling_rate, outrate, None
            )
            if outchannels == 1:
                converted = audioop.tomono(converted[0], 2, 1, 0)
        except Exception as ex_down:
            Log.error(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Downsample exception: ' + str(ex_down)
            )
            return False

        try:
            s_write.setparams((outchannels, 2, outrate, 0, 'NONE', 'Uncompressed'))
            s_write.writeframes(converted)
        except Exception as ex_write:
            Log.error(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Write file "' + str(dst_filepath) + '" exception: ' + str(ex_write)
            )
            return False

        try:
            s_read.close()
            s_write.close()
        except Exception as ex_close:
            Log.error(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Close error: ' + str(ex_close)
            )
            return False
        return True

    #
    # Convert between audio formats mp3, m4a, wav, etc.
    #
    def convert_format(
            self,
            filepath,
            to_format = 'wav'
    ):
        file_extension = self.get_audio_filepath_extension(filepath=filepath)
        filepath_converted = re.sub(pattern='[.][a-zA-Z0-9]+$', repl='.wav', string=filepath)
        Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Convert "' + str(filepath) + '" with extension "' + str(file_extension)
            + '" New filepath "' + str(filepath_converted) + '"'
        )
        try:
            track = AudioSegment.from_file(
                file   = filepath,
                format = file_extension
            )
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Converting "' + str(filepath)
                + '" to "' + str(filepath_converted) + '"..'
            )
            file_handle = track.export(filepath_converted, format=to_format)
            file_handle.close()
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Successful Conversion from "' + str(filepath)
                + '" to "' + str(filepath_converted) + '"..'
            )
            return filepath_converted
        except Exception as ex:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Exception converting "' + str(filepath)
                + '" to "' + str(filepath_converted)
                + '": ' + str(ex)
            )


if __name__ == '__main__':
    audio_file = '/usr/local/git/nwae/nwae.lang/app.data/voice-recordings/Lenin_-_In_Memory_Of_Sverdlov.ogg.mp3'

    obj = AudioUtils()

    audio_file_wav = obj.convert_format(
        filepath  = audio_file,
        to_format = 'wav'
    )
    # print('Frame Rate = ' + str(obj.get_audio_file_properties(wav_filepath=obj.get_audio_filepath())))
    print(
        'Format, Channels, Frame Rate, N Frames = '
        + str(obj.get_audio_file_properties(wav_filepath=audio_file_wav))
    )

    # Play
    obj.play_wav(
        wav_filepath = audio_file_wav,
        n_chunks = 100
    )

    arr = obj.load_as_array(
        audio_filepath = audio_file_wav
    )
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
