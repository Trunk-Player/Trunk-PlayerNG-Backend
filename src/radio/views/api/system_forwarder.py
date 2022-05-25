import logging
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


from radio.filters import (
    SystemForwarderFilter
)

from radio.serializers import (
    SystemForwarderSerializer
)

from radio.permission import (
    IsSiteAdmin
)

from radio.models import (
    SystemForwarder
)

from radio.views.misc import (
    PaginationMixin
)


if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SystemForwarderFilter

    @swagger_auto_schema(
        tags=["SystemForwarder"],
    )
    def get(self, request):
        """
        System Forwarder List EP
        """
        system_forwarders = SystemForwarder.objects.all()

        filterobject_fs = SystemForwarderFilter(self.request.GET, queryset=system_forwarders)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = SystemForwarderSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["SystemForwarder"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "name",
                "enabled",
                "recorder_key",
                "remote_url",
                "forwarded_systems",
            ],
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Forwarder Name"
                ),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="enabled"
                ),
                "recorder_key": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Forwarder Key"
                ),
                "remote_url": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Remote URL of the TP-NG to forward to",
                ),
                "forward_incidents": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Forward Incidents"
                ),
                "forwarded_systems": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="System UUIDs",
                ),
                "talkgroup_filter": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Filtered TG UUIDs",
                ),
            },
        ),
    )
    def post(self, request):
        """
        SystemForwarder Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = SystemForwarderSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class View(APIView):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, request_uuid):
        """
        Gets SystemForwarder ORM Object
        """
        try:
            return SystemForwarder.objects.get(UUID=request_uuid)
        except SystemForwarder.DoesNotExist:
            raise Http404 from SystemForwarder.DoesNotExist

    @swagger_auto_schema(tags=["SystemForwarder"])
    def get(self, request, request_uuid):
        """
        SystemForwarder GET EP
        """
        system_forwarder = self.get_object(request_uuid)
        serializer = SystemForwarderSerializer(system_forwarder)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["SystemForwarder"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Forwarder Name"
                ),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="enabled"
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        SystemForwarder Update EP
        """
        data = JSONParser().parse(request)
        system_forwarder = self.get_object(request_uuid)
        if "feedKey" in data:
            del data["feedKey"]
        serializer = SystemForwarderSerializer(system_forwarder, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["SystemForwarder"])
    def delete(self, request, request_uuid):
        """
        SystemForwarder Delete EP
        """
        system_forwarder = self.get_object(request_uuid)
        system_forwarder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
