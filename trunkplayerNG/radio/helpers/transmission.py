import base64, json, logging
import os
import requests
from django.conf import settings

from requests.api import request
import socketio
from .utils import TransmissionDetails
from django.core.files.base import ContentFile
from radio.models import System, SystemRecorder, SystemForwarder, TalkGroup
import asyncio
if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)



def new_transmission_handler(data):
    """
    Converts API call to DB format and stores file
    """
    from radio.tasks import forward_Transmission
    

    recorderUUID = data["recorder"]
    jsonx = data["json"]
    audio = data["audioFile"]

    recorder: SystemRecorder = SystemRecorder.objects.get(
        forwarderWebhookUUID=recorderUUID
    )
    system: System = recorder.system
    jsonx["system"] = str(system.UUID)

    Payload: TransmissionDetails = TransmissionDetails(jsonx)
    audio_bytes: bytes = base64.b64decode(audio)

    if Payload.validate_upload(recorderUUID):
        Payload = Payload._to_json()
    else:
        return False

    Payload["recorder"] = recorderUUID
    Payload["audioFile"] = ContentFile(audio_bytes, name=f'{data["name"]}')
   
    forward_Transmission.delay(data, Payload["talkgroup"])
    return Payload


def handle_forwarding(data, TG_UUID):
    """
    Handles Forwarding New Transmissions
    """
    from radio.tasks import send_transmission

    recorder: SystemRecorder = SystemRecorder.objects.get(
        forwarderWebhookUUID=data["recorder"]
    )

    talkgroup: TalkGroup = TalkGroup.objects.get(UUID=TG_UUID)

    mgr = socketio.KombuManager(os.getenv("CELERY_BROKER_URL", "ampq://user:pass@127.0.0.1/"))
    sio = socketio.Server(async_mode='gevent', client_manager=mgr, logger=True, engineio_logger=True)
    sio.emit("TX", f"New TX {data['name']}")

    for Forwarder in SystemForwarder.objects.filter(enabled=True):
        Forwarder: SystemForwarder
        if recorder.system in Forwarder.forwardedSystems.all():
            if len(Forwarder.talkGroupFilter.all()) == 0:
                send_transmission.delay(
                    data, Forwarder.name, Forwarder.recorderKey, Forwarder.remoteURL,TG_UUID
                )
            if not talkgroup in Forwarder.talkGroupFilter.all():
                send_transmission.delay(
                    data, Forwarder.name, Forwarder.recorderKey, Forwarder.remoteURL,TG_UUID
                )


def forwardTX(data, ForwarderName, recorderKey, ForwarderURL, TG_UUID):
    """
    Sends a single new transmission via API Call
    """
    try:
        data["recorder"] = str(recorderKey)
        Response = requests.post(
            f"{ForwarderURL}/api/radio/transmission/create", json=data
        )
        assert Response.ok
        logger.info(
            f"[+] SUCCESSFULLY FORWARDED TRANSMISSION {data['name']} to {ForwarderName} - {Response.text}"
        )
        
        return f"[+] SUCCESSFULLY FORWARDED TRANSMISSION {data['name']} to {ForwarderName} - {Response.text}"
    except Exception as e:        
        logger.warning(f"[!] FAILED FORWARDING TX {data['name']} to {ForwarderName}")
        
        # if settings.SEND_TELEMETRY:
        #     capture_exception(e)
        raise (e)
