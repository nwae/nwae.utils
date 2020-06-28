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

class AudioWavProperties:
    def __init__(
            self,
            format,
            n_channels,
            frame_rate,
            n_frames,
            sample_width,
            bytes_per_frame,
            data_bytes
    ):
        self.format = format
        self.n_channels = n_channels
        self.frame_rate = frame_rate
        self.n_frames = n_frames
        self.sample_width = sample_width
        self.bytes_per_frame = bytes_per_frame
        self.data_bytes = data_bytes
        return

    def to_json(self):
        return {
            'format': self.format,
            'n_channels': self.n_channels,
            'frame_rate': self.frame_rate,
            'n_frames': self.n_frames,
            'sample_width': self.sample_width,
            'bytes_per_frame': self.bytes_per_frame,
            'data_bytes': 'First 100 bytes: ' + str(self.data_bytes[0:min(100, len(self.data_bytes))])
        }

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

            with wave.open(wav_filepath, "rb") as f:
                format = p.get_format_from_width(f.getsampwidth())
                n_channels = f.getnchannels()
                frame_rate = f.getframerate()
                n_frames = f.getnframes()
                sample_width = f.getsampwidth()
                # Each frame contains all channel values, so should be 2 bytes * n_channels
                bytes_per_frame = len(f.readframes(1))
                data_bytes = f.readframes(n_frames)

                return AudioWavProperties(
                    format = format,
                    n_channels = n_channels,
                    frame_rate = frame_rate,
                    n_frames   = n_frames,
                    sample_width = sample_width,
                    bytes_per_frame = bytes_per_frame,
                    data_bytes = data_bytes
                )
        except Exception as ex:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Could not get frame rate from "' + str(wav_filepath) + '". Exception: ' + str(ex)
            )

    def play_wav(
            self,
            wav_filepath,
            play_secs = 0.0,
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
            n_frames_required = int(min(play_secs * sample_rate, n_frames))
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

    def load_as_np_array(
            self,
            audio_filepath
    ):
        wav_properties = self.get_audio_file_properties(
            wav_filepath = audio_filepath
        )

        # Convert buffer to float32 using NumPy
        # Anything above 8 bits are signed, only 8-bit is unsigned
        if wav_properties.sample_width == 1:
            audio_as_np = np.frombuffer(wav_properties.data_bytes, dtype=np.uint8)
        elif wav_properties.sample_width == 2:
            audio_as_np = np.frombuffer(wav_properties.data_bytes, dtype=np.int16)
        else:
            raise Exception('Wrong sample width ' + str(wav_properties.sample_width))

        audio_as_np_float32 = audio_as_np.astype(np.float32)

        Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Loaded audio "' + str(audio_filepath) + '" from ' + str(len(wav_properties.data_bytes))
            + ' bytes to ' + str(len(audio_as_np_float32)) + ' samples.'
        )

        # Normalise float32 array so that values are between -1.0 and +1.0
        n_bits = 8*wav_properties.sample_width - 1
        audio_normalised = audio_as_np_float32 / (2**n_bits)
        return audio_normalised

    def convert_sampling_rate(
            self,
            # wav file format
            src_filepath,
            dst_filepath,
            outrate     = 16000,
            outchannels = 1
    ):
        wav_properties = self.get_audio_file_properties(
            wav_filepath = src_filepath
        )
        try:
            s_write = wave.open(dst_filepath, 'w')
        except Exception as ex_file:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Cannot open file "' + str(dst_filepath) + '" for writing: ' + str(ex_file)
            )

        Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Source audio file "' + str(src_filepath) + '", ' + str(wav_properties.n_channels) + ' channels, '
            + str(wav_properties.n_frames) + ' frames, total data bytes length = ' + str(len(wav_properties.data_bytes))
        )

        ratio_retain = float(outrate) / wav_properties.frame_rate
        n_retained_data_bytes = round(len(wav_properties.data_bytes) * ratio_retain)
        Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Try to resample from ' + str(wav_properties.frame_rate) + 'Hz to '
            + str(outrate) + 'Hz, or total samples '
            + str(len(wav_properties.data_bytes)) + ' to ' + str(n_retained_data_bytes) + ' samples'
        )

        try:
            data_resampled = sps.resample(wav_properties.data_bytes, n_retained_data_bytes)

            Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Resampled from ' + str(len(wav_properties.data_bytes)) + ' frames to '
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
        'File "' + str(audio_file_wav)
        + ' properties:\n\r'
        + str(obj.get_audio_file_properties(wav_filepath=audio_file_wav).to_json())
    )

    # Play
    obj.play_wav(
        wav_filepath = audio_file_wav,
        play_secs = 1
    )

    arr = obj.load_as_np_array(
        audio_filepath = audio_file_wav
    )
    print(arr.tolist()[0:10000])

    l = min(len(arr), 200000)
    x = np.array(list(range(l)))
    y = arr[0:l]

    import matplotlib.pyplot as plt

    # plt.style.use('seaborn-whitegrid')
    # fig = plt.figure()
    # ax = plt.axes()
    # ax.plot(x, y)
    plt.plot(x, y)
    plt.show()

    #
    # Resample
    #
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

    exit(0)
