from django.conf import settings
from django.http import Http404
from django.core.exceptions import PermissionDenied

from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework.response import Response

from django_filters import rest_framework as filters


from drf_yasg.utils import swagger_auto_schema


from radio.filters import (
    UserInboxFilter
)

from radio.serializers import (
    UserInboxSerializer
)


from radio.permission import (
    IsSAOrReadOnly,
    IsSAOrUser
)

from radio.models import (
    UserInbox
)

from radio.views.misc import (
    PaginationMixin
)

if settings.SEND_TELEMETRY:
    import sentry_sdk # pylint: disable=unused-import



class List(APIView, PaginationMixin):
    queryset = UserInbox.objects.all()
    serializer_class = UserInboxSerializer
    permission_classes = [IsSAOrUser]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UserInboxFilter

    @swagger_auto_schema(tags=["UserInbox"])
    def get(self, request):
        """
        UserInbox GET EP
        """
        user = request.user.userProfile
        if user.site_admin:
            user_profile = UserInbox.objects.all()
        else:
            user_profile = UserInbox.objects.filter(user__UUID=user.UUID)

        filtered_result = UserInboxFilter(self.request.GET, queryset=user_profile)
        page = self.paginate_queryset(filtered_result.qs)
        if page is not None:
            serializer = UserInboxSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class DirectView(APIView):
    queryset = UserInbox.objects.all()
    serializer_class = UserInboxSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        User profile fetch function
        """
        try:
            return UserInbox.objects.get(user__UUID=request_uuid)
        except UserInbox.DoesNotExist:
            raise Http404 from UserInbox.DoesNotExist

    @swagger_auto_schema(tags=["UserInbox"])
    def get(self, request, request_uuid):
        """
        UserInbox Get EP
        """
        user = request.user.userProfile
        if user.site_admin:
            user_inbox = self.get_object(request_uuid)
        elif user_inbox.user.UUID == user.UUID:
            user_inbox = self.get_object(request_uuid)
        else:
            raise PermissionDenied
        serializer = UserInboxSerializer(user_inbox)
        return Response(serializer.data)

    # @swagger_auto_schema(
    #     tags=["UserInbox"],
    #     request_body=openapi.Schema(
    #         type=openapi.TYPE_OBJECT,
    #         properties={
    #             "messages": openapi.Schema(
    #                 type=openapi.TYPE_STRING, description="The users messages"
    #             ),
    #             "user": openapi.Schema(
    #                 type=openapi.TYPE_ARRAY,
    #                 items=openapi.Items(type=openapi.TYPE_STRING),
    #                 description="The user"
    #             ),
    #         },
    #     ),
    # )
    # def put(self, request, request_uuid):
    #     """
    #     UserInbox Update EP
    #     """
    #     user = request.user.userProfile
    #     if user.site_admin:
    #         user_inbox = self.get_object(request_uuid)
    #     elif user_inbox.user.UUID == user.UUID:
    #         user_inbox = self.get_object(request_uuid)
    #     else:
    #         raise PermissionDenied
    #     serializer = UserInboxSerializer(user_inbox, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @swagger_auto_schema(tags=["UserInbox"])
    # def delete(self, request, request_uuid):
    #     """
    #     UserInbox Delete EP
    #     """
    #     user = request.user.userProfile
    #     if user.site_admin:
    #         user_inbox = self.get_object(request_uuid)
    #     elif user_inbox.user.UUID == user.UUID:
    #         user_inbox = self.get_object(request_uuid)
    #     else:
    #         raise PermissionDenied
    #     user_inbox.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class View(APIView):
    queryset = UserInbox.objects.all()
    serializer_class = UserInboxSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        User profile fetch function
        """
        try:
            return UserInbox.objects.get(UUID=request_uuid)
        except UserInbox.DoesNotExist:
            raise Http404 from UserInbox.DoesNotExist

    @swagger_auto_schema(tags=["UserInbox"])
    def get(self, request, request_uuid):
        """
        UserInbox Get EP
        """
        user = request.user.userProfile
        user_inbox = self.get_object(request_uuid)
        if not user.site_admin:
            if not user_inbox.user.UUID == user.UUID:
                raise PermissionDenied

        serializer = UserInboxSerializer(user_inbox)
        return Response(serializer.data)

    # @swagger_auto_schema(
    #     tags=["UserInbox"],
    #     request_body=openapi.Schema(
    #         type=openapi.TYPE_OBJECT,
    #         properties={
    #             "messages": openapi.Schema(
    #                 type=openapi.TYPE_STRING, description="The users messages"
    #             ),
    #             "user": openapi.Schema(
    #                 type=openapi.TYPE_ARRAY,
    #                 items=openapi.Items(type=openapi.TYPE_STRING),
    #                 description="The user"
    #             ),
    #         },
    #     ),
    # )
    # def put(self, request, request_uuid):
    #     """
    #     UserInbox Update EP
    #     """
    #     user = request.user.userProfile
    #     if user.site_admin:
    #         user_inbox = self.get_object(request_uuid)
    #     elif user_inbox.user.UUID == user.UUID:
    #         user_inbox = self.get_object(request_uuid)
    #     else:
    #         raise PermissionDenied
    #     serializer = UserInboxSerializer(user_inbox, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @swagger_auto_schema(tags=["UserInbox"])
    # def delete(self, request, request_uuid):
    #     """
    #     UserInbox Delete EP
    #     """
    #     user = request.user.userProfile
    #     if user.site_admin:
    #         user_inbox = self.get_object(request_uuid)
    #     elif user_inbox.user.UUID == user.UUID:
    #         user_inbox = self.get_object(request_uuid)
    #     else:
    #         raise PermissionDenied
    #     user_inbox.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)
