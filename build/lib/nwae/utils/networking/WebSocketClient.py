# -*- coding: utf-8 -*-

import websockets
import asyncio
import json
import sys
import ssl
import certifi
from nwae.utils.Log import Log


class WebSocketClient:

    @staticmethod
    def get_access_token():
        access_token = '3c34f2861d3fe170abe1d150e28b0b7033381c6cb6d3764bf3f317ffcc5186501bc25914a35ba3d1fe833fcdc28e01089e8343924d83a7a4660500b8b664c4b875960996ee2dd9fcc9956bdd8b0a22277ebbb4cd57ebd0613c23517459846b2e19b9327070712c724ea6e22c6969e238f98bdf5622411927661072420b968172dbd3034cef2afbc24054cd31a73964ff'
        Log.info('Access token "' + str(access_token) + '".')
        return access_token

    def __init__(self, server_uri):
        self.server = server_uri
        self.chat_id = None
        self.conn_disconnected = False

        self.access_token = WebSocketClient.get_access_token()

        return

    async def init_ws(
            self
    ):
        #
        # We need to do this to make sure it won't fail SSL Cert verification
        #
        ssl_context = ssl.create_default_context()
        ssl_context.load_verify_locations(certifi.where())

        self.ws = await websockets.connect(
            self.uri,
            ssl = ssl_context
        )
        print('Websocket to "' + str(self.uri) + '" formed..')

        conn_packet = ClientRequest(
            event_type = ClientRequest.VALUE_EVENT_TYPE_CONNECT,
            access_token = self.access_token
        ).to_json()

        # First connection
        await self.ws.send(json.dumps(conn_packet))
        print('Sent connection packet ' + str(conn_packet) + ' to server..')

        server_reply = await self.ws.recv()
        print(server_reply)
        print('Server reply (type ' + str(type(server_reply)) + '): ' + str(server_reply))

        server_response = ServerResponse(
            server_response = server_reply
        )
        # Extract chat id
        self.chat_id = server_response.get_chat_id()
        print('Chat ID from server: ' + str(self.chat_id))
        return

    async def handle_ws(
            self
    ):
        while True:
            # This call is blocking
            user_msg = input('Enter message: ')

            if self.conn_disconnected:
                print('Server disconnected.')
                return

            msg_packet = ClientRequest(
                event_type = ClientRequest.VALUE_EVENT_TYPE_MESSAGE,
                access_token = self.access_token,
                chat_id = self.chat_id,
                message = user_msg
            ).to_json()

            try:
                await self.ws.send(
                    json.dumps(msg_packet)
                )
            except Exception as ex_send:
                print('Cannot send msg: ' + str(msg_packet) + '. Got exception: ' + str(ex_send) + '.')
                return

            server_reply = await self.ws.recv()
            server_response = None
            try:
                server_response = ServerResponse(
                    server_response = server_reply
                )
                print(server_response.json)
            except Exception as ex:
                print('Could not get server response. Exception "' + str(ex) + '"')
                print(server_reply)

            if server_response.get_event_type() == ClientRequest.VALUE_EVENT_TYPE_SESSION_EXPIRED:
                print('Connection expired')
                return


if sys.version_info < (3, 7, 0):
    print('Python version ' + str(sys.version) + ' not supported')
    exit(1)

async def main_ws():
    ws_client = WebSocketClient(server_uri='ws://localhost:8080/socket')
    await ws_client.init_ws()
    await asyncio.gather(
        ws_client.handle_ws()
    )

asyncio.run(main_ws())
exit(0)

# asyncio.get_event_loop().run_until_complete(
#     WsClient.chat(server = 'local')
# )
