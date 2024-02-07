"""
WSGI config for trunkplayer_ng project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
import socketio

from django.conf import settings

from radio.helpers.socket import sio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trunkplayer_ng.settings")

django_app = get_wsgi_application()


# mgr = socketio.KombuManager(
#     settings.SOCKETS_BROKER_URL
# )
# sio = socketio.Server(
#     async_mode="gevent",
#     client_manager=mgr,
#     logger=True,
#     engineio_logger=True,
#     cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS
# )

application = socketio.WSGIApp(sio, wsgi_app=django_app)
