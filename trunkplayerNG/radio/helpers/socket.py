import base64
from curses.ascii import US
import json
import os
import sentry_sdk
import socketio
import logging

from django.conf import settings
from django.http.response import HttpResponse
from django.contrib.auth import authenticate

from kombu import Queue, Exchange
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.renderers import JSONRenderer

mgr = socketio.KombuManager(
    os.getenv("CELERY_BROKER_URL", "ampq://user:pass@127.0.0.1/")
)
sio = socketio.Server(
    async_mode="gevent_uwsgi", client_manager=mgr, logger=False, engineio_logger=False
)


if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


@sio.event
def tx_request(sid, message):
    from radio.helpers.utils import user_allowed_to_access_transmission, UUIDEncoder
    from radio.models import Transmission
    from radio.serializers import TransmissionListSerializer

    try:
        session = sio.get_session(sid)
        User = session['user']
        TX = Transmission.objects.get(UUID=message['UUID'])

        if user_allowed_to_access_transmission(TX, User.userProfile.UUID):
            resp = TransmissionListSerializer(TX)
            logging.warn(resp.data)
            # Clean me up
            data = json.loads(json.dumps(resp.data, cls=UUIDEncoder))
            sio.emit("tx_response", {"UUID": str(message['UUID']), "data": data}, room=sid)
        else:
            sio.emit("tx_response", {"UUID": message['UUID'], "error": "PERMISSION TO OBJECT DENIED"}, room=sid)
    except Exception as e:
        if settings.SEND_TELEMETRY:
            sentry_sdk.capture_exception(e)
        sio.emit("tx_response", {"UUID": message['UUID'], "error": f"ERROR: {str(e)}"}, room=sid)
        

@sio.event
def deregister_tx_source(sid, message):
    for uuid in message["UUIDs"]:
        sio.leave_room(sid, f'tx_{uuid}')
        sio.emit("debug", {"data":f"disconnected to room tx_{uuid}"}, room=sid)

@sio.event
def register_tx_source(sid, message):
    for uuid in message["UUIDs"]:
        sio.enter_room(sid, f'tx_{uuid}')
        sio.emit("debug", {"data":f"connected to room tx_{uuid}"}, room=sid)
    


@sio.event
def connect(sid, environ, auth):
    JWT_authenticator = JWTAuthentication()
    
    try:
        jwt = environ["HTTP_AUTHORIZATION"]
        valid_jwt = JWT_authenticator.get_validated_token(jwt)
        user = JWT_authenticator.get_user(valid_jwt)
    except:
        raise ConnectionRefusedError('authentication failed')

    sio.save_session(sid, {'user': user})
    logging.debug(f"[+] User {user.email} has connected to the socket")
    sio.enter_room(sid, 'unicast')
    sio.enter_room(sid, f'alert_{user.userProfile.UUID}')
    sio.emit("debug", {"data": "Connected"}, room=sid)


@sio.event
def disconnect(sid):
    print("Client disconnected")
