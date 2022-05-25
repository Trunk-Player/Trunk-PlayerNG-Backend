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
    GlobalEmailTemplateFilter,
)

from radio.serializers import (
    GlobalEmailTemplateSerializer
)

from radio.permission import (
    IsSiteAdmin
)

from radio.models import (
    GlobalEmailTemplate
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = GlobalEmailTemplate.objects.all()
    serializer_class = GlobalEmailTemplateSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = GlobalEmailTemplateFilter

    @swagger_auto_schema(tags=["GlobalEmailTemplate"])
    def get(self, request):
        """
        GlobalEmailTemplate List EP
        """
        global_email_templates = GlobalEmailTemplate.objects.all()

        filterobject_fs = GlobalEmailTemplateFilter(self.request.GET, queryset=global_email_templates)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = GlobalEmailTemplateSerializer(global_email_templates, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
    queryset = GlobalEmailTemplate.objects.all()
    serializer_class = GlobalEmailTemplateSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["GlobalEmailTemplate"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "template_type": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Email type"
                ),
                "HTML": openapi.Schema(type=openapi.TYPE_STRING, description="HTML"),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Enabled"
                ),
            },
        ),
    )
    def post(self, request):
        """
        GlobalEmailTemplate Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = GlobalEmailTemplateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class View(APIView):
    queryset = GlobalEmailTemplate.objects.all()
    serializer_class = GlobalEmailTemplateSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, request_uuid):
        """
        Fetches GlobalEmailTemplate ORM Object
        """
        try:
            return GlobalEmailTemplate.objects.get(UUID=request_uuid)
        except GlobalEmailTemplate.DoesNotExist:
            raise Http404 from GlobalEmailTemplate.DoesNotExist

    @swagger_auto_schema(tags=["GlobalEmailTemplate"])
    def get(self, request, request_uuid):
        """
        GlobalEmailTemplate Get EP
        """
        # pylint: disable=unused-variable
        global_email_template = self.get_object(request_uuid)
        serializer = GlobalEmailTemplateSerializer(GlobalEmailTemplate)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["GlobalEmailTemplate"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "template_type": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Email type"
                ),
                "HTML": openapi.Schema(type=openapi.TYPE_STRING, description="HTML"),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Enabled"
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        GlobalEmailTemplate Update EP
        """
        data = JSONParser().parse(request)
        global_email_template = self.get_object(request_uuid)
        serializer = GlobalEmailTemplateSerializer(
            global_email_template, data=data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["GlobalEmailTemplate"])
    def delete(self, request, request_uuid):
        """
        GlobalEmailTemplate delete EP
        """
        global_email_template = self.get_object(request_uuid)
        global_email_template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
