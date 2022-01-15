import os
from django.http.response import HttpResponse
import socketio, logging
#from trunkplayerNG.wsgi import sio

logger = logging.getLogger(__name__)

mgr = socketio.KombuManager(os.getenv("CELERY_BROKER_URL", "ampq://user:pass@127.0.0.1/"))
sio = socketio.Server(async_mode='gevent', client_manager=mgr)




@sio.on('message')
def message(data):
    print(data)
    sio.emit('test',data)

def broadcast_new_transmission():
    sio.emit('new_transmission', room=[], data={})
    sio.emit()