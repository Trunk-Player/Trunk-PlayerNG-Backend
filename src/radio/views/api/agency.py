# import logging
import logging
import uuid

from django.conf import settings
from django.http import Http404

from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework import status

from django_filters import rest_framework as filters

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from radio.filters import (
    AgencyFilter,
)

from radio.serializers import (
    AgencySerializer,
    AgencyViewListSerializer,
)

from radio.permission import (
    IsSAOrReadOnly,
    IsSiteAdmin
)

from radio.models import (
    UserProfile,
    Agency
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = Agency.objects.all()
    serializer_class = AgencyViewListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = AgencyFilter

    @swagger_auto_schema(tags=["Agency"])
    def get(self, request):
        """
        Agency List EP
        """
        agencys = Agency.objects.all()
        filterobject_fs = AgencyFilter(self.request.GET, queryset=agencys)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = AgencyViewListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
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


class View(APIView):
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

