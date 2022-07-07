from django.urls import path
from radio.views import misc
from radio.views.api import (
    user_alert,
    user_profile,
    user_inbox,
    user_message,
    system_acl,
    system,
    system_forwarder,
    city,
    agency,
    talkgroup,
    talkgroup_acl,
    system_recorder,
    unit,
    transmission,
    incident,
    scanlist,
    scanner,
    global_announcement,
    global_email_template
)

urlpatterns = [
    path(
        "users/alerts/list",
        user_alert.List.as_view(),
        name="users_alerts_list",
    ),
    path(
        "users/alerts/create",
        user_alert.Create.as_view(),
        name="users_alerts_create",
    ),
    path(
        "users/alerts/<uuid:request_uuid>",
        user_alert.View.as_view(),
        name="users_alerts_view",
    ),
    path("users/list", user_profile.List.as_view(), name="users_list"),
    path("users/<uuid:request_uuid>", user_profile.View.as_view(), name="users_view"),
    path("users/<uuid:request_uuid>/inbox", user_inbox.DirectView.as_view(), name="users_inbox_direct_view"),
    path("users/inbox/list", user_inbox.List.as_view(), name="users_inbox_list"),
    path("users/inbox/<uuid:request_uuid>", user_inbox.View.as_view(), name="users_inbox_view"),
    path("users/message/<uuid:request_uuid>", user_message.View.as_view(), name="users_message_view"),
    path("systemacl/list", system_acl.List.as_view(), name="systemacl_list"),
    path(
        "systemacl/create",
        system_acl.Create.as_view(),
        name="systemacl_create",
    ),
    path(
        "systemacl/<uuid:request_uuid>",
        system_acl.View.as_view(),
        name="systemacl_view",
    ),
    path("system/list", system.List.as_view(), name="system_list"),
    path("system/create", system.Create.as_view(), name="system_create"),
    path("system/<uuid:request_uuid>", system.View.as_view(), name="system_view"),
    path(
        "system/<uuid:request_uuid>/importrr",
        system.RRImport.as_view(),
        name="system_rr_import_view",
    ),
    path(
        "systemforwarder/list",
        system_forwarder.List.as_view(),
        name="systemforwarder_list",
    ),
    path(
        "systemforwarder/create",
        system_forwarder.Create.as_view(),
        name="systemforwarder_create",
    ),
    path(
        "systemforwarder/<uuid:request_uuid>",
        system_forwarder.View.as_view(),
        name="systemforwarder_view",
    ),
    path("city/list", city.List.as_view(), name="city_list"),
    path("city/create", city.Create.as_view(), name="city_create"),
    path("city/<uuid:request_uuid>", city.View.as_view(), name="city_view"),
    path("agency/list", agency.List.as_view(), name="agency_list"),
    path("agency/create", agency.Create.as_view(), name="agency_create"),
    path("agency/<uuid:request_uuid>", agency.View.as_view(), name="agency_view"),
    path("talkgroup/list", talkgroup.List.as_view(), name="talkgroup_list"),
    path(
        "talkgroup/create",
        talkgroup.Create.as_view(),
        name="talkgroup_create",
    ),
    path(
        "talkgroup/<uuid:request_uuid>",
        talkgroup.View.as_view(),
        name="talkgroup_view",
    ),
    path(
        "talkgroup/<uuid:request_uuid>/transmissions",
        talkgroup.TransmissionList.as_view(),
        name="talkgroup_transmissions",
    ),
    path(
        "systemrecorder/list",
        system_recorder.List.as_view(),
        name="systemrecorder_list",
    ),
    path(
        "systemrecorder/create",
        system_recorder.Create.as_view(),
        name="systemrecorder_create",
    ),
    path(
        "systemrecorder/<uuid:request_uuid>",
        system_recorder.View.as_view(),
        name="systemrecorder_view",
    ),
    path("unit/list", unit.List.as_view(), name="unit_list"),
    path("unit/create", unit.Create.as_view(), name="unit_create"),
    path("unit/<uuid:request_uuid>", unit.View.as_view(), name="unit_view"),
    path(
        "transmission/unit/<uuid:request_uuid>",
        transmission.UnitView.as_view(),
        name="transmissionunit_view",
    ),
    path(
        "transmission/freq/<uuid:request_uuid>",
        transmission.FreqView.as_view(),
        name="transmissionunit_view",
    ),
    path(
        "transmission/list",
        transmission.List.as_view(),
        name="transmission_list",
    ),
    path(
        "transmission/<uuid:request_uuid>/units",
        transmission.UnitList.as_view(),
        name="transmissionunit_list",
    ),
    path(
        "transmission/<uuid:request_uuid>/freqs",
        transmission.FreqList.as_view(),
        name="transmissionunit_list",
    ),
    path(
        "transmission/<uuid:request_uuid>/download",
        misc.transmission_download,
        name="transmissionunit_list",
    ),
    path(
        "transmission/create",
        transmission.Create.as_view(),
        name="transmission_create",
    ),
    path(
        "transmission/<uuid:request_uuid>",
        transmission.View.as_view(),
        name="transmission_view",
    ),
    path("incident/list", incident.List.as_view(), name="incident_list"),
    path("incident/create", incident.Create.as_view(), name="incident_create"),
    path(
        "incident/forward",
        incident.Forward.as_view(),
        name="incident_forward",
    ),
    path(
        "incident/<uuid:request_uuid>/update",
        incident.Update.as_view(),
        name="incident_update",
    ),
    path("incident/<uuid:request_uuid>", incident.View.as_view(), name="incident_view"),
    path(
        "talkGroupacl/list",
        talkgroup_acl.List.as_view(),
        name="talkGroupacl_list",
    ),
    path(
        "talkGroupacl/create",
        talkgroup_acl.Create.as_view(),
        name="talkGroupacl_create",
    ),
    path(
        "talkGroupacl/<uuid:request_uuid>",
        talkgroup_acl.View.as_view(),
        name="talkGroupacl_view",
    ),
    path("scanlist/all/list", scanlist.List.as_view(), name="scanlist_list"),
    path(
        "scanlist/list",
        scanlist.PersonalList.as_view(),
        name="scanlist_personal_list",
    ),
    path(
        "scanlist/user/<uuid:user_uuid>/list",
        scanlist.UserList.as_view(),
        name="scanlist_user_list",
    ),
    path("scanlist/create", scanlist.Create.as_view(), name="scanlist_create"),
    path("scanlist/<uuid:request_uuid>", scanlist.View.as_view(), name="scanlist_view"),
    path(
        "scanlist/<uuid:request_uuid>/transmissions",
        scanlist.TransmissionList.as_view(),
        name="scanlist_transmissions",
    ),
    path("scanner/list", scanner.List.as_view(), name="scanner_list"),
    path("scanner/create", scanner.Create.as_view(), name="scanner_create"),
    path("scanner/<uuid:request_uuid>", scanner.View.as_view(), name="scanner_view"),
    path(
        "scanner/<uuid:request_uuid>/transmissions",
        scanner.TransmissionList.as_view(),
        name="scanner_transmissions",
    ),
    path(
        "globalannouncement/list",
        global_announcement.List.as_view(),
        name="globalannouncement_list",
    ),
    path(
        "globalannouncement/create",
        global_announcement.Create.as_view(),
        name="globalannouncement_create",
    ),
    path(
        "globalannouncement/<uuid:request_uuid>",
        global_announcement.View.as_view(),
        name="globalannouncement_view",
    ),
    path(
        "globalemailtemplate/list",
        global_email_template.List.as_view(),
        name="globalemailtemplate_list",
    ),
    path(
        "globalemailtemplate/create",
        global_email_template.Create.as_view(),
        name="globalemailtemplate_create",
    ),
    path(
        "globalemailtemplate/<uuid:request_uuid>",
        global_email_template.View.as_view(),
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
    #     "systemreciverate/<uuid:request_uuid>",
    #     views.SystemReciveRateView.as_view(),
    #     name="systemreciverate_view",
    # ),
    # path("call/list", views.CallList.as_view(), name="call_list"),
    # path("call/create", views.CallCreate.as_view(), name="call_create"),
    # # path(
    # #     "call/<uuid:request_uuid>/update", views.CallUpdate.as_view(), name="call_update"
    # # ),
    # path("call/<uuid:request_uuid>", views.CallView.as_view(), name="call_view"),
]
