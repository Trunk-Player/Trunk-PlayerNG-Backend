import logging, requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from radio.models import System, SystemForwarder, Transmission


if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


def pruneTransmissions():
    for system in System.objects.all():
        system:System

        if system.pruneTransmissions:
            prunetime = timezone.now() - timedelta(days=system.pruneTransmissionsAfterDays)
            TXs = Transmission.objects.filter(system=system, startTime__lte=prunetime)
            for TX in TXs:
                TX:Transmission

                Units = TX.units.all()
                Units.delete()

                freqs = TX.frequencys.all()
                freqs.delete()
            TXs.delete()