import django_filters

from django.db import models

from django_filters import rest_framework as filters, IsoDateTimeFromToRangeFilter

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

class UserAlertFilter(filters.FilterSet):
    class Meta:
        model = UserAlert
        fields = [
            "UUID",
            "name",
            "user",
            "enabled",
            "description",
            "web_notification",
            "app_rise_notification",
            "app_rise_urls",
            "emergency_only",
        ]

class UserProfileFilter(filters.FilterSet):
    class Meta:
        model = UserProfile
        fields = ["UUID", "site_admin", "description", "site_theme"]

class SystemACLFilter(filters.FilterSet):
    class Meta:
        model = SystemACL
        fields = ["UUID", "name", "users", "public"]

class SystemFilter(filters.FilterSet):
    prune_transmissions_after_days = django_filters.NumberFilter()
    prune_transmissions_after_days__gt = django_filters.NumberFilter(field_name='prune_transmissions_after_days', lookup_expr='gt')
    prune_transmissions_after_days__lt = django_filters.NumberFilter(field_name='prune_transmissions_after_days', lookup_expr='lt')

    class Meta:
        model = System
        fields =  [
            "UUID",
            "name",
            "systemACL",
            "enable_talkgroup_acls",
            "prune_transmissions",
            "prune_transmissions_after_days",
        ]

class SystemForwarderFilter(filters.FilterSet):
    talkgroup_filter__alpha_tag = django_filters.CharFilter(lookup_expr='icontains')
    forwarded_systems__name = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = SystemForwarder
        fields = [
            "UUID",
            "name",
            "enabled",
            "recorder_key",
            "remote_url",
            "forward_incidents",
            "forwarded_systems",
            "talkgroup_filter",
        ]

class CityFilter(filters.FilterSet):
    class Meta:
        model = City
        fields = ["UUID", "name", "description"]

class AgencyFilter(filters.FilterSet):
    city__name = django_filters.CharFilter(lookup_expr='icontains')
    city__description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Agency
        fields = ["UUID", "name", "description", "city"]

class TalkGroupFilter(filters.FilterSet):
    system__name = django_filters.CharFilter(lookup_expr='icontains')
    agency__name = django_filters.CharFilter(lookup_expr='icontains')
    agency__description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = TalkGroup
        fields = [
            "UUID",
            "system",
            "decimal_id",
            "alpha_tag",
            "description",
            "encrypted",
            "agency",
        ]

class TalkGroupACLFilter(filters.FilterSet):
    allowed_talkgroups__decimal_id = django_filters.CharFilter(field_name='allowed_talkgroups__decimal_id', lookup_expr='exact')
    allowed_talkgroups__alpha_tag = django_filters.CharFilter(field_name='allowed_talkgroups__alpha_tag', lookup_expr='icontains')
    allowed_talkgroups__agency__name = django_filters.CharFilter(field_name='allowed_talkgroups__agency__name', lookup_expr='icontains')

    class Meta:
        model = TalkGroupACL
        fields = [
            "UUID",
            "name",
            "users",
            "allowed_talkgroups",
            "default_new_talkgroups",
            "default_new_users",
            "download_allowed",
        ]

class SystemRecorderFilter(filters.FilterSet):
    system__name = django_filters.CharFilter(lookup_expr='icontains')

    talkgroups_allowed__decimal_id = django_filters.CharFilter(field_name='talkgroups_allowed__decimal_id', lookup_expr='exact')
    talkgroups_allowed__alpha_tag = django_filters.CharFilter(field_name='talkgroups_allowed__alpha_tag', lookup_expr='icontains')
    talkgroups_allowed__agency__name = django_filters.CharFilter(field_name='talkgroups_allowed__agency__name', lookup_expr='icontains')

    talkgroups_denyed__decimal_id = django_filters.CharFilter(field_name='talkgroups_denyed__decimal_id', lookup_expr='exact')
    talkgroups_denyed__alpha_tag = django_filters.CharFilter(field_name='talkgroups_denyed__alpha_tag', lookup_expr='icontains')
    talkgroups_denyed__agency__name = django_filters.CharFilter(field_name='talkgroups_denyed__agency__name', lookup_expr='icontains')

    class Meta:
        model = SystemRecorder
        fields = [
            "UUID",
            "system",
            "name",
            "site_id",
            "enabled",
            "user",
            "talkgroups_allowed",
            "talkgroups_denyed",
            "api_key",
        ]

class UnitFilter(filters.FilterSet):
    system__name = django_filters.CharFilter(lookup_expr='icontains')

    decimal_id = django_filters.NumberFilter()
    decimal_id__gt = django_filters.NumberFilter(field_name='decimal_id', lookup_expr='gt')
    decimal_id__lt = django_filters.NumberFilter(field_name='decimal_id', lookup_expr='lt')


    class Meta:
        model = Unit
        fields = ["UUID", "system", "decimal_id", "description"]

class TransmissionUnitFilter(filters.FilterSet):
    time = IsoDateTimeFromToRangeFilter()

    units__decimal_id = django_filters.CharFilter(field_name='unit__decimal_id', lookup_expr='icontains')
    units__description = django_filters.CharFilter(field_name='unit__description', lookup_expr='icontains')

    length = django_filters.NumberFilter()
    length__gt = django_filters.NumberFilter(field_name='length', lookup_expr='gt')
    length__lt = django_filters.NumberFilter(field_name='length', lookup_expr='lt')

    pos = django_filters.NumberFilter()
    pos__gt = django_filters.NumberFilter(field_name='pos', lookup_expr='gt')
    pos__lt = django_filters.NumberFilter(field_name='pos', lookup_expr='lt')

    class Meta:
        model = TransmissionUnit
        fields = [
            "UUID",
            "time",
            "unit",
            "pos",
            "emergency",
            "signal_system",
            "tag",
            "length",
        ]

class TransmissionFreqFilter(filters.FilterSet):
    time = IsoDateTimeFromToRangeFilter()

    len = django_filters.NumberFilter()
    len__gt = django_filters.NumberFilter(field_name='len', lookup_expr='gt')
    len__lt = django_filters.NumberFilter(field_name='len', lookup_expr='lt')

    pos = django_filters.NumberFilter()
    pos__gt = django_filters.NumberFilter(field_name='pos', lookup_expr='gt')
    pos__lt = django_filters.NumberFilter(field_name='pos', lookup_expr='lt')

    freq = django_filters.NumberFilter()
    freq__gt = django_filters.NumberFilter(field_name='freq', lookup_expr='gt')
    freq__lt = django_filters.NumberFilter(field_name='freq', lookup_expr='lt')

    error_count = django_filters.NumberFilter()
    error_count__gt = django_filters.NumberFilter(field_name='error_count', lookup_expr='gt')
    error_count__lt = django_filters.NumberFilter(field_name='error_count', lookup_expr='lt')

    spike_count = django_filters.NumberFilter()
    spike_count__gt = django_filters.NumberFilter(field_name='spike_count', lookup_expr='gt')
    spike_count__lt = django_filters.NumberFilter(field_name='spike_count', lookup_expr='lt')


    class Meta:
        model = TransmissionFreq
        fields = ["UUID", "time", "freq", "pos", "len", "error_count", "spike_count"]

class IncidentFilter(filters.FilterSet):
    time = IsoDateTimeFromToRangeFilter()
    system__name = django_filters.CharFilter(lookup_expr='icontains')
    agency__name = django_filters.CharFilter(field_name='agency__name', lookup_expr='contains')

    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Incident
        fields = [
            "UUID",
            "system",
            "transmission",
            "name",
            "active",
            "description",
            "agency",
            "time",
        ]

class ScanListFilter(filters.FilterSet):
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    talkgroups__alpha_tag = django_filters.CharFilter(field_name='talkgroups__alpha_tag', lookup_expr='icontains')
    talkgroups__decimal_id = django_filters.CharFilter(field_name='talkgroups__decimal_id', lookup_expr='exact')
    talkgroups__agency__name = django_filters.CharFilter(field_name='talkgroups__agency__name', lookup_expr='icontains')


    class Meta:
        model = ScanList
        fields = [
            "UUID",
            "owner",
            "name",
            "description",
            "public",
            "community_shared",
            "talkgroups",
        ]

class ScannerFilter(filters.FilterSet):
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    talkgroups__alpha_tag = django_filters.CharFilter(field_name='talkgroups__alpha_tag', lookup_expr='icontains')
    talkgroups__decimal_id = django_filters.CharFilter(field_name='talkgroups__decimal_id', lookup_expr='exact')
    talkgroups__agency__name = django_filters.CharFilter(field_name='talkgroups__agency__name', lookup_expr='icontains')


    class Meta:
        model = ScanList
        fields = [
            "UUID",
            "owner",
            "name",
            "description",
            "public",
            "community_shared",
            "talkgroups",
        ]


class TransmissionFilter(filters.FilterSet):
    start_time = IsoDateTimeFromToRangeFilter()
    end_time = IsoDateTimeFromToRangeFilter()

    system__name = django_filters.CharFilter(lookup_expr='icontains')
    recorder__name = django_filters.CharFilter(lookup_expr='icontains')
    units__decimal_id = django_filters.CharFilter(field_name='units__unit__decimal_id', lookup_expr='icontains')
    units__description = django_filters.CharFilter(field_name='units__unit__description', lookup_expr='icontains')
    frequencys__freq = django_filters.CharFilter(lookup_expr='icontains')

    talkgroup__alpha_tag = django_filters.CharFilter(field_name='talkgroup__alpha_tag', lookup_expr='contains')
    talkgroup__decimal_id = django_filters.CharFilter(field_name='talkgroup__decimal_id', lookup_expr='exact')
    talkgroup__agency__name = django_filters.CharFilter(field_name='talkgroup__agency__name', lookup_expr='contains')

    frequency = django_filters.NumberFilter()
    frequency__gt = django_filters.NumberFilter(field_name='frequency', lookup_expr='gt')
    frequency__lt = django_filters.NumberFilter(field_name='frequency', lookup_expr='lt')

    length = django_filters.NumberFilter()
    length__gt = django_filters.NumberFilter(field_name='length', lookup_expr='gt')
    length__lt = django_filters.NumberFilter(field_name='length', lookup_expr='lt')


    class Meta:
        model = Transmission
        fields = [
            "UUID",
            "system",
            "recorder",
            "start_time",
            "end_time",
            "talkgroup",
            "encrypted",
            "units",
            "frequency",
            "frequencys",
            "length",
            "locked",
            "transcript",
        ]
