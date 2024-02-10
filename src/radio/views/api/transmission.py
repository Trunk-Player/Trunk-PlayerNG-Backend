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
)

from radio.serializers import (
    TransmissionListSerializer,
    TransmissionUploadSerializer,
    TransmissionSerializer
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
    Transmission
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

logger = logging.getLogger(__name__)

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
            allowed_transmissions_non_acl = Transmission.objects.none()
            allowed_transmissions_acl = Transmission.objects.none()

            for system in systems:
                system: System
                if system.enable_talkgroup_acls:
                    talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)
                    allowed_transmissions_acl = allowed_transmissions_acl | Transmission.objects.filter(
                            system=system, talkgroup__in=talkgroups_allowed
                        )
                else:
                    allowed_transmissions_non_acl = allowed_transmissions_non_acl | Transmission.objects.filter(system=system)
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
                "tones": openapi.Schema(
                    type=openapi.TYPE_OBJECT, description="Tones Info",
                    required=[],
                    properties={
                        "has_tones": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, description="Has Tones"
                        ),
                        "is_dispatch": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN, description="Is a Dispatch"
                        ),
                        "tones_detected": openapi.Schema(
                            type=openapi.TYPE_STRING, description="Tones Detected"
                        ),
                        "tones_meta": openapi.Schema(
                             type=openapi.TYPE_OBJECT, description="Any Arbatray extra data",
                        )
                    }
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
