from rest_framework.views import APIView
from django.http import Http404
from rest_framework.response import Response
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from radio.models import UserProfile

from users.models import CustomUser
from users.serializers import UserSerializer
from users.permission import IsSiteAdmin, IsSAOrUser


class UserList(APIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSAOrUser]

    @swagger_auto_schema(tags=["User"])
    def get(self, request, format=None):
        user: UserProfile = request.user.userProfile
        if user.siteAdmin:
            userProfile = CustomUser.objects.all()
        else:
            userProfile = CustomUser.objects.filter(pk=request.user.pk)
        serializer = UserSerializer(userProfile, many=True)
        return Response(serializer.data)


class UserView(APIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSAOrUser]

    def get_object(self, UUID):
        try:
            return UserProfile.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["User"])
    def get(self, request, pk, format=None):
        user: UserProfile = request.user.userProfile
        if user.siteAdmin or request.user.pk == pk:
            userProfile = self.get_object(pk)
        else:
            return Response(status=401)
        serializer = UserSerializer(userProfile)
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
    def put(self, request, pk, format=None):
        user = request.user.userProfile
        if user.siteAdmin or request.user.pk == pk:
            userProfile = self.get_object(pk)
        else:
            return Response(status=401)
        serializer = UserSerializer(userProfile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["UserProfile"])
    def delete(self, request, pk, format=None):
        user = request.user.userProfile
        if user.siteAdmin or request.user.pk == pk:
            userProfile = self.get_object(pk)
        else:
            return Response(status=401)
        userProfile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
