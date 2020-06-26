# Need ffmpeg
# > brew install ffmpeg
from pydub import AudioSegment
import re
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe


class AudioFormats:

    def __init__(self):
        return

    def convert_to_wav(
            self,
            filepath,
            to_format = 'wav'
    ):
        file_extension = re.sub(pattern='(.*[.])([a-zA-Z0-9]+$)', repl='\\2', string=filepath)
        new_filepath = re.sub(pattern='[.][a-zA-Z0-9]+$', repl='.wav', string=filepath)
        Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Convert "' + str(filepath) + '" with extension "' + str(file_extension)
            + '" New filepath "' + str(new_filepath) + '"'
        )
        try:
            track = AudioSegment.from_file(
                file   = filepath,
                format = file_extension
            )
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Converting "' + str(filepath) + '" to "' + str(new_filepath) + '"..'
            )
            file_handle = track.export(new_filepath, format=to_format)
            file_handle.close()
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Successful Conversion from "' + str(filepath) + '" to "' + str(new_filepath) + '"..'
            )
        except Exception as ex:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Exception converting "' + str(filepath) + '" to "' + str(new_filepath)
                + '": ' + str(ex)
            )
        return


if __name__ == '__main__':
    audio_file = 'music.m4a'
    AudioFormats().convert_to_wav(
        filepath = audio_file
    )
    exit(0)
