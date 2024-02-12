import logging

from celery import shared_task

from radio.helpers.cleanup import _prune_transmissions
from radio.helpers.mutations import _send_new_parental_mutation
from radio.helpers.incident import _send_incident, _forward_incident

from radio.helpers.notifications import (
    _broadcast_web_notification,
    _broadcast_user_notification,
    _send_transmission_notifications,
)

from radio.helpers.mqtt import (
    _send_transmission_mqtt
)

from radio.helpers.transmission import (
    _forward_transmission,
    _broadcast_transmission,
    _new_transmission_handler,
    _send_transmission_to_web,
    _forward_transmission_to_remote_instance,
)

logger = logging.getLogger(__name__)

@shared_task()
def forward_transmission(data: dict, tg_uuid: str, *args, **kwargs) -> None:
    """
    Iterates over Forwarders and dispatches send_transmission
    """
    _forward_transmission(data, tg_uuid)


@shared_task()
def send_transmission_to_web(data: dict, *args, **kwargs) -> None:
    """
    Sends socket.io messages to webclients
    """
    _send_transmission_to_web(data)


@shared_task()
def forward_transmission_to_remote_instance(
    data: dict,
    forwarder_name: str,
    recorder_key: str,
    forwarder_url: str,
    *args,
    **kwargs
) -> None:
    """
    Forwards a single TX to a single system
    """
    _forward_transmission_to_remote_instance(
        data, forwarder_name, recorder_key, forwarder_url
    )


@shared_task()
def forward_incidents(data: dict, created: bool, *args, **kwargs) -> None:
    """
    Iterates over Forwarders and dispatches send_Incident
    """
    _forward_incident(data, created)


@shared_task()
def send_incident(
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
    _send_incident(data, forwarder_name, recorder_key, forwarder_url, created)


@shared_task()
def import_radio_refrence(
    uuid: str, site_id: str, username: str, password: str, *args, **kwargs
) -> None:
    """
    Imports RR Data
    """
    from radio.helpers.radioreference import RR

    radio_refrence: RR = RR(site_id, username, password)
    radio_refrence.load_system(uuid)


@shared_task()
def prune_tranmissions(*args, **kwargs) -> None:
    """
    Prunes Transmissions per system based on age
    """
    _prune_transmissions()


@shared_task
def send_transmission_notifications(transmission: dict, *args, **kwargs) -> None:
    """
    Does the logic to send user notifications
    """
    _send_transmission_notifications(transmission)

@shared_task
def send_transmission_mqtt(transmission: dict, *args, **kwargs) -> None:
    """
    Does the logic to send user notifications
    """
    _send_transmission_mqtt(transmission)


@shared_task
def send_new_parental_mutation(uuid: str, type: str, event: str, *args, **kwargs) -> None:
    """
    Does the logic to send user notifications
    """
    _send_new_parental_mutation(uuid, type, event)


@shared_task
def broadcast_user_notification(
    alert_type: str,
    transmission: dict,
    alert_value: str,
    alertuser_uuid: str,
    app_rise_urls: str,
    app_rise_notification: bool,
    web_notification: bool,
    emergency: bool,
    title_template: str,
    body_template: str,
    *args,
    **kwargs
) -> None:
    """
    Sends the User a notification(s)
    """
    _broadcast_user_notification(
        alert_type,
        transmission,
        alert_value,
        alertuser_uuid,
        app_rise_urls,
        app_rise_notification,
        web_notification,
        emergency,
        title_template,
        body_template,
    )


@shared_task
def broadcast_web_notification(
    alertuser_uuid: str,
    transmission_uuid: str,
    emergency: bool,
    title: str,
    body: str,
    *args,
    **kwargs
) -> None:
    """
    Sends web based user notifications
    """
    _broadcast_web_notification(
        alertuser_uuid, transmission_uuid, emergency, title, body
    )


@shared_task
def broadcast_transmission(event: str, room: str, data: dict) -> None:
    """
    Sends new TX messsage to client
    """
    _broadcast_transmission(event, room, data)

@shared_task
def new_transmission_handler(data: dict):
    """
    Process new transmission
    """
    _new_transmission_handler(data)
