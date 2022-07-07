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
    UserAlertFilter
)
from radio.serializers import (
    UserAlertSerializer
)

from radio.permission import (
    IsSAOrUser
)

from radio.models import (
    UserProfile,
    UserAlert
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk # pylint: disable=unused-import


class List(APIView, PaginationMixin):
    queryset = UserAlert.objects.all()
    serializer_class = UserAlertSerializer
    permission_classes = [IsSAOrUser]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UserAlertFilter

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

        filtered_result = UserAlertFilter(self.request.GET, queryset=user_alerts)
        page = self.paginate_queryset(filtered_result.qs)
        if page is not None:
            serializer = UserAlertSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
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
                "emergency_only": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Only alert on Emergency Transmissions",
                ),
                "count": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Number of Transmissions over trigger time to alert"
                ),
                "trigger_time": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="trigger time"
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


class View(APIView):
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
            if not user.site_admin:
                raise PermissionDenied

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
                "emergency_only": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Only alert on Emergency Transmissions",
                ),
                "count": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Number of Transmissions over trigger time to alert"
                ),
                "trigger_time": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="trigger time"
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
            if not user.site_admin:
                raise PermissionDenied
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
            if not user.site_admin:
                raise PermissionDenied
        user_alert.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
