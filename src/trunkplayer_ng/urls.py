"""trunkplayer_ng URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import re_path, path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from users import views as user_views
from users import views as user_views
from users.views import unset_jwt_cookies

# import dj_rest_auth.jwt_auth as jwt_auth
# jwt_auth.unset_jwt_cookies = unset_jwt_cookies

schema_view = get_schema_view(
    openapi.Info(
        title="TrunkPlayer API",
        default_version="v2",
        description="",
        terms_of_service="",
        contact=openapi.Contact(email=""),
        license=openapi.License(name="AGPLv3 License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # path("", index),
    path("admin/", admin.site.urls),
    re_path(
        r"^api/v1/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("api/v1/radio/", include("radio.urls"), name="Radio"),
    # path("api/v1/users/", include("users.urls"), name="Radio"),
    path('api/v1/auth/user/', include("users.urls")),
    path(
        "api/v1/auth/token/",
        user_views.CookieTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "auth/token/",
        user_views.CookieTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "auth/token/refresh-token/",
        user_views.CookieTokenRefreshViewCustom.as_view(),
        name="token_refresh",
    ),
    path(
        "api/v1/auth/token/refresh-token/",
        user_views.CookieTokenRefreshViewCustom.as_view(),
        name="token_refresh",
    ),
    path("swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path('', include('django_prometheus.urls')),
]
