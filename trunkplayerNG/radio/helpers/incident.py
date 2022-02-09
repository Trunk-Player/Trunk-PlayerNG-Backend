import logging, requests

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

    SystemX = System.objects.get(UUID=data["system"])

    for Forwarder in SystemForwarder.objects.filter(
        enabled=True, forwardIncidents=True
    ):
        Forwarder: SystemForwarder
        if SystemX in Forwarder.forwardedSystems.all():
            send_incident.delay(
                data,
                Forwarder.name,
                Forwarder.recorderKey,
                Forwarder.remoteURL,
                created,
            )


def _send_incident(
    data: dict, ForwarderName: str, recorderKey: str, ForwarderURL: str, created: bool
) -> None:
    """
    Forwards a single Incident via API Call
    """
    try:
        data["recorder"] = str(recorderKey)
        del data["system"]

        if created:
            Response = requests.post(
                f"{ForwarderURL}/api/radio/incident/forward", json=data
            )
        else:
            Response = requests.put(
                f"{ForwarderURL}/api/radio/incident/forward", json=data
            )
        assert Response.ok
        logger.info(
            f"[+] SUCCESSFULLY FORWARDED INCIDENT {data['name']} to {ForwarderName} - {Response.text}"
        )
    except Exception as e:
        logger.error(
            f"[!] FAILED FORWARDING INCIDENT {data['name']} to {ForwarderName}"
        )
        if settings.SEND_TELEMETRY:
            capture_exception(e)
        raise (e)
