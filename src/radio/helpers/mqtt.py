import json
import logging

from django.conf import settings
from radio.helpers.utils import UUIDEncoder

from radio.models import Transmission
from radio.signals import new_transmission

if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)

def _send_transmission_mqtt(_transmission: dict) -> None:
    """
    Handles Dispatching Transmission Signals
    """
    from mqtt.tasks import dispatch_transmission

    transmission:Transmission = Transmission.objects.get(
        UUID=_transmission["UUID"]
    )
    _transmission = json.loads(json.dumps(_transmission, cls=UUIDEncoder))
    logging.debug(f'[+] Handling Signal for TX:{transmission.UUID}')
    _transmission["recorder"] = {
        "site_id": transmission.recorder.site_id,
        "name": transmission.recorder.name,
        "recorder": transmission.recorder.UUID
    }

    _agency = []
    for agency in transmission.talkgroup.agency.all():
        _agency.append({
            "UUID": agency.UUID,
            "name": agency.name,
            "description": agency.description,
            "city": [ 
                {
                    "name": city.name,
                    "UUID": city.UUID,
                    "description": city.description,
                }
                for city in agency.city.all()
            ]
        })
    _transmission["talkgroup"] = { "agency":  _agency }


    dispatch_transmission.delay(
        _transmission
    )