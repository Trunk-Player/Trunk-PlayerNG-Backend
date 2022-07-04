from rest_framework import serializers

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



class UserAlertSerializer(serializers.ModelSerializer):
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
            "title",
            "body",
            "emergency_only",
            "count",
            "trigger_time",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["UUID", "site_admin", "description", "site_theme"]


class UserMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["UUID", "urgent", "read", "time", "title", "body", "source"]


class UserInboxSerializer(serializers.ModelSerializer):
    messages = UserMessageSerializer(many=True)
    class Meta:
        model = UserProfile
        fields = ["UUID", "user", "messages", "site_theme"]



class SystemACLSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemACL
        fields = ["UUID", "name", "users", "public"]


class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = [
            "UUID",
            "name",
            "systemACL",
            "rr_system_id",
            "enable_talkgroup_acls",
            "prune_transmissions",
            "prune_transmissions_after_days",
            "notes"
        ]


class SystemForwarderSerializer(serializers.ModelSerializer):
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
            "decimal_id",
            "alpha_tag",
            "description",
            "mode",
            "encrypted",
            "agency",
            "notes"
        ]

class TalkGroupListSerializer(serializers.ModelSerializer):
    system = SystemSerializer(read_only=True)
    class Meta:
        model = TalkGroup
        fields = [
            "UUID",
            "system",
            "decimal_id",
            "alpha_tag",
            "description",
            "mode",
            "encrypted",
            "agency",
            "notes"
        ]


class TalkGroupViewListSerializer(serializers.ModelSerializer):
    agency = AgencyViewListSerializer(read_only=True, many=True)
    system = SystemSerializer(read_only=True)

    class Meta:
        model = TalkGroup
        fields = [
            "UUID",
            "system",
            "decimal_id",
            "alpha_tag",
            "description",
            "mode",
            "encrypted",
            "agency",
            "notes"
        ]


class SystemRecorderSerializer(serializers.ModelSerializer):
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


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["UUID", "system", "decimal_id", "description"]


class TransmissionUnitSerializer(serializers.ModelSerializer):
    unit = serializers.SlugRelatedField(
        read_only=False, queryset=Unit.objects.all(), slug_field="decimal_id"
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
        # pylint: disable=unused-variable
        unit_object, created = Unit.objects.get_or_create(decimal_id=int(unit))
        return Transmission.objects.create(unit=unit_object, **validated_data)


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
            "audio_type",
            "start_time",
            "end_time",
            "audio_file",
            "talkgroup",
            "encrypted",
            "units",
            "frequency",
            "frequencys",
            "length",
            "locked",
            "transcript"
        ]


class TransmissionListSerializer(serializers.ModelSerializer):
    talkgroup = TalkGroupSerializer()
    units = TransmissionUnitSerializer(read_only=True, many=True)
    frequencys = TransmissionFreqSerializer(read_only=True, many=True)

    system_name = serializers.SerializerMethodField()

    class Meta:
        model = Transmission
        fields = [
            "UUID",
            "system",
            "system_name",
            "recorder",
            "audio_type",
            "start_time",
            "end_time",
            "audio_file",
            "talkgroup",
            "encrypted",
            "units",
            "frequency",
            "frequencys",
            "length",
            "locked",
            "transcript"
        ]

    def get_system_name(self, obj):
        """
        Gets the name of a system
        """
        return obj.system.name


class TransmissionUploadSerializer(serializers.ModelSerializer):
    recorder = serializers.SlugRelatedField(
        read_only=False,
        queryset=SystemRecorder.objects.all(),
        slug_field="api_key",
    )

    units = serializers.SlugRelatedField(
        read_only=False,
        queryset=TransmissionUnit.objects.all(),
        slug_field="UUID",
        many=True,
        required=False,
    )
    frequencys = serializers.SlugRelatedField(
        read_only=False,
        queryset=TransmissionFreq.objects.all(),
        slug_field="UUID",
        many=True,
        required=False,
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
            "audio_file",
            "talkgroup",
            "encrypted",
            "emergency",
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
            "active",
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
            "allowed_talkgroups",
            "default_new_talkgroups",
            "default_new_users",
            "download_allowed",
            "transcript_allowed",
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
            "community_shared",
            "talkgroups",
            "notes"
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
            "community_shared",
            "scanlists",
            "notes"
        ]


class GlobalAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalAnnouncement
        fields = ["UUID", "name", "enabled", "description"]


class GlobalEmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalEmailTemplate
        fields = ["UUID", "name", "template_type", "enabled", "HTML"]


# class SystemReciveRateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SystemReciveRate
#         fields = ["UUID", "time", "rate", "recorder"]


# class SystemReciveRateCreateSerializer(serializers.ModelSerializer):
#     recorder = serializers.SlugRelatedField(
#         read_only=False,
#         queryset=SystemRecorder.objects.all(),
#         slug_field="api_key",
#     )

#     class Meta:
#         model = SystemReciveRate
#         fields = ["UUID", "time", "rate", "recorder"]


# class CallSerializer(serializers.ModelSerializer):
#     units = UnitSerializer(many=True)

#     class Meta:
#         model = Call
#         fields = [
#             "UUID",
#             "trunkRecorderID",
#             "start_time",
#             "end_time",
#             "units",
#             "active",
#             "emergency",
#             "encrypted",
#             "frequency",
#             "phase2",
#             "talkgroup",
#         ]


# class CallUpdateCreateSerializer(serializers.ModelSerializer):
#     # talkgroup = serializers.SlugRelatedField(
#     #     read_only=False, queryset=TalkGroup.objects.all(), slug_field="decimal_id"
#     # )
#     units = serializers.SlugRelatedField(
#         many=True, read_only=False, queryset=Unit.objects.all(), slug_field="decimal_id"
#     )
#     recorder = serializers.SlugRelatedField(
#         read_only=False,
#         queryset=SystemRecorder.objects.all(),
#         slug_field="api_key",
#     )

#     class Meta:
#         model = Call
#         fields = [
#             "UUID",
#             "trunkRecorderID",
#             "start_time",
#             "end_time",
#             "units",
#             "active",
#             "emergency",
#             "encrypted",
#             "frequency",
#             "phase2",
#             "talkgroup",
#             "recorder",
#         ]
