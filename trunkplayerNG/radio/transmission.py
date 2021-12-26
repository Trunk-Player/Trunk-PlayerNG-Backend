import base64, json
from .utils import TransmissionDetails
from django.core.files.base import ContentFile
from radio.models import System, SystemRecorder, TalkGroup


def new_transmission_handler(data):
    recorderUUID = data["recorder"]
    jsonx = data["json"]
    audio = data["audioFile"]

    recorder: SystemRecorder = SystemRecorder.objects.get(forwarderWebhookUUID=recorderUUID)
    system: System = recorder.system
    jsonx["system"] = str(system.UUID)

    Payload: TransmissionDetails = TransmissionDetails(jsonx)
    audio_bytes: bytes = base64.b64decode(audio)

    if Payload.validate_upload(recorderUUID):
        Payload = Payload._to_json()
    else:
        return False

    Payload["recorder"] = recorderUUID
    Payload["audioFile"] = ContentFile(audio_bytes, name=f'{data["name"]}.m4a')

    return Payload

