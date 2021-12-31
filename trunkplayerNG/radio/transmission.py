import base64, json
import requests

from requests.api import request
from .utils import TransmissionDetails
from django.core.files.base import ContentFile
from radio.models import System, SystemRecorder, SystemForwarder


def new_transmission_handler(data):
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

    handle_forwarding(data)

    return Payload

def handle_forwarding(data):
    recorder: SystemRecorder = SystemRecorder.objects.get(
        forwarderWebhookUUID=data["recorder"]
    )
    

    for Forwarder in SystemForwarder.objects.filter(enabled=True):
        Forwarder:SystemForwarder
        try:
            if recorder.system in Forwarder.forwardedSystems.all():
                data["recorder"] = str(Forwarder.recorderKey)
                Response = requests.post(f"{Forwarder.remoteURL}/api/radio/transmission/create", data=data)
                assert Response.ok
        except AssertionError: 
            print(f"[!] FAILED FORWARDING TX")
        except requests.exceptions.SSLError:
            print(f"[!] FAILED FORWARDING TX")