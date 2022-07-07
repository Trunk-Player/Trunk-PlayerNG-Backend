from django.conf import settings
from django.http import Http404
from django.core.exceptions import PermissionDenied

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


from radio.serializers import (
    UserMessageSerializer
)


from radio.permission import (
    IsSAOrReadOnly
)

from radio.models import (
    UserInbox,
    UserMessage
)


if settings.SEND_TELEMETRY:
    import sentry_sdk # pylint: disable=unused-import



class View(APIView):
    queryset = UserMessage.objects.all()
    serializer_class = UserMessageSerializer
    permission_classes = [IsSAOrReadOnly]

    def get_object(self, request_uuid):
        """
        User Message fetch function
        """
        try:
            return UserMessage.objects.get(UUID=request_uuid)
        except UserMessage.DoesNotExist:
            raise Http404 from UserMessage.DoesNotExist

    @swagger_auto_schema(tags=["UserMessage"])
    def get(self, request, request_uuid):
        """
        User Message Get EP
        """
        user = request.user.userProfile
        user_message = self.get_object(request_uuid)

        if not user.site_admin:
            user_inbox: UserInbox = UserInbox.objects.get(user=user)
            if not user_message in user_inbox.messages.all():
                raise PermissionDenied

        serializer = UserMessageSerializer(user_message)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["UserMessage"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "read": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN
                )
            },
        ),
    )
    def put(self, request, request_uuid):
        """
        UserInbox Update EP
        """
        user = request.user.userProfile
        user_message = self.get_object(request_uuid)

        if not user.site_admin:
            user_inbox: UserInbox = UserInbox.objects.get(user=user)
            if not user_message in user_inbox.messages.all():
                raise PermissionDenied

        data = request.data

        for propertyx in ["UUID", "urgent", "title", "time", "body", "source"]:
            if propertyx in data:
                del data[propertyx]


        serializer = UserMessageSerializer(user_message, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["UserMessage"])
    def delete(self, request, request_uuid):
        """
        User Message Delete EP
        """
        user = request.user.userProfile
        user_message = self.get_object(request_uuid)
        if not user.site_admin:
            user_inbox: UserInbox = UserInbox.objects.get(user=user)
            if not user_message in user_inbox.messages.all():
                raise PermissionDenied
        user_message.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
