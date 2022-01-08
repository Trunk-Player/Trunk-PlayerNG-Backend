import os
from django.http.response import HttpResponse
import socketio, logging
from trunkplayerNG.trunkplayerNG.settings import BASE_DIR
from trunkplayerNG.wsgi import sio

logger = logging.getLogger(__name__)


def broadcast_new_transmission():
    

    sio.emit('new_transmission', room=[], data={})
    sio.emit()