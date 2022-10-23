import logging
import json
import os
import socketio


from django.conf import settings

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed


mgr = socketio.KombuManager(
    settings.CELERY_BROKER_URL
)
sio = socketio.Server(
    async_mode="gevent_uwsgi", client_manager=mgr, logger=False, engineio_logger=False, cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS
)


if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


@sio.event
def tx_request(sid, message):
    """
    Answers a Socket request for a Transmisssion based on ACLs
    """
    from radio.helpers.utils import user_allowed_to_access_transmission, UUIDEncoder
    from radio.models import Transmission
    from radio.serializers import TransmissionListSerializer

    try:
        session = sio.get_session(sid)
        user = session["user"]
        transmission = Transmission.objects.get(UUID=message["UUID"])

        if user_allowed_to_access_transmission(transmission, user.userProfile.UUID):
            resp = TransmissionListSerializer(transmission)
            # Clean me up
            data = json.loads(json.dumps(resp.data, cls=UUIDEncoder))
            sio.emit(
                "tx_response", {"UUID": str(message["UUID"]), "data": data}, room=sid
            )
        else:
            sio.emit(
                "tx_response",
                {"UUID": message["UUID"], "error": "PERMISSION TO OBJECT DENIED"},
                room=sid,
            )
    except Exception as error:
        if settings.SEND_TELEMETRY:
            capture_exception(error)
        sio.emit(
            "tx_response",
            {"UUID": message["UUID"], "error": f"ERROR: {str(error)}"},
            room=sid,
        )


# @sio.event
# def deregister_tx_source(sid, message):
#     """
#     Deregisters a user to a Transmision source room
#     """
#     for uuid in message["UUIDs"]:
#         sio.leave_room(sid, f"tx_{uuid}")
#         sio.emit("debug", {"data": f"disconnected to room tx_{uuid}"}, room=sid)


# @sio.event
# def register_tx_source(sid, message):
#     """
#     Registers a user to a Transmision source room
#     """
#     for uuid in message["UUIDs"]:
#         sio.enter_room(sid, f"tx_{uuid}")
#         sio.emit("debug", {"data": f"connected to room tx_{uuid}"}, room=sid)

# pylint: disable=unused-argument
@sio.event
def connect(sid, environ, auth):
    """
    On user Connect
    """
    jwt_authenticator = JWTAuthentication()

    try:
        jwt = environ["HTTP_AUTHORIZATION"]
        valid_jwt = jwt_authenticator.get_validated_token(jwt)
        user = jwt_authenticator.get_user(valid_jwt)
    except InvalidToken:
        raise ConnectionRefusedError("authentication failed") from InvalidToken
    except AuthenticationFailed:
        raise ConnectionRefusedError("authentication failed") from InvalidToken

    sio.save_session(sid, {"user": user})
    logging.debug(f"[+] User {user.email} has connected to the socket")
    sio.enter_room(sid, "unicast")
    sio.enter_room(sid, "transmission_party_bus")
    sio.enter_room(sid, "parents_rapid_genetic_mutations")
    sio.enter_room(sid, f"alert_{user.userProfile.UUID}")
    sio.emit("debug", {"data": "Connected"}, room=sid)


@sio.event
def disconnect(sid):
    """
    On user Disconnect
    """
    print("Client disconnected")
