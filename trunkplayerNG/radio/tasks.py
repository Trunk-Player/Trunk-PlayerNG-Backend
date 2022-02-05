import logging

from celery import shared_task
from asgiref.sync import sync_to_async
from django.conf import settings


from radio.helpers.incident import forwardincident, handle_incident_forwarding
from radio.helpers.cleanup import _prune_transmissions

from radio.helpers.notifications import (
    handle_transmission_notification,
    broadcast_user_notification,
)

from radio.helpers.transmission import (
    handle_forwarding,
    handle_web_forwarding,
    forwardTX,
)

if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


@shared_task()
def forward_Transmission(data: dict, tg_uuid: str, *args, **kwargs):
    """
    Iterates over Forwarders and dispatches send_transmission
    """
    handle_forwarding(data, tg_uuid)


@shared_task()
def send_transmission_to_web(data: dict, *args, **kwargs):
    """
    Sends socket.io messages to webclients
    """
    sync_to_async(handle_web_forwarding(data))


@shared_task()
def send_transmission(
    data: dict,
    forwarder_name: str,
    recorder_key: str,
    forwarder_url: str,
    tg_uuid: str,
    *args,
    **kwargs
):
    """
    Forwards a single TX to a single system
    """
    sync_to_async(forwardTX(data, forwarder_name, recorder_key, forwarder_url, tg_uuid))


@shared_task()
def forward_Incident(data: dict, created: bool, *args, **kwargs):
    """
    Iterates over Forwarders and dispatches send_Incident
    """
    handle_incident_forwarding(data, created)


@shared_task()
def send_Incident(
    data: dict,
    forwarder_name: str,
    recorder_key: str,
    forwarder_url: str,
    created: bool,
    *args,
    **kwargs
):
    """
    Forwards a single Incident to a single system
    """
    forwardincident(data, forwarder_name, recorder_key, forwarder_url, created)


@shared_task()
def import_radio_refrence(
    uuid: str, site_id: str, username: str, password: str, *args, **kwargs
):
    """
    Imports RR Data
    """
    from radio.helpers.radioreference import RR

    rr: RR = RR(site_id, username, password)
    rr.load_system(uuid)


@shared_task()
def prune_tranmissions(*args, **kwargs):
    """
    Prunes Transmissions per system based on age
    """
    _prune_transmissions()


@shared_task
def send_tx_notifications(transmission: dict, *args, **kwargs):
    """
    Does the logic to send user notifications
    """
    sync_to_async(handle_transmission_notification(transmission))


@shared_task
def publish_user_notification(
    type: str,
    transmission: dict,
    value: str,
    app_rise_urls: str,
    app_rise_notification: bool,
    web_notification: bool,
    emergency: bool,
    title_template: str,
    body_template: str,
    *args,
    **kwargs
):
    """
    Sends the User a notification(s)
    """
    broadcast_user_notification(
        type,
        transmission,
        value,
        app_rise_urls,
        app_rise_notification,
        web_notification,
        emergency,
        title_template,
        body_template,
    )


@shared_task
def broadcast_web_notification(alert, transmission, type, value, *args, **kwargs):
    pass
