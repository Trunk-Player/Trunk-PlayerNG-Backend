import logging
import uuid

from django.conf import settings
from django.http import Http404

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
    SystemACLFilter
)
from radio.serializers import (
    SystemACLSerializer,
)

from radio.permission import (
    IsSiteAdmin
)

from radio.models import (
    SystemACL
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = SystemACL.objects.all()
    serializer_class = SystemACLSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SystemACLFilter

    @swagger_auto_schema(tags=["SystemACL"])
    def get(self, request):
        """
        System ACL get EP
        """
        system_acls = SystemACL.objects.all()
        filtered_result = SystemACLFilter(self.request.GET, queryset=system_acls)
        page = self.paginate_queryset(filtered_result.qs)
        if page is not None:
            serializer = SystemACLSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
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


class View(APIView):
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