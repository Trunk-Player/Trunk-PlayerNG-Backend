from asyncio import tasks
import os

from celery import Celery
from celery.schedules import crontab

from django.conf import settings
from django.apps import apps


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trunkplayerNG.settings")

app = Celery("trunkplayerNG")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'prune-transmissions': {
        'task': 'radio.tasks.prune_transmissions',
        'schedule': 3600.0,
        'args': None
    },
}