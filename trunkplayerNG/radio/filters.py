import django_filters

from django.db import models

from django_filters import rest_framework as filters, IsoDateTimeFromToRangeFilter

from radio.models import System, Transmission, TalkGroup

class SystemFilter(filters.FilterSet):
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

class TalkGroupFilter(filters.FilterSet):
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

class TransmissionFilter(filters.FilterSet):
    start_time = IsoDateTimeFromToRangeFilter()
    end_time = IsoDateTimeFromToRangeFilter()
    length = IsoDateTimeFromToRangeFilter()


    talkgroup_alpha_tag = django_filters.CharFilter(field_name='talkgroup__alpha_tag', lookup_expr='contains')

    class Meta:
        model = Transmission
        fields = [
            "UUID",
            "system",
            "recorder",
            "start_time",
            "end_time",
            "talkgroup",
            "talkgroup_alpha_tag",
            "encrypted",
            "units",
            "frequency",
            "frequencys",
            "length",
            "locked",
            "transcript",
        ]