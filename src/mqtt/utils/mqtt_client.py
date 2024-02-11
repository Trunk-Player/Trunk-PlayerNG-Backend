import logging

import gevent
from django.dispatch import receiver

import paho.mqtt.client as mqtt

from mqtt.signals import mqtt_message

from radio.signals import new_transmission

from radio.models import (
    TalkGroup,
    Transmission,
    System,
    Agency
)

logger = logging.getLogger(__name__)

def _send_mqtt_message_signal(sender, client, userdata, msg) -> None:
    mqtt_message.send(
        sender=sender,
        client=client,
        userdata=userdata, 
        msg=msg
    )
 

class MqttSystemClient():
    def __init__(self, mqtt_server) -> None:
        
        self.mqtt_server = mqtt_server
        self.client_id = 'tpng--' + str(mqtt_server.UUID)

        self.systems: list[System] = self.mqtt_server.systems
        self.agencies: list[Agency] = self.mqtt_server.agencies

        self.topicz: list[str] = []

        self.client = mqtt.Client(client_id=self.client_id)
        self._setup_callbacks()
        self._setup_topics()

    def _setup_topics(self) -> None:
        if self.systems:
            for system in self.systems:
                self.topicz.append(
                    f"system/{system.UUID}",
                    f"system/{system.name}",
                )

            talkgroups = TalkGroup.objects.filter(
                system__in=self.mqtt_server.systems
            )
            for talkgroup in talkgroups:
                self.topicz.append(
                    f"system/{talkgroup.system.UUID}/talkgroup/{talkgroup.UUID}",
                    f"system/{talkgroup.system.name}/talkgroup/{talkgroup.alpha_tag}",
                )
        else: 
            for system in System.objects.all():
                self.topicz.append(
                    f"system/{system.UUID}",
                    f"system/{system.name}",
                )

            for talkgroup in TalkGroup.objects.all():
                self.topicz.append(
                    f"system/{talkgroup.system.UUID}/talkgroup/{talkgroup.UUID}",
                    f"system/{talkgroup.system.name}/talkgroup/{talkgroup.alpha_tag}",
                )

        if self.agencies:
            for agency in self.agencies:
                self.topicz.append(
                    f"agency/{agency.UUID}",
                    f"agency/{agency.name}",
                )
        else:
            for agency in Agency.objects.all():
                self.topicz.append(
                    f"agency/{agency.UUID}",
                    f"agency/{agency.name}",
                )

    def send(self, _transmission: dict) -> None:
        targets = []

        if self.systems:
            if _transmission["system"] in [ str(sys.UUID) for sys in self.systems]:
                targets += [
                    f"system/{_transmission["system"]}",
                    f"system/{_transmission["system_name"]}",
                    f"system/{_transmission["system_name"]}/site/{_transmission["recorder"]["site_id"]}",
                    f"system/{_transmission["system_name"]}/site/{_transmission["recorder"]["name"]}",
                    f"system/{_transmission["system"]}/talkgroup/{_transmission["talkgroup"]["UUID"]}",
                    f"system/{_transmission["system_name"]}/talkgroup/{_transmission["talkgroup"]["alpha_tag"]}",
                    
                ]
        else:
            targets += [
                f"system/{_transmission["system"]}",
                f"system/{_transmission["system_name"]}",
                f"system/{_transmission["system_name"]}/site/{_transmission["recorder"]["site_id"]}",
                f"system/{_transmission["system_name"]}/site/{_transmission["recorder"]["name"]}",
                f"system/{_transmission["system"]}/talkgroup/{_transmission["talkgroup"]["UUID"]}",
                f"system/{_transmission["system_name"]}/talkgroup/{_transmission["talkgroup"]["alpha_tag"]}",
            ]

        if self.agencies and _transmission["talkgroup"]["talkgroup"]["agency"]:
            for agency in _transmission["talkgroup"]["talkgroup"]["agency"]:
                agency: Agency
                if agency in [ str(agency.UUID) for agency in self.agencies]:
                    targets += [
                        f"agency/{agency.UUID}",
                        f"agency/{agency.name}",
                    ]
        else:
            for agency in _transmission["talkgroup"]["talkgroup"]["agency"]:
                agency: Agency
                targets += [
                    f"agency/{agency.UUID}",
                    f"agency/{agency.name}",
                ]
        
        for topic in targets:
            self.client.publish(
                topic=topic,
                payload=_transmission,
            )

    def _setup_callbacks(self) -> None:
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc, *args, **kwargs) -> None:
        logger.debug(f"Connected with result code {rc}")
        # for topic in self.topicz:
        #     self.client.subscribe(topic)

    def _on_message(self, client, userdata, msg, *args, **kwargs) -> None:
        logger.debug(f"MQTT MESSAGE: {client} {userdata} {msg}")
        from mqtt.tasks import send_mqtt_message_signal
        send_mqtt_message_signal(
            self,
            client,
            userdata,
            msg
        )

    def start_mqtt_client(self):
        if self.mqtt_server.username and self.mqtt_server.password:
            self.client.username_pw_set(
                username=self.mqtt_server.username,
                password=self.mqtt_server.password,
            )

        self.client.connect(
            host = self.mqtt_server.host,
            port = self.mqtt_server.port,
            keepalive = self.mqtt_server.keepalive
        )
        self.client.loop_start()

class MqttClientManager():
    def __init__(self) -> None:
        from mqtt.models import MqttServer

        self.mqtt_servers = MqttServer.objects.filter(enabled=True)
        self.mqtt_clients: list[MqttSystemClient] = []

        self._setup_agency_clients()
        self._setup_system_clients()

    def _setup_agency_clients(self):
        for client in self.mqtt_servers:
            _mqtt = MqttSystemClient(client)
            self.mqtt_clients.append(_mqtt)

    def _setup_system_clients(self):
        for client in self.mqtt_servers:
            _mqtt = MqttSystemClient(client)
            self.mqtt_clients.append(_mqtt)

    def launch(self) -> None:
        for client in self.mqtt_clients:
            gevent.spawn(client.start_mqtt_client)

    def dispatch(self, _transmission: dict) -> None:
        for client in self.mqtt_clients:
            client.send(_transmission)
