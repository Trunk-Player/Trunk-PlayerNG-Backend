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
    TransmissionFilter,
    TransmissionFreqFilter,
    TransmissionUnitFilter
)

from radio.serializers import (
    TransmissionUnitSerializer,
    TransmissionFreqSerializer,
    TransmissionSerializer,
    TransmissionListSerializer
)

from radio.helpers.utils import (
    get_user_allowed_systems,
    get_user_allowed_talkgroups,
)

from radio.permission import (
    FeederFree,
    IsSAOrReadOnly
)

from radio.models import (
    UserProfile,
    System,
    SystemRecorder,
    TransmissionUnit,
    TransmissionFreq,
    Transmission
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

logger = logging.getLogger(__name__)

class UnitList(APIView, PaginationMixin):
    queryset = TransmissionUnit.objects.all()
    serializer_class = TransmissionUnitSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TransmissionUnitFilter

    @swagger_auto_schema(tags=["TransmissionUnit"])
    def get(self, request, request_uuid):
        """
        TransmissionUnit List EP
        """
        user: UserProfile = request.user.userProfile

        transmission: Transmission = Transmission.objects.get(UUID=request_uuid)
        units = transmission.units.all()

        if not user.site_admin:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            if transmission.system in systems:
                system: System = transmission.system

                if not system in systems:
                    raise PermissionDenied

                if system.enable_talkgroup_acls:
                    talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)
                    if not transmission.talkgroup in talkgroups_allowed:
                        raise PermissionDenied
            else:
                raise PermissionDenied


        filterobject_fs = TransmissionUnitFilter(self.request.GET, queryset=units)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = TransmissionUnitSerializer(page, many=True)
            return Response(serializer.data)


class UnitView(APIView):
    queryset = TransmissionUnit.objects.all()
    serializer_class = TransmissionUnitSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        Fetches TransmissionUnit ORM Object
        """
        try:
            return TransmissionUnit.objects.get(UUID=request_uuid)
        except TransmissionUnit.DoesNotExist:
            raise Http404 from TransmissionUnit.DoesNotExist

    @swagger_auto_schema(tags=["TransmissionUnit"])
    def get(self, request, request_uuid):
        """
        TransmissionUnit get EP
        """
        user: UserProfile = request.user.userProfile
        transmission_unit: TransmissionUnit = self.get_object(request_uuid)

        transmission: Transmission = Transmission.objects.filter(
            units__in=transmission_unit
        )

        if not user.site_admin:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            if transmission.system in systems:
                system: System = transmission.system
                if not system in systems:
                    raise PermissionDenied
                if system.enable_talkgroup_acls:
                    talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)
                    if not transmission.talkgroup in talkgroups_allowed:
                        raise PermissionDenied
            else:
                raise PermissionDenied

        serializer = TransmissionUnitSerializer(transmission)
        return Response(serializer.data)

    # @swagger_auto_schema(tags=['TransmissionUnit'], request_body=openapi.Schema(
    #     type=openapi.TYPE_OBJECT,
    #     properties={
    #         'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description'),
    #     }
    # ))
    # def put(self, request, UUID):
    #     data = JSONParser().parse(request)
    #     TransmissionUnit = self.get_object(UUID)
    #     serializer = TransmissionUnitSerializer(TransmissionUnit, data=data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["TransmissionUnit"])
    def delete(self, request, request_uuid):
        """
        TransmissionUnit delete EP
        """
        user: UserProfile = request.user.userProfile
        if user.site_admin:
            transmission_unit = self.get_object(request_uuid)
            transmission_unit.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise PermissionDenied


class FreqList(APIView):
    queryset = TransmissionFreq.objects.all()
    serializer_class = TransmissionFreqSerializer
    permission_classes = [IsSAOrReadOnly]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TransmissionFreqFilter

    @swagger_auto_schema(tags=["TransmissionFreq"])
    def get(self, request, request_uuid):
        """
        TransmissionFreq List EP
        """
        user: UserProfile = request.user.userProfile

        transmission: Transmission = Transmission.objects.get(UUID=request_uuid)
        freqs = transmission.frequencys.all()

        if not user.site_admin:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            if transmission.system in systems:
                system: System = transmission.system
                if not system in systems:
                    raise PermissionDenied
                if system.enable_talkgroup_acls:
                    talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)
                    if not transmission.talkgroup in talkgroups_allowed:
                        raise PermissionDenied
            else:
                raise PermissionDenied
        filterobject_fs = TransmissionFreqFilter(self.request.GET, queryset=freqs)
        serializer = TransmissionFreqSerializer(filterobject_fs.qs, many=True)
        return Response(serializer.data)


class FreqView(APIView):
    queryset = TransmissionFreq.objects.all()
    serializer_class = TransmissionFreqSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        Fetches TransmissionFreq ORM Object
        """
        try:
            return TransmissionFreq.objects.get(UUID=request_uuid)
        except TransmissionFreq.DoesNotExist:
            raise Http404 from TransmissionFreq.DoesNotExist

    @swagger_auto_schema(tags=["TransmissionFreq"])
    def get(self, request, request_uuid):
        """
        TransmissionFreq get EP
        """
        transmission_freq: TransmissionFreq = self.get_object(request_uuid)
        serializer = TransmissionFreqSerializer(transmission_freq)
        return Response(serializer.data)


class List(APIView, PaginationMixin):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TransmissionFilter

    @swagger_auto_schema(tags=["Transmission"])
    def get(self, request):
        """
        Transmission List EP
        """
        user: UserProfile = request.user.userProfile

        if user.site_admin:
            allowed_transmissions = Transmission.objects.all()
        else:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            del system_uuids
            allowed_transmissions_non_acl = []
            allowed_transmissions_acl = []

            for system in systems:
                if system.enable_talkgroup_acls:
                    talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)
                    allowed_transmissions_acl = Transmission.objects.filter(
                        system=system, talkgroup__in=talkgroups_allowed
                    )
                else:
                    allowed_transmissions_non_acl = Transmission.objects.filter(system=system)
            allowed_transmissions = allowed_transmissions_acl | allowed_transmissions_non_acl

        filterobject_fs = TransmissionFilter(self.request.GET, queryset=allowed_transmissions)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = TransmissionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer
    permission_classes = [FeederFree]

    @swagger_auto_schema(
        tags=["Transmission"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["recorder", "json", "audio"],
            properties={
                #'system': openapi.Schema(type=openapi.TYPE_STRING, description='System UUID'),
                "recorder": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Recorder Key"
                ),
                "json": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Trunk-Recorder JSON"
                ),
                "audio_file": openapi.Schema(
                    type=openapi.TYPE_STRING, description="M4A Base64"
                ),
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Audio File Name"
                ),
            },
        ),
    )
    def post(self, request):
        """
        Transmission Create EP
        """
        from radio.tasks import new_transmission_handler
        from radio.helpers.utils import validate_upload

        data = JSONParser().parse(request)
 
        try:
            recorder: SystemRecorder = SystemRecorder.objects.get(
                api_key=data["recorder"]
            )

            tg_id = data["json"]["talkgroup"]
            if not validate_upload(tg_id, recorder):
                return Response(
                    data={"error":"Not allowed to post this talkgroup"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except SystemRecorder.DoesNotExist:
            return Response(
                data={"error":"Not allowed to post this talkgroup"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            UUID = uuid.uuid4()
            data["UUID"] = UUID
            new_transmission_handler.delay(data)
            logger.info(f"[+] Got new tx - {UUID}", extra=data["json"])
            return Response(data={"UUID": UUID}, status=status.HTTP_201_CREATED)
        except Exception as error:
            if settings.SEND_TELEMETRY:
                sentry_sdk.set_context(
                    "add_tx_data",
                    {
                        "data": data,
                    },
                )
                sentry_sdk.capture_exception(error)

            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)


class View(APIView):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer

    def get_object(self, request_uuid):
        """
        Fetches Transmission ORM Object
        """
        try:
            return Transmission.objects.get(UUID=request_uuid)
        except Transmission.DoesNotExist:
            raise Http404 from Transmission.DoesNotExist

    @swagger_auto_schema(tags=["Transmission"])
    def get(self, request, request_uuid):
        """
        Transmission get EP
        """
        transmission: Transmission = self.get_object(request_uuid)
        user: UserProfile = request.user.userProfile

        if not user.site_admin:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            if not transmission.system in systems:
                raise PermissionDenied
            system: System = transmission.system
            if system.enable_talkgroup_acls:
                talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)
                if not transmission.talkgroup in talkgroups_allowed:
                    raise PermissionDenied

        serializer = TransmissionSerializer(transmission)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["Transmission"])
    def delete(self, request, request_uuid):
        """
        Transmission Delete EP
        """
        user: UserProfile = request.user.userProfile

        if not user.site_admin:
            raise PermissionDenied
        transmission = self.get_object(request_uuid)
        transmission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
