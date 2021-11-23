import base64
from utils import TransmissionDetails


def new_transmission_handler(data):
    recorder = data["recorder"]
    json = data["json"]
    audio = data["audioFile"]

    Payload: TransmissionDetails = TransmissionDetails(json)
    audio_bytes: str = base64.b64decode(audio).decode()

    Payload = Payload._to_json()

    Payload["recorder"] = recorder
    Payload["audioFile"] = audio_bytes

    

    return Payload
