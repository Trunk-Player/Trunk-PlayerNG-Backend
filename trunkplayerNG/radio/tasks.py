from datetime import date
import logging
import os
from celery import shared_task
from celery.utils.log import get_task_logger
from django.http import request
import socketio


from radio.helpers.transmission import handle_forwarding, handle_web_forwarding,  forwardTX
from radio.helpers.incident import forwardincident, handle_incident_forwarding
from radio.helpers.cleanup import pruneTransmissions
from radio.helpers.notifications import send_user_notification

logger = get_task_logger(__name__)

### Iterates over Forwarders and dispatches send_transmission
@shared_task()
def forward_Transmission(data, TG_UUID, *args, **kwargs):
    handle_forwarding(data, TG_UUID)

### Iterates over Forwarders and dispatches send_transmission
@shared_task()
def send_transmission_to_web(data, *args, **kwargs):
    
    handle_web_forwarding(data)


### Makes Web request to forward incident to single Forwarder
@shared_task()
def send_transmission(data, ForwarderName, recorderKey, ForwarderURL,TG_UUID):
    forwardTX(data, ForwarderName, recorderKey, ForwarderURL, TG_UUID)


### Iterates over Forwarders and dispatches send_Incident
@shared_task()
def forward_Incident(data,created):
    handle_incident_forwarding(data, created)
  

### Makes Web request to forward incident to single Forwarder
@shared_task()
def send_Incident(data, ForwarderName, recorderKey, ForwarderURL, created):
    forwardincident(data, ForwarderName, recorderKey, ForwarderURL, created)

### Imports RR Data
@shared_task()
def import_radio_refrence(UUID, siteid, username, password):
    from radio.helpers.radioreference import RR

    rr: RR = RR(siteid, username, password)
    rr.load_system(UUID)

### Prunes Transmissions per system based on age
@shared_task()
def prune_tranmissions(data, ForwarderName, recorderKey, ForwarderURL, created):
    pruneTransmissions(data, ForwarderName, recorderKey, ForwarderURL, created)

@shared_task
def publish_user_notification(type, Transmission, value,  appRiseURLs, appRiseNotification, webNotification):
    send_user_notification(type, Transmission, value,  appRiseURLs, appRiseNotification, webNotification)

@shared_task
def broadcast_web_notification(alert, Transmission, type, value):
    pass