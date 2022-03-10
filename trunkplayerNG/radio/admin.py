from django.contrib import admin

from radio.models import (
    UserProfile,
    SystemACL,
    System,
    City,
    Agency,
    TalkGroup,
    SystemForwarder,
    SystemRecorder,
    Unit,
    TransmissionUnit,
    TransmissionFreq,
    Transmission,
    Incident,
    TalkGroupACL,
    ScanList,
    Scanner,
    GlobalAnnouncement,
    GlobalEmailTemplate,
    UserAlert
)

# pylint: disable=unused-argument
@admin.action(description="Lock selected Transmissions")
def lock_transmssions(modeladmin, request, queryset):
    """
    Bulk Locks a TX from pruning
    """
    queryset.update(locked=True)

# pylint: disable=unused-argument
@admin.action(description="Unlock selected Transmissions")
def unlock_transmssions(modeladmin, request, queryset):
    """
    Bulk un-Locks a TX from pruning
    """
    queryset.update(locked=False)


class UserAlertAdmin(admin.ModelAdmin):
    ordering = ("-user",)
    list_display = ("name", "user", "web_notification", "app_rise_notification")
    list_filter = ("web_notification", "app_rise_notification")


class UserProfileAdmin(admin.ModelAdmin):
    list_filter = ("site_admin",)


class SystemACLAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "public",
    )
    list_filter = ("public",)


class SystemAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "systemACL",
        "enable_talkgroup_acls",
        "prune_transmissions",
        "prune_transmissions_after_days",
    )
    list_filter = (
        "systemACL",
        "enable_talkgroup_acls",
        "prune_transmissions",
        "prune_transmissions_after_days",
    )


class SystemForwarderAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = ("name", "enabled", "forward_incidents", "remote_url", "recorder_key")
    list_filter = ("enabled", "forward_incidents")


class CityAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "description",
    )


class AgencyAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "description",
    )


class TalkgroupAdmin(admin.ModelAdmin):
    ordering = ("-decimal_id",)
    list_display = (
        "decimal_id",
        "alpha_tag",
        "encrypted",
        "mode",
        "system",
        "description",
    )
    list_filter = ("system", "mode", "encrypted")
    search_fields = ("UUID", "alpha_tag", "decimal_id")


class SystemRecorderAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "system",
        "site_id",
        "enabled",
        "user",
    )
    list_filter = (
        "system",
        "enabled",
    )


class UnitAdmin(admin.ModelAdmin):
    ordering = ("-decimal_id",)
    list_display = (
        "decimal_id",
        "system",
        "description",
    )
    list_filter = ("system",)
    search_fields = ("decimal_id", "system", "description")


class TransmissionUnitAdmin(admin.ModelAdmin):
    ordering = ("-time",)
    list_display = (
        "UUID",
        "unit",
        "emergency",
        "tag",
        "length",
        "pos",
        "signal_system",
    )
    list_filter = ("emergency",)
    search_fields = ("UUID",)


class TransmissionFreqAdmin(admin.ModelAdmin):
    ordering = ("-time",)
    list_display = (
        "UUID",
        "time",
        "freq",
        "len",
        "pos",
        "error_count",
        "spike_count",
    )
    search_fields = ("UUID",)


class TransmissionAdmin(admin.ModelAdmin):
    ordering = ("-start_time",)
    autocomplete_fields = ("units", "frequencys")
    list_display = (
        "UUID",
        "system",
        "recorder",
        "start_time",
        "talkgroup",
        "locked",
        "length",
        "encrypted",
        "emergency",
        "length",
        "frequency",
    )
    list_filter = ("system", "recorder", "emergency", "locked")
    search_fields = ("UUID", "talkgroup", "frequency")
    actions = [lock_transmssions, unlock_transmssions]


class IncidentAdmin(admin.ModelAdmin):
    ordering = ("-time",)
    autocomplete_fields = ("transmission",)
    list_display = ("name", "time", "system", "description")
    list_filter = ("system",)


class TalkgroupACLAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    # autocomplete_fields = ("transmission",)
    list_display = (
        "name",
        "default_new_users",
        "default_new_users",
    )
    list_filter = (
        "default_new_users",
        "default_new_users",
    )


class ScanlistAdmin(admin.ModelAdmin):
    # ordering = ("-owner",)
    # autocomplete_fields = ("transmission",)
    list_display = ("UUID", "name", "owner", "public", "community_shared")
    list_filter = (
        "public",
        "community_shared",
    )


class ScannerAdmin(admin.ModelAdmin):
    # ordering = ("-owner",)
    # autocomplete_fields = ("transmission",)
    list_display = ("UUID", "name", "owner", "public", "community_shared")
    list_filter = (
        "public",
        "community_shared",
    )


class GlobalAnnouncementAdmin(admin.ModelAdmin):
    # ordering = ("-owner",)
    # autocomplete_fields = ("transmission",)
    list_display = ("name", "enabled", "description")
    list_filter = ("enabled",)


class GlobalEmailTemplateAdmin(admin.ModelAdmin):
    # ordering = ("-owner",)
    # autocomplete_fields = ("transmission",)
    list_display = (
        "name",
        "template_type",
        "enabled",
    )
    list_filter = ("enabled",)


# class SystemReciveRateAdmin(admin.ModelAdmin):
#     ordering = ("-time",)
#     # autocomplete_fields = ("transmission",)
#     list_display = (
#         "UUID",
#         "time",
#         "recorder",
#         "rate",
#     )
#     list_filter = ("recorder",)


# class CallAdmin(admin.ModelAdmin):
#     ordering = ("-start_time",)
#     # autocomplete_fields = ("transmission",)
#     list_display = (
#         "trunkRecorderID",
#         "talkgroup",
#         "recorder",
#         "start_time",
#         "end_time",
#         "active",
#         "encrypted",
#         "emergency",
#         "frequency",
#         "phase2",
#         "emergency",
#     )
#     list_filter = ("emergency", "active", "encrypted")


admin.site.register(UserAlert, UserAlertAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(SystemACL, SystemACLAdmin)
admin.site.register(System, SystemAdmin)
admin.site.register(SystemForwarder, SystemForwarderAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Agency, AgencyAdmin)
admin.site.register(TalkGroup, TalkgroupAdmin)
admin.site.register(SystemRecorder, SystemRecorderAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(TransmissionUnit, TransmissionUnitAdmin)
admin.site.register(TransmissionFreq, TransmissionFreqAdmin)
admin.site.register(Transmission, TransmissionAdmin)
admin.site.register(Incident, IncidentAdmin)
admin.site.register(TalkGroupACL, TalkgroupACLAdmin)
admin.site.register(ScanList, ScanlistAdmin)
admin.site.register(Scanner, ScannerAdmin)
admin.site.register(GlobalAnnouncement, GlobalAnnouncementAdmin)
admin.site.register(GlobalEmailTemplate, GlobalEmailTemplateAdmin)
