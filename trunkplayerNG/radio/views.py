from logging import log
import operator
import logging, json
from celery.utils.log import logger_isa
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from django.http import Http404, HttpResponse
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from radio.models import *
from radio.serializers import *
from rest_framework.parsers import JSONParser
from rest_framework import status
from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from asgiref.sync import sync_to_async

from radio.tasks import import_radio_refrence

from radio.helpers.transmission import new_transmission_handler
from radio.helpers.utils import (
    getUserAllowedSystems,
    getUserAllowedTalkgroups,
)

from radio.permission import (
    FeederFree,
    IsSAOrReadOnly,
    IsSAOrUser,
    IsSiteAdmin,
    IsUser,
)



class PaginationMixin(object):
    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination
        is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given
        output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)



class UserAlertList(APIView, PaginationMixin):
    queryset = UserAlert.objects.all()
    serializer_class = UserAlertSerializer
    permission_classes = [IsSAOrUser]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["UserAlert"])
    def get(self, request, format=None):
        user:UserProfile = request.user.userProfile
        if user.siteAdmin:
            UserAlerts = UserAlert.objects.all()
        else:            
            UserAlerts = UserAlert.objects.filter(user=user)

        page = self.paginate_queryset(UserAlerts)
        if page is not None:
            serializer = UserAlertSerializer(page, many=True)
            return Response(serializer.data)


class UserAlertCreate(APIView):
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
                "webNotification": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Send Webpage Notification"
                ),
                "appRiseNotification": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Send AppRise Notification"
                ),
                "appRiseURLs": openapi.Schema(type=openapi.TYPE_STRING, description="appRiseURLs"),
            },
        ),
    )
    def post(self, request, format=None):
        user:UserProfile = request.user.userProfile
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        data["user"] = str(user.UUID)
        
        serializer = UserAlertSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAlertView(APIView):
    queryset = UserAlert.objects.all()
    serializer_class = UserAlertSerializer
    permission_classes = [IsSAOrUser]

    def get_object(self, UUID):
        try:
            return UserAlert.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["UserAlert"])
    def get(self, request, UUID, format=None):
        user:UserProfile = request.user.userProfile
        UserAlertX:UserAlert = self.get_object(UUID)
        if not UserAlertX.user == user:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
       
        serializer = UserAlertSerializer(UserAlertX)
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
                "webNotification": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Send Webpage Notification"
                ),
                "appRiseNotification": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Send AppRise Notification"
                ),
                "appRiseURLs": openapi.Schema(type=openapi.TYPE_STRING, description="appRiseURLs"),
            },
        ),
    )
    def put(self, request, UUID, format=None):
        user:UserProfile = request.user.userProfile
        UserAlertX:UserAlert = self.get_object(UUID)
        if not UserAlertX.user == user:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        data = request.data
        if "user" in data:
            del data["user"]

        serializer = UserAlertSerializer(UserAlertX, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["UserAlert"])
    def delete(self, request, UUID, format=None):
        user:UserProfile = request.user.userProfile
        UserAlertX:UserAlert = self.get_object(UUID)
        if not UserAlertX.user == user:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        UserAlertX.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class UserProfileList(APIView, PaginationMixin):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsSAOrUser]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["UserProfile"])
    def get(self, request, format=None):
        user = request.user.userProfile
        if user.siteAdmin:
            userProfile = UserProfile.objects.all()
        else:
            userProfile = UserProfile.objects.filter(UUID=user.UUID)

        page = self.paginate_queryset(userProfile)
        if page is not None:
            serializer = UserProfileSerializer(page, many=True)
            return Response(serializer.data)


class UserProfileView(APIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, UUID):
        try:
            return UserProfile.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["UserProfile"])
    def get(self, request, UUID, format=None):
        user = request.user.userProfile
        if user.siteAdmin or user.UUID == UUID:
            userProfile = self.get_object(UUID)
        else:
            return Response(status=401)
        serializer = UserProfileSerializer(userProfile)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["UserProfile"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "siteTheme": openapi.Schema(
                    type=openapi.TYPE_STRING, description="siteTheme"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="description"
                ),
                "siteAdmin": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Is user authorized to make changes",
                ),
            },
        ),
    )
    def put(self, request, UUID, format=None):
        user = request.user.userProfile
        if user.siteAdmin or user.UUID == UUID:
            userProfile = self.get_object(UUID)
        else:
            return Response(status=401)
        serializer = UserProfileSerializer(userProfile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["UserProfile"])
    def delete(self, request, UUID, format=None):
        user = request.user.userProfile
        if user.siteAdmin or user.UUID == UUID:
            userProfile = self.get_object(UUID)
        else:
            return Response(status=401)
        userProfile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemACLList(APIView, PaginationMixin):
    queryset = SystemACL.objects.all()
    serializer_class = SystemACLSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["SystemACL"])
    def get(self, request, format=None):
        SystemACLs = SystemACL.objects.all()
        page = self.paginate_queryset(SystemACLs)
        if page is not None:
            serializer = SystemACLSerializer(page, many=True)
            return Response(serializer.data)


class SystemACLCreate(APIView):
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
    def post(self, request, format=None):
        data = JSONParser().parse(request)
        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()
        serializer = SystemACLSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemACLView(APIView):
    queryset = SystemACL.objects.all()
    serializer_class = SystemACLSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, UUID):
        try:
            return SystemACL.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["SystemACL"])
    def get(self, request, UUID, format=None):
        SystemACL = self.get_object(UUID)
        serializer = SystemACLSerializer(SystemACL)
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
    def put(self, request, UUID, format=None):
        SystemACL = self.get_object(UUID)
        serializer = SystemACLSerializer(SystemACL, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["SystemACL"])
    def delete(self, request, UUID, format=None):
        SystemACL = self.get_object(UUID)
        SystemACL.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemList(APIView, PaginationMixin):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["System"])
    def get(self, request, format=None):
        user: UserProfile = request.user.userProfile
        if user.siteAdmin:
            Systems = System.objects.all()
        else:
            userACLs = []
            ACLs = SystemACL.objects.all()
            for ACL in ACLs:
                ACL: SystemACL
                if ACL.users.filter(UUID=user.UUID):
                    userACLs.append(ACL)
                elif ACL.public:
                    userACLs.append(ACL)
            Systems = System.objects.filter(systemACL__in=userACLs)

        page = self.paginate_queryset(Systems)
        if page is not None:
            serializer = SystemSerializer(page, many=True)
            return Response(serializer.data)


class SystemCreate(APIView):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["System"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "systemACL"],
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System Name"
                ),
                "systemACL": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System ACL UUID"
                ),
                "enableTalkGroupACLs": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Enable Talkgroup ACLs on system",
                ),
                "pruneTransmissions": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Enable Pruneing Transmissions on system",
                ),
                "pruneTransmissionsAfterDays": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Days to keep Transmissions (Prune)"
                ),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = SystemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemView(APIView):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, UUID):
        try:
            return System.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    def get_ACL(self, UUID):
        try:
            return SystemACL.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["System"])
    def get(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        userACLs = []
        ACLs = SystemACL.objects.all()
        for ACL in ACLs:
            ACL: SystemACL
            if ACL.users.filter(UUID=user.UUID):
                userACLs.append(ACL)
            elif ACL.public:
                userACLs.append(ACL)

        system: System = self.get_object(UUID)

        if user.siteAdmin:
            serializer = SystemSerializer(system)
            return Response(serializer.data)

        if system.systemACL.UUID in userACLs:
            serializer = SystemSerializer(system)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        tags=["System"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="string"),
                "systemACL": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System ACL UUID"
                ),
                "enableTalkGroupACLs": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Enable Talkgroup ACLs on system",
                ),
                "pruneTransmissions": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Enable Pruneing Transmissions on system",
                ),
                "pruneTransmissionsAfterDays": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Days to keep Transmissions (Prune)"
                ),
            },
        ),
    )
    def put(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        data = JSONParser().parse(request)
        System = self.get_object(UUID)
        serializer = SystemSerializer(System, data=data, partial=True)
        if user.siteAdmin:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["System"])
    def delete(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        System = self.get_object(UUID)
        if user.siteAdmin:
            System.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class SystemRRImportView(APIView):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["System"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["siteid", "username", "password"],
            properties={
                "siteid": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Radio Refrence Site ID"
                ),
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Radio Refrence Username"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Radio Refrence password",
                ),
            },
        ),
    )
    def post(self, request, UUID, format=None):
        data = JSONParser().parse(request)

        import_radio_refrence.delay(
            UUID, data["siteid"], data["username"], data["password"]
        )

        return Response({"message": "System Import from Radio Refrence Qued"})


class SystemForwarderList(APIView, PaginationMixin):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(
        tags=["SystemForwarder"],
    )
    def get(self, request, format=None):
        SystemForwarders = SystemForwarder.objects.all()

        page = self.paginate_queryset(SystemForwarders)
        if page is not None:
            serializer = SystemForwarderSerializer(page, many=True)
            return Response(serializer.data)


class SystemForwarderCreate(APIView):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["SystemForwarder"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "name",
                "enabled",
                "recorderKey",
                "remoteURL",
                "forwardedSystems",
            ],
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Forwarder Name"
                ),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="enabled"
                ),
                "recorderKey": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Forwarder Key"
                ),
                "remoteURL": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Remote URL of the TP-NG to forward to",
                ),
                "forwardIncidents": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Forward Incidents"
                ),
                "forwardedSystems": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="System UUIDs",
                ),
                "talkGroupFilter": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Filtered TG UUIDs",
                ),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = SystemForwarderSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemForwarderView(APIView):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, UUID):
        try:
            return SystemForwarder.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["SystemForwarder"])
    def get(self, request, UUID, format=None):
        SystemForwarder = self.get_object(UUID)
        serializer = SystemForwarderSerializer(SystemForwarder)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["SystemForwarder"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Forwarder Name"
                ),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="enabled"
                ),
            },
        ),
    )
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)
        SystemForwarder = self.get_object(UUID)
        if "feedKey" in data:
            del data["feedKey"]
        serializer = SystemForwarderSerializer(SystemForwarder, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["SystemForwarder"])
    def delete(self, request, UUID, format=None):
        SystemForwarder = self.get_object(UUID)
        SystemForwarder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CityList(APIView, PaginationMixin):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["City"])
    def get(self, request, format=None):
        Citys = City.objects.all()
        page = self.paginate_queryset(Citys)
        if page is not None:
            serializer = CitySerializer(page, many=True)
            return Response(serializer.data)


class CityCreate(APIView):
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
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = CitySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CityView(APIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, UUID):
        try:
            return City.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["City"])
    def get(self, request, UUID, format=None):
        City = self.get_object(UUID)
        serializer = CitySerializer(City)
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
    def put(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            raise PermissionDenied
        data = JSONParser().parse(request)
        City = self.get_object(UUID)
        serializer = CitySerializer(City, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["City"])
    def delete(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            raise PermissionDenied
        City = self.get_object(UUID)
        City.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgencyList(APIView, PaginationMixin):
    queryset = Agency.objects.all()
    serializer_class = AgencyViewListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["Agency"])
    def get(self, request, format=None):
        Agencys = Agency.objects.all()
        page = self.paginate_queryset(Agencys)
        if page is not None:
            serializer = AgencyViewListSerializer(page, many=True)
            return Response(serializer.data)


class AgencyCreate(APIView):
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
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = AgencySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AgencyView(APIView):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, UUID):
        try:
            return Agency.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["Agency"])
    def get(self, request, UUID, format=None):
        Agency = self.get_object(UUID)
        serializer = AgencyViewListSerializer(Agency)
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
    def put(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            raise PermissionDenied
        data = JSONParser().parse(request)
        Agency = self.get_object(UUID)
        serializer = AgencySerializer(Agency, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["Agency"])
    def delete(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            raise PermissionDenied
        Agency = self.get_object(UUID)
        Agency.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TalkGroupList(APIView, PaginationMixin):
    queryset = TalkGroup.objects.all()
    serializer_class = TalkGroupViewListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["TalkGroup"])
    def get(self, request, format=None):
        user: UserProfile = request.user.userProfile
        if user.siteAdmin:
            AllowedTalkgroups = TalkGroup.objects.all()
        else:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)

            AllowedTalkgroups = []
            for system in systems:
                AllowedTalkgroups.extend(getUserAllowedTalkgroups(system, user.UUID))

        page = self.paginate_queryset(AllowedTalkgroups)
        if page is not None:
            serializer = TalkGroupViewListSerializer(page, many=True)
            return Response(serializer.data)


class TalkGroupCreate(APIView):
    queryset = TalkGroup.objects.all()
    serializer_class = TalkGroupSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["TalkGroup"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["system", "decimalID"],
            properties={
                "system": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System UUID"
                ),
                "decimalID": openapi.Schema(
                    type=openapi.TYPE_STRING, description="decimalID"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="decimalID"
                ),
                "alphaTag": openapi.Schema(
                    type=openapi.TYPE_STRING, description="alphaTag"
                ),
                "encrypted": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="encrypted"
                ),
                "agency": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Agency UUIDs",
                ),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = (
                uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"{str(data['system'])}+{str(data['decimalID'])}",
                ),
            )

        serializer = TalkGroupSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TalkGroupView(APIView):
    queryset = TalkGroup.objects.all()
    serializer_class = TalkGroupSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, UUID):
        try:
            return TalkGroup.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["TalkGroup"])
    def get(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        talkGroup: TalkGroup = self.get_object(UUID)
        if user.siteAdmin:
            serializer = TalkGroupViewListSerializer(talkGroup)
            return Response(serializer.data)
        else:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)

            AllowedTalkgroups = []
            for system in systems:
                AllowedTalkgroups.extend(getUserAllowedTalkgroups(system, user.UUID))

            if not talkGroup in AllowedTalkgroups:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = TalkGroupViewListSerializer(talkGroup)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["TalkGroup"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                #'system': openapi.Schema(type=openapi.TYPE_STRING, description='System UUID'),
                #'decimalID': openapi.Schema(type=openapi.TYPE_STRING, description='decimalID'),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="decimalID"
                ),
                "alphaTag": openapi.Schema(
                    type=openapi.TYPE_STRING, description="alphaTag"
                ),
                "encrypted": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="encrypted"
                ),
                "agency": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Agency UUIDs",
                ),
            },
        ),
    )
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)
        TalkGroup = self.get_object(UUID)

        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = TalkGroupSerializer(TalkGroup, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["TalkGroup"])
    def delete(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        TalkGroup = self.get_object(UUID)
        TalkGroup.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TalkGroupTransmissionList(APIView, PaginationMixin):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_object(self, UUID):
        try:
            return TalkGroup.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["Transmission"])
    def get(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        TalkGroupX: TalkGroup = self.get_object(UUID)

        Transmissions = Transmission.objects.filter(talkgroup=TalkGroupX)

        if not user.siteAdmin:
            SystemX: System = TalkGroupX.system
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            talkgroupsAllowed = getUserAllowedTalkgroups(SystemX, user.UUID)

            if not SystemX in systems:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

            if not TalkGroupX in talkgroupsAllowed:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        page = self.paginate_queryset(Transmissions)
        if page is not None:
            serializer = TransmissionSerializer(page, many=True)
            return Response(serializer.data)


class TalkGroupACLList(APIView):
    queryset = TalkGroupACL.objects.all()
    serializer_class = TalkGroupACLSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(tags=["TalkGroupACL"])
    def get(self, request, format=None):
        TalkGroupACLs = TalkGroupACL.objects.all()
        serializer = TalkGroupACLSerializer(TalkGroupACLs, many=True)
        return Response(serializer.data)


class TalkGroupACLCreate(APIView):
    queryset = TalkGroupACL.objects.all()
    serializer_class = TalkGroupACLSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["TalkGroupACL"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "users", "defaultNewUsers", "defaultNewTalkgroups"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "users": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup Allowed UUIDs",
                ),
                "defaultNewUsers": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Add New Users to ACL"
                ),
                "defaultNewTalkgroups": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Add New Talkgroups to ACL"
                ),
                "allowedTalkgroups": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup Allowed UUIDs",
                ),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = TalkGroupACLSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TalkGroupACLView(APIView):
    queryset = TalkGroupACL.objects.all()
    serializer_class = TalkGroupACLSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, UUID):
        try:
            return TalkGroupACL.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["TalkGroupACL"])
    def get(self, request, UUID, format=None):
        TalkGroupACL = self.get_object(UUID)
        serializer = TalkGroupACLSerializer(TalkGroupACL)
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
                "defaultNewUsers": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Add New Users to ACL"
                ),
                "defaultNewTalkgroups": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Add New Talkgroups to ACL"
                ),
                "allowedTalkgroups": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup Allowed UUIDs",
                ),
            },
        ),
    )
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)
        TalkGroupACL = self.get_object(UUID)
        serializer = TalkGroupACLSerializer(TalkGroupACL, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["TalkGroupACL"])
    def delete(self, request, UUID, format=None):
        TalkGroupACL = self.get_object(UUID)
        TalkGroupACL.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemRecorderList(APIView, PaginationMixin):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["SystemRecorder"])
    def get(self, request, format=None):
        SystemRecorders = SystemRecorder.objects.all()

        page = self.paginate_queryset(SystemRecorders)
        if page is not None:
            serializer = SystemRecorderSerializer(page, many=True)
            return Response(serializer.data)


class SystemRecorderCreate(APIView):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["SystemRecorder"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["system", "siteID", "name", "user"],
            properties={
                "system": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System UUID"
                ),
                "siteID": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Site ID"
                ),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Enabled"
                ),
                "user": openapi.Schema(
                    type=openapi.TYPE_STRING, description="User UUID"
                ),  # Replace me with resuestuser
                "talkgroupsAllowed": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroups Allowed UUIDs",
                ),
                "talkgroupsDenyed": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroups Allowed UUIDs",
                ),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        data["forwarderWebhookUUID"] = uuid.uuid4()

        serializer = SystemRecorderSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemRecorderView(APIView):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, UUID):
        try:
            return SystemRecorder.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["SystemRecorder"])
    def get(self, request, UUID, format=None):
        SystemRecorder = self.get_object(UUID)
        serializer = SystemRecorderSerializer(SystemRecorder)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["SystemRecorder"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                #'system': openapi.Schema(type=openapi.TYPE_STRING, description='System UUID'),
                "siteID": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Site ID"
                ),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Enabled"
                ),
                #'user': openapi.Schema(type=openapi.TYPE_STRING, description='User UUID'),
                "talkgroupsAllowed": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroups Allowed UUIDs",
                ),
                "talkgroupsDenyed": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroups Allowed UUIDs",
                ),
            },
        ),
    )
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)
        SystemRecorder = self.get_object(UUID)
        serializer = SystemRecorderSerializer(SystemRecorder, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["SystemRecorder"])
    def delete(self, request, UUID, format=None):
        SystemRecorder = self.get_object(UUID)
        SystemRecorder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UnitList(APIView, PaginationMixin):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["Unit"])
    def get(self, request, format=None):
        user: UserProfile = request.user.userProfile
        if user.siteAdmin:
            Units = Unit.objects.all()
        else:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            Units = Unit.objects.filter(system__in=systemUUIDs)

        page = self.paginate_queryset(Units)
        if page is not None:
            serializer = UnitSerializer(page, many=True)
            return Response(serializer.data)


class UnitCreate(APIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["Unit"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["system", "decimalID"],
            properties={
                "system": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System UUID"
                ),
                "decimalID": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System UUID"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = UnitSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnitView(APIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, UUID):
        try:
            return Unit.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["Unit"])
    def get(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        unit: Unit = self.get_object(UUID)
        if user.siteAdmin:
            serializer = UnitSerializer(unit)
        else:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            if not unit.system in systems:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

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
    def put(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = JSONParser().parse(request)
        Unit = self.get_object(UUID)
        serializer = UnitSerializer(Unit, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["Unit"])
    def delete(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        Unit = self.get_object(UUID)
        Unit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TransmissionUnitList(APIView):
    queryset = TransmissionUnit.objects.all()
    serializer_class = TransmissionUnitSerializer
    permission_classes = [IsSAOrReadOnly]

    @swagger_auto_schema(tags=["TransmissionUnit"])
    def get(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile

        TransmissionX: Transmission = Transmission.objects.get(UUID=UUID)
        Units = TransmissionX.units.all()

        if not user.siteAdmin:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            if TransmissionX.system in systems:
                SystemX: System = TransmissionX.system

                if not SystemX in systems:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)

                if SystemX.enableTalkGroupACLs:
                    talkgroupsAllowed = getUserAllowedTalkgroups(SystemX, user.UUID)
                    if not TransmissionX.talkgroup in talkgroupsAllowed:
                        return Response(status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = TransmissionUnitSerializer(Units, many=True)
        return Response(serializer.data)


class TransmissionUnitView(APIView):
    queryset = TransmissionUnit.objects.all()
    serializer_class = TransmissionUnitSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, UUID):
        try:
            return TransmissionUnit.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["TransmissionUnit"])
    def get(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        TransmissionUnitX: TransmissionUnit = self.get_object(UUID)

        TransmissionX: Transmission = Transmission.objects.filter(
            units__in=TransmissionUnitX
        )

        if not user.siteAdmin:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            if TransmissionX.system in systems:
                SystemX: System = TransmissionX.system
                if not SystemX in systems:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)
                if SystemX.enableTalkGroupACLs:
                    talkgroupsAllowed = getUserAllowedTalkgroups(SystemX, user.UUID)
                    if not TransmissionX.talkgroup in talkgroupsAllowed:
                        return Response(status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = TransmissionUnitSerializer(TransmissionX)
        return Response(serializer.data)

    # @swagger_auto_schema(tags=['TransmissionUnit'], request_body=openapi.Schema(
    #     type=openapi.TYPE_OBJECT,
    #     properties={
    #         'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description'),
    #     }
    # ))
    # def put(self, request, UUID, format=None):
    #     data = JSONParser().parse(request)
    #     TransmissionUnit = self.get_object(UUID)
    #     serializer = TransmissionUnitSerializer(TransmissionUnit, data=data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @swagger_auto_schema(tags=['TransmissionUnit'])
    # def delete(self, request, UUID, format=None):
    #     TransmissionUnit = self.get_object(UUID)
    #     TransmissionUnit.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class TransmissionFreqList(APIView):
    queryset = TransmissionFreq.objects.all()
    serializer_class = TransmissionFreqSerializer
    permission_classes = [IsSAOrReadOnly]

    @swagger_auto_schema(tags=["TransmissionFreq"])
    def get(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile

        TransmissionX: Transmission = Transmission.objects.get(UUID=UUID)
        Freqs = TransmissionX.frequencys.all()

        if not user.siteAdmin:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            if TransmissionX.system in systems:
                SystemX: System = TransmissionX.system
                if not SystemX in systems:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)
                if SystemX.enableTalkGroupACLs:
                    talkgroupsAllowed = getUserAllowedTalkgroups(SystemX, user.UUID)
                    if not TransmissionX.talkgroup in talkgroupsAllowed:
                        return Response(status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = TransmissionFreqSerializer(Freqs, many=True)
        return Response(serializer.data)


class TransmissionFreqView(APIView):
    queryset = TransmissionFreq.objects.all()
    serializer_class = TransmissionFreqSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, UUID):
        try:
            return TransmissionFreq.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["TransmissionFreq"])
    def get(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        TransmissionFreqX: TransmissionFreq = self.get_object(UUID)
        serializer = TransmissionFreqSerializer(TransmissionFreqX)
        return Response(serializer.data)


class TransmissionList(APIView, PaginationMixin):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["Transmission"])
    def get(self, request, format=None):
        user: UserProfile = request.user.userProfile

        if user.siteAdmin:
            AllowedTransmissions = Transmission.objects.all()
        else:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            AllowedTransmissions = []


            for system in systems:
                if system.enableTalkGroupACLs:
                    TGAllowed = getUserAllowedTalkgroups(system, user.UUID)
                    AllowedTransmissions.extend(Transmission.objects.filter(system=system, talkgroup__in=TGAllowed))
                else:
                    AllowedTransmissions.extend(Transmission.objects.filter(system=system))
                    

        AllowedTransmissions = sorted(AllowedTransmissions, key=lambda instance: instance.startTime, reverse=True)

        page = self.paginate_queryset(AllowedTransmissions)
        if page is not None:
            serializer = TransmissionSerializer(page, many=True)
            return Response(serializer.data)


class TransmissionCreate(APIView):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer
    permission_classes = [FeederFree]

    @swagger_auto_schema(
        tags=["Transmission"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["recorder", "json", "audio"],
            properties={
                #'system': openapi.Schema(type=openapi.TYPE_STRING, description='System UUID'),
                "recorder": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Recorder Key"
                ),
                "json": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Trunk-Recorder JSON"
                ),
                "audioFile": openapi.Schema(
                    type=openapi.TYPE_STRING, description="M4A Base64"
                ),
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Audio File Name"
                ),
            },
        ),
    )
    def post(self, request, format=None):
        from radio.helpers.notifications import handle_Transmission_Notification
        data = JSONParser().parse(request)

        if not SystemRecorder.objects.filter(forwarderWebhookUUID=data["recorder"]):
            return Response(
                "Not allowed to post this talkgroup",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # try:
        Callback = new_transmission_handler(data)

        if not Callback:
            return Response(
                "Not allowed to post this talkgroup",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        Callback["UUID"] = uuid.uuid4()

        recorderX: SystemRecorder = SystemRecorder.objects.get(
            forwarderWebhookUUID=Callback["recorder"]
        )
        Callback["system"] = str(recorderX.system.UUID)

        TX = TransmissionUploadSerializer(data=Callback, partial=True)

        if TX.is_valid(raise_exception=True):
            TX.save()
            handle_Transmission_Notification(TX.validated_data)
            return Response({"success": True, "UUID": Callback["UUID"]})
        else:
            Response(TX.errors)
        # except Exception as e:
        #    return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class TransmissionView(APIView):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer

    def get_object(self, UUID):
        try:
            return Transmission.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["Transmission"])
    def get(self, request, UUID, format=None):
        TransmissionX: Transmission = self.get_object(UUID)
        user: UserProfile = request.user.userProfile

        if not user.siteAdmin:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            if not TransmissionX.system in systems:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            SystemX: System = TransmissionX.system
            if SystemX.enableTalkGroupACLs:
                talkgroupsAllowed = getUserAllowedTalkgroups(SystemX, user.UUID)
                if not TransmissionX.talkgroup in talkgroupsAllowed:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = TransmissionSerializer(TransmissionX)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["Transmission"])
    def delete(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile

        if not user.siteAdmin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        Transmission = self.get_object(UUID)
        Transmission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IncidentList(APIView, PaginationMixin):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["Incident"])
    def get(self, request, format=None):
        user: UserProfile = request.user.userProfile

        if user.siteAdmin:
            Incidents = Incident.objects.all()
        else:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            Incidents = Incident.objects.filter(system__in=systems)

        page = self.paginate_queryset(Incidents)
        if page is not None:
            serializer = IncidentSerializer(page, many=True)
            return Response(serializer.data)


class IncidentCreate(APIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentCreateSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["Incident"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["system", "name", "transmission"],
            properties={
                "active": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Is the Event Active"
                ),
                "system": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System UUID"
                ),
                "transmission": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="TRANMISSIONS UUID",
                ),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "agency": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Agency UUIDs",
                ),
                "time": openapi.Schema(type=openapi.TYPE_STRING, description="Time"),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = IncidentCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IncidentForward(APIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentCreateSerializer
    permission_classes = [FeederFree]

    @swagger_auto_schema(
        tags=["Incident"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["recorder", "name", "transmission"],
            properties={
                "active": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Is the Event Active"
                ),
                "recorder": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Recorder Key"
                ),
                "transmission": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="TRANMISSIONS UUID",
                ),
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "agency": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Agency UUIDs",
                ),
                "time": openapi.Schema(type=openapi.TYPE_STRING, description="Time"),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not SystemRecorder.objects.filter(forwarderWebhookUUID=data["recorder"]):
            return Response(
                "Not allowed to post this talkgroup",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        SR: SystemRecorder = SystemRecorder.objects.get(
            forwarderWebhookUUID=data["recorder"]
        )
        data["system"] = SR.system.UUID

        del data["recorder"]

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = IncidentCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IncidentUpdate(APIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentCreateSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, UUID):
        try:
            return Incident.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(
        tags=["Incident"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "active": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Is the Event Active"
                ),
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "transmission": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="TRANMISSIONS UUID",
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "agency": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Agency UUIDs",
                ),
            },
        ),
    )
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)
        Incident = self.get_object(UUID)
        serializer = IncidentCreateSerializer(Incident, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IncidentView(APIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, UUID):
        try:
            return Incident.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["Incident"])
    def get(self, request, UUID, format=None):
        IncidentX: Incident = self.get_object(UUID)
        user: UserProfile = request.user.userProfile

        if not user.siteAdmin:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            if not IncidentX.system in systems:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = IncidentSerializer(IncidentX)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["Incident"])
    def delete(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        IncidentX: Incident = self.get_object(UUID)
        IncidentX.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScanListList(APIView, PaginationMixin):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["ScanList"])
    def get(self, request, format=None):
        user: UserProfile = request.user.userProfile
        if user.siteAdmin:
            ScanLists = ScanList.objects.all()
        else:
            ScanLists = ScanList.objects.filter(
                Q(owner=user) | Q(communityShared=True) | Q(public=True)
            )

        page = self.paginate_queryset(ScanLists)
        if page is not None:
            serializer = ScanListSerializer(page, many=True)
            return Response(serializer.data)


class ScanListPersonalList(APIView, PaginationMixin):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["ScanList"])
    def get(self, request, format=None):
        user: UserProfile = request.user.userProfile
        ScanLists = ScanList.objects.filter(owner=user)

        page = self.paginate_queryset(ScanLists)
        if page is not None:
            serializer = ScanListSerializer(page, many=True)
            return Response(serializer.data)


class ScanListUserList(APIView, PaginationMixin):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["ScanList"])
    def get(self, request, USER_UUID, format=None):
        user: UserProfile = request.user.userProfile
        userScan: UserProfile = UserProfile.objects.get(UUID=USER_UUID)
        if user.siteAdmin:
            ScanLists = ScanList.objects.filter(owner=userScan)
        else:
            ScanLists = ScanList.objects.filter(owner=userScan).filter(
                Q(public=True) | Q(communityShared=True)
            )

        page = self.paginate_queryset(ScanLists)
        if page is not None:
            serializer = ScanListSerializer(page, many=True)
            return Response(serializer.data)


class ScanListCreate(APIView):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsUser]

    @swagger_auto_schema(
        tags=["ScanList"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "public", "talkgroups"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "communityShared": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Wether it is shared or user-only",
                ),
                "talkgroups": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup UUIDs",
                ),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)
        user: UserProfile = request.user.userProfile

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        data["owner"] = user.UUID

        if not user.siteAdmin:
            data["public"] = False

        if not "public" in data:
            data["public"] = False

        serializer = ScanListSerializer(data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScanListView(APIView):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer
    permission_classes = [IsUser]

    def get_object(self, UUID):
        try:
            return ScanList.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["ScanList"])
    def get(self, request, UUID, format=None):
        ScanListX: ScanList = self.get_object(UUID)
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            if not ScanListX.owner == user:
                if not ScanListX.public and not ScanListX.communityShared:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = ScanListSerializer(ScanListX)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["ScanList"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "owner": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Owner User UUID"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "public": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Wether it is shared or user-only",
                ),
                "talkgroups": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Talkgroup UUIDs",
                ),
            },
        ),
    )
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)
        ScanListX: ScanList = self.get_object(UUID)
        serializer = ScanListSerializer(ScanListX, data=data, partial=True)

        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            if not ScanListX.owner == user:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["ScanList"])
    def delete(self, request, UUID, format=None):
        ScanListX: ScanList = self.get_object(UUID)

        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            if not ScanListX.owner == user:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        ScanListX.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScanListTransmissionList(APIView, PaginationMixin):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_object(self, UUID):
        try:
            return ScanList.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["Transmission"])
    def get(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        ScanListX: ScanList = self.get_object(UUID)

        Talkgroups = ScanListX.talkgroups.all()
        Transmissions = Transmission.objects.filter(talkgroup__in=Talkgroups)
        AllowedTransmissions = []

        if not user.siteAdmin:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            for TransmissionX in Transmissions:
                SystemX: System = TransmissionX.system
                if not SystemX in systems:
                    continue

                if SystemX.enableTalkGroupACLs:
                    talkgroupsAllowed = getUserAllowedTalkgroups(SystemX, user.UUID)
                    if TransmissionX.talkgroup in talkgroupsAllowed:
                        AllowedTransmissions.append(TransmissionX)
                else:
                    AllowedTransmissions.append(TransmissionX)
        else:
            AllowedTransmissions = Transmissions

        page = self.paginate_queryset(AllowedTransmissions)
        if page is not None:
            serializer = TransmissionSerializer(page, many=True)
            return Response(serializer.data)


class ScannerList(APIView, PaginationMixin):
    queryset = Scanner.objects.all()
    serializer_class = ScannerSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["Scanner"])
    def get(self, request, format=None):
        user: UserProfile = request.user.userProfile
        if user.siteAdmin:
            scanner = Scanner.objects.all()
        else:
            scanner = Scanner.objects.filter(
                Q(owner=user) | Q(communityShared=True) | Q(public=True)
            )

        page = self.paginate_queryset(scanner)
        if page is not None:
            serializer = ScannerSerializer(page, many=True)
            return Response(serializer.data)


class ScannerCreate(APIView):
    queryset = Scanner.objects.all()
    serializer_class = ScannerSerializer
    permission_classes = [IsUser]

    @swagger_auto_schema(
        tags=["Scanner"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "public", "scanlists"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "communityShared": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Wether it is shared or user-only",
                ),
                "scanlists": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Scanlist UUIDs",
                ),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)
        user: UserProfile = request.user.userProfile

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        data["owner"] = user.UUID

        if not user.siteAdmin:
            data["public"] = False

        if not "public" in data:
            data["public"] = False

        serializer = ScannerSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScannerView(APIView):
    queryset = Scanner.objects.all()
    serializer_class = ScannerSerializer
    permission_classes = [IsUser]

    def get_object(self, UUID):
        try:
            return Scanner.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["Scanner"])
    def get(self, request, UUID, format=None):
        ScannerX: Scanner = self.get_object(UUID)
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            if not ScannerX.owner == user:
                if not ScannerX.public and not ScannerX.communityShared:
                    return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = ScannerSerializer(Scanner)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Scanner"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "owner": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Owner User UUID"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Description"
                ),
                "public": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Wether it is shared or user-only",
                ),
                "scanlists": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Scanlist UUIDs",
                ),
            },
        ),
    )
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)
        ScannerX: Scanner = self.get_object(UUID)

        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            if not ScannerX.owner == user:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = ScannerSerializer(ScannerX, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["Scanner"])
    def delete(self, request, UUID, format=None):
        ScannerX: Scanner = self.get_object(UUID)
        user: UserProfile = request.user.userProfile

        if not user.siteAdmin:
            if not ScannerX.owner == user:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        ScannerX.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScannerTransmissionList(APIView, PaginationMixin):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_object(self, UUID):
        try:
            return Scanner.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["Transmission"])
    def get(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        ScannerX: Scanner = self.get_object(UUID)
        systemUUIDs, systems = getUserAllowedSystems(user.UUID)

        AllowedTransmissions = []
        ScanListTalkgroups = []
        Transmissions = []

        for ScanListX in ScannerX.scanlists.all():
            ScanListX: ScanList
            ScanListTalkgroups.extend(ScanListX.talkgroups.all())

        TransmissionList = Transmission.objects.filter(talkgroup__in=ScanListTalkgroups)

        for TransmissionX in TransmissionList:
            Transmissions.append(TransmissionX)

        if not user.siteAdmin:
            for TransmissionX in Transmissions:
                TransmissionX: Transmission
                if not user.siteAdmin:
                    SystemX: System = TransmissionX.system

                    if not SystemX in systems:
                        continue

                    if SystemX.enableTalkGroupACLs:
                        talkgroupsAllowed = getUserAllowedTalkgroups(SystemX, user.UUID)
                        if TransmissionX.talkgroup in talkgroupsAllowed:
                            AllowedTransmissions.append(TransmissionX)
                    else:
                        AllowedTransmissions.append(TransmissionX)
        else:
            AllowedTransmissions = Transmissions

        page = self.paginate_queryset(AllowedTransmissions)
        if page is not None:
            serializer = TransmissionSerializer(page, many=True)
            return Response(serializer.data)


class GlobalAnnouncementList(APIView, PaginationMixin):
    queryset = GlobalAnnouncement.objects.all()
    serializer_class = GlobalAnnouncementSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["GlobalAnnouncement"])
    def get(self, request, format=None):
        user: UserProfile = request.user.userProfile
        if user.siteAdmin:
            GlobalAnnouncements = GlobalAnnouncement.objects.all()
        else:
            GlobalAnnouncements = GlobalAnnouncement.objects.filter(enabled=True)

        page = self.paginate_queryset(GlobalAnnouncements)
        if page is not None:
            serializer = GlobalAnnouncementSerializer(page, many=True)
            return Response(serializer.data)


class GlobalAnnouncementCreate(APIView):
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
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = GlobalAnnouncementSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GlobalAnnouncementView(APIView):
    queryset = GlobalAnnouncement.objects.all()
    serializer_class = GlobalAnnouncementSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, UUID):
        try:
            return GlobalAnnouncement.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["GlobalAnnouncement"])
    def get(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        GlobalAnnouncementX: GlobalAnnouncement = self.get_object(UUID)
        if not user.siteAdmin:
            if not GlobalAnnouncementX.enabled:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = GlobalAnnouncementSerializer(GlobalAnnouncementX)
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
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)
        user: UserProfile = request.user.userProfile

        if user.siteAdmin:
            GlobalAnnouncementX: GlobalAnnouncement = self.get_object(UUID)
            serializer = GlobalAnnouncementSerializer(
                GlobalAnnouncementX, data=data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["GlobalAnnouncement"])
    def delete(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        GlobalAnnouncementX: GlobalAnnouncement = self.get_object(UUID)
        GlobalAnnouncementX.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GlobalEmailTemplateList(APIView, PaginationMixin):
    queryset = GlobalEmailTemplate.objects.all()
    serializer_class = GlobalEmailTemplateSerializer
    permission_classes = [IsSiteAdmin]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["GlobalEmailTemplate"])
    def get(self, request, format=None):
        GlobalEmailTemplates = GlobalEmailTemplate.objects.all()

        page = self.paginate_queryset(GlobalEmailTemplates)
        if page is not None:
            serializer = GlobalEmailTemplateSerializer(GlobalEmailTemplates, many=True)
            return Response(serializer.data)


class GlobalEmailTemplateCreate(APIView):
    queryset = GlobalEmailTemplate.objects.all()
    serializer_class = GlobalEmailTemplateSerializer
    permission_classes = [IsSiteAdmin]

    @swagger_auto_schema(
        tags=["GlobalEmailTemplate"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "type": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Email type"
                ),
                "HTML": openapi.Schema(type=openapi.TYPE_STRING, description="HTML"),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Enabled"
                ),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = GlobalEmailTemplateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GlobalEmailTemplateView(APIView):
    queryset = GlobalEmailTemplate.objects.all()
    serializer_class = GlobalEmailTemplateSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, UUID):
        try:
            return GlobalEmailTemplate.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["GlobalEmailTemplate"])
    def get(self, request, UUID, format=None):
        GlobalEmailTemplate = self.get_object(UUID)
        serializer = GlobalEmailTemplateSerializer(GlobalEmailTemplate)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["GlobalEmailTemplate"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "type": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Email type"
                ),
                "HTML": openapi.Schema(type=openapi.TYPE_STRING, description="HTML"),
                "enabled": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Enabled"
                ),
            },
        ),
    )
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)
        GlobalEmailTemplate = self.get_object(UUID)
        serializer = GlobalEmailTemplateSerializer(
            GlobalEmailTemplate, data=data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["GlobalEmailTemplate"])
    def delete(self, request, UUID, format=None):
        GlobalEmailTemplate = self.get_object(UUID)
        GlobalEmailTemplate.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemReciveRateList(APIView, PaginationMixin):
    queryset = SystemReciveRate.objects.all()
    serializer_class = SystemReciveRateSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["SystemReciveRate"])
    def get(self, request, format=None):
        SystemReciveRates = SystemReciveRate.objects.all()

        page = self.paginate_queryset(SystemReciveRates)
        if page is not None:
            serializer = SystemReciveRateSerializer(SystemReciveRates, many=True)
            return Response(serializer.data)


class SystemReciveRateCreate(APIView):
    queryset = SystemReciveRate.objects.all()
    serializer_class = SystemReciveRateCreateSerializer
    permission_classes = [FeederFree]

    @swagger_auto_schema(
        tags=["SystemReciveRate"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["time", "rate", "recorder"],
            properties={
                "time": openapi.Schema(type=openapi.TYPE_STRING, description="time"),
                "rate": openapi.Schema(
                    type=openapi.TYPE_STRING, description="System Message rate"
                ),
                "recorder": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Recorder Key"
                ),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not SystemRecorder.objects.filter(forwarderWebhookUUID=data["recorder"]):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data["UUID"] = uuid.uuid4()

        serializer = SystemReciveRateCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            dataX = serializer.data
            print(dataX)
            dataX["UUID"] = str(dataX["UUID"])
            return Response(dataX)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemReciveRateView(APIView):
    queryset = SystemReciveRate.objects.all()
    serializer_class = SystemReciveRateSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, UUID):
        try:
            return SystemReciveRate.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["SystemReciveRate"])
    def get(self, request, UUID, format=None):
        SystemReciveRateX: SystemReciveRate = self.get_object(UUID)
        serializer = SystemReciveRateSerializer(SystemReciveRateX)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["SystemReciveRate"])
    def delete(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        SystemReciveRateX: SystemReciveRate = self.get_object(UUID)
        SystemReciveRateX.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CallList(APIView, PaginationMixin):
    queryset = Call.objects.all()
    serializer_class = CallSerializer
    permission_classes = [IsSAOrReadOnly]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(tags=["Call"])
    def get(self, request, format=None):
        user: UserProfile = request.user.userProfile

        if user.siteAdmin:
            Calls = Call.objects.all()
        else:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            TalkGroups = TalkGroup.objects.filter(system__in=systems)
            Calls = Call.objects.filter(talkgroup__in=TalkGroups)

        page = self.paginate_queryset(Calls)
        if page is not None:
            serializer = CallSerializer(page, many=True, read_only=True)
            return Response(serializer.data)


class CallCreate(APIView):
    queryset = Call.objects.all()
    serializer_class = CallUpdateCreateSerializer
    permission_classes = [FeederFree]

    @swagger_auto_schema(
        tags=["Call"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "trunkRecorderID",
                "startTime",
                "endTime",
                "units",
                "emergency",
                "encrypted",
                "frequency",
                "phase2",
                "talkgroup",
                "recorder",
            ],
            properties={
                "trunkRecorderID": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Trunk Recorder ID"
                ),
                "startTime": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Start Time"
                ),
                "endTime": openapi.Schema(
                    type=openapi.TYPE_STRING, description="End Time"
                ),
                "units": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Unit Decimal IDs",
                ),
                "emergency": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Emergency Call"
                ),
                "active": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Active Call"
                ),
                "encrypted": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Encrypted Call"
                ),
                "frequency": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Frequency"
                ),
                "phase2": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Phase2"
                ),
                "talkgroup": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Talk Group DecimalID"
                ),
                "recorder": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Recorder Key"
                ),
            },
        ),
    )
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not SystemRecorder.objects.filter(forwarderWebhookUUID=data["recorder"]):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if not "UUID" in data:
            data["UUID"] = uuid.uuid4()

        serializer = CallUpdateCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CallView(APIView):
    queryset = Call.objects.all()
    serializer_class = CallSerializer
    permission_classes = [IsSiteAdmin]

    def get_object(self, UUID):
        try:
            return Call.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["Call"])
    def get(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        CallX: Call = self.get_object(UUID)

        if not user.siteAdmin:
            systemUUIDs, systems = getUserAllowedSystems(user.UUID)
            TalkGroups = TalkGroup.objects.filter(system__in=systems)
            if not CallX.talkgroup in TalkGroups:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = CallSerializer(CallX)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["Call"])
    def delete(self, request, UUID, format=None):
        user: UserProfile = request.user.userProfile
        if not user.siteAdmin:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        CallX: Call = self.get_object(UUID)
        CallX.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
