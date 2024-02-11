"""trunkplayer_ng URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
"""
from django.contrib import admin
from django.urls import re_path, path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from users import views as user_views

auth_api_patterns = [
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
]

radio_api_patterns = [
    path("api/v1/radio/", include("radio.urls"), name="Radio"),
]

mqtt_api_patterns = [
    path("api/v1/mqtt/", include("mqtt.urls"), name="MQTT"),
]

schema_view = get_schema_view(
    openapi.Info(
        title="TrunkPlayer API",
        default_version="v1",
        description="",
        terms_of_service="",
        contact=openapi.Contact(email=""),
        license=openapi.License(name="AGPLv3 License"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticatedOrReadOnly,),
)

auth_schema_view = get_schema_view(
    openapi.Info(
        title="TrunkPlayer API",
        default_version="v1",
        description="Authj API",
        terms_of_service="",
        contact=openapi.Contact(email=""),
        license=openapi.License(name="AGPLv3 License"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticatedOrReadOnly,),
    patterns=auth_api_patterns
)

radio_schema_view = get_schema_view(
    openapi.Info(
        title="TrunkPlayer API",
        default_version="v1",
        description="Radio API",
        terms_of_service="",
        contact=openapi.Contact(email=""),
        license=openapi.License(name="AGPLv3 License"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticatedOrReadOnly,),
    patterns=radio_api_patterns
)

mqtt_schema_view = get_schema_view(
    openapi.Info(
        title="TrunkPlayer API",
        default_version="v1",
        description="MQTT API",
        terms_of_service="",
        contact=openapi.Contact(email=""),
        license=openapi.License(name="AGPLv3 License"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticatedOrReadOnly,),
    patterns=mqtt_api_patterns
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Swagger Paths
    re_path(
        r"^api/v1/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^api/v1/radio/$",
        radio_schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui-radio",
    ),
    re_path(
        r"^api/v1/mqtt/$",
        radio_schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui-mqtt",
    ),
    re_path(
        r"^api/v1/auth/$",
        auth_schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui-auth",
    ),
    path("swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
] + auth_api_patterns + radio_api_patterns + mqtt_api_patterns