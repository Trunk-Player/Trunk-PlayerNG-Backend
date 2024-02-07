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
    UnitFilter
)

from radio.serializers import (
    UnitSerializer
)

from radio.helpers.utils import (
    get_user_allowed_systems
)

from radio.permission import (
    IsSAOrReadOnly,
    IsSiteAdmin
)

from radio.models import (
    UserProfile,
    Unit
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk


class List(APIView, PaginationMixin):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UnitFilter

    @swagger_auto_schema(tags=["Unit"])
    def get(self, request):
        """
        Unit List EP
        """
        user: UserProfile = request.user.userProfile
        if user.site_admin:
            units = Unit.objects.all()
        else:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            del systems
            units = Unit.objects.filter(system__in=system_uuids)

        filterobject_fs = UnitFilter(self.request.GET, queryset=units)
        page = self.paginate_queryset(filterobject_fs.qs)
        if page is not None:
            serializer = UnitSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class Create(APIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["Unit"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["system", "decimal_id"],
            properties={
                "system": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System UUID"
                ),
                "decimal_id": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System UUID"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
            },
        ),
    )
    def post(self, request):
        """
        Unit Create EP
        """
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = UnitSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class View(APIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_id):
        """
        UFetches Unit ORM Object
        """
        try:
            return Unit.objects.get(UUID=request_id)
        except Unit.DoesNotExist:
            try:
                return Unit.objects.get(decimal_id=request_id)
            except:
                raise Http404 from Unit.DoesNotExist

    @swagger_auto_schema(tags=["Unit"])
    def get(self, request, request_uuid):
        """
        Unit get EP
        """
        user: UserProfile = request.user.userProfile
        unit: Unit = self.get_object(request_uuid)
        if user.site_admin:
            serializer = UnitSerializer(unit)
        else:
            # pylint: disable=unused-variable
            system_uuids, systems = get_user_allowed_systems(user.UUID)
            if not unit.system in systems:
                raise PermissionDenied

        serializer = UnitSerializer(unit)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Unit"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        Unit update EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            raise PermissionDenied

        data = JSONParser().parse(request)
        unit = self.get_object(request_uuid)
        serializer = UnitSerializer(unit, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["Unit"])
    def delete(self, request, request_uuid):
        """
        Unit delete EP
        """
        user: UserProfile = request.user.userProfile
        if not user.site_admin:
            raise PermissionDenied

        unit = self.get_object(request_uuid)
        unit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

