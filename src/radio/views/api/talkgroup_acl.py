import logging
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
    TalkGroupACLFilter
)

from radio.serializers import (
    TalkGroupACLSerializer
)

from radio.permission import (
    IsSiteAdmin
)

from radio.models import (
    TalkGroupACL
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk

class List(APIView, PaginationMixin):
    queryset = TalkGroupACL.objects.all()
    serializer_class = TalkGroupACLSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TalkGroupACLFilter
   
    @swagger_auto_schema(tags=["TalkGroupACL"])
    def get(self, request):
        """
        Talkgroup ACL List EP
        """
        talkgroup_acls = TalkGroupACL.objects.all()
        filterobject_fs = TalkGroupACLFilter(self.request.GET, queryset=talkgroup_acls)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = TalkGroupACLSerializer(page, many=True)
            return Response(serializer.data)


class Create(APIView):
    queryset = TalkGroupACL.objects.all()
    serializer_class = TalkGroupACLSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["TalkGroupACL"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "users", "default_new_users", "default_new_users"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "users": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup Allowed UUIDs",
                ),
                "default_new_users": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Add New Users to ACL"
                ),
                "allowed_talkgroups": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup Allowed UUIDs",
                ),
                "download_allowed": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Display Download Option"
                ),
                "transcript_allowed": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Display Transcript of transmission"
                ),
            },
        ),
    )
    def post(self, request):
        """
        Talkgroup ACL Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = TalkGroupACLSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class View(APIView):
    queryset = TalkGroupACL.objects.all()
    serializer_class = TalkGroupACLSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, request_uuid):
        """
        Fetch Talkgroup ORM Object
        """
        try:
            return TalkGroupACL.objects.get(UUID=request_uuid)
        except TalkGroupACL.DoesNotExist:
            raise Http404 from TalkGroupACL.DoesNotExist

    @swagger_auto_schema(tags=["TalkGroupACL"])
    def get(self, request, request_uuid):
        """
        Talkgroup ACL get EP
        """
        talkgroup_acl = self.get_object(request_uuid)
        serializer = TalkGroupACLSerializer(talkgroup_acl)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["TalkGroupACL"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "users": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup Allowed UUIDs",
                ),
                "default_new_users": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Add New Users to ACL"
                ),
                "allowed_talkgroups": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup Allowed UUIDs",
                ),
                "download_allowed": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Display Download Option"
                ),
                "transcript_allowed": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Display Transcript of transmission"
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        Talkgroup ACL Update EP
        """
        data = JSONParser().parse(request)
        talkgroup_acl = self.get_object(request_uuid)
        serializer = TalkGroupACLSerializer(talkgroup_acl, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["TalkGroupACL"])
    def delete(self, request, request_uuid):
        """
        Talkgroup ACL Delete EP
        """
        talkgroup_acl = self.get_object(request_uuid)
        talkgroup_acl.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

