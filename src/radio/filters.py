import django_filters

from django_filters import rest_framework as filters, IsoDateTimeFromToRangeFilter
from django_filters.filters import OrderingFilter


from radio.models import (
    UserInbox,
    UserMessage,
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

class UserAlertFilter(filters.FilterSet):
    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
        )
    )

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
            "count",
            "trigger_time"
        ]


class UserProfileFilter(filters.FilterSet):
    class Meta:
        model = UserProfile
        fields = ["UUID", "site_admin", "description", "site_theme"]

class UserInboxFilter(filters.FilterSet):
    class Meta:
        model = UserInbox
        fields = [
            "UUID",
            "user",
            "messages"
        ]

class UserMessageFilter(filters.FilterSet):
    class Meta:
        model = UserMessage
        fields = [
            "UUID",
            "urgent",
            "read",
            "time",
            "title",
            "body",
            "source"
        ]



class SystemACLFilter(filters.FilterSet):
    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
        )
    )

    class Meta:
        model = SystemACL
        fields = ["UUID", "name", "users", "public"]

class SystemFilter(filters.FilterSet):
    prune_transmissions_after_days = django_filters.NumberFilter()
    prune_transmissions_after_days__gt = django_filters.NumberFilter(field_name='prune_transmissions_after_days', lookup_expr='gt')
    prune_transmissions_after_days__lt = django_filters.NumberFilter(field_name='prune_transmissions_after_days', lookup_expr='lt')

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
            ('rr_system_id', 'rr_system_id')
        )
    )

    class Meta:
        model = System
        fields =  [
            "UUID",
            "name",
            "systemACL",
            "rr_system_id",
            "enable_talkgroup_acls",
            "prune_transmissions",
            "prune_transmissions_after_days",
        ]

class SystemForwarderFilter(filters.FilterSet):
    talkgroup_filter__alpha_tag = django_filters.CharFilter(lookup_expr='icontains')
    forwarded_systems__name = django_filters.CharFilter(lookup_expr='icontains')

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
        )
    )


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
    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
            ('description', 'description'),
        )
    )

    class Meta:
        model = City
        fields = ["UUID", "name", "description"]

class AgencyFilter(filters.FilterSet):
    city__name = django_filters.CharFilter(lookup_expr='icontains')
    city__description = django_filters.CharFilter(lookup_expr='icontains')

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
            ('description', 'description'),
        )
    )


    class Meta:
        model = Agency
        fields = ["UUID", "name", "description", "city"]

class TalkGroupFilter(filters.FilterSet):
    system__UUID = django_filters.CharFilter(lookup_expr='icontains')
    system__name = django_filters.CharFilter(lookup_expr='icontains')
    agency__name = django_filters.CharFilter(lookup_expr='icontains')
    agency__description = django_filters.CharFilter(lookup_expr='icontains')

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('decimal_id', 'decimal_id'),
            ('alpha_tag', 'alpha_tag'),
            ('description', 'description'),
        )
    )

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

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
        )
    )


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
            "transcript_allowed",
        ]

class SystemRecorderFilter(filters.FilterSet):
    system__name = django_filters.CharFilter(lookup_expr='icontains')

    talkgroups_allowed__decimal_id = django_filters.CharFilter(field_name='talkgroups_allowed__decimal_id', lookup_expr='exact')
    talkgroups_allowed__alpha_tag = django_filters.CharFilter(field_name='talkgroups_allowed__alpha_tag', lookup_expr='icontains')
    talkgroups_allowed__agency__name = django_filters.CharFilter(field_name='talkgroups_allowed__agency__name', lookup_expr='icontains')

    talkgroups_denyed__decimal_id = django_filters.CharFilter(field_name='talkgroups_denyed__decimal_id', lookup_expr='exact')
    talkgroups_denyed__alpha_tag = django_filters.CharFilter(field_name='talkgroups_denyed__alpha_tag', lookup_expr='icontains')
    talkgroups_denyed__agency__name = django_filters.CharFilter(field_name='talkgroups_denyed__agency__name', lookup_expr='icontains')

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
        )
    )

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

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('decimal_id', 'decimal_id'),
            ('description', 'description'),
        )
    )

    class Meta:
        model = Unit
        fields = ["UUID", "system", "decimal_id", "description"]

class IncidentFilter(filters.FilterSet):
    time = IsoDateTimeFromToRangeFilter()
    system__name = django_filters.CharFilter(lookup_expr='icontains')
    agency__name = django_filters.CharFilter(field_name='agency__name', lookup_expr='contains')

    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
            ('description', 'description'),
            ('time', 'time'),
        )
    )

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

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
            ('description', 'description'),
        )
    )

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

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
            ('description', 'description'),
        )
    )

    class Meta:
        model = Scanner
        fields = [
            "UUID",
            "owner",
            "name",
            "description",
            "public",
            "community_shared",
            "scanlists",
        ]


class TransmissionFilter(filters.FilterSet):
    start_time = IsoDateTimeFromToRangeFilter()
    end_time = IsoDateTimeFromToRangeFilter()

    system__name = django_filters.CharFilter(lookup_expr='icontains')
    recorder__name = django_filters.CharFilter(lookup_expr='icontains')

    talkgroup__alpha_tag = django_filters.CharFilter(field_name='talkgroup__alpha_tag', lookup_expr='icontains')
    talkgroup__decimal_id = django_filters.CharFilter(field_name='talkgroup__decimal_id', lookup_expr='exact')
    talkgroup__agency__name = django_filters.CharFilter(field_name='talkgroup__agency__name', lookup_expr='icontains')

    frequency = django_filters.NumberFilter()
    frequency__gt = django_filters.NumberFilter(field_name='frequency', lookup_expr='gt')
    frequency__lt = django_filters.NumberFilter(field_name='frequency', lookup_expr='lt')

    length = django_filters.NumberFilter()
    length__gt = django_filters.NumberFilter(field_name='length', lookup_expr='gt')
    length__lt = django_filters.NumberFilter(field_name='length', lookup_expr='lt')

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('start_time', 'start_time'),
            ('end_time', 'end_time'),
            ('frequency', 'frequency'),
            ('length', 'length'),
        )
    )

    class Meta:
        model = Transmission
        fields = [
            "UUID",
            "system",
            "recorder",
            "audio_type",
            "start_time",
            "end_time",
            "talkgroup",
            "encrypted",
            #"units",
            "frequency",
            #"frequencys",
            "length",
            "locked",
            "transcript",
        ]

class GlobalAnnouncementFilter(filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
            ('description', 'description'),
        )
    )

    class Meta:
        model = GlobalAnnouncement
        fields = ["UUID", "name", "enabled", "description"]

class GlobalEmailTemplateFilter(filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    template_type = django_filters.CharFilter(lookup_expr='icontains')

    order_by_field = 'ordering'
    ordering = OrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('name', 'name'),
            ('template_type', 'template_type'),
        )
    )

    class Meta:
        model = GlobalEmailTemplate
        fields = ["UUID", "name", "template_type", "enabled", "HTML"]
