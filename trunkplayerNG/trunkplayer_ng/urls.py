"""trunkplayerNG URL Configuration

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
from django.conf.urls import url
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from allauth.account.views import confirm_email

from users import views as user_views

schema_view = get_schema_view(
    openapi.Info(
        title="TrunkPlayer API",
        default_version="v1",
        description="",
        terms_of_service="",
        contact=openapi.Contact(email=""),
        license=openapi.License(name="GPLv3 License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # path("", index),
    path("admin/", admin.site.urls),
    re_path(r"^api/$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui",),
    path("api/radio/", include("radio.urls"), name="Radio"),
    path("api/users/", include("users.urls"), name="Radio"),
    path("api/auth/", include("dj_rest_auth.urls")),
    path('api/auth/login/', user_views.CookieTokenObtainPairView.as_view(), name='login_obtain_pair'),
    path('api/auth/token/', user_views.CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', user_views.CookieTokenRefreshView.as_view(), name='token_refresh'),
    path("api/registration/", include("dj_rest_auth.registration.urls")),
    url(r"^account/", include("allauth.urls")),
    url(
        r"^accounts-rest/registration/account-confirm-email/(?P<key>.+)/$",
        confirm_email,
        name="account_confirm_email",
    ),
    path("swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
