from django.contrib import admin

from radio.models import *


class UserAlertAdmin(admin.ModelAdmin):
    ordering = ("-user",)
    list_display = (
        "name",
        "user",
        "webNotification",
        "appRiseNotification"
    )
    list_filter = ("webNotification", "appRiseNotification")


class UserProfileAdmin(admin.ModelAdmin):
    list_filter = ("siteAdmin",)


class systemACLAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "public",       
    )
    list_filter = ("public",)


class systemAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "systemACL",
        "enableTalkGroupACLs",
        "pruneTransmissions",
        "pruneTransmissionsAfterDays",
    )
    list_filter = ("systemACL", "enableTalkGroupACLs", "pruneTransmissions", "pruneTransmissionsAfterDays", )


class systemForwarderAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "enabled",
        "forwardIncidents",
        "remoteURL",
        "recorderKey"
    )
    list_filter = ("enabled", "forwardIncidents")


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


class TalkGroupAdmin(admin.ModelAdmin):
    ordering = ("-decimalID",)
    list_display = (
        "decimalID",
        "alphaTag",
        "system",
        "description"

    )
    list_filter = ("system",)


class SystemRecorderAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    list_display = (
        "name",
        "system",
        "siteID",
        "enabled",
        "user",

    )
    list_filter = ("system","enabled", )


class UnitAdmin(admin.ModelAdmin):
    ordering = ("-decimalID",)
    list_display = (
        "decimalID",
        "system",
        "description",
    )
    list_filter = ("system",)


class transmissionUnitAdmin(admin.ModelAdmin):
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


class transmissionFreqAdmin(admin.ModelAdmin):
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


class transmissionAdmin(admin.ModelAdmin):
    ordering = ("-startTime",)
    list_display = (
        "UUID",
        "system",
        "recorder",
        "startTime",
        "talkgroup",
        "locked",
        "length",
        "encrypted",
        "emergency",
        "length",
        "frequency",
    )
    list_filter = ("system", "recorder", "emergency")
    search_fields= ("UUID",)


class IncidentAdmin(admin.ModelAdmin):
    ordering = ("-time",)
    autocomplete_fields = ("transmission",)
    list_display = (
        "name",
        "time",
        "system",
        "description"

    )
    list_filter = ("system",)


class TalkGroupACLAdmin(admin.ModelAdmin):
    ordering = ("-name",)
    #autocomplete_fields = ("transmission",)
    list_display = (
        "name",
        "defaultNewUsers",
        "defaultNewTalkgroups",
    )
    list_filter = ("defaultNewUsers", "defaultNewTalkgroups", )


class ScanListAdmin(admin.ModelAdmin):
    #ordering = ("-owner",)
    #autocomplete_fields = ("transmission",)
    list_display = (
        "UUID",
        "name",
        "owner",
        "public",
        "communityShared"
    )
    list_filter = ("public", "communityShared", )


class ScannerAdmin(admin.ModelAdmin):
    #ordering = ("-owner",)
    #autocomplete_fields = ("transmission",)
    list_display = (
        "UUID",
        "name",
        "owner",
        "public",
        "communityShared"
    )
    list_filter = ("public", "communityShared", )


class GlobalAnnouncementAdmin(admin.ModelAdmin):
    #ordering = ("-owner",)
    #autocomplete_fields = ("transmission",)
    list_display = (
        "name",
        "enabled",
        "description"
    )
    list_filter = ("enabled", )


class GlobalEmailTemplateAdmin(admin.ModelAdmin):
    #ordering = ("-owner",)
    #autocomplete_fields = ("transmission",)
    list_display = (
        "name",
        "type",
        "enabled",
    )
    list_filter = ("enabled", )


class SystemReciveRateAdmin(admin.ModelAdmin):
    ordering = ("-time",)
    #autocomplete_fields = ("transmission",)
    list_display = (
        "UUID",
        "time",
        "recorder",
        "rate",
    )
    list_filter = ("recorder", )


class CallAdmin(admin.ModelAdmin):
    ordering = ("-startTime",)
    #autocomplete_fields = ("transmission",)
    list_display = (
        "trunkRecorderID",
        "talkgroup",
        "recorder",
        "startTime",
        "endTime",
        "active",
        "encrypted",
        "emergency",
        "frequency",
        "phase2",
        "emergency",
    )
    list_filter = ("emergency", "active", "encrypted")

admin.site.register(UserAlert,UserAlertAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(SystemACL,systemACLAdmin)
admin.site.register(System, systemAdmin)
admin.site.register(SystemForwarder, systemForwarderAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Agency, AgencyAdmin)
admin.site.register(TalkGroup, TalkGroupAdmin)
admin.site.register(SystemRecorder, SystemRecorderAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(TransmissionUnit, transmissionUnitAdmin)
admin.site.register(TransmissionFreq, transmissionFreqAdmin)
admin.site.register(Transmission, transmissionAdmin)
admin.site.register(Incident, IncidentAdmin)
admin.site.register(TalkGroupACL, TalkGroupACLAdmin)
admin.site.register(ScanList,ScanListAdmin)
admin.site.register(Scanner, ScannerAdmin)
admin.site.register(GlobalAnnouncement, GlobalAnnouncementAdmin)
admin.site.register(GlobalEmailTemplate, GlobalEmailTemplateAdmin)
admin.site.register(SystemReciveRate, SystemReciveRateAdmin)
admin.site.register(Call, CallAdmin)
