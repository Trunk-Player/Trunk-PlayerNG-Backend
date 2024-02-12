import logging

from django.conf import settings
from celery import shared_task
from django.dispatch import receiver


from mqtt.utils.mqtt_client import (
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



@shared_task
def dispatch_transmission(_transmission: dict) -> None:
    """
    Does the logic to send user notifications
    """
    publisher = RabbitMQPublisher(settings.MQTT_AMQP_QUQUE)
    publisher.publish_message(_transmission)
    publisher.close_connection()


    