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
    TalkGroupFilter,
    TransmissionFilter
)
from radio.serializers import (
    TalkGroupSerializer,
    TalkGroupViewListSerializer,
    TransmissionListSerializer
)

from radio.helpers.utils import (
    get_user_allowed_talkgroups_for_systems,
    get_user_allowed_systems,
    get_user_allowed_talkgroups,
)

from radio.permission import (
    IsSAOrReadOnly,
    IsSiteAdmin
)

from radio.models import (
    UserProfile,
    System,
    TalkGroup,
    Transmission
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = TalkGroup.objects.all()
    serializer_class = TalkGroupViewListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TalkGroupFilter

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
            del system_uuids
            allowed_talkgroups = get_user_allowed_talkgroups_for_systems(systems, user.UUID)

        filterobject_fs = TalkGroupFilter(self.request.GET, queryset=allowed_talkgroups)

        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = TalkGroupViewListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
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
                "mode": openapi.Schema(
                    type=openapi.TYPE_STRING, description="mode"
                ),
                "encrypted": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="encrypted"
                ),
                "agency": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Agency UUIDs",
                ),
                "notes": openapi.Schema(
                    type=openapi.TYPE_STRING, description="notes"
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


class View(APIView):
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
                "mode": openapi.Schema(
                    type=openapi.TYPE_STRING, description="mode"
                ),
                "agency": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Agency UUIDs",
                ),
                "notes": openapi.Schema(
                    type=openapi.TYPE_STRING, description="notes"
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


class TransmissionList(APIView, PaginationMixin):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TransmissionFilter

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
            return self.get_paginated_response(serializer.data)
