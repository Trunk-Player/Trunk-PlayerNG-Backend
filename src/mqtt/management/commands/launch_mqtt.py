import json
from gevent import monkey
monkey.patch_all()

from django.core.management.base import BaseCommand
import pika
import paho.mqtt.client as mqtt
import gevent

from django.conf import settings

class Command(BaseCommand):
    help = 'Listens on a RabbitMQ queue and forwards messages to an MQTT topic using gevent for asynchronous operations'

    # def add_arguments(self, parser):
    #     parser.add_argument('--rabbitmq_queue', type=str, help='The RabbitMQ queue to subscribe to')
    #     parser.add_argument('--mqtt_topic', type=str, help='The MQTT topic to publish messages to')
    #     parser.add_argument('--mqtt_broker', type=str, help='The MQTT broker address')

    def handle(self, *args, **options):
        self.rabbitmq_queue = settings.MQTT_AMQP_QUQUE
        self.broker_url = settings.CELERY_BROKER_URL
        
        from mqtt.utils.mqtt_client import MqttClientManager
        self.mqtt_system = MqttClientManager()
        self.mqtt_system.launch()
    
        # Start the RabbitMQ consumer in a greenlet
        gevent.spawn(self.start_rabbitmq_consumer)

        # Start gevent's loop
        try:
            gevent.wait()
        except KeyboardInterrupt:
            print('Stopping...')
        finally:
            print('Disconnected from MQTT.')

    def start_rabbitmq_consumer(self):
        # Setup RabbitMQ connection and start consuming in a non-blocking manner
        connection_params = pika.URLParameters(self.broker_url)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.queue_declare(queue=self.rabbitmq_queue, durable=True)

        for method_frame, properties, body in channel.consume(self.rabbitmq_queue, inactivity_timeout=1, auto_ack=True):
            if method_frame:
                message = body.decode('utf-8')
            else:
                # Check if we should stop consuming (based on some condition or external signal)
                # If so, break from the loop and close RabbitMQ connection
                continue

            try:
                message = json.loads(message)
                self.mqtt_system.dispatch(message)
            except:
                print("ERROR")
                print(message)

        channel.cancel()
        connection.close()
        print('Disconnected from RabbitMQ.')
