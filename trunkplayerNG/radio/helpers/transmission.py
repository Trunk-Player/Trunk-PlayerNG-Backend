import base64, logging, os, uuid, requests, socketio

from django.conf import settings
from django.core.files.base import ContentFile
from asgiref.sync import sync_to_async

from .utils import TransmissionDetails
from radio.models import ScanList, Scanner, System, SystemRecorder, SystemForwarder, TalkGroup


if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


def new_transmission_handler(data: dict) -> dict:
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
    name = data["name"].split(".")
    Payload["audioFile"] = ContentFile(
        audio_bytes, name=f'{name[0]}_{str(uuid.uuid4()).split("-")[-1]}.{name[1]}'
    )

    forward_Transmission.delay(data, Payload["talkgroup"])
    return Payload


def handle_web_forwarding(data: dict) -> None:
    """
    Handles Forwarding New Transmissions
    """
    from radio.tasks import broadcast_transmission

    talkgroup = TalkGroup.objects.filter(UUID=data["talkgroup"])
    broadcast_transmission.delay(f"tx_{data['talkgroup']}",  f'tx_{data["talkgroup"]}', data)

    scanlists = ScanList.objects.filter(talkgroups__in=talkgroup)
    for scanlist in scanlists:
        broadcast_transmission.delay(f"tx_{scanlist.UUID}", f'tx_{scanlist.UUID}', data )
        
    scanners = Scanner.objects.filter(scanlists__in=scanlists)
    for scanner in scanners:
       broadcast_transmission.delay(f"tx_{scanner.UUID}", f'tx_{scanner.UUID}', data )




def handle_forwarding(data, TG_UUID: str) -> None:
    """
    Handles Forwarding New Transmissions
    """
    from radio.tasks import send_transmission

    recorder: SystemRecorder = SystemRecorder.objects.get(
        forwarderWebhookUUID=data["recorder"]
    )

    talkgroup: TalkGroup = TalkGroup.objects.get(UUID=TG_UUID)

    for Forwarder in SystemForwarder.objects.filter(enabled=True):
        Forwarder: SystemForwarder
        if recorder.system in Forwarder.forwardedSystems.all():
            if len(Forwarder.talkGroupFilter.all()) == 0:
                send_transmission.delay(
                    data,
                    Forwarder.name,
                    Forwarder.recorderKey,
                    Forwarder.remoteURL,
                    TG_UUID,
                )
            if not talkgroup in Forwarder.talkGroupFilter.all():
                send_transmission.delay(
                    data,
                    Forwarder.name,
                    Forwarder.recorderKey,
                    Forwarder.remoteURL,
                    TG_UUID,
                )


def forwardTX(
    data: dict, ForwarderName: str, recorderKey: str, ForwarderURL: str, TG_UUID: str
) -> None:
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

        if settings.SEND_TELEMETRY:
            capture_exception(e)
        raise (e)
        
def _broadcast_tx(event: str, room: str, data: dict):
    try:
        mgr = socketio.KombuManager(
            os.getenv("CELERY_BROKER_URL", "ampq://user:pass@127.0.0.1/")
        )
        sio = socketio.Server(
            async_mode="gevent", client_manager=mgr, logger=False, engineio_logger=False
        )
        sync_to_async(sio.emit(event, data, room=room))
        logging.debug(f"[+] BROADCASTING TO {room}")
    except Exception as e:
        if settings.SEND_TELEMETRY:
            capture_exception(e)
        raise(e)