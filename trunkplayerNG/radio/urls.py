from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from radio import views

urlpatterns = [
    path('radio/users/', views.UserProfile.as_view()),
    path('radio/SystemACL/', views.SystemACL.as_view()),
    path('radio/System/', views.System.as_view()),
    
]

urlpatterns = format_suffix_patterns(urlpatterns)