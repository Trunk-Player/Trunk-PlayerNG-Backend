import base64
import os
import sentry_sdk
import socketio
import logging

from django.conf import settings
from django.http.response import HttpResponse
from django.contrib.auth import authenticate

from rest_framework_simplejwt.authentication import JWTAuthentication


mgr = socketio.KombuManager(
    os.getenv("CELERY_BROKER_URL", "ampq://user:pass@127.0.0.1/")
)
sio = socketio.Server(
    async_mode="gevent_uwsgi", client_manager=mgr, logger=False, engineio_logger=False
)


if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


# def index(data):
#     return HttpResponse("HELO")


# @sio.event
# def my_event(sid, message):
#     sio.emit("my_response", {"data": message["data"]}, room=sid)


# @sio.event
# def my_broadcast_event(sid, message):
#     sio.emit("my_response", {"data": message["data"]})


# @sio.event
# def join(sid, message):
#     sio.enter_room(sid, message["room"])
#     sio.emit("my_response", {"data": "Entered room: " + message["room"]}, room=sid)


# @sio.event
# def leave(sid, message):
#     sio.leave_room(sid, message["room"])
#     sio.emit("my_response", {"data": "Left room: " + message["room"]}, room=sid)


# @sio.event
# def close_room(sid, message):
#     sio.emit(
#         "my_response",
#         {"data": "Room " + message["room"] + " is closing."},
#         room=message["room"],
#     )
#     sio.close_room(message["room"])


# @sio.event
# def my_room_event(sid, message):
#     sio.emit("my_response", {"data": message["data"]}, room=message["room"])


# @sio.event
# def disconnect_request(sid):
#     sio.disconnect(sid)

@sio.event
def deregister_tx_source(sid, message):
    uuid = message["uuid"]
    type = message["type"]
    sio.leave_room(sid, f'tx_{type}_{uuid}')

@sio.event
def register_tx_source(sid, message):
    uuid = message["uuid"]
    type = message["type"]
    sio.enter_room(sid, f'tx_{type}_{uuid}')


@sio.event
def connect(sid, environ, auth):
    JWT_authenticator = JWTAuthentication()
    
    try:
        jwt = environ["HTTP_AUTHORIZATION"]
        valid_jwt = JWT_authenticator.get_validated_token(jwt)
        user = JWT_authenticator.get_user(valid_jwt)
    except:
        raise ConnectionRefusedError('authentication failed')

    sio.save_session(sid, {'username': user})
    logging.debug(f"[+] User {user.email} has connected to the socket")
    sio.emit("debug", {"data": "Connected"}, room=sid)
    sio.enter_room(sid, 'unicast')
    sio.enter_room(sid, f'alert_{user.userProfile.UUID}')
    sio.emit('unicast', {"ping":"pong"}, room='unicast')


@sio.event
def disconnect(sid):
    print("Client disconnected")
