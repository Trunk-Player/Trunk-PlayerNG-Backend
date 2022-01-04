import logging, requests, apprise
from os import posix_fadvise
from django.contrib.auth.models import User
from django.conf import settings
from radio.models import System, UserAlert, Transmission, TransmissionUnit
from trunkplayerNG.radio.tasks import publish_user_notification

if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


def handle_Transmission_Notification(TransmissionX:Transmission):
    """
    Handles Forwarding New Inicidents
    """
    talkgroup = TransmissionX.talkgroup
    transunits:TransmissionUnit = TransmissionX.units.all()
    units = []
    for unit in transunits:
        units.append(unit.unit)


    for alert in UserAlert.objects.all():
        alert:UserAlert

        if talkgroup in alert.talkgroups.all():
            publish_user_notification.delay("Talkgroup", TransmissionX, talkgroup, alert)
        
        AlertUnits = alert.units.all()
        for unit in units:
            if unit in AlertUnits:
                publish_user_notification.delay("Unit", TransmissionX, unit, alert)

def send_user_notification(type, Transmission, value, alert:UserAlert):
    if alert.webNotification:
        # broadcast_web_notification(alert, Transmission, type, value)
        pass
    if alert.appRiseNotification:
        URLs = alert.appRiseURLs.split(",")
        apobj = apprise.Apprise()

        for URL in URLs:
            apobj.add(URL)
        
        apobj.notify(    
            body=f'New Activity on {type} {value} Transmission {Transmission.UUID}',
            title=f'New {type} Activity Alert!',
        )