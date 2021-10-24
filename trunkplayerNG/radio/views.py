from django.shortcuts import render
from radio.models import *
from radio.serializers import *
from rest_framework import generics


class UserProfile(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer


class SystemACL(generics.ListAPIView):
    queryset = SystemACL.objects.all()
    serializer_class = SystemACLSerializer

class System(generics.ListAPIView):
    queryset = System.objects.all()
    serializer_class = SystemSerializer

class SystemForwarder(generics.ListAPIView):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer

class City(generics.ListAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

class SysteAgencymACL(generics.ListAPIView):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer

class TalkGroup(generics.ListAPIView):
    queryset = TalkGroup.objects.all()
    serializer_class = TalkGroupSerializer

class SystemRecorder(generics.ListAPIView):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer

class Unit(generics.ListAPIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

class Transmission(generics.ListAPIView):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer

class Incident(generics.ListAPIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

class TalkGroupACL(generics.ListAPIView):
    queryset = TalkGroupACL.objects.all()
    serializer_class = TalkGroupACLSerializer

class ScanList(generics.ListAPIView):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer

class GlobalScanList(generics.ListAPIView):
    queryset = GlobalScanList.objects.all()
    serializer_class = GlobalScanListSerializer

class GlobalAnnouncement(generics.ListAPIView):
    queryset = GlobalAnnouncement.objects.all()
    serializer_class = GlobalAnnouncementSerializer

class GlobalEmailTemplate(generics.ListAPIView):
    queryset = GlobalEmailTemplate.objects.all()
    serializer_class = GlobalEmailTemplateSerializer

class SystemReciveRate(generics.ListAPIView):
    queryset = SystemReciveRate.objects.all()
    serializer_class = SystemReciveRateSerializer

class Call(generics.ListAPIView):
    queryset = Call.objects.all()
    serializer_class = CallSerializer

class SystemRecorderMetrics(generics.ListAPIView):
    queryset = SystemRecorderMetrics.objects.all()
    serializer_class = SystemRecorderMetricsSerializer





