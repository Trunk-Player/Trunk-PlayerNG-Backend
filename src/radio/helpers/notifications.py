import os
import logging
from unittest.mock import sentinel
import apprise
import sentry_sdk
import socketio

from datetime import timedelta

from django.utils import timezone
from django.conf import settings

from radio.models import TalkGroup, Unit, UserAlert, Transmission

if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


def format_message(
    msg_type: str, value: str, url: str, emergency: bool, title: str, body: str
) -> tuple[str, str]:
    """
    Takes the alert data and template to produce the fomatted message
    """
    title = title.replace("%T", msg_type)
    title = title.replace("%I", value)
    title = title.replace("%E", str(emergency))
    title = title.replace("%U", url)

    body = body.replace("%T", msg_type)
    body = body.replace("%I", value)
    body = body.replace("%E", str(emergency))
    body = body.replace("%U", url)

    return title, body


def _send_transmission_notifications(transmission: dict) -> None:
    """
    Handles Dispatching Transmission Notifications
    """
    from radio.tasks import broadcast_user_notification


    talkgroup = transmission["talkgroup"]
    units = transmission["units"]
    logging.debug(f'[+] Handling Notifications for TX:{transmission["UUID"]}')

    for alert in UserAlert.objects.all():
        alert: UserAlert
        if not alert.enabled:
            continue

        if alert.count != 1:
            transmission_count = Transmission.objects.filter(talkgroup__UUID=talkgroup, end_time__gte=timezone.now()-timedelta(seconds=alert.trigger_time)) 
            if len(transmission_count) < alert.count:
                continue


        try:
            if alert.talkgroups.filter(UUID=talkgroup).exists():
                talkgroup_object = TalkGroup.objects.get(UUID=talkgroup)
                talkgroup: TalkGroup
                if alert.emergency_only:
                    if transmission["emergency"]:
                        broadcast_user_notification.delay(
                            "Talkgroup",
                            transmission["UUID"],
                            talkgroup_object.alpha_tag,
                            alert.user.UUID,
                            alert.app_rise_urls,
                            alert.app_rise_notification,
                            alert.web_notification,
                            transmission["emergency"],
                            alert.body,
                            alert.title,
                        )
                        logging.debug(
                            f'[+] Handling Sent notification for TX:{transmission["UUID"]} - {alert.name} - {alert.user}'
                        )
                else:
                    broadcast_user_notification.delay(
                        "Talkgroup",
                        transmission["UUID"],
                        talkgroup_object.alpha_tag,
                        alert.user.UUID,
                        alert.app_rise_urls,
                        alert.app_rise_notification,
                        alert.web_notification,
                        transmission["emergency"],
                        alert.body,
                        alert.title,
                    )
                    logging.debug(
                        f'[+] Handling Sent notification for TX:{transmission["UUID"]} - {alert.name} - {alert.user}'
                    )

            alert_units = alert.units.all()
            alert_unit_uuids = [str(unit.UUID) for unit in alert_units]

            active_units = []
            for unit in units:
                if str(unit) in alert_unit_uuids:
                    active_units.append(unit)

            if len(active_units) > 0:
                active_unit_list = ""

                for active_unit in active_units:
                    active_unit: Unit = Unit.objects.get(UUID=active_unit)
                    if active_unit.description != "" and active_unit.description is not None:
                        unit_id = active_unit.description
                    else:
                        unit_id = str(active_unit.decimal_id)
                    active_unit_list = active_unit_list + f"; {unit_id}"

                if alert.emergency_only:
                    if transmission["emergency"]:
                        broadcast_user_notification.delay(
                            "Unit",
                            transmission["UUID"],
                            active_unit_list,
                            alert.user.UUID,
                            alert.app_rise_urls,
                            alert.app_rise_notification,
                            alert.web_notification,
                            transmission["emergency"],
                            alert.body,
                            alert.title,
                        )
                        logging.debug(
                            f'[+] Handling Sent notification for TX:{transmission["UUID"]} - {alert.name} - {alert.user}'
                        )
                else:
                    broadcast_user_notification.delay(
                        "Unit",
                        transmission["UUID"],
                        active_unit_list,
                        alert.user.UUID,
                        alert.app_rise_urls,
                        alert.app_rise_notification,
                        alert.web_notification,
                        transmission["emergency"],
                        alert.body,
                        alert.title,
                    )
                    logging.debug(
                        f'[+] Handling Sent notification for TX:{transmission["UUID"]} - {alert.name} - {alert.user}'
                    )
        except Exception as error:
            if settings.SEND_TELEMETRY:
                capture_exception(error)


def _broadcast_user_notification(
    msg_type: str,
    trannsmission_uuid: str,
    alert_value: str,
    alertuser_uuid: str,
    app_rise_urls: str,
    app_rise_notification: bool,
    web_notification: bool,
    emergency: bool,
    title_template: str,
    body_template: str,
) -> None:

    body, title = format_message(
        msg_type, alert_value, trannsmission_uuid, emergency, title_template, body_template
    )

    if web_notification:
        from radio.tasks import broadcast_web_notification

        broadcast_web_notification.delay(
            alertuser_uuid, trannsmission_uuid, emergency, title, body
        )

    if app_rise_notification:
        urls = app_rise_urls.split(",")
        apobj = apprise.Apprise()

        for url in urls:
            apobj.add(url)

        logging.debug(f"[+] BROADCASTING TO APPRISE {trannsmission_uuid}")
        apobj.notify(
            body=body,
            title=title,
        )


def _broadcast_web_notification(
    alertuser_uuid: str, trannsmission_uuid: str, emergency: bool, title: str, body: str
) -> None:
    mgr = socketio.KombuManager(
        os.getenv("CELERY_BROKER_URL", "ampq://user:pass@127.0.0.1/")
    )
    sio = socketio.Server(
        async_mode="gevent", client_manager=mgr, logger=True, engineio_logger=True
    )
    data = {
        "trannsmission_uuid": trannsmission_uuid,
        "emergency": emergency,
        "title": title,
        "body": body,
    }
    sio.emit("alert", data, room=f"alert_{alertuser_uuid}")
