from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from users import views

urlpatterns = [
    path("list", views.UserList.as_view(), name="user_list"),
    path("<uuid:uuid>", views.UserView.as_view(), name="user_view"),
]
