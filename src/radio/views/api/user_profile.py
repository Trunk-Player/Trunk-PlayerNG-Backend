import logging

from django.conf import settings
from django.http import  Http404
from django.core.exceptions import PermissionDenied

from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django_filters import rest_framework as filters


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


from radio.filters import (
    UserProfileFilter
)

from radio.serializers import (
    UserProfileSerializer
)

from radio.permission import (
    IsSAOrReadOnly,
    IsSAOrUser
)

from radio.models import (
    UserProfile
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk


class List(APIView, PaginationMixin):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsSAOrUser]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UserProfileFilter

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

        filtered_result = UserProfileFilter(self.request.GET, queryset=user_profile)
        page = self.paginate_queryset(filtered_result.qs)
        if page is not None:
            serializer = UserProfileSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class View(APIView):
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
