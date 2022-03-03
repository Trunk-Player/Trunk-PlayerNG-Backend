from django.urls import path
from radio import views

urlpatterns = [
    path(
        "users/alerts/list",
        views.UserAlertList.as_view(),
        name="users_alerts_list",
    ),
    path(
        "users/alerts/create",
        views.UserAlertCreate.as_view(),
        name="users_alerts_create",
    ),
    path(
        "users/alerts/<uuid:UUID>",
        views.UserAlertView.as_view(),
        name="users_alerts_view",
    ),
    path("users/list", views.UserProfileList.as_view(), name="users_list"),
    path("users/<uuid:UUID>", views.UserProfileView.as_view(), name="users_view"),
    path("systemacl/list", views.SystemACLList.as_view(), name="systemacl_list"),
    path(
        "systemacl/create",
        views.SystemACLCreate.as_view(),
        name="systemacl_create",
    ),
    path(
        "systemacl/<uuid:UUID>",
        views.SystemACLView.as_view(),
        name="systemacl_view",
    ),
    path("system/list", views.SystemList.as_view(), name="system_list"),
    path("system/create", views.SystemCreate.as_view(), name="system_create"),
    path("system/<uuid:UUID>", views.SystemView.as_view(), name="system_view"),
    path(
        "system/<uuid:UUID>/importrr",
        views.SystemRRImportView.as_view(),
        name="system_rr_import_view",
    ),
    path(
        "systemforwarder/list",
        views.SystemForwarderList.as_view(),
        name="systemforwarder_list",
    ),
    path(
        "systemforwarder/create",
        views.SystemForwarderCreate.as_view(),
        name="systemforwarder_create",
    ),
    path(
        "systemforwarder/<uuid:UUID>",
        views.SystemForwarderView.as_view(),
        name="systemforwarder_view",
    ),
    path("city/list", views.CityList.as_view(), name="city_list"),
    path("city/create", views.CityCreate.as_view(), name="city_create"),
    path("city/<uuid:UUID>", views.CityView.as_view(), name="city_view"),
    path("agency/list", views.AgencyList.as_view(), name="agency_list"),
    path("agency/create", views.AgencyCreate.as_view(), name="agency_create"),
    path("agency/<uuid:UUID>", views.AgencyView.as_view(), name="agency_view"),
    path("talkgroup/list", views.TalkGroupList.as_view(), name="talkgroup_list"),
    path(
        "talkgroup/create",
        views.TalkGroupCreate.as_view(),
        name="talkgroup_create",
    ),
    path(
        "talkgroup/<uuid:UUID>",
        views.TalkGroupView.as_view(),
        name="talkgroup_view",
    ),
    path(
        "talkgroup/<uuid:UUID>/transmissions",
        views.TalkGroupTransmissionList.as_view(),
        name="talkgroup_transmissions",
    ),
    path(
        "systemrecorder/list",
        views.SystemRecorderList.as_view(),
        name="systemrecorder_list",
    ),
    path(
        "systemrecorder/create",
        views.SystemRecorderCreate.as_view(),
        name="systemrecorder_create",
    ),
    path(
        "systemrecorder/<uuid:UUID>",
        views.SystemRecorderView.as_view(),
        name="systemrecorder_view",
    ),
    path("unit/list", views.UnitList.as_view(), name="unit_list"),
    path("unit/create", views.UnitCreate.as_view(), name="unit_create"),
    path("unit/<uuid:UUID>", views.UnitView.as_view(), name="unit_view"),
    path(
        "transmission/unit/<uuid:UUID>",
        views.TransmissionUnitView.as_view(),
        name="transmissionunit_view",
    ),
    path(
        "transmission/freq/<uuid:UUID>",
        views.TransmissionFreqView.as_view(),
        name="transmissionunit_view",
    ),
    path(
        "transmission/list",
        views.TransmissionList.as_view(),
        name="transmission_list",
    ),
    path(
        "transmission/<uuid:UUID>/units",
        views.TransmissionUnitList.as_view(),
        name="transmissionunit_list",
    ),
    path(
        "transmission/<uuid:UUID>/freqs",
        views.TransmissionFreqList.as_view(),
        name="transmissionunit_list",
    ),
    path(
        "transmission/<uuid:uuid>/download",
        views.transmission_download,
        name="transmissionunit_list",
    ),
    path(
        "transmission/create",
        views.TransmissionCreate.as_view(),
        name="transmission_create",
    ),
    path(
        "transmission/<uuid:UUID>",
        views.TransmissionView.as_view(),
        name="transmission_view",
    ),
    path("incident/list", views.IncidentList.as_view(), name="incident_list"),
    path(
        "incident/create", views.IncidentCreate.as_view(), name="incident_create"
    ),
    path(
        "incident/forward",
        views.IncidentForward.as_view(),
        name="incident_forward",
    ),
    path(
        "incident/<uuid:UUID>/update",
        views.IncidentUpdate.as_view(),
        name="incident_update",
    ),
    path(
        "incident/<uuid:UUID>", views.IncidentView.as_view(), name="incident_view"
    ),
    path(
        "talkGroupacl/list",
        views.TalkGroupACLList.as_view(),
        name="talkGroupacl_list",
    ),
    path(
        "talkGroupacl/create",
        views.TalkGroupACLCreate.as_view(),
        name="talkGroupacl_create",
    ),
    path(
        "talkGroupacl/<uuid:UUID>",
        views.TalkGroupACLView.as_view(),
        name="talkGroupacl_view",
    ),
    path("scanlist/all/list", views.ScanListList.as_view(), name="scanlist_list"),
    path(
        "scanlist/list",
        views.ScanListPersonalList.as_view(),
        name="scanlist_personal_list",
    ),
    path(
        "scanlist/user/<uuid:USER_UUID>/list",
        views.ScanListUserList.as_view(),
        name="scanlist_user_list",
    ),
    path(
        "scanlist/create", views.ScanListCreate.as_view(), name="scanlist_create"
    ),
    path(
        "scanlist/<uuid:UUID>", views.ScanListView.as_view(), name="scanlist_view"
    ),
    path(
        "scanlist/<uuid:UUID>/transmissions",
        views.ScanListTransmissionList.as_view(),
        name="scanlist_transmissions",
    ),
    path("scanner/list", views.ScannerList.as_view(), name="scanner_list"),
    path("scanner/create", views.ScannerCreate.as_view(), name="scanner_create"),
    path("scanner/<uuid:UUID>", views.ScannerView.as_view(), name="scanner_view"),
    path(
        "scanner/<uuid:UUID>/transmissions",
        views.ScannerTransmissionList.as_view(),
        name="scanner_transmissions",
    ),
    path(
        "globalannouncement/list",
        views.GlobalAnnouncementList.as_view(),
        name="globalannouncement_list",
    ),
    path(
        "globalannouncement/create",
        views.GlobalAnnouncementCreate.as_view(),
        name="globalannouncement_create",
    ),
    path(
        "globalannouncement/<uuid:UUID>",
        views.GlobalAnnouncementView.as_view(),
        name="globalannouncement_view",
    ),
    path(
        "globalemailtemplate/list",
        views.GlobalEmailTemplateList.as_view(),
        name="globalemailtemplate_list",
    ),
    path(
        "globalemailtemplate/create",
        views.GlobalEmailTemplateCreate.as_view(),
        name="globalemailtemplate_create",
    ),
    path(
        "globalemailtemplate/<uuid:UUID>",
        views.GlobalEmailTemplateView.as_view(),
        name="globalemailtemplate_view",
    ),
    # path(
    #     "systemreciverate/list",
    #     views.SystemReciveRateList.as_view(),
    #     name="systemreciverate_list",
    # ),
    # path(
    #     "systemreciverate/create",
    #     views.SystemReciveRateCreate.as_view(),
    #     name="systemreciverate_create",
    # ),
    # path(
    #     "systemreciverate/<uuid:UUID>",
    #     views.SystemReciveRateView.as_view(),
    #     name="systemreciverate_view",
    # ),
    # path("call/list", views.CallList.as_view(), name="call_list"),
    # path("call/create", views.CallCreate.as_view(), name="call_create"),
    # # path(
    # #     "call/<uuid:UUID>/update", views.CallUpdate.as_view(), name="call_update"
    # # ),
    # path("call/<uuid:UUID>", views.CallView.as_view(), name="call_view"),
]
