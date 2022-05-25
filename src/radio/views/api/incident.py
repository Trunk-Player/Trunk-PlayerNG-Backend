# import logging
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
    IncidentFilter
)

from radio.serializers import (
    IncidentSerializer,
    IncidentCreateSerializer
)

from radio.helpers.utils import (
    get_user_allowed_systems,
)

from radio.permission import (
    FeederFree,
    IsSAOrReadOnly,
    IsSiteAdmin
)

from radio.models import (
    UserProfile,
    SystemRecorder,
    Incident
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = IncidentFilter

    @swagger_auto_schema(tags=["Incident"])
    def get(self, request):
        """
        Incident List EP
        """
        user: UserProfile = request.user.userProfile

        if user.site_admin:
            incidents = Incident.objects.all()
        else:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            del system_uuids
            incidents = Incident.objects.filter(system__in=systems)

        filterobject_fs = IncidentFilter(self.request.GET, queryset=incidents)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = IncidentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentCreateSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["Incident"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["system", "name", "transmission"],
            properties={
                "active": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Is the Event Active"
                ),
                "system": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System UUID"
                ),
                "transmission": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="TRANMISSIONS UUID",
                ),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "agency": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Agency UUIDs",
                ),
                "time": openapi.Schema(type=openapi.TYPE_STRING, description="Time"),
            },
        ),
    )
    def post(self, request):
        """
        Incident Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = IncidentCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Forward(APIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentCreateSerializer
    permission_classes = [FeederFree]

    def get_object(self, request_uuid):
        """
        Fetches Incident ORM Object
        """
        try:
            return Incident.objects.get(UUID=request_uuid)
        except Incident.DoesNotExist:
            raise Http404 from Incident.DoesNotExist

    @swagger_auto_schema(
        tags=["Incident"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["recorder", "name", "transmission"],
            properties={
                "active": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Is the Event Active"
                ),
                "recorder": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Recorder Key"
                ),
                "transmission": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="TRANMISSIONS UUID",
                ),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "agency": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Agency UUIDs",
                ),
                "time": openapi.Schema(type=openapi.TYPE_STRING, description="Time"),
            },
        ),
    )
    def post(self, request):
        """
        Incident Forward EP
        """
        data = JSONParser().parse(request)

        # try:
        system_recorder: SystemRecorder = SystemRecorder.objects.get(
            api_key=data["recorder"]
        )
        # except:
        #     return Response(
        #         "Not allowed to post this talkgroup",
        #         status=status.HTTP_401_UNAUTHORIZED,
        #     )

        if not system_recorder:
            return Response(
                "Not allowed to post this talkgroup",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data["system"] = str(system_recorder.system.UUID)
        del data["recorder"]

        serializer = IncidentCreateSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, request_uuid):
        """
        Incident Update EP
        """
        data = JSONParser().parse(request)

        # try:
        system_recorder: SystemRecorder = SystemRecorder.objects.get(
            api_key=data["recorder"]
        )
        # except:
        #     return Response(
        #         "Not allowed to post this talkgroup",
        #         status=status.HTTP_401_UNAUTHORIZED,
        #     )

        if not system_recorder:
            return Response(
                "Not allowed to post this talkgroup",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data["system"] = str(system_recorder.system.UUID)

        del data["recorder"]

        incident = self.get_object(request_uuid)
        serializer = IncidentCreateSerializer(incident, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Update(APIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentCreateSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, request_uuid):
        """
        Fetches Incident ORM Object
        """
        try:
            return Incident.objects.get(UUID=request_uuid)
        except Incident.DoesNotExist:
            raise Http404 from Incident.DoesNotExist

    @swagger_auto_schema(
        tags=["Incident"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "active": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Is the Event Active"
                ),
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "transmission": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="TRANMISSIONS UUID",
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "agency": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Agency UUIDs",
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        Incident Update EP
        """
        data = JSONParser().parse(request)
        incident = self.get_object(request_uuid)
        serializer = IncidentCreateSerializer(incident, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class View(APIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        Fetches Incident ORM Object
        """
        try:
            return Incident.objects.get(UUID=request_uuid)
        except Incident.DoesNotExist:
            raise Http404 from Incident.DoesNotExist

    @swagger_auto_schema(tags=["Incident"])
    def get(self, request, request_uuid):
        """
        Incident Get EP
        """
        incident: Incident = self.get_object(request_uuid)
        user: UserProfile = request.user.userProfile

        if not user.site_admin:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            if not incident.system in systems:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = IncidentSerializer(incident)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["Incident"])
    def delete(self, request, request_uuid):
        """
        Incident Delete EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        incident: Incident = self.get_object(request_uuid)
        incident.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

