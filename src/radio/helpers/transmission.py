import base64
import logging
import os
import uuid
import requests
import sentry_sdk
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
from radio.serializers import TransmissionUploadSerializer


if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


def _new_transmission_handler(data: dict) -> dict:
    """
    Converts API call to DB format and stores file
    """
    from radio.tasks import forward_transmission, send_transmission_to_web, send_transmission_notifications

    logger.info(f"Got new transmission - {data['name'].split('.')[0]}", extra=data["json"])
    recorder_uuid = data["recorder"]
    jsonx = data["json"]
    audio = data["audio_file"]
    tx_uuid = data["UUID"]

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

    payload["UUID"] = tx_uuid
    payload["recorder"] = recorder_uuid
    payload["system"] = str(system.UUID)

    name = data["name"].split(".")
    payload["audio_file"] = ContentFile(
        audio_bytes, name=f'{name[0]}_{str(uuid.uuid4()).rsplit("-", maxsplit=1)[-1]}.{name[1]}'
    )
    
    transmission = TransmissionUploadSerializer(data=payload, partial=True)

    if transmission.is_valid(raise_exception=True):
        transmission.save()
        socket_data = {
            "UUID": transmission.data["UUID"],
            "talkgroup": transmission.data["talkgroup"],
        }
        send_transmission_to_web.delay(socket_data, payload["talkgroup"])
        send_transmission_notifications.delay(transmission.data)
        forward_transmission.delay(data, payload["talkgroup"])
        return transmission.data


def _get_transmission_parents(talkgroup_uuid: str) -> dict[list[dict[str, str]]]:
    meet_the_parents = []

    talkgroup:TalkGroup = TalkGroup.objects.filter(UUID=talkgroup_uuid)
    meet_the_parents.append({'uuid': list(talkgroup.values_list("UUID", flat=True)), 'type': 'talkgroup'})

    scanlists = ScanList.objects.filter(talkgroups__in=talkgroup)
    meet_the_parents.append({'uuid':list(scanlists.values_list("UUID", flat=True)), 'type': 'scanlist'})

    scanners = Scanner.objects.filter(scanlists__in=scanlists)
    meet_the_parents.append({'uuid':list(scanners.values_list("UUID", flat=True)), 'type': 'scanner'})

    return meet_the_parents

def _send_transmission_to_web(data: dict) -> None:
    """
    Handles Forwarding New Transmissions
    """
    from radio.tasks import broadcast_transmission

    logger.debug(f"[+] GOT NEW TX - {data['UUID']}")

    parents = _get_transmission_parents(data["talkgroup"])
    payload = {'uuid': data['UUID'], 'parents': parents}


    broadcast_transmission.delay('transmission_party_bus', 'transmission_party_bus', payload)

    # talkgroup = TalkGroup.objects.filter(UUID=data["talkgroup"])
    # broadcast_transmission.delay(
    #     f"tx_{data['talkgroup']}", f'tx_{data["talkgroup"]}', data
    # )

    # scanlists = ScanList.objects.filter(talkgroups__in=talkgroup)
    # for scanlist in scanlists:
    #     broadcast_transmission.delay(f"tx_{scanlist.UUID}", f"tx_{scanlist.UUID}", data)

    # scanners = Scanner.objects.filter(scanlists__in=scanlists)
    # for scanner in scanners:
    #     broadcast_transmission.delay(f"tx_{scanner.UUID}", f"tx_{scanner.UUID}", data)


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
            settings.CELERY_BROKER_URL
        )
        sio = socketio.Server(
            async_mode="gevent", client_manager=mgr, logger=False, engineio_logger=False, cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS
        )
        sio.emit(event, data, room=room)
        logger.debug(f"[+] BROADCASTING TO {room}")
    except Exception as error:
        if settings.SEND_TELEMETRY:
            capture_exception(error)
        raise error
