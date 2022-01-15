"""
WSGI config for trunkplayerNG project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import gevent.monkey
gevent.monkey.patch_all()

import os
from django.core.wsgi import get_wsgi_application
import socketio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trunkplayerNG.settings")

django_app  = get_wsgi_application()

mgr = socketio.KombuManager(os.getenv("CELERY_BROKER_URL", "ampq://user:pass@127.0.0.1/"))
sio = socketio.Server(async_mode='gevent_uwsgi', client_manager=mgr)
application = socketio.WSGIApp(sio, django_app)