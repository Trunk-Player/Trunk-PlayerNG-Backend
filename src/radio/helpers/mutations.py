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

def _send_new_parental_mutation(uuid: str, type: str, event: str) -> None:
    """
    Handles sending parent collection updates
    """
    from radio.tasks import broadcast_transmission

    logger.debug(f"[+] SENDING NEW PARENT MUTATION NOTIFICATION - {uuid} - {type} - {event}")

    payload = {'uuid': uuid, 'type': type, 'event': event}


    broadcast_transmission.delay('parents_rapid_genetic_mutations', 'parents_rapid_genetic_mutations', payload)