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
    units = [UnitX.unit.UUID for UnitX in transunits]

    for alert in UserAlert.objects.all():
        alert:UserAlert

        if talkgroup in alert.talkgroups.all():
            talkgroup:TalkGroup
            if alert.emergencyOnly:
                if TransmissionX["emergency"]:
                    publish_user_notification.delay("Talkgroup", TransmissionX["UUID"], talkgroup.alphaTag, alert.appRiseURLs, alert.appRiseNotification, alert.webNotification, TransmissionX["emergency"], alert.body, alert.title)
            else:
                publish_user_notification.delay("Talkgroup", TransmissionX["UUID"], talkgroup.alphaTag, alert.appRiseURLs, alert.appRiseNotification, alert.webNotification, TransmissionX["emergency"], alert.body, alert.title)
        
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

            if alert.emergencyOnly:
                if TransmissionX["emergency"]:                
                    publish_user_notification.delay("Unit", TransmissionX["UUID"], AUs, alert.appRiseURLs, alert.appRiseNotification, alert.webNotification, TransmissionX["emergency"], alert.body, alert.title)
            else:
                publish_user_notification.delay("Unit", TransmissionX["UUID"], AUs, alert.appRiseURLs, alert.appRiseNotification, alert.webNotification, TransmissionX["emergency"], alert.body, alert.title)

def format_message(type: str, value: str, url: str, emergency: bool, title: str, body: str):
    title = title.replace("%T",type)
    title = title.replace("%I",value)
    title = title.replace("%E",str(emergency))
    title = title.replace("%U",url)

    body = body.replace("%T",type)
    body = body.replace("%I",value)
    body = body.replace("%E",str(emergency))
    body = body.replace("%U",url)

    return title, body

def send_user_notification(type, TransmissionUUID, value, appRiseURLs, appRiseNotification, webNotification, emergency, titleTemplate, bodyTemplate):
    if webNotification:
        # broadcast_web_notification(alert, Transmission, type, value)
        pass
    if appRiseNotification:
        URLs = appRiseURLs.split(",")
        apobj = apprise.Apprise()

        for URL in URLs:
            apobj.add(URL)
        
        body, title  = format_message(type,value, TransmissionUUID, emergency,titleTemplate,bodyTemplate)

        apobj.notify(    
            body=body,
            title=title,
        )
        