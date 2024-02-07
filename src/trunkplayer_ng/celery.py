from __future__ import absolute_import, unicode_literals

import os
from celery import Celery

from django.apps import apps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trunkplayer_ng.settings')

app = Celery('trunkplayer_ng')
app.config_from_object('django.conf:settings', namespace='CELERY')

#app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])
app.autodiscover_tasks()