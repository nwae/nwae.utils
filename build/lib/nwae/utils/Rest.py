
import requests
import json
import nwae.utils.Log as lg
from inspect import currentframe, getframeinfo
from nwae.utils.Profiling import Profiling


class Rest():

    TIMEOUT_DEFAULT = 10

    def __init__(
            self,
            url
    ):
        self.url = url
        return

    def get(
            self,
            headers = None,
            ext = None,
            # By default verify certificate
            verify = True,
            # By default wait forever?
            timeout = TIMEOUT_DEFAULT
    ):
        resturl = self.url
        if ext is not None:
            resturl = self.url + '/' + ext

        lg.Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Rest GET Request String "' + str(resturl) + '"'
        )

        # Return data
        jData = None
        restResponse = None

        # Make REST GET query
        try:
            start_time = Profiling.start()
            restResponse = requests.get(
                url     = resturl,
                headers = headers,
                verify  = verify,
                timeout = timeout
            )
            stop_time = Profiling.stop()
            lg.Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                + ': GET Request "' + str(resturl) + '" took '
                + str(Profiling.get_time_dif_secs(start=start_time, stop=stop_time))
                + ' secs.'
            )
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': REST GET API ERROR. URL=' + str(resturl) + ' Exception=' + str(ex)
            lg.Log.critical(errmsg)
            raise Exception(errmsg)

        lg.Log.debugdebug(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                          + ': Rest Response Code ' + str(restResponse.status_code))

        # For successful API call, response code will be 200 (OK)
        if (restResponse.ok):
            # Loads (Load String) takes a Json file and converts into python data structure (dict or list, depending on JSON)
            try:
                jData = json.loads(restResponse.content)
            except Exception as ex:
                errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                         + ': LOAD JSON ERROR. URL=' + resturl + ' Exception=' + str(ex)
                lg.Log.critical(errmsg)
                raise Exception(errmsg)

            lg.Log.debugdebug(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                       + ": The response contains {0} properties".format(len(jData)))
            lg.Log.debugdebug(jData)

            return jData

        else:
            # If response code is not ok (200), print the resulting http error code with description
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': REST GET RESPONSE ERROR. URL=[' +  str(resturl)\
                     + ']. Status Code=' + str(restResponse.status_code)
            lg.Log.critical(errmsg)
            #restResponse.raise_for_status()
            raise Exception(errmsg)

    def post(
            self,
            data,
            headers = None,
            ext = None,
            # By default verify certificate
            verify = True,
            # By default wait forever?
            timeout = TIMEOUT_DEFAULT,
            return_true_false_status = False
    ):
        resturl = self.url
        if ext is not None:
            resturl = self.url + '/' + ext

        lg.Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Rest POST Request [' + self.url +
            '], headers [' + str(headers) + ']' +
            '], data [' + str(data) + ']'
        )

        # Make REST POST query
        try:
            start_time = Profiling.start()
            is_json_type = type(data) in [dict, list, tuple]
            if is_json_type:
                lg.Log.debugdebug(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                                  + ': POST Rest data type is ' + str(type(data)) + '...')
                restResponse = requests.post(
                    url     = resturl,
                    json    = data,
                    headers = headers,
                    verify  = verify,
                    timeout = timeout
                )
            else:
                restResponse = requests.post(
                    url     = resturl,
                    data    = data,
                    headers = headers,
                    verify  = verify,
                    timeout = timeout
                )
            stop_time = Profiling.stop()
            lg.Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                + ': POST Request "' + str(resturl) + '" took '
                + str(Profiling.get_time_dif_secs(start=start_time, stop=stop_time))
                + ' secs. Data: ' + str(data)
            )
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': REST POST API ERROR. URL=' + resturl + ' Exception=' + str(ex)
            lg.Log.critical(errmsg)
            raise Exception(errmsg)

        lg.Log.debugdebug(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                          + 'Rest POST Response Code ' + str(restResponse.status_code))

        # For successful API call, response code will be 200 (OK)
        lg.Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
            + ': Rest response OK from "' + str(resturl) + '", content: ' + str(restResponse.content)
        )
        if (restResponse.ok):
            try:
                jData = json.loads(restResponse.content)
            except Exception as ex:
                errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                         + ': LOAD JSON ERROR. URL=' + resturl + ' Exception=' + str(ex)
                lg.Log.critical(errmsg)
                raise Exception(errmsg)

            if jData:
                lg.Log.debugdebug(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                           + ": The response contains {0} properties".format(len(jData)))
                lg.Log.debugdebug(jData)

            if return_true_false_status:
                return True
            else:
                return jData
        else:
            # If response code is not ok (200), print the resulting http error code with description
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': REST RESPONSE ERROR. URL=[' +  resturl \
                     + ']. Status Code=' + str(restResponse.status_code) \
                     + ' Data=' + str(data)
            lg.Log.critical(errmsg)
            raise Exception(
                ': REST RESPONSE ERROR. URL=[' +  resturl
                + ']. Status Code=' + str(restResponse.status_code)
            )

    def put(
            self,
            data,
            headers = None,
            ext = None,
            # By default verify certificate
            verify  = True,
            # By default wait forever?
            timeout = TIMEOUT_DEFAULT,
    ):
        resturl = self.url
        if ext is not None:
            resturl = self.url + '/' + ext

        lg.Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Rest PUT Request [' + self.url + ']'
        )

        # Return status
        restResponse = False

        # Make REST POST query
        try:
            is_json_type = type(data) in [dict, list, tuple]
            if is_json_type:
                lg.Log.debugdebug(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                                  + ': PUT Rest data type is ' + str(type(data)) + '...')
                restResponse = requests.put(
                    url     = resturl,
                    json    = data,
                    headers = headers,
                    verify  = verify,
                    timeout = timeout
                )
            else:
                restResponse = requests.put(
                    url     = resturl,
                    data    = data,
                    headers = headers,
                    verify  = verify,
                    timeout = timeout
                )
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': REST PUT API ERROR. URL=' + resturl + ' Exception=' + str(ex)
            lg.Log.critical(errmsg)
            raise Exception(errmsg)

        # For successful API call, response code will be 200 (OK)
        if (restResponse.ok):
            lg.Log.debug(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                       + ': Successful Rest PUT for URL [' + resturl + '] data [' + str(data) + ']')
            return True
        else:
            # If response code is not ok (200), print the resulting http error code with description
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': REST PUT RESPONSE ERROR. URL=[' +  resturl\
                     + ']. Status Code=' + str(restResponse.status_code)\
                     +' Data=' + str(data)
            lg.Log.critical(errmsg)
            raise Exception(errmsg)


    def delete(
            self,
            headers = None,
            ext = None,
            # By default verify certificate
            verify  = True,
            # By default wait forever?
            timeout = TIMEOUT_DEFAULT,
    ):
        resturl = self.url
        if ext is not None:
            resturl = self.url + '/' + ext

        lg.Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Rest PUT Request [' + self.url + ']'
        )

        # Return status
        restResponse = False

        # Make REST DELETE query
        try:
            restResponse = requests.delete(
                url  = resturl,
                headers = headers,
                verify  = verify,
                timeout = timeout
            )
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': REST DELETE API ERROR. URL=' + resturl + ' Exception=' + str(ex)
            lg.Log.critical(errmsg)
            raise Exception(errmsg)

        # For successful API call, response code will be 200 (OK)
        if (restResponse.ok):
            lg.Log.important(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                       + ': Successful Rest DELETE for URL [' + resturl + '] data [' + '' + ']')
            return True
        else:
            # If response code is not ok (200), print the resulting http error code with description
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)\
                     + ': REST DELETE RESPONSE ERROR. URL=[' + resturl\
                     + ']. Status Code=' + str(restResponse.status_code)
            lg.Log.critical(errmsg)
            raise Exception(errmsg)


if __name__ == '__main__':
    lg.Log.DEBUG_PRINT_ALL_TO_SCREEN = True
    lg.Log.LOGLEVEL = lg.Log.LOG_LEVEL_DEBUG_2

    rest_sec = Rest(url='http://dummy.restapiexample.com/api/v1/employees')
    rest_response = rest_sec.get(
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'request'
        }
    )

    print(rest_response)
