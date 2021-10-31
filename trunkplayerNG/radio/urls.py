from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from radio import views

urlpatterns = [
    path('radio/users/list', views.UserProfileList.as_view()),
    path('radio/users/<uuid:UUID>', views.UserProfileView.as_view()),
    path('radio/systemacl/list', views.SystemACLList.as_view()),
    path('radio/systemacl/create', views.SystemACLCreate.as_view()),
    path('radio/SystemACL/<uuid:UUID>', views.SystemACLView.as_view()),
    path('radio/system/list', views.SystemList.as_view()),
    path('radio/system/create', views.SystemCreate.as_view()),
    path('radio/system/<uuid:UUID>', views.SystemView.as_view()),
    path('radio/systemforwarder/list', views.SystemForwarderList.as_view()),
    path('radio/systemforwarder/create', views.SystemForwarderCreate.as_view()),
    path('radio/systemforwarder/<uuid:UUID>', views.SystemForwarderView.as_view()),
    path('radio/city/list', views.CityList.as_view()),
    path('radio/city/create', views.CityCreate.as_view()),
    path('radio/city/<uuid:UUID>', views.CityView.as_view()),
    path('radio/agency/list', views.AgencyList.as_view()),
    path('radio/agency/create', views.AgencyCreate.as_view()),
    path('radio/agency/<uuid:UUID>', views.AgencyView.as_view()),
    path('radio/agency/', views.AgencyView.as_view()),
    path('radio/TalkGroup/', views.TalkGroupView.as_view()),
    path('radio/SystemRecorder/', views.SystemRecorderView.as_view()),
    path('radio/Unit/', views.UnitView.as_view()),
    path('radio/TransmissionUnit/', views.TransmissionUnitView.as_view()),    
    path('radio/Transmission/', views.TransmissionView.as_view()),
    path('radio/TalkGroupACL/', views.TalkGroupACLView.as_view()),
    path('radio/GlobalScanList/', views.GlobalScanListView.as_view()),
    path('radio/ScanList/', views.ScanListView.as_view()),
    path('radio/GlobalAnnouncement/', views.GlobalAnnouncementView.as_view()),
    path('radio/GlobalEmailTemplate/', views.GlobalEmailTemplateView.as_view()),
    path('radio/SystemReciveRate/', views.SystemReciveRateView.as_view()),
    path('radio/Call/', views.CallView.as_view()),
    path('radio/SystemRecorderMetrics/', views.SystemRecorderMetricsView.as_view()),
    
]
