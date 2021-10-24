from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from radio import views

urlpatterns = [
    path('radio/users/', views.UserProfile.as_view()),
    path('radio/SystemACL/', views.SystemACL.as_view()),
    path('radio/System/', views.System.as_view()),
    path('radio/SystemForwarder/', views.SystemForwarder.as_view()),
    path('radio/City/', views.City.as_view()),
    path('radio/Agency/', views.Agency.as_view()),
    path('radio/TalkGroup/', views.TalkGroup.as_view()),
    path('radio/SystemRecorder/', views.SystemRecorder.as_view()),
    path('radio/Unit/', views.Unit.as_view()),
    path('radio/Transmission/', views.Transmission.as_view()),
    path('radio/TalkGroupACL/', views.TalkGroupACL.as_view()),
    path('radio/GlobalScanList/', views.GlobalScanList.as_view()),
    path('radio/GlobalAnnouncement/', views.GlobalAnnouncement.as_view()),
    path('radio/GlobalEmailTemplate/', views.GlobalEmailTemplate.as_view()),
    path('radio/SystemReciveRate/', views.SystemReciveRate.as_view()),
    path('radio/Call/', views.Call.as_view()),
    path('radio/SystemRecorderMetrics/', views.SystemRecorderMetrics.as_view()),
    
]

urlpatterns = format_suffix_patterns(urlpatterns)