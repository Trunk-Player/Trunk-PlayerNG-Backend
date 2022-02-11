import logging, apprise, os, socketio

from django.conf import settings

from radio.models import TalkGroup, Unit, UserAlert

if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)

def format_message(
    type: str, value: str, url: str, emergency: bool, title: str, body: str
) -> tuple[str, str]:
    '''
    Takes the alert data and template to produce the fomatted message
    '''
    title = title.replace("%T", type)
    title = title.replace("%I", value)
    title = title.replace("%E", str(emergency))
    title = title.replace("%U", url)

    body = body.replace("%T", type)
    body = body.replace("%I", value)
    body = body.replace("%E", str(emergency))
    body = body.replace("%U", url)

    return title, body


def _send_transmission_notifications(TransmissionX: dict) -> None:
    """
    Handles Dispatching Transmission Notifications
    """
    from radio.tasks import broadcast_user_notification

    talkgroup = TransmissionX["talkgroup"]
    units = TransmissionX["units"]
    logging.debug(f'[+] Handling Notifications for TX:{TransmissionX["UUID"]}')

    for alert in UserAlert.objects.all():
        alert: UserAlert
        if not alert.enabled:
            continue

        try:
            if alert.talkgroups.filter(UUID=talkgroup).exists():
                talkgroupObject = TalkGroup.objects.get(UUID=talkgroup)
                talkgroup: TalkGroup
                if alert.emergencyOnly:
                    if TransmissionX["emergency"]:
                        broadcast_user_notification.delay(
                            "Talkgroup",
                            TransmissionX["UUID"],
                            talkgroupObject.alphaTag,
                            alert.user.UUID,
                            alert.appRiseURLs,
                            alert.appRiseNotification,
                            alert.webNotification,
                            TransmissionX["emergency"],
                            alert.body,
                            alert.title,
                        )
                        logging.debug(
                            f'[+] Handling Sent notification for TX:{TransmissionX["UUID"]} - {alert.name} - {alert.user}'
                        )
                else:
                    broadcast_user_notification.delay(
                        "Talkgroup",
                        TransmissionX["UUID"],
                        talkgroupObject.alphaTag,
                        alert.user.UUID,
                        alert.appRiseURLs,
                        alert.appRiseNotification,
                        alert.webNotification,
                        TransmissionX["emergency"],
                        alert.body,
                        alert.title,
                    )
                    logging.debug(
                        f'[+] Handling Sent notification for TX:{TransmissionX["UUID"]} - {alert.name} - {alert.user}'
                    )

            AlertUnits = alert.units.all()
            AlertUnitUUIDs = [str(unit.UUID) for unit in AlertUnits]

            ActiveUnits = []
            for unit in units:
                if str(unit) in AlertUnitUUIDs:
                    ActiveUnits.append(unit)

            if len(ActiveUnits) > 0:
                AUs = ""

                for AU in ActiveUnits:
                    AU: Unit = Unit.objects.get(UUID=AU)
                    if AU.description != "" and AU.description != None:
                        UnitID = AU.description
                    else:
                        UnitID = str(AU.decimalID)
                    AUs = AUs + f"; {UnitID}"

                if alert.emergencyOnly:
                    if TransmissionX["emergency"]:
                        broadcast_user_notification.delay(
                            "Unit",
                            TransmissionX["UUID"],
                            AUs,
                            alert.user.UUID,
                            alert.appRiseURLs,
                            alert.appRiseNotification,
                            alert.webNotification,
                            TransmissionX["emergency"],
                            alert.body,
                            alert.title,
                        )
                        logging.debug(
                            f'[+] Handling Sent notification for TX:{TransmissionX["UUID"]} - {alert.name} - {alert.user}'
                        )
                else:
                    broadcast_user_notification.delay(
                        "Unit",
                        TransmissionX["UUID"],
                        AUs,
                        alert.user.UUID,
                        alert.appRiseURLs,
                        alert.appRiseNotification,
                        alert.webNotification,
                        TransmissionX["emergency"],
                        alert.body,
                        alert.title,
                    )
                    logging.debug(
                        f'[+] Handling Sent notification for TX:{TransmissionX["UUID"]} - {alert.name} - {alert.user}'
                    )
        except Exception as e:
            if settings.SEND_TELEMETRY:
                capture_exception(e)




def _broadcast_user_notification(
    type: str,
    TransmissionUUID: str,
    value: str,
    alertuser_uuid: str,
    appRiseURLs: str,
    appRiseNotification: bool,
    webNotification: bool,
    emergency: bool,
    titleTemplate: str,
    bodyTemplate: str,
) -> None:

    body, title = format_message(
        type, value, TransmissionUUID, emergency, titleTemplate, bodyTemplate
    )

    if webNotification:
        from radio.tasks import broadcast_web_notification

        broadcast_web_notification.delay(
            alertuser_uuid, TransmissionUUID, emergency, title, body
        )

    if appRiseNotification:
        URLs = appRiseURLs.split(",")
        apobj = apprise.Apprise()

        for URL in URLs:
            apobj.add(URL)

        logging.debug(f"[+] BROADCASTING TO APPRISE {TransmissionUUID}")
        apobj.notify(
            body=body,
            title=title,
        )


def _broadcast_web_notification(
    alertuser_uuid: str, TransmissionUUID: str, emergency: bool, title: str, body: str
):
    mgr = socketio.KombuManager(
        os.getenv("CELERY_BROKER_URL", "ampq://user:pass@127.0.0.1/")
    )
    sio = socketio.Server(
        async_mode="gevent", client_manager=mgr, logger=False, engineio_logger=False
    )
    data = {
        "TransmissionUUID": TransmissionUUID,
        "emergency": emergency,
        "title": title,
        "body": body,
    }
    sio.emit(f"alert", data, room=f"alert_{alertuser_uuid}")
