import logging
import requests

from django.conf import settings
from radio.models import System, SystemForwarder

if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)

def _forward_incident(data: dict, created: bool) -> None:
    """
    Handles Forwarding New Inicidents
    """
    from radio.tasks import send_incident

    system = System.objects.get(UUID=data["system"])

    for forwarder in SystemForwarder.objects.filter(
        enabled=True, forward_incidents=True
    ):
        forwarder: SystemForwarder
        if system in forwarder.forwarded_systems.all():
            send_incident.delay(
                data,
                forwarder.name,
                forwarder.recorder_key,
                forwarder.remote_url,
                created,
            )


def _send_incident(
    data: dict, forwarder_name: str, recorder_key: str, forwarder_url: str, created: bool
) -> None:
    """
    Forwards a single Incident via API Call
    """
    try:
        data["recorder"] = str(recorder_key)
        del data["system"]

        if created:
            response = requests.post(
                f"{forwarder_url}/api/radio/incident/forward", json=data
            )
        else:
            response = requests.put(
                f"{forwarder_url}/api/radio/incident/forward", json=data
            )
        assert response.ok
        logger.info(
            f"[+] SUCCESSFULLY FORWARDED INCIDENT {data['name']} to {forwarder_name} - {response.text}"
        )
    except Exception as error:
        logger.error(
            f"[!] FAILED FORWARDING INCIDENT {data['name']} to {forwarder_name}"
        )
        if settings.SEND_TELEMETRY:
            capture_exception(error)
        raise error
