

import os
from celery import Celery
from django.conf import settings
from django.apps import apps


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trunkplayerNG.settings")

app = Celery("trunkplayerNG")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
