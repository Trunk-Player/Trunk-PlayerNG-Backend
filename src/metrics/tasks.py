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

