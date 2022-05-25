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
    GlobalAnnouncementFilter
)

from radio.serializers import (
    GlobalAnnouncementSerializer
)

from radio.permission import (
    IsSAOrReadOnly,
    IsSiteAdmin
)

from radio.models import (
    UserProfile,
    GlobalAnnouncement
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = GlobalAnnouncement.objects.all()
    serializer_class = GlobalAnnouncementSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = GlobalAnnouncementFilter

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

        filterobject_fs = GlobalAnnouncementFilter(self.request.GET, queryset=global_announcements)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = GlobalAnnouncementSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
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


class View(APIView):
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
