import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trunkplayer_ng.settings")

app = Celery("trunkplayer_ng")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# app.conf.beat_schedule = {
#     "prune-transmissions": {
#         "task": "radio.tasks.prune_transmissions",
#         "schedule": 3600.0,
#         "args": None,
#     },
# }
