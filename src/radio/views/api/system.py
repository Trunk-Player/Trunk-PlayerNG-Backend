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
    SystemFilter,
)
from radio.serializers import (
    SystemSerializer
)

from radio.permission import (
    IsSAOrReadOnly,
    IsSiteAdmin
)

from radio.models import (
    UserProfile,
    SystemACL,
    System,
)

from radio.tasks import (
    import_radio_refrence
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SystemFilter

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
            return self.get_paginated_response(serializer.data)


class Create(APIView):
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
                "rr_system_id": openapi.Schema(
                    type=openapi.TYPE_STRING, description="The Radio Refrence system ID"
                ),
                "prune_transmissions": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Enable Pruneing Transmissions on system",
                ),
                "prune_transmissions_after_days": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Days to keep Transmissions (Prune)",
                ),
                "notes": openapi.Schema(
                    type=openapi.TYPE_STRING, description="notes"
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


class View(APIView):
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
            raise PermissionDenied

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
                "rr_system_id": openapi.Schema(
                    type=openapi.TYPE_STRING, description="The Radio Refrence system ID"
                ),
                "prune_transmissions": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Enable Pruneing Transmissions on system",
                ),
                "prune_transmissions_after_days": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Days to keep Transmissions (Prune)",
                ),
                "notes": openapi.Schema(
                    type=openapi.TYPE_STRING, description="notes"
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
            raise PermissionDenied
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
            raise PermissionDenied

class RRImport(APIView):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["System"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["username", "password"],
            properties={
                "siteid": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Radio Refrence Site ID - Only needed if not in DB"
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

        system: System = System.objects.get(uuid=request_uuid)
        if system.rr_system_id:
            site_id = system.rr_system_id
        elif "siteid" in data:
            site_id = data["siteid"]
        else:
            return Response({"message": "Please add 'siteid' to your request or add the rr id to the system"}, status=status.HTTP_400_BAD_REQUEST)


        import_radio_refrence.delay(
            request_uuid, site_id, data["username"], data["password"]
        )

        return Response({"message": "System Import from Radio Refrence Qued"})
