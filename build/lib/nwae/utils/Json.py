
import json
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo


#
# All Response classes inherit this
#
class Json:

    KEY_DESCRIPTION = 'description'
    KEY_URL = 'url'

    def __init__(
            self
    ):
        self.data = {}
        return

    def to_json(self):
        return self.data.copy()

    # Old function name only
    def get_data_copy_json_friendly(self):
        return self.to_json()

    def get_json_bytes(self):
        try:
            json_data = json.dumps(obj=self.data, ensure_ascii=False).encode(encoding='utf-8')
            return json_data
        except Exception as ex:
            lg.Log.critical(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                       + ': Exception occurred converting to JSON object [' + str(ex) + ']')
            raise ex

    def get_json_string(self):
        return self.get_json_bytes().decode('utf-8').replace("'", '"')

