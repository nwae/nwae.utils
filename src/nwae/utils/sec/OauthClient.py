# -*- encoding: utf-8 -*-

from flask import Flask, abort, request
from urllib import parse
import requests
import requests.auth
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe
from nwae.utils.ObjectPersistence import ObjectPersistence
from datetime import datetime, timedelta

rest_flask = Flask(__name__)


#
# OAuth2 Client Server
#  1. Redirects user to external identity server (IDS) login page
#  2. Receive callback from IDS on success
#
class OauthClient:
    # IDS URL
    IDS_URL_AUTH_USER = 'https://ssl.reddit.com/api/v1/authorize'
    IDS_URL_ACCESS_TOKEN = 'https://ssl.reddit.com/api/v1/access_token'
    IDS_URL_GET_USERNAME = 'https://oauth.reddit.com/api/v1/me'

    # Client (our) ID and secret with IDS
    CLIENT_ID = "UpodnBI3vHdAtw"
    CLIENT_SECRET = "srGtVbBmBnLnqtk4z6pE3zG8eeI"

    # Our client URL after authentication success/failure
    REDIRECT_URI = "http://localhost:65010/ids_callback"

    KEY_REDIRECT_URI = 'redirect_uri'
    KEY_RELAY_STATE = 'state'
    KEY_CLIENT_ID = 'client_id'
    KEY_GRANT_TYPE = 'grant_type'
    KEY_RESP_TYPE = 'response_type'
    KEY_DURATION = 'duration'
    KEY_SCOPE = 'scope'
    KEY_AUTH_CODE = 'code'

    RESP_TYPE_AUTH_CODE = 'code'
    GRANT_TYPE_AUTH_CODE = 'authorization_code'

    RELAY_STATE_CACHE_FILE = '/tmp/oauth_relay_state_cache'
    RELAY_STATE_CACHE_LOCK_FILE = '/tmp/oauth_relay_state_cache.lock'

    def __init__(self):
        self.app = rest_flask
        self.relay_state_cache = {}
        self.relay_state_cache_file = OauthClient.RELAY_STATE_CACHE_FILE
        self.relay_state_cache_lock_file = OauthClient.RELAY_STATE_CACHE_LOCK_FILE
        # Call once
        self.update_relay_state_from_cache()

        @rest_flask.route('/')
        def ids_login_page():
            text = '<a href="%s">Authenticate with reddit</a>'
            return text % self.make_authorization_url()

        @rest_flask.route('/ids_callback')
        def ids_callback():
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Received callback from "' + str(request.remote_addr) + '": ' + str(request.args)
            )
            error = request.args.get('error', '')
            if error:
                # Show user error message
                Log.important(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Error from callback: "' + str(error) + '"'
                )
                return "Error: " + error
            state = request.args.get(OauthClient.KEY_RELAY_STATE, '')
            if not self.check_validity_of_relay_state(state):
                # Uh-oh, this request wasn't started by us!
                abort(403)
            auth_code = request.args.get(OauthClient.KEY_AUTH_CODE)
            Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Authorization code from "' + str(request.remote_addr) + '": "' + str(auth_code) + '"'
            )

            # Get access token from IDS
            ret_token = self.get_token(authorization_code=auth_code)
            Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Access token from ' + str(request.remote_addr) + ': ' + str(ret_token.access_token)
            )

            username = None
            if ret_token.ok:
                username = self.get_username(ret_token.access_token)
                Log.important(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Username "' + str(username) + '" OK.'
                )
            return "Your username is: " + str(username)

    def make_authorization_url(self):
        # Generate a random string for the state parameter
        # Save it for use later to prevent xsrf attacks
        from uuid import uuid4
        state = str(uuid4())
        Log.important(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Created relay state "' + str(state) + '" for new request.'
        )
        self.save_created_state(state)
        params = {
            OauthClient.KEY_CLIENT_ID:    OauthClient.CLIENT_ID,
            OauthClient.KEY_RESP_TYPE:    OauthClient.RESP_TYPE_AUTH_CODE,
            OauthClient.KEY_RELAY_STATE:  state,
            OauthClient.KEY_REDIRECT_URI: OauthClient.REDIRECT_URI,
            OauthClient.KEY_DURATION:     "temporary",
            OauthClient.KEY_SCOPE:        "identity"
        }
        url = OauthClient.IDS_URL_AUTH_USER + '?' + parse.urlencode(params)
        return url

    #
    # Get access token from IDS, after receiving authorization code
    #
    def get_token(self, authorization_code):
        client_auth = requests.auth.HTTPBasicAuth(
            OauthClient.CLIENT_ID,
            OauthClient.CLIENT_SECRET
        )
        # Our request for access token, using authorization code received
        post_data = {
            OauthClient.KEY_GRANT_TYPE:      OauthClient.GRANT_TYPE_AUTH_CODE,
            OauthClient.KEY_AUTH_CODE:       authorization_code,
            OauthClient.KEY_REDIRECT_URI:    OauthClient.REDIRECT_URI
        }
        Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Requesting access token using authorization code "' + str(authorization_code)
            + '", post data: ' + str(post_data)
        )
        response = requests.post(
            OauthClient.IDS_URL_ACCESS_TOKEN,
            auth = client_auth,
            data = post_data
        )
        token_json = response.json()
        Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Received reply for access token request "' + str(token_json) + '"'
        )

        class retclass:
            def __init__(self, ok, access_token=None, error_no=None, error_msg=None):
                self.ok = ok
                self.access_token = access_token
                self.error_no = error_no
                self.error_msg = error_msg

        if 'access_token' in token_json.keys():
            return retclass(ok=True, access_token=token_json['access_token'])
        else:
            error_no = None
            error_msg = None
            if 'error' in token_json.keys():
                error_no = token_json['error']
            if 'message' in token_json.keys():
                error_msg = token_json['message']
            retmsg = 'No access token received, error ' + str(error_no) + ', error message "' + str(error_msg) + '"'
            Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': ' + retmsg
            )
            return retclass(ok=False, error_no=error_no, error_msg=error_msg)

    def get_username(self, access_token):
        Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Getting username using access token "' + str(access_token) + '".'
        )
        headers = {"Authorization": "bearer " + access_token}

        try:
            response = requests.get(OauthClient.IDS_URL_GET_USERNAME, headers=headers)
        except Exception as ex:
            Log.error(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Error getting username: ' + str(ex) + '.'
            )
            return None

        try:
            me_json = response.json()
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Get username response: ' + str(me_json)
            )
            if 'name' in me_json.keys():
                return me_json['name']
            else:
                Log.warning(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Key "name" not found in response json: ' + str(me_json)
                )
                return None
        except:
            return None

    def check_validity_of_relay_state(self, state):
        self.update_relay_state_from_cache()
        return self.is_state_valid(state=state)

    #
    # We don't update the cache from memory, caller is supposed to do that.
    # Because this function is called from many places.
    #
    def is_state_valid(self, state):
        if state in self.relay_state_cache.keys():
            state_obj = self.relay_state_cache[state]
            create_time = state_obj['create_timestamp']
            expire_time = state_obj['expire_timestamp']
            is_valid = datetime.now() < expire_time
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': State "' + str(state) + '" create/expire "' + str(create_time) + '", "' + str(expire_time)
                + '". Valid = ' + str(is_valid)
            )
            return is_valid
        else:
            return False

    def update_relay_state_from_cache(self):
        rs_from_cache = ObjectPersistence.deserialize_object_from_file(
            obj_file_path = self.relay_state_cache_file,
            lock_file_path = self.relay_state_cache_lock_file
        )
        if rs_from_cache is None:
            Log.warning(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Relay state cache empty from file "' + str(self.relay_state_cache_file)
            )
        else:
            self.relay_state_cache = rs_from_cache

        # Cleanup
        states_to_delete = []
        for state in self.relay_state_cache.keys():
            if not self.is_state_valid(state=state):
                states_to_delete.append(state)

        for state in states_to_delete:
            del self.relay_state_cache[state]
            Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Expired Relay state "' + str(state) + '" removed from relay state cache successfully'
            )
        self.update_relay_state_to_storage()

    def update_relay_state_to_storage(self):
        res = ObjectPersistence.serialize_object_to_file(
            obj = self.relay_state_cache,
            obj_file_path = self.relay_state_cache_file,
            lock_file_path = self.relay_state_cache_lock_file
        )
        if not res:
            Log.warning(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Relay state not serialized to file!'
            )
        else:
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Relay state successfully serialized to file "' + str(self.relay_state_cache_file)
                + '": ' + str(self.relay_state_cache)
            )

    # You may want to store valid states in a database or memcache,
    # or perhaps cryptographically sign them and verify upon retrieval.
    def save_created_state(self, state):
        self.update_relay_state_from_cache()
        self.relay_state_cache[state] = {
            'create_timestamp': datetime.now(),
            'expire_timestamp': datetime.now() + timedelta(seconds=30)
        }
        self.update_relay_state_to_storage()


if __name__ == '__main__':
    svr = OauthClient()
    svr.app.run(debug=True, port=65010)
