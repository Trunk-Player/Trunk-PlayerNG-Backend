from os import system
from typing import SupportsRound
from rest_framework import serializers
from radio.models import *
from rest_framework import permissions

class UserAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAlert
        fields = ["UUID", "name", "user", "description", "webNotification", "appRiseNotification", "appRiseURLs"]

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["UUID", "siteAdmin", "description", "siteTheme"]


class SystemACLSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemACL
        fields = ["UUID", "name", "users", "public"]


class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = ["UUID", "name", "systemACL", "enableTalkGroupACLs", "pruneTransmissions", "pruneTransmissionsAfterDays"]


class SystemForwarderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemForwarder
        fields = [
            "UUID",
            "name",
            "enabled",
            "recorderKey",
            "remoteURL",
            "forwardIncidents",
            "forwardedSystems",
            "talkGroupFilter"
        ]


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["UUID", "name", "description"]


class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = ["UUID", "name", "description", "city"]


class AgencyViewListSerializer(serializers.ModelSerializer):
    city = CitySerializer(many=True)

    class Meta:
        model = Agency
        fields = ["UUID", "name", "description", "city"]


class TalkGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalkGroup
        fields = [
            "UUID",
            "system",
            "decimalID",
            "alphaTag",
            "description",
            "encrypted",
            "agency",
        ]


class TalkGroupViewListSerializer(serializers.ModelSerializer):
    agency = AgencyViewListSerializer(read_only=True, many=True)

    class Meta:
        model = TalkGroup
        fields = [
            "UUID",
            "system",
            "decimalID",
            "alphaTag",
            "description",
            "encrypted",
            "agency",
        ]


class SystemRecorderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemRecorder
        fields = [
            "UUID",
            "system",
            "name",
            "siteID",
            "enabled",
            "user",
            "talkgroupsAllowed",
            "talkgroupsDenyed",
            "forwarderWebhookUUID",
        ]


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["UUID", "system", "decimalID", "description"]


class TransmissionUnitSerializer(serializers.ModelSerializer):
    unit = serializers.SlugRelatedField(
        read_only=False, queryset=Unit.objects.all(), slug_field="decimalID"
    )

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

    def create(self, validated_data):
        unit = validated_data.pop("unit")
        UTX, created = Unit.objects.get_or_create(decimalID=int(unit))

        return Transmission.objects.create(unit=UTX, **validated_data)


class TransmissionFreqSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransmissionFreq
        fields = ["UUID", "time", "freq", "pos", "len", "error_count", "spike_count"]


class TransmissionSerializer(serializers.ModelSerializer):
    talkgroup = TalkGroupSerializer()

    class Meta:
        model = Transmission
        fields = [
            "UUID",
            "system",
            "recorder",
            "startTime",
            "endTime",
            "audioFile",
            "talkgroup",
            "encrypted",
            "units",
            "frequency",
            "frequencys",
            "length",
            "locked",
            "transcript"
        ]


class TransmissionUploadSerializer(serializers.ModelSerializer):
    recorder = serializers.SlugRelatedField(
        read_only=False,
        queryset=SystemRecorder.objects.all(),
        slug_field="forwarderWebhookUUID",
    )

    class Meta:
        model = Transmission
        fields = [
            "UUID",
            "system",
            "recorder",
            "startTime",
            "endTime",
            "audioFile",
            "talkgroup",
            "encrypted",
            "units",
            "frequency",
            "frequencys",
            "length",
            "locked",
            "transcript"
        ]


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = [
            "UUID",
            "system",
            "transmission",
            "name",
            "description",
            "agency",
            "time",
        ]


class IncidentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = [
            "UUID",
            "active",
            "time",
            "system",
            "transmission",
            "name",
            "description",
            "agency",
        ]


class TalkGroupACLSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalkGroupACL
        fields = [
            "UUID",
            "name",
            "users",
            "allowedTalkgroups",
            "defaultNewUsers",
            "defaultNewTalkgroups",
        ]


class ScanListSerializer(serializers.ModelSerializer):
    # talkgroups = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='TalkGroupView')

    class Meta:
        model = ScanList
        fields = [
            "UUID",
            "owner",
            "name",
            "description",
            "public",
            "communityShared",
            "talkgroups",
        ]


class ScannerSerializer(serializers.ModelSerializer):
    # talkgroups = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='TalkGroupView')

    class Meta:
        model = Scanner
        fields = [
            "UUID",
            "owner",
            "name",
            "description",
            "public",
            "communityShared",
            "scanlists",
        ]


class GlobalAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalAnnouncement
        fields = ["UUID", "name", "enabled", "description"]


class GlobalEmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalEmailTemplate
        fields = ["UUID", "name", "type", "enabled", "HTML"]


class SystemReciveRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemReciveRate
        fields = ["UUID", "time", "rate", "recorder"]


class SystemReciveRateCreateSerializer(serializers.ModelSerializer):
    recorder = serializers.SlugRelatedField(
        read_only=False,
        queryset=SystemRecorder.objects.all(),
        slug_field="forwarderWebhookUUID",
    )

    class Meta:
        model = SystemReciveRate
        fields = ["UUID", "time", "rate", "recorder"]


class CallSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True)

    class Meta:
        model = Call
        fields = [
            "UUID",
            "trunkRecorderID",
            "startTime",
            "endTime",
            "units",
            "active",
            "emergency",
            "encrypted",
            "frequency",
            "phase2",
            "talkgroup",
        ]


class CallUpdateCreateSerializer(serializers.ModelSerializer):
    # talkgroup = serializers.SlugRelatedField(
    #     read_only=False, queryset=TalkGroup.objects.all(), slug_field="decimalID"
    # )
    units = serializers.SlugRelatedField(
        many=True, read_only=False, queryset=Unit.objects.all(), slug_field="decimalID"
    )
    recorder = serializers.SlugRelatedField(
        read_only=False,
        queryset=SystemRecorder.objects.all(),
        slug_field="forwarderWebhookUUID",
    )

    class Meta:
        model = Call
        fields = [
            "UUID",
            "trunkRecorderID",
            "startTime",
            "endTime",
            "units",
            "active",
            "emergency",
            "encrypted",
            "frequency",
            "phase2",
            "talkgroup",
            "recorder",
        ]
