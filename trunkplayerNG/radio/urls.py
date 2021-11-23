from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from radio import views

urlpatterns = [
    path("radio/users/list", views.UserProfileList.as_view(), name="users_list"),
    path("radio/users/<uuid:UUID>", views.UserProfileView.as_view(), name="users_view"),
    path("radio/systemacl/list", views.SystemACLList.as_view(), name="systemacl_list"),
    path(
        "radio/systemacl/create",
        views.SystemACLCreate.as_view(),
        name="systemacl_create",
    ),
    path(
        "radio/SystemACL/<uuid:UUID>",
        views.SystemACLView.as_view(),
        name="systemacl_view",
    ),
    path("radio/system/list", views.SystemList.as_view(), name="system_list"),
    path("radio/system/create", views.SystemCreate.as_view(), name="system_create"),
    path("radio/system/<uuid:UUID>", views.SystemView.as_view(), name="system_view"),
    path(
        "radio/systemforwarder/list",
        views.SystemForwarderList.as_view(),
        name="systemforwarder_list",
    ),
    path(
        "radio/systemforwarder/create",
        views.SystemForwarderCreate.as_view(),
        name="systemforwarder_create",
    ),
    path(
        "radio/systemforwarder/<uuid:UUID>",
        views.SystemForwarderView.as_view(),
        name="systemforwarder_view",
    ),
    path("radio/city/list", views.CityList.as_view(), name="city_list"),
    path("radio/city/create", views.CityCreate.as_view(), name="city_create"),
    path("radio/city/<uuid:UUID>", views.CityView.as_view(), name="city_view"),
    path("radio/agency/list", views.AgencyList.as_view(), name="agency_list"),
    path("radio/agency/create", views.AgencyCreate.as_view(), name="agency_create"),
    path("radio/agency/<uuid:UUID>", views.AgencyView.as_view(), name="agency_view"),
    path("radio/talkgroup/list", views.TalkGroupList.as_view(), name="talkgroup_list"),
    path(
        "radio/talkgroup/create",
        views.TalkGroupCreate.as_view(),
        name="talkgroup_create",
    ),
    path(
        "radio/talkgroup/<uuid:UUID>",
        views.TalkGroupView.as_view(),
        name="talkgroup_view",
    ),
    path(
        "radio/systemrecorder/list",
        views.SystemRecorderList.as_view(),
        name="systemrecorder_list",
    ),
    path(
        "radio/systemrecorder/create",
        views.SystemRecorderCreate.as_view(),
        name="systemrecorder_create",
    ),
    path(
        "radio/systemrecorder/<uuid:UUID>",
        views.SystemRecorderView.as_view(),
        name="systemrecorder_view",
    ),
    path("radio/unit/list", views.UnitList.as_view(), name="unit_list"),
    path("radio/unit/create", views.UnitCreate.as_view(), name="unit_create"),
    path("radio/unit/<uuid:UUID>", views.UnitView.as_view(), name="unit_view"),
    path(
        "radio/transmissionunit/list",
        views.TransmissionUnitList.as_view(),
        name="transmissionunit_list",
    ),
    path(
        "radio/transmissionunit/<uuid:UUID>",
        views.TransmissionUnitView.as_view(),
        name="transmissionunit_view",
    ),
    path(
        "radio/transmission/list",
        views.TransmissionList.as_view(),
        name="transmission_list",
    ),
    path(
        "radio/transmission/create",
        views.TransmissionCreate.as_view(),
        name="transmission_create",
    ),
    path(
        "radio/transmission/<uuid:UUID>",
        views.TransmissionView.as_view(),
        name="transmission_view",
    ),
    path("radio/incident/list", views.IncidentList.as_view(), name="incident_list"),
    path(
        "radio/incident/create", views.IncidentCreate.as_view(), name="incident_create"
    ),
    path(
        "radio/incident/<uuid:UUID>/update",
        views.IncidentUpdate.as_view(),
        name="incident_update",
    ),
    path(
        "radio/incident/<uuid:UUID>", views.IncidentView.as_view(), name="incident_view"
    ),
    path(
        "radio/talkGroupacl/list",
        views.TalkGroupACLList.as_view(),
        name="talkGroupacl_list",
    ),
    path(
        "radio/talkGroupacl/create",
        views.TalkGroupACLCreate.as_view(),
        name="talkGroupacl_create",
    ),
    path(
        "radio/talkGroupacl/<uuid:UUID>",
        views.TalkGroupACLView.as_view(),
        name="talkGroupacl_view",
    ),
    path(
        "radio/globalscanlist/list",
        views.GlobalScanListList.as_view(),
        name="globalscanlist_list",
    ),
    path(
        "radio/globalscanlist/create",
        views.GlobalScanListCreate.as_view(),
        name="globalscanlist_create",
    ),
    path(
        "radio/globalscanlist/<uuid:UUID>",
        views.GlobalScanListView.as_view(),
        name="globalscanlist_view",
    ),
    path("radio/scanlist/list", views.ScanListList.as_view(), name="scanlist_list"),
    path(
        "radio/scanlist/create", views.ScanListCreate.as_view(), name="scanlist_create"
    ),
    path(
        "radio/scanlist/<uuid:UUID>", views.ScanListView.as_view(), name="scanlist_view"
    ),
    path(
        "radio/globalannouncement/list",
        views.GlobalAnnouncementList.as_view(),
        name="globalannouncement_list",
    ),
    path(
        "radio/globalannouncement/create",
        views.GlobalAnnouncementCreate.as_view(),
        name="globalannouncement_create",
    ),
    path(
        "radio/globalannouncement/<uuid:UUID>",
        views.GlobalAnnouncementView.as_view(),
        name="globalannouncement_view",
    ),
    path(
        "radio/globalemailtemplate/list",
        views.GlobalEmailTemplateList.as_view(),
        name="globalemailtemplate_list",
    ),
    path(
        "radio/globalemailtemplate/create",
        views.GlobalEmailTemplateCreate.as_view(),
        name="globalemailtemplate_create",
    ),
    path(
        "radio/globalemailtemplate/<uuid:UUID>",
        views.GlobalEmailTemplateView.as_view(),
        name="globalemailtemplate_view",
    ),
    path(
        "radio/systemreciverate/list",
        views.SystemReciveRateList.as_view(),
        name="systemreciverate_list",
    ),
    path(
        "radio/systemreciverate/create",
        views.SystemReciveRateCreate.as_view(),
        name="systemreciverate_create",
    ),
    path(
        "radio/systemreciverate/<uuid:UUID>",
        views.SystemReciveRateView.as_view(),
        name="systemreciverate_view",
    ),
    path("radio/call/list", views.CallList.as_view(), name="call_list"),
    path("radio/call/create", views.CallCreate.as_view(), name="call_create"),
    path(
        "radio/call/<uuid:UUID>/update", views.CallUpdate.as_view(), name="call_update"
    ),
    path("radio/call/<uuid:UUID>", views.CallView.as_view(), name="call_view"),
    path(
        "radio/systemrecordermetrics/list",
        views.SystemRecorderMetricsList.as_view(),
        name="systemrecordermetrics_list",
    ),
    # path('radio/systemrecordermetrics/create', views.SystemReciveRateCreate.as_view(), name='systemrecordermetrics_create'),
    path(
        "radio/systemrecordermetrics/<uuid:UUID>",
        views.SystemRecorderMetricsView.as_view(),
        name="systemrecordermetrics_view",
    ),
]
