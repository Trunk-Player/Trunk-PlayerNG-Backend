# import logging
import logging
import uuid

from django.conf import settings
from django.http import Http404
from django.core.exceptions import PermissionDenied


from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework import status

from django_filters import rest_framework as filters


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


from radio.filters import (
    SystemRecorderFilter
)

from radio.serializers import (
    SystemRecorderSerializer
)

from radio.permission import (
    IsSAOrUser,
    IsSiteAdmin
)

from radio.models import (
    UserProfile,
    SystemRecorder
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer
    permission_classes = [IsSAOrUser]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SystemRecorderFilter

    @swagger_auto_schema(tags=["SystemRecorder"])
    def get(self, request):
        """
        System Recorder list EP
        """
        user: UserProfile = request.user.userProfile


        if not user.site_admin:
            system_recorders = SystemRecorder.objects.filter(user=user)
        else:
            system_recorders = SystemRecorder.objects.all()
        
        filterobject_fs = SystemRecorderFilter(self.request.GET, queryset=system_recorders)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = SystemRecorderSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["SystemRecorder"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["system", "site_id", "name", "user"],
            properties={
                "system": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System UUID"
                ),
                "site_id": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Site ID"
                ),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Enabled"
                ),
                "user": openapi.Schema(
                    type=openapi.TYPE_STRING, description="User UUID"
                ),  # Replace me with resuestuser
                "talkgroups_allowed": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroups Allowed UUIDs",
                ),
                "talkgroups_denyed": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroups Allowed UUIDs",
                ),
            },
        ),
    )
    def post(self, request):
        """
        System Recorder Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()
        if not "api_key" in data:
            data["api_key"] = uuid.uuid4()

        serializer = SystemRecorderSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class View(APIView):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer
    permission_classes = [IsSAOrUser]

    def get_object(self, request_uuid):
        """
        Fetch System Recorder ORM Object
        """
        try:
            return SystemRecorder.objects.get(UUID=request_uuid)
        except SystemRecorder.DoesNotExist:
            raise Http404 from SystemRecorder.DoesNotExist

    @swagger_auto_schema(tags=["SystemRecorder"])
    def get(self, request, request_uuid):
        """
        System Recorder Get EP
        """
        user: UserProfile = request.user.userProfile
        system_recorder = self.get_object(request_uuid)
        if not user.site_admin:
            if not system_recorder.user == user:
                raise PermissionDenied
        serializer = SystemRecorderSerializer(system_recorder)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["SystemRecorder"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                #'system': openapi.Schema(type=openapi.TYPE_STRING, description='System UUID'),
                "site_id": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Site ID"
                ),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Enabled"
                ),
                #'user': openapi.Schema(type=openapi.TYPE_STRING, description='User UUID'),
                "talkgroups_allowed": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroups Allowed UUIDs",
                ),
                "talkgroups_denyed": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroups Allowed UUIDs",
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        System Recorder update EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            raise PermissionDenied
        data = JSONParser().parse(request)
        system_recorder = self.get_object(request_uuid)
        serializer = SystemRecorderSerializer(system_recorder, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["SystemRecorder"])
    def delete(self, request, request_uuid):
        """
        System Recorder delete EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            raise PermissionDenied
        system_recorder = self.get_object(request_uuid)
        system_recorder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

