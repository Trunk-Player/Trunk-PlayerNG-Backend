from rest_framework import serializers
from radio.models import *

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['UUID', 'user', 'enabled', 'siteAdmin', 'Description', 'siteTheme', 'feedAllowed']

class SystemACLSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemACL
        fields = ['UUID', 'name', 'users', 'public']

class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = ['UUID', 'name', 'systemACL']

class SystemForwarderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemForwarder
        fields = ['UUID', 'name', 'feedKey', 'webhook']

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['UUID', 'name', 'description']

class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = ['UUID', 'name', 'description', 'city']

class TalkGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['UUID', 'system', 'decimalID', 'alphaTag', 'commonName', 'description', 'encrypted', 'agency']

class SystemRecorderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemRecorder
        fields = ['UUID', 'system', 'name', 'siteID', 'enabled', 'user', 'talkgroupsAllowed', 'talkgroupsDenyed', 'forwarderWebhookUUID']

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['UUID', 'system', 'decimalID', 'description']


class TransmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transmission
        fields = ['UUID', 'system', 'recorder', 'startTime', 'endTime', 'audioFile', 'talkgroup', 'encrypted', 'units', 'frequency', 'length']

class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ['UUID', 'system', 'transmission', 'name', 'description', 'agency']

class TalkGroupACLSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalkGroupACL
        fields = ['UUID', 'name', 'users', 'allowedTalkgroups', 'defualtNewUsers', 'defualtNewTalkgroups']

class ScanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanList
        fields = ['UUID', 'owner', 'name', 'description', 'public', 'talkgroups']

class GlobalScanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalScanList
        fields = ['UUID', 'scanList', 'name', 'enabled']

class GlobalAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalAnnouncement
        fields = ['UUID', 'name', 'enabled', 'description']

class GlobalEmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalEmailTemplate
        fields = ['UUID', 'name', 'type', 'enabled', 'HTML']

class SystemReciveRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemReciveRate
        fields = ['UUID', 'time', 'rate']

class CallSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanList
        fields = ['UUID', 'trunkRecorderID', 'startTime', 'endTime', 'units', 'active', 'emergency', 'encrypted', 'frequency', 'phase2', 'talkgroup']

class SystemRecorderMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemRecorderMetrics
        fields = ['UUID', 'systemRecorder', 'rates', 'calls']