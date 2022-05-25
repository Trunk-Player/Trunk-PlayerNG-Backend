# import logging
import logging
import uuid

from django.conf import settings
from django.http import  Http404
from django.db.models import Q

from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework import status

from django_filters import rest_framework as filters


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


from radio.filters import (
    ScanListFilter,
    TransmissionFilter
)

from radio.serializers import (
    TransmissionListSerializer,
    ScanListSerializer
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
    Transmission,
    ScanList
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk


class List(APIView, PaginationMixin):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ScanListFilter

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

        filterobject_fs = ScanListFilter(self.request.GET, queryset=scanlists)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = ScanListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class PersonalList(APIView, PaginationMixin):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ScanListFilter

    @swagger_auto_schema(tags=["ScanList"])
    def get(self, request):
        """
        ScanList personal List EP
        """
        user: UserProfile = request.user.userProfile
        scanlists = ScanList.objects.filter(owner=user)

        filterobject_fs = ScanListFilter(self.request.GET, queryset=scanlists)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = ScanListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class UserList(APIView, PaginationMixin):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ScanListFilter

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

        filterobject_fs = ScanListFilter(self.request.GET, queryset=scanlists)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = ScanListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
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


class View(APIView):
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


class TransmissionList(APIView, PaginationMixin):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TransmissionFilter

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
            del system_uuids
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
            return self.get_paginated_response(serializer.data)
