import base64
import logging
import os
import uuid
import requests
import socketio

from django.conf import settings
from django.core.files.base import ContentFile

from radio.helpers.utils import TransmissionDetails
from radio.models import (
    ScanList,
    Scanner,
    System,
    SystemRecorder,
    SystemForwarder,
    TalkGroup,
)


if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


def new_transmission_handler(data: dict) -> dict:
    """
    Converts API call to DB format and stores file
    """
    from radio.tasks import forward_transmission

    recorder_uuid = data["recorder"]
    jsonx = data["json"]
    audio = data["audio_file"]

    recorder: SystemRecorder = SystemRecorder.objects.get(
        api_key=recorder_uuid
    )
    system: System = recorder.system
    jsonx["system"] = str(system.UUID)

    payload: TransmissionDetails = TransmissionDetails(jsonx)
    audio_bytes: bytes = base64.b64decode(audio)

    if payload.validate_upload(recorder_uuid):
        payload = payload.to_json()
    else:
        return False

    payload["recorder"] = recorder_uuid
    name = data["name"].split(".")
    payload["audio_file"] = ContentFile(
        audio_bytes, name=f'{name[0]}_{str(uuid.uuid4()).rsplit("-", maxsplit=1)[-1]}.{name[1]}'
    )

    forward_transmission.delay(data, payload["talkgroup"])
    return payload


def _send_transmission_to_web(data: dict) -> None:
    """
    Handles Forwarding New Transmissions
    """
    from radio.tasks import broadcast_transmission

    logging.debug(f"[+] GOT NEW TX - {data['UUID']}")

    talkgroup = TalkGroup.objects.filter(UUID=data["talkgroup"])
    broadcast_transmission.delay(
        f"tx_{data['talkgroup']}", f'tx_{data["talkgroup"]}', data
    )

    scanlists = ScanList.objects.filter(talkgroups__in=talkgroup)
    for scanlist in scanlists:
        broadcast_transmission.delay(f"tx_{scanlist.UUID}", f"tx_{scanlist.UUID}", data)

    scanners = Scanner.objects.filter(scanlists__in=scanlists)
    for scanner in scanners:
        broadcast_transmission.delay(f"tx_{scanner.UUID}", f"tx_{scanner.UUID}", data)


def _forward_transmission(data, talkgroup_uuid: str) -> None:
    """
    Handles Forwarding New Transmissions
    """
    from radio.tasks import forward_transmission_to_remote_instance

    recorder: SystemRecorder = SystemRecorder.objects.get(
        api_key=data["recorder"]
    )

    talkgroup: TalkGroup = TalkGroup.objects.get(UUID=talkgroup_uuid)

    for forwarder in SystemForwarder.objects.filter(enabled=True):
        forwarder: SystemForwarder
        if recorder.system in forwarder.forwarded_systems.all():
            if len(forwarder.talkgroup_filter.all()) == 0:
                forward_transmission_to_remote_instance.delay(
                    data,
                    forwarder.name,
                    forwarder.recorder_key,
                    forwarder.remote_url,
                )
            if not talkgroup in forwarder.talkgroup_filter.all():
                forward_transmission_to_remote_instance.delay(
                    data,
                    forwarder.name,
                    forwarder.recorder_key,
                    forwarder.remote_url,
                )


def _forward_transmission_to_remote_instance(
    data: dict, forwarder_name: str, recorder_key: str, forwarder_url: str
) -> None:
    """
    Sends a single new transmission via API Call
    """
    try:
        data["recorder"] = str(recorder_key)
        response = requests.post(
            f"{forwarder_url}/api/radio/transmission/create", json=data
        )
        assert response.ok
        logger.info(
            f"[+] SUCCESSFULLY FORWARDED TRANSMISSION {data['name']} to {forwarder_name} - {response.text}"
        )

        return f"[+] SUCCESSFULLY FORWARDED TRANSMISSION {data['name']} to {forwarder_name} - {response.text}"
    except Exception as error:
        logger.warning(f"[!] FAILED FORWARDING TX {data['name']} to {forwarder_name}")

        if settings.SEND_TELEMETRY:
            capture_exception(error)
        raise error


def _broadcast_transmission(event: str, room: str, data: dict):
    try:
        mgr = socketio.KombuManager(
            os.getenv("CELERY_BROKER_URL", "ampq://user:pass@127.0.0.1/")
        )
        sio = socketio.Server(
            async_mode="gevent", client_manager=mgr, logger=False, engineio_logger=False
        )
        sio.emit(event, data, room=room)
        logging.debug(f"[+] BROADCASTING TO {room}")
    except Exception as error:
        if settings.SEND_TELEMETRY:
            capture_exception(error)
        raise error
