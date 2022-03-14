# import logging
import uuid
import traceback

from django.conf import settings
from django.http import ( Http404, HttpResponse )
from django.db.models import Q

from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework import status

from django_filters import rest_framework as filters

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from radio.filters import SystemFilter, TransmissionFilter
from radio.serializers import (
    UserAlertSerializer,
    UserProfileSerializer,
    SystemACLSerializer,
    SystemSerializer,
    SystemForwarderSerializer,
    CitySerializer,
    AgencySerializer,
    AgencyViewListSerializer,
    TalkGroupSerializer,
    TalkGroupViewListSerializer,
    SystemRecorderSerializer,
    UnitSerializer,
    TransmissionUnitSerializer,
    TransmissionFreqSerializer,
    TransmissionSerializer,
    TransmissionListSerializer,
    TransmissionUploadSerializer,
    IncidentSerializer,
    IncidentCreateSerializer,
    TalkGroupACLSerializer,
    ScanListSerializer,
    ScannerSerializer,
    GlobalAnnouncementSerializer,
    GlobalEmailTemplateSerializer
)
from radio.tasks import import_radio_refrence, send_transmission_to_web
from radio.helpers.transmission import new_transmission_handler
from radio.helpers.utils import (
    user_allowed_to_download_transmission,
    get_user_allowed_systems,
    get_user_allowed_talkgroups,
)

from radio.permission import (
    FeederFree,
    IsSAOrReadOnly,
    IsSAOrUser,
    IsSiteAdmin,
    IsUser,
)

from radio.models import (
    UserProfile,
    SystemACL,
    System,
    City,
    Agency,
    TalkGroup,
    SystemForwarder,
    SystemRecorder,
    Unit,
    TransmissionUnit,
    TransmissionFreq,
    Transmission,
    Incident,
    TalkGroupACL,
    ScanList,
    Scanner,
    GlobalAnnouncement,
    GlobalEmailTemplate,
    UserAlert
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

def transmission_download(request, transmission_uuid):
    """
    Handles Transmission download URL
    """
    import requests

    try:
        transmission: Transmission = Transmission.objects.get(UUID=transmission_uuid)
    except Transmission.DoesNotExist:
        raise Http404 from Transmission.DoesNotExist

    user = request.user.userProfile
    if not user.site_admin:
        if not user_allowed_to_download_transmission(transmission, user.UUID):
            return HttpResponse("UNAUTHORIZED", status=401)

    file_url = transmission.audio_file.url
    # file_size = transmission.audio_file.size

    if not settings.USE_S3:
        file_url = f"{settings.AUDIO_DOWNLOAD_HOST}{file_url}"

    audio_type = f'audio/{file_url.split(".")[-1].strip()}'
    filename = f'{str(transmission.talkgroup.decimal_id)}_{str(transmission.start_time.isoformat())}_{str(transmission.UUID)}.{file_url.split(".")[-1].strip()}'

    response = HttpResponse(content_type=audio_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    data = requests.get(file_url, verify=False)
    response.write(data.content)

    return response


class PaginationMixin(object):
    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination
        is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given
        output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)


class UserAlertList(APIView, PaginationMixin):
    queryset = UserAlert.objects.all()
    serializer_class = UserAlertSerializer
    permission_classes = [IsSAOrUser]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["UserAlert"])
    def get(self, request):
        """
        UserAlert List EP
        """
        user: UserProfile = request.user.userProfile
        if user.site_admin:
            user_alerts = UserAlert.objects.all()
        else:
            user_alerts = UserAlert.objects.filter(user=user)

        page = self.paginate_queryset(user_alerts)
        if page is not None:
            serializer = UserAlertSerializer(page, many=True)
            return Response(serializer.data)


class UserAlertCreate(APIView):
    queryset = UserAlert.objects.all()
    serializer_class = UserAlertSerializer
    permission_classes = [IsSAOrUser]

    @swagger_auto_schema(
        tags=["UserAlert"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "description": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Description",
                ),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Enable Notification"
                ),
                "web_notification": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Send Webpage Notification"
                ),
                "app_rise_notification": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Send AppRise Notification"
                ),
                "app_rise_urls": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Comma seperated list of urls"
                ),
                "title": openapi.Schema(
                    type=openapi.TYPE_STRING, description="The title of the alert"
                ),
                "body": openapi.Schema(
                    type=openapi.TYPE_STRING, description="The body of the alert"
                ),
                "emergencyOnly": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Only alert on Emergency Transmissions",
                ),
            },
        ),
    )
    def post(self, request):
        """
        UserAlert Create EP POST
        """
        user: UserProfile = request.user.userProfile
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        data["user"] = str(user.UUID)

        serializer = UserAlertSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAlertView(APIView):
    queryset = UserAlert.objects.all()
    serializer_class = UserAlertSerializer
    permission_classes = [IsSAOrUser]

    def get_object(self, alert_uuid):
        """
        Gets User Alert by UUID
        """
        try:
            return UserAlert.objects.get(UUID=alert_uuid)
        except UserAlert.DoesNotExist:
            raise Http404 from UserAlert.DoesNotExist

    @swagger_auto_schema(tags=["UserAlert"])
    def get(self, request, request_uuid):
        """
        UserAlert Get EP
        """
        user: UserProfile = request.user.userProfile
        user_alert: UserAlert = self.get_object(request_uuid)
        if not user_alert.user == user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = UserAlertSerializer(user_alert)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["UserAlert"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "description": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Description",
                ),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Enable Notification"
                ),
                "web_notification": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Send Webpage Notification"
                ),
                "app_rise_notification": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Send AppRise Notification"
                ),
                "app_rise_urls": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Comma seperated list of urls"
                ),
                "title": openapi.Schema(
                    type=openapi.TYPE_STRING, description="The title of the alert"
                ),
                "body": openapi.Schema(
                    type=openapi.TYPE_STRING, description="The body of the alert"
                ),
                "emergencyOnly": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Only alert on Emergency Transmissions",
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        user update EP
        """
        user: UserProfile = request.user.userProfile
        user_alert: UserAlert = self.get_object(request_uuid)
        if not user_alert.user == user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        data = request.data
        if "user" in data:
            del data["user"]

        serializer = UserAlertSerializer(user_alert, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["UserAlert"])
    def delete(self, request, request_uuid):
        """
        user delete EP
        """
        user: UserProfile = request.user.userProfile
        user_alert: UserAlert = self.get_object(request_uuid)
        if not user_alert.user == user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user_alert.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserProfileList(APIView, PaginationMixin):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsSAOrUser]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["UserProfile"])
    def get(self, request):
        """
        Userprofile GET EP
        """
        user = request.user.userProfile
        if user.site_admin:
            user_profile = UserProfile.objects.all()
        else:
            user_profile = UserProfile.objects.filter(UUID=user.UUID)

        page = self.paginate_queryset(user_profile)
        if page is not None:
            serializer = UserProfileSerializer(page, many=True)
            return Response(serializer.data)


class UserProfileView(APIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        User profile fetch function
        """
        try:
            return UserProfile.objects.get(UUID=request_uuid)
        except UserProfile.DoesNotExist:
            raise Http404 from UserProfile.DoesNotExist

    @swagger_auto_schema(tags=["UserProfile"])
    def get(self, request, request_uuid):
        """
        UserProfile Get EP
        """
        user = request.user.userProfile
        if user.site_admin or user.UUID == request_uuid:
            user_profile = self.get_object(request_uuid)
        else:
            return Response(status=401)
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["UserProfile"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "site_theme": openapi.Schema(
                    type=openapi.TYPE_STRING, description="site_theme"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="description"
                ),
                "site_admin": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Is user authorized to make changes",
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        UserProfile Update EP
        """
        user = request.user.userProfile
        if user.site_admin or user.UUID == request_uuid:
            user_profile = self.get_object(request_uuid)
        else:
            return Response(status=401)
        serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["UserProfile"])
    def delete(self, request, request_uuid):
        """
        UserProfile Delete EP
        """
        user = request.user.userProfile
        if user.site_admin or user.UUID == request_uuid:
            user_profile = self.get_object(request_uuid)
        else:
            return Response(status=401)
        user_profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemACLList(APIView, PaginationMixin):
    queryset = SystemACL.objects.all()
    serializer_class = SystemACLSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ["UUID", "name", "users", "public"]

    @swagger_auto_schema(tags=["SystemACL"])
    def get(self, request):
        """
        System ACL get EP
        """
        system_acls = SystemACL.objects.all()
        page = self.paginate_queryset(system_acls)
        if page is not None:
            serializer = SystemACLSerializer(page, many=True)
            return Response(serializer.data)


class SystemACLCreate(APIView):
    queryset = SystemACL.objects.all()
    serializer_class = SystemACLSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["SystemACL"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "public"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="string"),
                "users": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="List of user UUID",
                ),
                "public": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Make viable to all users"
                ),
            },
        ),
    )
    def post(self, request):
        """
        SystemACL Update EP
        """
        data = JSONParser().parse(request)
        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()
        serializer = SystemACLSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemACLView(APIView):
    queryset = SystemACL.objects.all()
    serializer_class = SystemACLSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, request_uuid):
        """
        Fetches SystemACL Object
        """
        try:
            return SystemACL.objects.get(UUID=request_uuid)
        except SystemACL.DoesNotExist:
            raise Http404 from SystemACL.DoesNotExist

    @swagger_auto_schema(tags=["SystemACL"])
    def get(self, request, request_uuid):
        """
        Get SystemACL View
        """
        system_acl = self.get_object(request_uuid)
        serializer = SystemACLSerializer(system_acl)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["SystemACL"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="string"),
                "users": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="List of user UUID",
                ),
                "public": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Make viable to all users"
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        systemACL Update EP
        """
        system_acl = self.get_object(request_uuid)
        serializer = SystemACLSerializer(system_acl, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["SystemACL"])
    def delete(self, request, request_uuid):
        """
        SystemACL Delete EP
        """
        system_acl = self.get_object(request_uuid)
        system_acl.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemList(APIView, PaginationMixin):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["System"])
    def get(self, request):
        """
        System List EP
        """
        user: UserProfile = request.user.userProfile
        if user.site_admin:
            systems = self.queryset
        else:
            user_acls = []
            acls = SystemACL.objects.all()
            for acl in acls:
                acl: SystemACL
                if acl.users.filter(UUID=user.UUID):
                    user_acls.append(acl)
                elif acl.public:
                    user_acls.append(acl)
            systems = self.queryset.filter(systemACL__in=user_acls)

        systems_fs = SystemFilter(self.request.GET, queryset=systems)
        page = self.paginate_queryset(systems_fs.qs)
        if page is not None:
            serializer = SystemSerializer(page, many=True)
            return Response(serializer.data)


class SystemCreate(APIView):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["System"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "systemACL"],
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System Name"
                ),
                "systemACL": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System ACL UUID"
                ),
                "enable_talkgroup_acls": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Enable Talkgroup ACLs on system",
                ),
                "prune_transmissions": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Enable Pruneing Transmissions on system",
                ),
                "prune_transmissions_after_days": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Days to keep Transmissions (Prune)",
                ),
            },
        ),
    )
    def post(self, request):
        """
        System Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = SystemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemView(APIView):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        Fetches System ORM object
        """
        try:
            return System.objects.get(UUID=request_uuid)
        except System.DoesNotExist:
            raise Http404 from System.DoesNotExist

    def get_acl(self, request_uuid):
        """
        fetches SystemACL ORM OBJECT
        """
        try:
            return SystemACL.objects.get(UUID=request_uuid)
        except SystemACL.DoesNotExist:
            raise Http404 from SystemACL.DoesNotExist

    @swagger_auto_schema(tags=["System"])
    def get(self, request, request_uuid):
        """
        System Get EP
        """
        user: UserProfile = request.user.userProfile
        user_acls = []
        acls = SystemACL.objects.all()
        for acl in acls:
            acl: SystemACL
            if acl.users.filter(UUID=user.UUID):
                user_acls.append(acl)
            elif acl.public:
                user_acls.append(acl)

        system: System = self.get_object(request_uuid)

        if user.site_admin:
            serializer = SystemSerializer(system)
            return Response(serializer.data)

        if system.systemACL.UUID in user_acls:
            serializer = SystemSerializer(system)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        tags=["System"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="string"),
                "systemACL": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System ACL UUID"
                ),
                "enable_talkgroup_acls": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Enable Talkgroup ACLs on system",
                ),
                "prune_transmissions": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Enable Pruneing Transmissions on system",
                ),
                "prune_transmissions_after_days": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Days to keep Transmissions (Prune)",
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        Put Request for Updating User Profile
        """
        user: UserProfile = request.user.userProfile
        data = JSONParser().parse(request)
        system = self.get_object(request_uuid)
        serializer = SystemSerializer(system, data=data, partial=True)
        if user.site_admin:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["System"])
    def delete(self, request, request_uuid):
        """
        UserProfile Delete EP
        """
        user: UserProfile = request.user.userProfile
        system = self.get_object(request_uuid)
        if user.site_admin:
            system.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class SystemRRImportView(APIView):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["System"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["siteid", "username", "password"],
            properties={
                "siteid": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Radio Refrence Site ID"
                ),
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Radio Refrence Username"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Radio Refrence password",
                ),
            },
        ),
    )
    def post(self, request, request_uuid):
        """
        RR import EP
        """
        data = JSONParser().parse(request)

        import_radio_refrence.delay(
            request_uuid, data["siteid"], data["username"], data["password"]
        )

        return Response({"message": "System Import from Radio Refrence Qued"})


class SystemForwarderList(APIView, PaginationMixin):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ["UUID", "name", "enabled", "recorder_key", "remote_url", "forward_incidents", "forwarded_systems", "talkgroup_filter"]

    @swagger_auto_schema(
        tags=["SystemForwarder"],
    )
    def get(self, request):
        """
        System Forwarder List EP
        """
        system_forwarders = SystemForwarder.objects.all()

        page = self.paginate_queryset(system_forwarders)
        if page is not None:
            serializer = SystemForwarderSerializer(page, many=True)
            return Response(serializer.data)


class SystemForwarderCreate(APIView):
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


class SystemForwarderView(APIView):
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


class CityList(APIView, PaginationMixin):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["City"])
    def get(self, request):
        """
        City List EP
        """
        citys = City.objects.all()
        page = self.paginate_queryset(citys)
        if page is not None:
            serializer = CitySerializer(page, many=True)
            return Response(serializer.data)


class CityCreate(APIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["City"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name"],
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="City Name"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="description"
                ),
            },
        ),
    )
    def post(self, request):
        """
        City Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = CitySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CityView(APIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        Fetches City ORM Object
        """
        try:
            return City.objects.get(UUID=request_uuid)
        except City.DoesNotExist:
            raise Http404 from City.DoesNotExist

    @swagger_auto_schema(tags=["City"])
    def get(self, request, request_uuid):
        """
        City Get EP
        """
        city = self.get_object(request_uuid)
        serializer = CitySerializer(city)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["City"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="City Name"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="description"
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        City Update EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            raise PermissionDenied
        data = JSONParser().parse(request)
        city = self.get_object(request_uuid)
        serializer = CitySerializer(city, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["City"])
    def delete(self, request, request_uuid):
        """
        City Delete EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            raise PermissionDenied
        city = self.get_object(request_uuid)
        city.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgencyList(APIView, PaginationMixin):
    queryset = Agency.objects.all()
    serializer_class = AgencyViewListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["Agency"])
    def get(self, request):
        """
        Agency List EP
        """
        agencys = Agency.objects.all()
        page = self.paginate_queryset(agencys)
        if page is not None:
            serializer = AgencyViewListSerializer(page, many=True)
            return Response(serializer.data)


class AgencyCreate(APIView):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["Agency"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "city"],
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Agency Name"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="description"
                ),
                "city": openapi.Schema(
                    type=openapi.TYPE_STRING, description="City UUID"
                ),
            },
        ),
    )
    def post(self, request):
        """
        Agency Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = AgencySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AgencyView(APIView):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        Fetches Agency ORM object
        """
        try:
            return Agency.objects.get(UUID=request_uuid)
        except Agency.DoesNotExist:
            raise Http404 from Agency.DoesNotExist

    @swagger_auto_schema(tags=["Agency"])
    def get(self, request, request_uuid):
        """
        Agency get EP
        """
        agency = self.get_object(request_uuid)
        serializer = AgencyViewListSerializer(agency)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Agency"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Agency Name"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="description"
                ),
                "city": openapi.Schema(
                    type=openapi.TYPE_STRING, description="City UUID"
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        Agency update EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            raise PermissionDenied
        data = JSONParser().parse(request)
        agency = self.get_object(request_uuid)
        serializer = AgencySerializer(agency, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["Agency"])
    def delete(self, request, request_uuid):
        """
        Agency Delete EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            raise PermissionDenied
        agency = self.get_object(request_uuid)
        agency.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TalkGroupList(APIView, PaginationMixin):
    queryset = TalkGroup.objects.all()
    serializer_class = TalkGroupViewListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["TalkGroup"])
    def get(self, request):
        """
        Talkgroup List EP
        """
        # pylint: disable=unused-argument
        user: UserProfile = request.user.userProfile
        if user.site_admin:
            allowed_talkgroups = TalkGroup.objects.all()
        else:
            system_uuids, systems = get_user_allowed_systems(user.UUID)

            allowed_talkgroups = []
            for system in systems:
                allowed_talkgroups.extend(get_user_allowed_talkgroups(system, user.UUID))

        page = self.paginate_queryset(allowed_talkgroups)
        if page is not None:
            serializer = TalkGroupViewListSerializer(page, many=True)
            return Response(serializer.data)


class TalkGroupCreate(APIView):
    queryset = TalkGroup.objects.all()
    serializer_class = TalkGroupSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["TalkGroup"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["system", "decimal_id"],
            properties={
                "system": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System UUID"
                ),
                "decimal_id": openapi.Schema(
                    type=openapi.TYPE_STRING, description="decimal_id"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="decimal_id"
                ),
                "alpha_tag": openapi.Schema(
                    type=openapi.TYPE_STRING, description="alpha_tag"
                ),
                "encrypted": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="encrypted"
                ),
                "agency": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Agency UUIDs",
                ),
            },
        ),
    )
    def post(self, request):
        """
        Talkgroup Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = (
                uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"{str(data['system'])}+{str(data['decimal_id'])}",
                ),
            )

        serializer = TalkGroupSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TalkGroupView(APIView):
    queryset = TalkGroup.objects.all()
    serializer_class = TalkGroupSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        Fetch Talkgroup ORM Object
        """
        try:
            return TalkGroup.objects.get(UUID=request_uuid)
        except UserProfile.DoesNotExist:
            raise Http404 from UserProfile.DoesNotExist

    @swagger_auto_schema(tags=["TalkGroup"])
    def get(self, request, request_uuid):
        """
        Talkgroup Get EP
        """
        user: UserProfile = request.user.userProfile
        talkgroup: TalkGroup = self.get_object(request_uuid)
        if user.site_admin:
            serializer = TalkGroupViewListSerializer(talkgroup)
            return Response(serializer.data)
        else:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)

            allowed_talkgroups = []
            for system in systems:
                allowed_talkgroups.extend(get_user_allowed_talkgroups(system, user.UUID))

            if not talkgroup in allowed_talkgroups:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = TalkGroupViewListSerializer(talkgroup)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["TalkGroup"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                #'system': openapi.Schema(type=openapi.TYPE_STRING, description='System UUID'),
                #'decimal_id': openapi.Schema(type=openapi.TYPE_STRING, description='decimal_id'),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="decimal_id"
                ),
                "alpha_tag": openapi.Schema(
                    type=openapi.TYPE_STRING, description="alpha_tag"
                ),
                "encrypted": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="encrypted"
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
        Talkgroup Update EP
        """
        data = JSONParser().parse(request)
        talkgroup = self.get_object(request_uuid)

        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = TalkGroupSerializer(talkgroup, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["TalkGroup"])
    def delete(self, request, request_uuid):
        """
        Talkgroup Delete EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        talkgroup = self.get_object(request_uuid)
        talkgroup.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TalkGroupTransmissionList(APIView, PaginationMixin):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_object(self, request_uuid):
        """
        Fetch Talkgroup ORM Object
        """
        try:
            return TalkGroup.objects.get(UUID=request_uuid)
        except TalkGroup.DoesNotExist:
            raise Http404 from TalkGroup.DoesNotExist

    @swagger_auto_schema(tags=["Transmission"])
    def get(self, request, request_uuid):
        """
        Talkgroup Transmission list EP
        """
        user: UserProfile = request.user.userProfile
        talkgroup: TalkGroup = self.get_object(request_uuid)

        transmissions = Transmission.objects.filter(talkgroup=talkgroup)

        if not user.site_admin:
            system: System = talkgroup.system
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)

            if not system in systems:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

            if not talkgroup in talkgroups_allowed:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        transmissions_fs = TransmissionFilter(self.request.GET, queryset=transmissions)
        page = self.paginate_queryset(transmissions_fs.qs)
        if page is not None:
            serializer = TransmissionListSerializer(page, many=True)
            return Response(serializer.data)


class TalkGroupACLList(APIView):
    queryset = TalkGroupACL.objects.all()
    serializer_class = TalkGroupACLSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(tags=["TalkGroupACL"])
    def get(self, request):
        """
        Talkgroup ACL List EP
        """
        talkgroup_acls = TalkGroupACL.objects.all()
        serializer = TalkGroupACLSerializer(talkgroup_acls, many=True)
        return Response(serializer.data)


class TalkGroupACLCreate(APIView):
    queryset = TalkGroupACL.objects.all()
    serializer_class = TalkGroupACLSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["TalkGroupACL"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "users", "default_new_users", "default_new_users"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "users": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup Allowed UUIDs",
                ),
                "default_new_users": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Add New Users to ACL"
                ),
                "allowed_talkgroups": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup Allowed UUIDs",
                ),
                "download_allowed": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Display Download Option"
                ),
            },
        ),
    )
    def post(self, request):
        """
        Talkgroup ACL Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = TalkGroupACLSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TalkGroupACLView(APIView):
    queryset = TalkGroupACL.objects.all()
    serializer_class = TalkGroupACLSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, request_uuid):
        """
        Fetch Talkgroup ORM Object
        """
        try:
            return TalkGroupACL.objects.get(UUID=request_uuid)
        except TalkGroupACL.DoesNotExist:
            raise Http404 from TalkGroupACL.DoesNotExist

    @swagger_auto_schema(tags=["TalkGroupACL"])
    def get(self, request, request_uuid):
        """
        Talkgroup ACL get EP
        """
        talkgroup_acl = self.get_object(request_uuid)
        serializer = TalkGroupACLSerializer(talkgroup_acl)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["TalkGroupACL"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "users": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup Allowed UUIDs",
                ),
                "default_new_users": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Add New Users to ACL"
                ),
                "allowed_talkgroups": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup Allowed UUIDs",
                ),
                "download_allowed": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Display Download Option"
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        Talkgroup ACL Update EP
        """
        data = JSONParser().parse(request)
        talkgroup_acl = self.get_object(request_uuid)
        serializer = TalkGroupACLSerializer(talkgroup_acl, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["TalkGroupACL"])
    def delete(self, request, request_uuid):
        """
        Talkgroup ACL Delete EP
        """
        talkgroup_acl = self.get_object(request_uuid)
        talkgroup_acl.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemRecorderList(APIView, PaginationMixin):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["SystemRecorder"])
    def get(self, request):
        """
        System Recorder list EP
        """
        system_recorders = SystemRecorder.objects.all()

        page = self.paginate_queryset(system_recorders)
        if page is not None:
            serializer = SystemRecorderSerializer(page, many=True)
            return Response(serializer.data)


class SystemRecorderCreate(APIView):
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

        data["api_key"] = uuid.uuid4()

        serializer = SystemRecorderSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemRecorderView(APIView):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer
    permission_classes = [IsSiteAdmin]

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
        system_recorder = self.get_object(request_uuid)
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
        system_recorder = self.get_object(request_uuid)
        system_recorder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UnitList(APIView, PaginationMixin):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["Unit"])
    def get(self, request):
        """
        Unit List EP
        """
        user: UserProfile = request.user.userProfile
        if user.site_admin:
            units = Unit.objects.all()
        else:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            units = Unit.objects.filter(system__in=system_uuids)

        page = self.paginate_queryset(units)
        if page is not None:
            serializer = UnitSerializer(page, many=True)
            return Response(serializer.data)


class UnitCreate(APIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["Unit"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["system", "decimal_id"],
            properties={
                "system": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System UUID"
                ),
                "decimal_id": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System UUID"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
            },
        ),
    )
    def post(self, request):
        """
        Unit Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = UnitSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnitView(APIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        UFetches Unit ORM Object
        """
        try:
            return Unit.objects.get(UUID=request_uuid)
        except Unit.DoesNotExist:
            raise Http404 from Unit.DoesNotExist

    @swagger_auto_schema(tags=["Unit"])
    def get(self, request, request_uuid):
        """
        Unit get EP
        """
        user: UserProfile = request.user.userProfile
        unit: Unit = self.get_object(request_uuid)
        if user.site_admin:
            serializer = UnitSerializer(unit)
        else:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            if not unit.system in systems:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = UnitSerializer(unit)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Unit"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        Unit update EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = JSONParser().parse(request)
        unit = self.get_object(request_uuid)
        serializer = UnitSerializer(unit, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["Unit"])
    def delete(self, request, request_uuid):
        """
        Unit delete EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        unit = self.get_object(request_uuid)
        unit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TransmissionUnitList(APIView):
    queryset = TransmissionUnit.objects.all()
    serializer_class = TransmissionUnitSerializer
    permission_classes = [IsSAOrReadOnly]

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
                    return Response(status=status.HTTP_401_UNAUTHORIZED)

                if system.enable_talkgroup_acls:
                    talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)
                    if not transmission.talkgroup in talkgroups_allowed:
                        return Response(status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = TransmissionUnitSerializer(units, many=True)
        return Response(serializer.data)


class TransmissionUnitView(APIView):
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
                    return Response(status=status.HTTP_401_UNAUTHORIZED)
                if system.enable_talkgroup_acls:
                    talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)
                    if not transmission.talkgroup in talkgroups_allowed:
                        return Response(status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

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
        return Response(status=status.HTTP_401_UNAUTHORIZED)


class TransmissionFreqList(APIView):
    queryset = TransmissionFreq.objects.all()
    serializer_class = TransmissionFreqSerializer
    permission_classes = [IsSAOrReadOnly]

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
                    return Response(status=status.HTTP_401_UNAUTHORIZED)
                if system.enable_talkgroup_acls:
                    talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)
                    if not transmission.talkgroup in talkgroups_allowed:
                        return Response(status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = TransmissionFreqSerializer(freqs, many=True)
        return Response(serializer.data)


class TransmissionFreqView(APIView):
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


class TransmissionList(APIView, PaginationMixin):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = []

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
            allowed_transmissions = []

            for system in systems:
                if system.enable_talkgroup_acls:
                    talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)
                    allowed_transmissions.extend(
                        Transmission.objects.filter(
                            system=system, talkgroup__in=talkgroups_allowed
                        )
                    )
                else:
                    allowed_transmissions.extend(
                        Transmission.objects.filter(system=system)
                    )

        # allowed_transmissions = sorted(
        #     allowed_transmissions, key=lambda instance: instance.start_time, reverse=True
        # )

        transmissions_fs = TransmissionFilter(self.request.GET, queryset=allowed_transmissions)
        page = self.paginate_queryset(transmissions_fs.qs)
        if page is not None:
            serializer = TransmissionListSerializer(page, many=True)
            return Response(serializer.data)


class TransmissionCreate(APIView):
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
        from radio.tasks import send_transmission_notifications

        data = JSONParser().parse(request)

        if not SystemRecorder.objects.filter(api_key=data["recorder"]):
            return Response(
                "Not allowed to post this talkgroup",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            cleaned_data = new_transmission_handler(data)

            if not cleaned_data:
                return Response(
                    "Not allowed to post this talkgroup",
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            cleaned_data["UUID"] = uuid.uuid4()

            recorder: SystemRecorder = SystemRecorder.objects.get(
                api_key=cleaned_data["recorder"]
            )
            cleaned_data["system"] = str(recorder.system.UUID)

            transmission = TransmissionUploadSerializer(data=cleaned_data, partial=True)

            if transmission.is_valid(raise_exception=True):
                transmission.save()
                socket_data = {
                    "UUID": transmission.data["UUID"],
                    "talkgroup": transmission.data["talkgroup"],
                }
                send_transmission_to_web.delay(socket_data, cleaned_data["talkgroup"])
                send_transmission_notifications.delay(transmission.data)
                return Response({"success": True, "UUID": cleaned_data["UUID"]})
            else:
                Response(transmission.errors)
        except Exception as error:
            if settings.SEND_TELEMETRY:
                sentry_sdk.set_context(
                    "add_tx_data",
                    {
                        "data": data,
                    },
                )
                sentry_sdk.capture_exception(error)
            raise error
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)


class TransmissionView(APIView):
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
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            system: System = transmission.system
            if system.enable_talkgroup_acls:
                talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)
                if not transmission.talkgroup in talkgroups_allowed:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = TransmissionSerializer(transmission)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["Transmission"])
    def delete(self, request, request_uuid):
        """
        Transmission Delete EP
        """
        user: UserProfile = request.user.userProfile

        if not user.site_admin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        transmission = self.get_object(request_uuid)
        transmission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IncidentList(APIView, PaginationMixin):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

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
            incidents = Incident.objects.filter(system__in=systems)

        page = self.paginate_queryset(incidents)
        if page is not None:
            serializer = IncidentSerializer(page, many=True)
            return Response(serializer.data)


class IncidentCreate(APIView):
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


class IncidentForward(APIView):
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


class IncidentUpdate(APIView):
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


class IncidentView(APIView):
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


class ScanListList(APIView, PaginationMixin):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["ScanList"])
    def get(self, request):
        """
        ScanList List EP
        """
        user: UserProfile = request.user.userProfile
        if user.site_admin:
            scanlists = ScanList.objects.all()
        else:
            scanlists = ScanList.objects.filter(
                Q(owner=user) | Q(community_shared=True) | Q(public=True)
            )

        page = self.paginate_queryset(scanlists)
        if page is not None:
            serializer = ScanListSerializer(page, many=True)
            return Response(serializer.data)


class ScanListPersonalList(APIView, PaginationMixin):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["ScanList"])
    def get(self, request):
        """
        ScanList personal List EP
        """
        user: UserProfile = request.user.userProfile
        scanlists = ScanList.objects.filter(owner=user)

        page = self.paginate_queryset(scanlists)
        if page is not None:
            serializer = ScanListSerializer(page, many=True)
            return Response(serializer.data)


class ScanListUserList(APIView, PaginationMixin):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["ScanList"])
    def get(self, request, user_uuid):
        """
        ScanList User List EP
        """
        user: UserProfile = request.user.userProfile
        user_scan: UserProfile = UserProfile.objects.get(UUID=user_uuid)
        if user.site_admin:
            scanlists = ScanList.objects.filter(owner=user_scan)
        else:
            scanlists = ScanList.objects.filter(owner=user_scan).filter(
                Q(public=True) | Q(community_shared=True)
            )

        page = self.paginate_queryset(scanlists)
        if page is not None:
            serializer = ScanListSerializer(page, many=True)
            return Response(serializer.data)


class ScanListCreate(APIView):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsUser]

    @swagger_auto_schema(
        tags=["ScanList"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "public", "talkgroups"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "community_shared": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Wether it is shared or user-only",
                ),
                "talkgroups": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup UUIDs",
                ),
            },
        ),
    )
    def post(self, request):
        """
        ScanList Create EP
        """
        data = JSONParser().parse(request)
        user: UserProfile = request.user.userProfile

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        data["owner"] = user.UUID

        if not user.site_admin:
            data["public"] = False

        if not "public" in data:
            data["public"] = False

        serializer = ScanListSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScanListView(APIView):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsUser]

    def get_object(self, request_uuid):
        """
        Fetches ScanList ORM Object
        """
        try:
            return ScanList.objects.get(UUID=request_uuid)
        except ScanList.DoesNotExist:
            raise Http404 from ScanList.DoesNotExist

    @swagger_auto_schema(tags=["ScanList"])
    def get(self, request, request_uuid):
        """
        ScanList Get EP
        """
        scanlist: ScanList = self.get_object(request_uuid)
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            if not scanlist.owner == user:
                if not scanlist.public and not scanlist.community_shared:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = ScanListSerializer(scanlist)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["ScanList"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "owner": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Owner User UUID"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "public": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Wether it is shared or user-only",
                ),
                "talkgroups": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup UUIDs",
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        ScanList Update EP
        """
        data = JSONParser().parse(request)
        scanlist: ScanList = self.get_object(request_uuid)
        serializer = ScanListSerializer(scanlist, data=data, partial=True)

        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            if not scanlist.owner == user:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["ScanList"])
    def delete(self, request, request_uuid):
        """
        ScanList Delete EP
        """
        scanlist: ScanList = self.get_object(request_uuid)

        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            if not scanlist.owner == user:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        scanlist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScanListTransmissionList(APIView, PaginationMixin):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_object(self, request_uuid):
        """
        Fetches ScanList ORM Object
        """
        try:
            return ScanList.objects.get(UUID=request_uuid)
        except ScanList.DoesNotExist:
            raise Http404 from ScanList.DoesNotExist

    @swagger_auto_schema(tags=["Transmission"])
    def get(self, request, request_uuid):
        """
        ScanList Transmission List EP
        """
        user: UserProfile = request.user.userProfile
        scanlist: ScanList = self.get_object(request_uuid)

        talkgroups = scanlist.talkgroups.all()
        transmissions = Transmission.objects.filter(talkgroup__in=talkgroups)
        allowed_transmissions = []

        if user.site_admin:
            allowed_transmissions = transmissions
        else:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            for system in systems:
                if system.enable_talkgroup_acls:
                    talkgroups_allowed = get_user_allowed_talkgroups(system, user.UUID)
                    allowed_transmissions.extend(
                        transmissions.filter(system=system, talkgroup__in=talkgroups_allowed)
                    )
                else:
                    allowed_transmissions.extend(transmissions.filter(system=system))

        transmissions_fs = TransmissionFilter(self.request.GET, queryset=allowed_transmissions)
        page = self.paginate_queryset(transmissions_fs.qs)
        if page is not None:
            serializer = TransmissionListSerializer(page, many=True)
            return Response(serializer.data)


class ScannerList(APIView, PaginationMixin):
    queryset = Scanner.objects.all()
    serializer_class = ScannerSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["Scanner"])
    def get(self, request):
        """
        Scanner List EP
        """
        user: UserProfile = request.user.userProfile
        if user.site_admin:
            scanner = Scanner.objects.all()
        else:
            scanner = Scanner.objects.filter(
                Q(owner=user) | Q(community_shared=True) | Q(public=True)
            )

        page = self.paginate_queryset(scanner)
        if page is not None:
            serializer = ScannerSerializer(page, many=True)
            return Response(serializer.data)


class ScannerCreate(APIView):
    queryset = Scanner.objects.all()
    serializer_class = ScannerSerializer
    permission_classes = [IsUser]

    @swagger_auto_schema(
        tags=["Scanner"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "public", "scanlists"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "community_shared": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Wether it is shared or user-only",
                ),
                "scanlists": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Scanlist UUIDs",
                ),
            },
        ),
    )
    def post(self, request):
        """
        Scanner Update EP
        """
        data = JSONParser().parse(request)
        user: UserProfile = request.user.userProfile

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        data["owner"] = user.UUID

        if not user.site_admin:
            data["public"] = False

        if not "public" in data:
            data["public"] = False

        serializer = ScannerSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScannerView(APIView):
    queryset = Scanner.objects.all()
    serializer_class = ScannerSerializer
    permission_classes = [IsUser]

    def get_object(self, request_uuid):
        """
        Fetches Scanner ORM Object
        """
        try:
            return Scanner.objects.get(UUID=request_uuid)
        except Scanner.DoesNotExist:
            raise Http404 from Scanner.DoesNotExist

    @swagger_auto_schema(tags=["Scanner"])
    def get(self, request, request_uuid):
        """
        Scanner Get EP
        """
        scanner: Scanner = self.get_object(request_uuid)
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            if not scanner.owner == user:
                if not scanner.public and not scanner.community_shared:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = ScannerSerializer(Scanner)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Scanner"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "owner": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Owner User UUID"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "public": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Wether it is shared or user-only",
                ),
                "scanlists": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Scanlist UUIDs",
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        Scanner Update EP
        """
        data = JSONParser().parse(request)
        scanner: Scanner = self.get_object(request_uuid)

        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            if not scanner.owner == user:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = ScannerSerializer(scanner, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["Scanner"])
    def delete(self, request, request_uuid):
        """
        Scanner Delete EP
        """
        scanner: Scanner = self.get_object(request_uuid)
        user: UserProfile = request.user.userProfile

        if not user.site_admin:
            if not scanner.owner == user:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        scanner.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScannerTransmissionList(APIView, PaginationMixin):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_object(self, request_uuid):
        """
        Fetches Scanner ORM Object
        """
        try:
            return Scanner.objects.get(UUID=request_uuid)
        except Scanner.DoesNotExist:
            raise Http404 from Scanner.DoesNotExist

    @swagger_auto_schema(tags=["Transmission"])
    def get(self, request, request_uuid):
        """
        Scanner Transmission List EP
        """
        user: UserProfile = request.user.userProfile
        scanner: Scanner = self.get_object(request_uuid)
        # pylint: disable=unused-variable
        system_uuids, systems = get_user_allowed_systems(user.UUID)

        allowed_transmisssions = []
        scanlist_talkgroups = []
        transmissions = []

        scanlist_talkgroups = scanner.scanlists.all().values_list(
            "talkgroups", flat=True
        )
        scanlist_talkgroups = list(dict.fromkeys(scanlist_talkgroups))
        transmissions = Transmission.objects.filter(talkgroup__in=scanlist_talkgroups)

        if not user.site_admin:
            acl_systems = transmissions.filter(
                system__enable_talkgroup_acls=True, system__in=systems
            ).values_list("system", flat=True)
            non_acl_systems = transmissions.filter(
                system__enable_talkgroup_acls=False, system__in=systems
            ).values_list("system", flat=True)

            non_acl_systems = list(dict.fromkeys(non_acl_systems))
            acl_systems = list(dict.fromkeys(acl_systems))

            talkgroups_allowed = []
            talkgroups_allowed.extend(
                TalkGroup.objects.filter(system__UUID__in=non_acl_systems)
            )

            for system in acl_systems:
                system_object = System.objects.get(UUID=system)
                user_allowed_talkgroups = get_user_allowed_talkgroups(
                    system_object, user.UUID
                )
                talkgroups_allowed.extend(user_allowed_talkgroups)

            allowed_transmisssions = transmissions.filter(talkgroup__in=talkgroups_allowed)
        else:
            allowed_transmisssions = transmissions

        transmissions_fs = TransmissionFilter(self.request.GET, queryset=allowed_transmisssions)
        page = self.paginate_queryset(transmissions_fs.qs)
        if page is not None:
            serializer = TransmissionListSerializer(page, many=True)
            return Response(serializer.data)


class GlobalAnnouncementList(APIView, PaginationMixin):
    queryset = GlobalAnnouncement.objects.all()
    serializer_class = GlobalAnnouncementSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["GlobalAnnouncement"])
    def get(self, request):
        """
        GlobalAnnouncement List EP
        """
        user: UserProfile = request.user.userProfile
        if user.site_admin:
            global_announcements = GlobalAnnouncement.objects.all()
        else:
            global_announcements = GlobalAnnouncement.objects.filter(enabled=True)

        page = self.paginate_queryset(global_announcements)
        if page is not None:
            serializer = GlobalAnnouncementSerializer(page, many=True)
            return Response(serializer.data)


class GlobalAnnouncementCreate(APIView):
    queryset = GlobalAnnouncement.objects.all()
    serializer_class = GlobalAnnouncementSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["GlobalAnnouncement"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "enabled"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Enabled"
                ),
            },
        ),
    )
    def post(self, request):
        """
        GlobalAnnouncement Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = GlobalAnnouncementSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GlobalAnnouncementView(APIView):
    queryset = GlobalAnnouncement.objects.all()
    serializer_class = GlobalAnnouncementSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        Fetches GlobalAnnouncement ORM Object
        """
        try:
            return GlobalAnnouncement.objects.get(UUID=request_uuid)
        except GlobalAnnouncement.DoesNotExist:
            raise Http404 from GlobalAnnouncement.DoesNotExist

    @swagger_auto_schema(tags=["GlobalAnnouncement"])
    def get(self, request, request_uuid):
        """
        GlobalAnnouncement Get EP
        """
        user: UserProfile = request.user.userProfile
        global_announcement: GlobalAnnouncement = self.get_object(request_uuid)
        if not user.site_admin:
            if not global_announcement.enabled:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = GlobalAnnouncementSerializer(global_announcement)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["GlobalAnnouncement"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Enabled"
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        GlobalAnnouncement Update EP
        """
        data = JSONParser().parse(request)
        user: UserProfile = request.user.userProfile

        if user.site_admin:
            global_announcement: GlobalAnnouncement = self.get_object(request_uuid)
            serializer = GlobalAnnouncementSerializer(
                global_announcement, data=data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["GlobalAnnouncement"])
    def delete(self, request, request_uuid):
        """
        GlobalAnnouncement Delete EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        global_announcement: GlobalAnnouncement = self.get_object(request_uuid)
        global_announcement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GlobalEmailTemplateList(APIView, PaginationMixin):
    queryset = GlobalEmailTemplate.objects.all()
    serializer_class = GlobalEmailTemplateSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["GlobalEmailTemplate"])
    def get(self, request):
        """
        GlobalEmailTemplate List EP
        """
        global_email_templates = GlobalEmailTemplate.objects.all()

        page = self.paginate_queryset(global_email_templates)
a        if page is not None:
            serializer = GlobalEmailTemplateSerializer(global_email_templates, many=True)
            return Response(serializer.data)


class GlobalEmailTemplateCreate(APIView):
    queryset = GlobalEmailTemplate.objects.all()
    serializer_class = GlobalEmailTemplateSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["GlobalEmailTemplate"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "template_type": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Email type"
                ),
                "HTML": openapi.Schema(type=openapi.TYPE_STRING, description="HTML"),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Enabled"
                ),
            },
        ),
    )
    def post(self, request):
        """
        GlobalEmailTemplate Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = GlobalEmailTemplateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GlobalEmailTemplateView(APIView):
    queryset = GlobalEmailTemplate.objects.all()
    serializer_class = GlobalEmailTemplateSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, request_uuid):
        """
        Fetches GlobalEmailTemplate ORM Object
        """
        try:
            return GlobalEmailTemplate.objects.get(UUID=request_uuid)
        except GlobalEmailTemplate.DoesNotExist:
            raise Http404 from GlobalEmailTemplate.DoesNotExist

    @swagger_auto_schema(tags=["GlobalEmailTemplate"])
    def get(self, request, request_uuid):
        """
        GlobalEmailTemplate Get EP
        """
        # pylint: disable=unused-variable
        global_email_template = self.get_object(request_uuid)
        serializer = GlobalEmailTemplateSerializer(GlobalEmailTemplate)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["GlobalEmailTemplate"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "template_type": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Email type"
                ),
                "HTML": openapi.Schema(type=openapi.TYPE_STRING, description="HTML"),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Enabled"
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        GlobalEmailTemplate Update EP
        """
        data = JSONParser().parse(request)
        global_email_template = self.get_object(request_uuid)
        serializer = GlobalEmailTemplateSerializer(
            global_email_template, data=data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["GlobalEmailTemplate"])
    def delete(self, request, request_uuid):
        """
        GlobalEmailTemplate delete EP
        """
        global_email_template = self.get_object(request_uuid)
        global_email_template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# class SystemReciveRateList(APIView, PaginationMixin):
#     queryset = SystemReciveRate.objects.all()
#     serializer_class = SystemReciveRateSerializer
#     permission_classes = [IsSAOrReadOnly]
#     pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

#     @swagger_auto_schema(tags=["SystemReciveRate"])
#     def get(self, request):
#         SystemReciveRates = SystemReciveRate.objects.all()

#         page = self.paginate_queryset(SystemReciveRates)
#         if page is not None:
#             serializer = SystemReciveRateSerializer(SystemReciveRates, many=True)
#             return Response(serializer.data)


# class SystemReciveRateCreate(APIView):
#     queryset = SystemReciveRate.objects.all()
#     serializer_class = SystemReciveRateCreateSerializer
#     permission_classes = [FeederFree]

#     @swagger_auto_schema(
#         tags=["SystemReciveRate"],
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=["time", "rate", "recorder"],
#             properties={
#                 "time": openapi.Schema(type=openapi.TYPE_STRING, description="time"),
#                 "rate": openapi.Schema(
#                     type=openapi.TYPE_STRING, description="System Message rate"
#                 ),
#                 "recorder": openapi.Schema(
#                     type=openapi.TYPE_STRING, description="Recorder Key"
#                 ),
#             },
#         ),
#     )
#     def post(self, request):
#         data = JSONParser().parse(request)

#         if not SystemRecorder.objects.filter(api_key=data["recorder"]):
#             return Response(status=status.HTTP_401_UNAUTHORIZED)

#         data["UUID"] = uuid.uuid4()

#         serializer = SystemReciveRateCreateSerializer(data=data)
#         if serializer.is_valid():
#             serializer.save()
#             dataX = serializer.data
#             print(dataX)
#             dataX["UUID"] = str(dataX["UUID"])
#             return Response(dataX)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class SystemReciveRateView(APIView):
#     queryset = SystemReciveRate.objects.all()
#     serializer_class = SystemReciveRateSerializer
#     permission_classes = [IsSAOrReadOnly]

#     def get_object(self, UUID):
#         try:
#             return SystemReciveRate.objects.get(UUID=UUID)
#         except UserProfile.DoesNotExist:
#             raise Http404

#     @swagger_auto_schema(tags=["SystemReciveRate"])
#     def get(self, request, UUID):
#         SystemReciveRateX: SystemReciveRate = self.get_object(UUID)
#         serializer = SystemReciveRateSerializer(SystemReciveRateX)
#         return Response(serializer.data)

#     @swagger_auto_schema(tags=["SystemReciveRate"])
#     def delete(self, request, UUID):
#         user: UserProfile = request.user.userProfile
#         if not user.site_admin:
#             return Response(status=status.HTTP_401_UNAUTHORIZED)
#         SystemReciveRateX: SystemReciveRate = self.get_object(UUID)
#         SystemReciveRateX.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# class CallList(APIView, PaginationMixin):
#     queryset = Call.objects.all()
#     serializer_class = CallSerializer
#     permission_classes = [IsSAOrReadOnly]
#     pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

#     @swagger_auto_schema(tags=["Call"])
#     def get(self, request):
#         user: UserProfile = request.user.userProfile

#         if user.site_admin:
#             Calls = Call.objects.all()
#         else:
#             system_uuids, systems = get_user_allowed_systems(user.UUID)
#             TalkGroups = TalkGroup.objects.filter(system__in=systems)
#             Calls = Call.objects.filter(talkgroup__in=TalkGroups)

#         page = self.paginate_queryset(Calls)
#         if page is not None:
#             serializer = CallSerializer(page, many=True, read_only=True)
#             return Response(serializer.data)


# class CallCreate(APIView):
#     queryset = Call.objects.all()
#     serializer_class = CallUpdateCreateSerializer
#     permission_classes = [FeederFree]

#     @swagger_auto_schema(
#         tags=["Call"],
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=[
#                 "trunkRecorderID",
#                 "start_time",
#                 "end_time",
#                 "units",
#                 "emergency",
#                 "encrypted",
#                 "frequency",
#                 "phase2",
#                 "talkgroup",
#                 "recorder",
#             ],
#             properties={
#                 "trunkRecorderID": openapi.Schema(
#                     type=openapi.TYPE_STRING, description="Trunk Recorder ID"
#                 ),
#                 "start_time": openapi.Schema(
#                     type=openapi.TYPE_STRING, description="Start Time"
#                 ),
#                 "end_time": openapi.Schema(
#                     type=openapi.TYPE_STRING, description="End Time"
#                 ),
#                 "units": openapi.Schema(
#                     type=openapi.TYPE_ARRAY,
#                     items=openapi.Items(type=openapi.TYPE_STRING),
#                     description="Unit Decimal IDs",
#                 ),
#                 "emergency": openapi.Schema(
#                     type=openapi.TYPE_BOOLEAN, description="Emergency Call"
#                 ),
#                 "active": openapi.Schema(
#                     type=openapi.TYPE_BOOLEAN, description="Active Call"
#                 ),
#                 "encrypted": openapi.Schema(
#                     type=openapi.TYPE_BOOLEAN, description="Encrypted Call"
#                 ),
#                 "frequency": openapi.Schema(
#                     type=openapi.TYPE_BOOLEAN, description="Frequency"
#                 ),
#                 "phase2": openapi.Schema(
#                     type=openapi.TYPE_STRING, description="Phase2"
#                 ),
#                 "talkgroup": openapi.Schema(
#                     type=openapi.TYPE_STRING, description="Talk Group DecimalID"
#                 ),
#                 "recorder": openapi.Schema(
#                     type=openapi.TYPE_STRING, description="Recorder Key"
#                 ),
#             },
#         ),
#     )
#     def post(self, request):
#         data = JSONParser().parse(request)

#         if not SystemRecorder.objects.filter(api_key=data["recorder"]):
#             return Response(status=status.HTTP_401_UNAUTHORIZED)

#         if not "UUID" in data:
#             data["UUID"] = uuid.uuid4()

#         serializer = CallUpdateCreateSerializer(data=data)

#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class CallView(APIView):
#     queryset = Call.objects.all()
#     serializer_class = CallSerializer
#     permission_classes = [IsSiteAdmin]

#     def get_object(self, UUID):
#         try:
#             return Call.objects.get(UUID=UUID)
#         except UserProfile.DoesNotExist:
#             raise Http404

#     @swagger_auto_schema(tags=["Call"])
#     def get(self, request, UUID):
#         user: UserProfile = request.user.userProfile
#         CallX: Call = self.get_object(UUID)

#         if not user.site_admin:
#             system_uuids, systems = get_user_allowed_systems(user.UUID)
#             TalkGroups = TalkGroup.objects.filter(system__in=systems)
#             if not CallX.talkgroup in TalkGroups:
#                 return Response(status=status.HTTP_401_UNAUTHORIZED)

#         serializer = CallSerializer(CallX)
#         return Response(serializer.data)

#     @swagger_auto_schema(tags=["Call"])
#     def delete(self, request, UUID):
#         user: UserProfile = request.user.userProfile
#         if not user.site_admin:
#             return Response(status=status.HTTP_401_UNAUTHORIZED)
#         CallX: Call = self.get_object(UUID)
#         CallX.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
