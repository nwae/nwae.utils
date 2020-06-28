# Need ffmpeg
# > brew install ffmpeg
from pydub import AudioSegment
import re
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
import numpy as np
import wave
import audioop
from scipy.io import wavfile
import scipy.signal as sps
# To get audio from microphone for Mac
#  > brew install portaudio
#  > pip install PyAudio
import pyaudio
from datetime import datetime


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
            play_secs = 0,
            chunk = 1024
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
        n_channels = f.getnchannels()
        n_frames = f.getnframes()
        sample_rate = f.getframerate()
        if play_secs > 0:
            n_frames_required = min(play_secs * sample_rate, n_frames)
        else:
            n_frames_required = n_frames
        Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Require ' + str(n_frames_required) + ' frames to play ' + str(play_secs)
            + ' seconds of total ' + str(n_frames / sample_rate) + ' secs.'
        )

        starttime = datetime.now()
        i_frames = 0
        while i_frames < n_frames_required:
            data = f.readframes(chunk)
            stream.write(data)
            i_frames += chunk
        difftime = datetime.now() - starttime
        Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Played ' + str(difftime.seconds + difftime.microseconds / 1000000) + ' secs.'
        )
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

    def convert_sampling_rate(
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
        Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Source audio file "' + str(src_filepath) + '", ' + str(n_channels) + ' channels, '
            + str(n_frames) + ' frames, total data length = ' + str(len(data))
        )

        try:
            # Resample data
            number_of_samples = round(len(data) * float(outrate) / sampling_rate)
            data_resampled = sps.resample(data, number_of_samples)

            Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Resampled from ' + str(len(data)) + ' frames to '
                + str(len(data_resampled)) + ' frames'
            )
        except Exception as ex_down:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Convert sampling rate exception: ' + str(ex_down)
            )

        try:
            s_write.setparams((outchannels, 2, outrate, 0, 'NONE', 'Uncompressed'))
            s_write.writeframes(data_resampled)
        except Exception as ex_write:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Write file "' + str(dst_filepath) + '" exception: ' + str(ex_write)
            )

        try:
            s_read.close()
            s_write.close()
        except Exception as ex_close:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Close error: ' + str(ex_close)
            )
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
        'File "' + str(audio_file_wav) + '" Format, Channels, Frame Rate, N Frames = '
        + str(obj.get_audio_file_properties(wav_filepath=audio_file_wav))
    )

    # Play
    obj.play_wav(
        wav_filepath = audio_file_wav,
        play_secs = 2
    )

    dst_filepath = 'converted_8000.wav'
    obj.convert_sampling_rate(
        src_filepath = audio_file_wav,
        dst_filepath = dst_filepath,
        outrate = 8000
    )
    print(
        'File "' + str(dst_filepath) + '" Format, Channels, Frame Rate, N Frames = '
        + str(obj.get_audio_file_properties(wav_filepath=dst_filepath))
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
