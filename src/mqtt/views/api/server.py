import uuid

from django.conf import settings
from django.http import Http404

from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework import status

from django_filters import rest_framework as filters

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from mqtt.filters import (
    MqttServerFilter,
)

from mqtt.serializers import (
    MqttServerListSerializer,
    MqttServerSerializer,
)

from radio.permission import (
    IsSiteAdmin
)

from mqtt.models import (
    MqttServer
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = MqttServer.objects.all()
    serializer_class = MqttServerListSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = MqttServerFilter

    @swagger_auto_schema(tags=["Agency"])
    def get(self, request):
        """
        Agency List EP
        """
        agencys = self.queryset
        filterobject_fs = self.filterset_class(self.request.GET, queryset=agencys)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

class Create(APIView):
    serializer_class = MqttServerSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["MQTT", "Server"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["host", "port"],
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Server Name"
                ),
                "host": openapi.Schema(
                    type=openapi.TYPE_STRING, description="MQTT Hostname or IP"
                ),
                "port": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="MQTT Port",
                    default=1883
                ),
                "keepalive": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="MQTT Keepalive seconds",
                    default=60
                ),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Enable MQTT Client"
                ),
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="MQTT Username"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="MQTT Username"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_ARRAY, description="Sytems to send",
                    items=openapi.Items(type=openapi.TYPE_STRING)
                ),
            },
        ),
    )
    def post(self, request):
        """
        MQTT Server Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class View(APIView):
    queryset = MqttServer.objects.all()
    serializer_class = MqttServerListSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, request_uuid) -> MqttServer:
        """
        Fetches Agency ORM object
        """
        try:
            return self.queryset.objects.get(UUID=request_uuid)
        except self.queryset.DoesNotExist:
            raise Http404 from self.queryset.DoesNotExist

    @swagger_auto_schema(tags=["Agency"])
    def get(self, request, request_uuid):
        """
        Agency get EP
        """
        agency = self.get_object(request_uuid)
        serializer = self.serializer_class(agency)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["MQTT", "Server"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["host", "port"],
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Server Name"
                ),
                "host": openapi.Schema(
                    type=openapi.TYPE_STRING, description="MQTT Hostname or IP"
                ),
                "port": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="MQTT Port",
                    default=1883
                ),
                "keepalive": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="MQTT Keepalive seconds",
                    default=60
                ),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Enable MQTT Client"
                ),
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="MQTT Username"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="MQTT Username"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_ARRAY, description="Sytems to send",
                    items=openapi.Items(type=openapi.TYPE_STRING)
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        Mqtt Server update EP
        """
        data = JSONParser().parse(request)
        mqtt_server = self.get_object(request_uuid)
        serializer = MqttServerSerializer(mqtt_server, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["Agency"])
    def delete(self, request, request_uuid):
        """
        Agency Delete EP
        """
        mqtt_server = self.get_object(request_uuid)
        mqtt_server.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
