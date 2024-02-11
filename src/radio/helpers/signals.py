import logging

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from radio.models import TalkGroup, Unit, UserAlert, Transmission

from radio.signals import new_transmission

if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)

def _send_transmission_signal(_transmission: dict) -> None:
    """
    Handles Dispatching Transmission Signals
    """

    transmission:Transmission = Transmission.objects.get(
        UUID=_transmission["UUID"]
    )

    logging.debug(f'[+] Handling Signal for TX:{transmission.UUID}')
    new_transmission.send(
        sender=transmission,
        system=transmission.system,
        _transmission=_transmission
    )