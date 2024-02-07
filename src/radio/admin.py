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

# pylint: disable=unused-argument
# @admin.action(description="Import Talkgroups from RR")
# def import_talkgroups(modeladmin, request, queryset):
#     """
#     Bulk Imports RR talkgroups
#     """
#     from radio.tasks import import_radio_refrence
#     for system in queryset:
#         system:System
#         import_radio_refrence.delay(
#             system.uuid, system.rr_system_id, data["username"], data["password"]
#         )

@admin.register(UserAlert)
class UserAlertAdmin(admin.ModelAdmin):
    ordering = ("-user",)
    list_display = ("name", "user", "web_notification", "app_rise_notification", "emergency_only", "count", "trigger_time")
    list_filter = ("web_notification", "app_rise_notification")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_filter = ("site_admin",)

@admin.register(SystemACL)
class SystemACLAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "public",
    )
    list_filter = ("public",)

@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "systemACL",
        "rr_system_id",
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

@admin.register(SystemForwarder)
class SystemForwarderAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = ("name", "enabled", "forward_incidents", "remote_url", "recorder_key")
    list_filter = ("enabled", "forward_incidents")

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "description",
    )

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "description",
    )

@admin.register(TalkGroup)
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

@admin.register(SystemRecorder)
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

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    ordering = ("-decimal_id",)
    list_display = (
        "decimal_id",
        "system",
        "description",
    )
    list_filter = ("system",)
    search_fields = ("decimal_id", "system", "description")

@admin.register(Transmission)
class TransmissionAdmin(admin.ModelAdmin):
    ordering = ("-start_time",)
    list_display = (
        "UUID",
        "system",
        "recorder",
        "audio_type",
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
    search_fields = ("UUID", "talkgroup__alpha_tag", "frequency")
    actions = [lock_transmssions, unlock_transmssions]

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    ordering = ("-time",)
    autocomplete_fields = ("transmission",)
    list_display = ("name", "time", "system", "description")
    list_filter = ("system",)

@admin.register(TalkGroupACL)
class TalkgroupACLAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    # autocomplete_fields = ("transmission",)
    list_display = (
        "name",
        "default_new_talkgroups",
        "default_new_users",
        "download_allowed",
        "transcript_allowed",
    )
    list_filter = (
        "default_new_talkgroups",
        "default_new_users",
        "download_allowed",
        "transcript_allowed",
    )

@admin.register(ScanList)
class ScanlistAdmin(admin.ModelAdmin):
    # ordering = ("-owner",)
    # autocomplete_fields = ("transmission",)
    list_display = ("UUID", "name", "owner", "public", "community_shared")
    list_filter = (
        "public",
        "community_shared",
    )

@admin.register(Scanner)
class ScannerAdmin(admin.ModelAdmin):
    # ordering = ("-owner",)
    # autocomplete_fields = ("transmission",)
    list_display = ("UUID", "name", "owner", "public", "community_shared")
    list_filter = (
        "public",
        "community_shared",
    )

@admin.register(GlobalAnnouncement)
class GlobalAnnouncementAdmin(admin.ModelAdmin):
    # ordering = ("-owner",)
    # autocomplete_fields = ("transmission",)
    list_display = ("name", "enabled", "description")
    list_filter = ("enabled",)

@admin.register(GlobalEmailTemplate)
class GlobalEmailTemplateAdmin(admin.ModelAdmin):
    # ordering = ("-owner",)
    # autocomplete_fields = ("transmission",)
    list_display = (
        "name",
        "template_type",
        "enabled",
    )
    list_filter = ("enabled",)