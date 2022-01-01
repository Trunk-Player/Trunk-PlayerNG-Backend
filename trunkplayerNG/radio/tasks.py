import logging
from celery import shared_task
from celery.utils.log import get_task_logger

from radio.transmission import handle_forwarding, handle_incident_forwarding

logger = get_task_logger(__name__)

@shared_task()
def forward_Transmission(data):
    handle_forwarding(data)

@shared_task()
def forward_Incident(data):
    handle_incident_forwarding(data)