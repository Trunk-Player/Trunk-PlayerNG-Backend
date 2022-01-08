import logging, requests, apprise
from re import T
import uuid
from os import posix_fadvise
from django.contrib.auth.models import User
from django.conf import settings
from radio.models import System, TalkGroup, Unit, UserAlert, Transmission, TransmissionUnit


if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


def handle_Transmission_Notification(TransmissionX:Transmission):
    """
    Handles Forwarding New Inicidents
    """
    from radio.tasks import publish_user_notification
    talkgroup = TransmissionX["talkgroup"]
    transunits = TransmissionX["units"]
    units = []
    for UnitX in transunits:
        units.append(UnitX.unit.UUID)

    logging.warning(talkgroup.UUID)

    for alert in UserAlert.objects.all():
        alert:UserAlert

        if talkgroup in alert.talkgroups.all():
            talkgroup:TalkGroup
            publish_user_notification.delay("Talkgroup", TransmissionX["UUID"], talkgroup.alphaTag, alert.appRiseURLs, alert.appRiseNotification, alert.webNotification)
        
        AlertUnits = alert.units.all()
        AlertUnitUUIDs = []
        for unit in AlertUnits:
            AlertUnitUUIDs.append(str(unit.UUID))

        ActiveUnits = []
        for unit in units:
            if str(unit) in AlertUnitUUIDs:
                ActiveUnits.append(unit)

        if len(ActiveUnits) > 0:
            AUs = ""

            for AU in ActiveUnits:
                AU:Unit = Unit.objects.get(UUID=AU)                
                if AU.description != "" and AU.description != None:
                    UnitID = AU.description
                else:
                    UnitID = str(AU.decimalID)
                AUs = AUs + f"; {UnitID}" 
                
            publish_user_notification.delay("Unit", TransmissionX["UUID"], AUs, alert.appRiseURLs, alert.appRiseNotification, alert.webNotification)

def send_user_notification(type, TransmissionUUID, value, appRiseURLs, appRiseNotification, webNotification):
    if webNotification:
        # broadcast_web_notification(alert, Transmission, type, value)
        pass
    if appRiseNotification:
        URLs = appRiseURLs.split(",")
        apobj = apprise.Apprise()

        for URL in URLs:
            apobj.add(URL)
        
        apobj.notify(    
            body=f'New Activity on {type} - {value}\nTransmission: {TransmissionUUID}',
            title=f'Activity Alert! - {type} - {value}',
        )