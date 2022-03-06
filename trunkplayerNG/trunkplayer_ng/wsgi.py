"""
WSGI config for trunkplayerNG project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
import socketio

from radio.helpers.socket import sio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trunkplayerNG.settings")

django_app = get_wsgi_application()


application = socketio.WSGIApp(sio, wsgi_app=django_app)
