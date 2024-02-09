from django.urls import path

from users import views

urlpatterns = [
    # path("list", views.UserList.as_view(), name="user_list"),
    path("", views.UserView.as_view(), name="user_view"),
]
