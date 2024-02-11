import logging

from django.conf import settings
from celery import shared_task
from django.dispatch import receiver


from radio.signals import new_transmission
from mqtt.utils.mqtt import (
    _send_mqtt_message_signal
)
from mqtt.utils.publisher import (
    RabbitMQPublisher
)

logger = logging.getLogger(__name__)

@shared_task
def send_mqtt_message_signal(sender, client, userdata, msg) -> None:
    """
    Does the logic to send user notifications
    """
    _send_mqtt_message_signal(sender, client, userdata, msg)


@receiver(new_transmission)
@shared_task
def dispatch_transmission(sender, transmission, _transmission: dict) -> None:
    """
    Does the logic to send user notifications
    """
    transmission["recorder"] = {
        "site_id": transmission.recorder.site_id,
        "name": transmission.recorder.name,
        "recorder": transmission.recorder.UUID
    }

    _agency = []
    for agency in transmission.talkgroup.agency.all():
        _agency.append({
            "UUID": agency.UUID,
            "name": agency.name,
            "description": agency.description,
            "city": [ 
                {
                    "name": city.name,
                    "UUID": city.UUID,
                    "description": city.description,
                }
                for city in agency.city.all()
            ]
        })
    transmission["talkgroup"]["agency"] = _agency
    publisher = RabbitMQPublisher(settings.MQTT_AMQP_QUQUE)
    publisher.publish_message(_transmission)
    publisher.close_connection()


    