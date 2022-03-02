from django.http import Http404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from radio.models import UserProfile
from users.models import CustomUser
from users.serializers import UserSerializer
from users.permission import IsSAOrUser


from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken

class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = None
    def validate(self, attrs):
        attrs['refresh'] = self.context['request'].COOKIES.get('refresh-token')
        if attrs['refresh']:
            return super().validate(attrs)
        else:
            raise InvalidToken('No valid token found in cookie \'refresh-token\'')

class CookieTokenObtainPairView(TokenObtainPairView):
  def finalize_response(self, request, response, *args, **kwargs):
    if response.data.get('refresh'):
        cookie_max_age = 3600 * 24 * 14 # 14 days
        response.set_cookie('TPNG-app-auth', response.data['access'], max_age=cookie_max_age, httponly=True, secure=True, samesite='None' )
        response.set_cookie('refresh-token', response.data['refresh'], max_age=cookie_max_age, httponly=True, secure=True, samesite='None' )
        del response.data['refresh']
    return super().finalize_response(request, response, *args, **kwargs)

class CookieTokenRefreshView(TokenRefreshView):
    def finalize_response(self, request, response, *args, **kwargs):
        if response.data.get('refresh'):
            cookie_max_age = 3600 * 24 * 14 # 14 days
            response.set_cookie('refresh-token', response.data['refresh'], max_age=cookie_max_age, httponly=True, secure=True, samesite=None  )
            del response.data['refresh']
        return super().finalize_response(request, response, *args, **kwargs)
    serializer_class = CookieTokenRefreshSerializer

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
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSAOrUser]

    def get_object(self, id):
        try:
            return CustomUser.objects.get(id=id)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=["User"])
    def get(self, request, id, format=None):
        user: CustomUser = request.user.userProfile
        if user.siteAdmin or request.user.id == id:
            userProfile = self.get_object(id)
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
    def put(self, request, id, format=None):
        user = request.user.userProfile
        if user.siteAdmin or request.user.id == id:
            userProfile = self.get_object(id)
        else:
            return Response(status=401)
        serializer = UserSerializer(userProfile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["UserProfile"])
    def delete(self, request, id, format=None):
        user = request.user.userProfile
        if user.siteAdmin or request.user.id == id:
            userProfile = self.get_object(id)
        else:
            return Response(status=401)
        userProfile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
