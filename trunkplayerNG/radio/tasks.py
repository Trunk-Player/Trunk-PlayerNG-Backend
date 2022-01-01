from datetime import date
import logging
from celery import shared_task
from celery.utils.log import get_task_logger

from radio.transmission import handle_forwarding, forwardTX
from radio.incident import forwardincident, handle_incident_forwarding 

logger = get_task_logger(__name__)

### Iterates over Forwarders and dispatches send_transmission
@shared_task()
def forward_Transmission(data):
    handle_forwarding(data)

### Makes Web request to forward incident to single Forwarder
@shared_task()
def send_transmission(data, ForwarderName, recorderKey, ForwarderURL):
    forwardTX(data, ForwarderName, recorderKey, ForwarderURL)


### Iterates over Forwarders and dispatches send_Incident
@shared_task()
def forward_Incident(data):
    handle_incident_forwarding(data)

### Makes Web request to forward incident to single Forwarder
@shared_task()
def send_Incident(data, ForwarderName, recorderKey, ForwarderURL):
    forwardincident(data, ForwarderName, recorderKey, ForwarderURL)

### Imports RR Data 
@shared_task()
def import_radio_refrence(UUID, siteid, username, password):
    from radio.radioreference import RR
    rr: RR = RR(siteid, username, password)
    rr.load_system(UUID)