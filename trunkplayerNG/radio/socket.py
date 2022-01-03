import socketio, logging
from trunkplayerNG.wsgi import sio

logger = logging.getLogger(__name__)


@sio.on("connection-bind")
def connection_bind(sid, data):
    logger.debug("sid:",sid,"data",data)