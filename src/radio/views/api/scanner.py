# import logging
import logging
import uuid

from django.conf import settings
from django.http import Http404
from django.db.models import Q

from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser
from rest_framework import status

from django_filters import rest_framework as filters


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from radio.filters import (
    ScannerFilter,
    TransmissionFilter
)

from radio.serializers import (
    TransmissionListSerializer,
    ScannerSerializer
)

from radio.helpers.utils import (
    get_user_allowed_systems,
    get_user_allowed_talkgroups,
)

from radio.permission import (
    IsSAOrReadOnly,
    IsUser
)

from radio.models import (
    UserProfile,
    System,
    TalkGroup,
    Transmission,
    Scanner,
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = Scanner.objects.all()
    serializer_class = ScannerSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ScannerFilter

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

        filterobject_fs = ScannerFilter(self.request.GET, queryset=scanner)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = ScannerSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
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
                "notes": openapi.Schema(
                    type=openapi.TYPE_STRING, description="notes"
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


class View(APIView):
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
                    raise PermissionDenied
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
                "notes": openapi.Schema(
                    type=openapi.TYPE_STRING, description="notes"
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
                raise PermissionDenied

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
                raise PermissionDenied

        scanner.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TransmissionList(APIView, PaginationMixin):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TransmissionFilter

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

        filterobject_fs = TransmissionFilter(self.request.GET, queryset=allowed_transmisssions)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = TransmissionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
