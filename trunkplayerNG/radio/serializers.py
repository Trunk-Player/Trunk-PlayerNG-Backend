from typing import SupportsRound
from rest_framework import serializers
from radio.models import *

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['UUID', 'siteAdmin', 'description', 'siteTheme', 'feedAllowed']

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
        fields = ['UUID', 'name', 'enabled', 'feedKey', 'webhook']

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
        model = TalkGroup
        fields = ['UUID', 'system', 'decimalID', 'alphaTag',  'description', 'encrypted', 'agency']

class SystemRecorderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemRecorder
        fields = ['UUID', 'system', 'name', 'siteID', 'enabled', 'user', 'talkgroupsAllowed', 'talkgroupsDenyed', 'forwarderWebhookUUID']

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['UUID', 'system', 'decimalID', 'description']

class TransmissionUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransmissionUnit
        fields = ['UUID', 'time', 'unit', 'pos', 'emergency', 'signal_system', 'tag',  'length']


class TransmissionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Transmission
        fields = ['UUID', 'system', 'recorder', 'startTime', 'endTime', 'audioFile', 'talkgroup', 'encrypted', 'units', 'frequency', 'length']

class IncidentSerializer(serializers.ModelSerializer):
    transmission = TransmissionSerializer()

    class Meta:
        model = Incident
        fields = ['UUID', 'system', 'transmission', 'name', 'description', 'agency']

class TalkGroupACLSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalkGroupACL
        fields = ['UUID', 'name', 'users', 'allowedTalkgroups', 'defaultNewUsers', 'defaultNewTalkgroups']

class ScanListSerializer(serializers.ModelSerializer):
    talkgroups = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='TalkGroupView')

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
    units = UnitSerializer(many=True)
    class Meta:
        model = Call
        fields = ['UUID', 'trunkRecorderID', 'startTime', 'endTime', 'units', 'active', 'emergency', 'encrypted', 'frequency', 'phase2', 'talkgroup']

class CallCreateSerializer(serializers.ModelSerializer):
    talkgroup = serializers.IntegerField(write_only=True)
    units = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = Call
        fields = ['UUID', 'trunkRecorderID', 'startTime', 'endTime', 'units', 'active', 'emergency', 'encrypted', 'frequency', 'phase2', 'talkgroup']


    def create(self, validated_data):
        if validated_data["talkgroup"]:
            TGOBJ:TalkGroup =  TalkGroup.objects.get(decimalID=int(validated_data['talkgroup']))
            validated_data["talkgroup"] = TGOBJ
        
        if validated_data["units"]:
            units = []
            for unit in validated_data["units"]:
                unitObj:Unit = Unit.objects.get(decimalID=unit)
                units.append(unitObj.UUID)

            validated_data["units"] = units
        return super().create(validated_data)

class CallUpdateSerializer(serializers.ModelSerializer):
    talkgroup = serializers.SlugRelatedField(
        read_only=False,
        queryset=TalkGroup.objects.all(),
        slug_field='decimalID'
    )
    #units = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    units = serializers.SlugRelatedField(
        many=True,
        read_only=False,
        queryset=Unit.objects.all(),
        slug_field='decimalID'
    )
    startTime = serializers.DateTimeField(required=False)
    class Meta:
        model = Call
        fields = ['UUID', 'trunkRecorderID', 'startTime', 'endTime', 'units', 'active', 'emergency', 'encrypted', 'frequency', 'phase2', 'talkgroup']

    # def update(self, instance, validated_data):

    #     if validated_data["units"]:
    #         units = []
    #         for unit in validated_data["units"]:
    #             unitObj:Unit = Unit.objects.get(decimalID=unit)
    #             units.append(unitObj)

    #         instance.units.set(units)
    #         instance.save()
    #     return super(CallUpdateSerializer, self).update(instance, validated_data)

    def create(self, validated_data):
        if validated_data["talkgroup"]:
            TGOBJ:TalkGroup =  TalkGroup.objects.get(decimalID=int(validated_data['talkgroup']))
            validated_data["talkgroup"] = TGOBJ
        
        if validated_data["units"]:
            units = []
            for unit in validated_data["units"]:
                unitObj:Unit = Unit.objects.get(decimalID=unit)
                units.append(unitObj.UUID)

            validated_data["units"] = units
        return super().create(validated_data)

class SystemRecorderMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemRecorderMetrics
        fields = ['UUID', 'systemRecorder', 'rates', 'calls']