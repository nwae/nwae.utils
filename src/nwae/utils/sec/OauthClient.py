# -*- encoding: utf-8 -*-

from flask import Flask, abort, request
from urllib import parse
import requests
import requests.auth
from nwae.utils.Log import Log
from inspect import getframeinfo, currentframe

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

    def __init__(self):
        self.app = rest_flask

        @rest_flask.route('/')
        def ids_login_page():
            text = '<a href="%s">Authenticate with reddit</a>'
            return text % self.make_authorization_url()

        @rest_flask.route('/ids_callback')
        def ids_callback():
            Log.info(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Received callback from "' + str(request.remote_addr) + '"'
            )
            error = request.args.get('error', '')
            if error:
                # Show user error message
                Log.important(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Error from callback: "' + str(error) + '"'
                )
                return "Error: " + error
            state = request.args.get('state', '')
            if not self.is_valid_state(state):
                # Uh-oh, this request wasn't started by us!
                abort(403)
            code = request.args.get('code')
            Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Authorization code from "' + str(request.remote_addr) + '": "' + str(code) + '".'
            )

            # Get access token from IDS
            ret_token = self.get_token(code)
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
            # Return message to user
            return "Your reddit username is: " + str(username)

    def make_authorization_url(self):
        # Generate a random string for the state parameter
        # Save it for use later to prevent xsrf attacks
        from uuid import uuid4
        state = str(uuid4())
        self.save_created_state(state)
        params = {
            "client_id": OauthClient.CLIENT_ID,
            "response_type": "code",
            "state": state,
            "redirect_uri": OauthClient.REDIRECT_URI,
            "duration": "temporary",
            "scope": "identity"
        }
        url = OauthClient.IDS_URL_AUTH_USER + '?' + parse.urlencode(params)
        return url

    #
    # Get access token from IDS, after receiving authorization code
    #
    def get_token(self, code):
        client_auth = requests.auth.HTTPBasicAuth(
            OauthClient.CLIENT_ID,
            OauthClient.CLIENT_SECRET
        )
        post_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OauthClient.REDIRECT_URI
        }
        Log.info(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Requesting access token using authorization code "' + str(code)
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
        headers = {"Authorization": "bearer " + access_token}
        response = requests.get(OauthClient.IDS_URL_GET_USERNAME, headers=headers)
        me_json = response.json()
        return me_json['name']

    # You may want to store valid states in a database or memcache,
    # or perhaps cryptographically sign them and verify upon retrieval.
    def save_created_state(self, state):
        #
        # TODO Save state
        #
        pass

    def is_valid_state(self, state):
        #
        # TODO Check for valid state
        #
        return True


if __name__ == '__main__':
    svr = OauthClient()
    svr.app.run(debug=True, port=65010)
