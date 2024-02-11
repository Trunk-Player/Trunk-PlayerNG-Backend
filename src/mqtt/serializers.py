from rest_framework import serializers

from mqtt.models import (
   MqttServer
)
from radio.serializers import SystemSerializer

class MqttServerListSerializer(serializers.ModelSerializer):
    system = SystemSerializer(read_only=True, many=True)
    class Meta:
        model = MqttServer
        fields = [
            "UUID",
            "name",
            "host",
            "port",
            "enabled",
            "keepalive",
            "username",
            "systems"
        ]

class MqttServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MqttServer
        fields = [
            "UUID",
            "name",
            "host",
            "port",
            "enabled",
            "keepalive",
            "username",
            "password",
            "systems"
        ]
