import pika
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

class RabbitMQPublisher:
    def __init__(self, queue_name):
        self.queue_name = queue_name
        self.connection = self.create_connection()
        self.channel = self.connection.channel()
        self.declare_queue()

    def create_connection(self):
        parameters = pika.URLParameters(settings.CELERY_BROKER_URL)
        return pika.BlockingConnection(parameters)

    def declare_queue(self):
        self.channel.queue_declare(queue=self.queue_name, durable=True)

    def publish_message(self, message):
        self.channel.basic_publish(exchange='',
                                   routing_key=self.queue_name,
                                   body=message,
                                   properties=pika.BasicProperties(
                                       delivery_mode=2,  # make message persistent
                                   ))
        logger.debug(f" [x] Sent '{message}'")

    def close_connection(self):
        self.connection.close()

