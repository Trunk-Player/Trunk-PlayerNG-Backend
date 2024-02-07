import logging

from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from radio.models import System, Transmission

if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)

def _prune_transmissions() -> None:
    """
    Prunes transmissions when set in the database
    """

    for system in System.objects.all():
        system: System

        if system.prune_transmissions:
            prunetime = timezone.now() - timedelta(
                days=system.prune_transmissions_after_days
            )
            TXs = Transmission.objects.filter(system=system, start_time__lte=prunetime)

            try:
                TXs.delete()
            except Exception as e:
                if settings.SEND_TELEMETRY:
                    capture_exception(e)
                logging.error(
                    f"[!] ERROR PRUNING TRANSMISSIONS ON SYSTEM {str(system)}"
                )
