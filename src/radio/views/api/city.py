# import logging
import logging
import uuid

from django.conf import settings
from django.http import  Http404

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
    CityFilter
)
from radio.serializers import (
    CitySerializer
)

from radio.permission import (
    IsSAOrReadOnly,
    IsSiteAdmin
)

from radio.models import (
    UserProfile,
    City
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CityFilter

    @swagger_auto_schema(tags=["City"])
    def get(self, request):
        """
        City List EP
        """
        citys = City.objects.all()
        filterobject_fs = CityFilter(self.request.GET, queryset=citys)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = CitySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
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


class View(APIView):
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