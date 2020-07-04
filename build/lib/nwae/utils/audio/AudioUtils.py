# Need ffmpeg
# > brew install ffmpeg
from pydub import AudioSegment
import re
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
import numpy as np
import wave
import scipy.signal as sps
# To get audio from microphone for Mac
#  > brew install portaudio
#  > pip install PyAudio
import pyaudio
from datetime import datetime


#
# wav format is something like this
#
#  (x1_c1 x1_c2), (x2_c1 x2_c2), (x3_c1, x3_c3), ...
#
# where x1 is sample 1, x2 is sample 2, x3 is sample 3, ...
# and c1 is channel 1, c2 is channel 2.
# (xn_c1, xn_c2) is 1 frame.
#
# Sample Width
#   Sample width = 1 means x is 8 bits (unsigned)
#   Sample width = 2 means x is 16 bits (signed)
#
# Thus
#   total_bytes_per_frame = sample_width * n_channels
#   total_bytes = total_bytes_per_frames * total_frames
#
class AudioWavProperties:

    def __init__(
            self,
            format,
            n_channels,
            frame_rate,
            n_frames,
            sample_width,
            data_bytes
    ):
        self.format = format
        self.n_channels = n_channels
        self.frame_rate = frame_rate
        self.n_frames = n_frames
        self.sample_width = sample_width

        # total_bytes_per_frame = sample_width * n_channels
        self.bytes_per_frame = int(self.n_channels * self.sample_width)

        # Anything above 8 bits are signed, only 8-bit is unsigned
        self.data_type = np.uint8
        if self.sample_width == 2:
            self.data_type = np.int16
        else:
            raise Exception('Wrong sample width ' + str(self.sample_width) + ' > 2')

        # total_bytes = total_bytes_per_frames * total_frames
        self.data_bytes_len = int(self.bytes_per_frame * self.n_frames)
        self.data_bytes = data_bytes

        #
        # Extract channel raw values
        #
        audio_as_np = np.frombuffer(
            buffer = self.data_bytes,
            dtype  = self.data_type
        )
        self.np_data = audio_as_np.astype(np.float32)

        # Normalise float32 array so that values are between -1.0 and +1.0
        n_bits = 8*self.sample_width - 1
        self.np_data_normalized = self.np_data / (2**n_bits)

        # Now add additional dimension for channel
        self.np_data_by_channel = np.zeros(
            shape = (self.n_channels, self.n_frames),
            dtype = self.data_type,
            order = 'C'
        )
        # Just an array 0,1,2,3,... to symbolize indexes
        n_sample = np.array(list(range(len(self.np_data_normalized))))
        Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Normalized data by channel shape: ' + str(self.np_data_by_channel.shape)
        )
        if self.n_channels > 1:
            for chnl in range(self.n_channels):
                # Pick the correct indexes for this channel
                indexes = n_sample % self.sample_width == chnl
                channel_n_frames = np.sum(indexes*1)
                assert channel_n_frames,\
                    'Channel ' + str(chnl) + ' with ' + str(channel_n_frames) + ' frames not ' + str(self.n_frames)
                # Assign channel data
                self.np_data_by_channel[chnl] = self.np_data[indexes]
        else:
            self.np_data_by_channel[0] = self.np_data.copy()

        return

    def to_json(
            self,
            show_first_n_bytes = 10
    ):
        data_bytes_part = self.data_bytes[0:min(100, len(self.data_bytes))]
        np_data_part = self.np_data[0:min(100, len(self.np_data))]
        return {
            'format': self.format,
            'n_channels': self.n_channels,
            'frame_rate': self.frame_rate,
            'n_frames': self.n_frames,
            'sample_width': self.sample_width,
            'bytes_per_frame': self.bytes_per_frame,
            'data_type': self.data_type,
            'data_bytes_len': self.data_bytes_len,
            'data_bytes': 'First ' + str(show_first_n_bytes) + ' bytes: ' + str(data_bytes_part),
            'np_data': 'First ' + str(show_first_n_bytes) + ' samples: ' + str(np_data_part)
        }


#
# Fundamental Utilities to Handle Audio Files
#  - conversion from mp3, m4a, etc formats to standard wav
#  - read wav file properties (frame rate, channels, sample width, etc)
#  - play wav files
#  - extract raw values to numpy array
#  - conversion to mono channel
#  - up/down sampling of raw audio values
#
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

    #
    # Fundamental properties required for all audio operations
    #
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
                data_bytes = f.readframes(n_frames)

                return AudioWavProperties(
                    format = format,
                    n_channels = n_channels,
                    frame_rate = frame_rate,
                    n_frames   = n_frames,
                    sample_width = sample_width,
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
        n_frames = f.getnframes()
        sample_rate = f.getframerate()
        if play_secs > 0:
            n_frames_required = int(min(play_secs * sample_rate, n_frames))
        else:
            n_frames_required = n_frames
        Log.debug(
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
        Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Played ' + str(difftime.seconds + difftime.microseconds / 1000000) + ' secs.'
        )
        stream.stop_stream()
        stream.close()

        # close PyAudio
        p.terminate()
        return

    def convert_sampling_rate(
            self,
            # wav file format
            src_filepath,
            dst_filepath,
            outrate
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

        Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Source audio file "' + str(src_filepath) + '", ' + str(wav_properties.n_channels) + ' channels, '
            + str(wav_properties.n_frames) + ' properties: ' + str(wav_properties.to_json())
        )

        ratio_retain_sample = float(outrate) / wav_properties.frame_rate
        n_retained_frames = round(wav_properties.n_frames * ratio_retain_sample)
        Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Try to resample from ' + str(wav_properties.frame_rate) + 'Hz to '
            + str(outrate) + 'Hz, or total frames  '
            + str(wav_properties.n_frames)
            + ' to ' + str(n_retained_frames) + ' frames'
        )

        try:
            # Do by channel
            sample_len_retained = wav_properties.sample_width * n_retained_frames
            data_resampled_final = np.zeros(
                shape = (sample_len_retained,),
                dtype = wav_properties.data_type,
                order = 'C'
            )
            np_indexes = np.array(list(range(sample_len_retained)))
            if wav_properties.n_channels > 1:
                for chnl in range(wav_properties.n_channels):
                    data_resampled = sps.resample(
                        wav_properties.np_data_by_channel[chnl],
                        n_retained_frames
                    )
                    data_resampled = data_resampled.astype(wav_properties.data_type)
                    # Assign channel data
                    data_resampled_final[np_indexes%wav_properties.sample_width==chnl] = data_resampled.copy(order='C')
            else:
                data_resampled_final = sps.resample(
                    wav_properties.np_data,
                    n_retained_frames
                )
                data_resampled_final = data_resampled_final.astype(wav_properties.data_type)

            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Resampled from ' + str(wav_properties.n_frames) + ' frames to '
                + str(len(data_resampled_final)) + ' frames'
            )
        except Exception as ex_down:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Convert sampling rate exception: ' + str(ex_down)
            )

        try:
            s_write.setnchannels(wav_properties.n_channels)
            s_write.setsampwidth(wav_properties.sample_width)
            s_write.setframerate(outrate)
            s_write.setnframes(len(data_resampled_final))
            s_write.setcomptype(comptype='NONE', compname='Uncompressed')
            s_write.writeframes(data_resampled_final.copy(order='C'))

            resampled_properties = self.get_audio_file_properties(
                wav_filepath = dst_filepath
            )
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Resampled file "' + str(dst_filepath) + '" audio properties: ' + str(resampled_properties.to_json())
            )
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

    def convert_sound_to_mono(
            self,
            src_filepath,
            dst_filepath
    ):
        try:
            sound = AudioSegment.from_wav(src_filepath)
            sound = sound.set_channels(1)
            sound.export(dst_filepath, format="wav")
        except Exception as ex:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Failed convert "' + str(src_filepath) + '" to mono: ' + str(ex)
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
            Log.debug(
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


def example_convert_format_to_wav(
        audio_filepath
):
    obj = AudioUtils()
    audio_file_wav = obj.convert_format(
        filepath  = audio_filepath,
        to_format = 'wav'
    )
    # print('Frame Rate = ' + str(obj.get_audio_file_properties(wav_filepath=obj.get_audio_filepath())))
    print(
        'File "' + str(audio_file_wav)
        + ' properties:\n\r'
        + str(obj.get_audio_file_properties(wav_filepath=audio_file_wav).to_json())
    )
    return audio_file_wav

def example_convert_sound_to_mono(
        audio_filepath,
        mono_filepath
):
    obj = AudioUtils()
    obj.convert_sound_to_mono(
        src_filepath = audio_filepath,
        dst_filepath = mono_filepath
    )
    print(
        'Mono File "' + str(audio_file_wav)
        + ' properties:\n\r'
        + str(obj.get_audio_file_properties(wav_filepath=mono_filepath).to_json())
    )
    return True

def example_play_wav(
        audio_filepath_wav,
        play_secs = 0
):
    obj = AudioUtils()
    # Play
    obj.play_wav(
        wav_filepath = audio_filepath_wav,
        play_secs = play_secs
    )
    wav_params = obj.get_audio_file_properties(wav_filepath=audio_filepath_wav)
    print(wav_params.np_data_normalized.tolist()[0:10000])

    l = min(len(wav_params.np_data_normalized), 200000)
    x = np.array(list(range(l)))
    y = wav_params.np_data_normalized[0:l]

    import matplotlib.pyplot as plt

    plt.plot(x, y)
    plt.show()
    return

def example_resample_wav(
        src_filepath,
        resampled_filepath,
        outrate
):
    obj = AudioUtils()
    obj.convert_sampling_rate(
        src_filepath = src_filepath,
        dst_filepath = resampled_filepath,
        outrate = outrate
    )
    print(
        'Resampled File "' + str(audio_file_wav)
        + ' properties:\n\r'
        + str(obj.get_audio_file_properties(wav_filepath=resampled_filepath).to_json())
    )
    return resampled_filepath


if __name__ == '__main__':
    Log.LOGLEVEL = Log.LOG_LEVEL_DEBUG_1
    audio_file = '/usr/local/git/nwae/nwae.lang/app.data/voice-recordings/Lenin_-_In_Memory_Of_Sverdlov.ogg.mp3'
    play_audio = True

    audio_file_wav = example_convert_format_to_wav(audio_filepath=audio_file)
    # if play_audio:
    #     example_play_wav(audio_filepath_wav=audio_file_wav, play_secs=2)

    mono_filepath = re.sub(pattern='.wav$', repl='', string=str(audio_file_wav)) + '_mono.wav'
    example_convert_sound_to_mono(
        audio_filepath = audio_file_wav,
        mono_filepath  = mono_filepath
    )
    # if play_audio:
    #     example_play_wav(audio_filepath_wav=mono_filepath, play_secs=2)

    for src_filepath in [mono_filepath, audio_file_wav]:
        dst_filepath = re.sub(pattern='.wav$', repl='', string=str(src_filepath)) + '_8000.wav'
        resampled_filepath = example_resample_wav(
            src_filepath = src_filepath,
            resampled_filepath = dst_filepath,
            outrate = 8000
        )
        if play_audio:
            example_play_wav(audio_filepath_wav=resampled_filepath, play_secs=2)
    exit(0)
