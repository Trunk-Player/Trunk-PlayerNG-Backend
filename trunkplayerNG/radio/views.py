from django.shortcuts import render
from rest_framework.views import APIView
from django.http import Http404
from rest_framework.response import Response
from radio.models import *
from radio.serializers import *
from rest_framework import generics
from rest_framework.parsers import JSONParser
from rest_framework import status
import json
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class UserProfileList(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

class UserProfileView(APIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def get_object(self, UUID):
        try:
            return UserProfile.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    def get(self, request, UUID, format=None):
        userProfile = self.get_object(UUID)
        serializer = UserProfileSerializer(userProfile)
        return Response(serializer.data)


    @swagger_auto_schema( request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            'siteTheme': openapi.Schema(type=openapi.TYPE_STRING, description='siteTheme'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='description'),
            'siteAdmin': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is user authorized to make changes'),
            'feedAllowed': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is user authorized to Feed System'),
        }
    ))
    def put(self, request, UUID, format=None):
        userProfile = self.get_object(UUID)
        serializer = UserProfileSerializer(userProfile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, UUID, format=None):
        userProfile = self.get_object(UUID)
        userProfile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SystemACLList(generics.ListAPIView):
    queryset = SystemACL.objects.all()
    serializer_class = SystemACLSerializer

class SystemACLCreate(APIView):
    queryset = SystemACL.objects.all()
    serializer_class = SystemACLSerializer

    def post(self, request, format=None):
        data = JSONParser().parse(request)
        if not "UUID" in data:
            data["UUID"] =  uuid.uuid4()
        serializer = SystemACLSerializer( data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SystemACLView(APIView):
    queryset = SystemACL.objects.all()
    serializer_class = SystemACLSerializer

    def get_object(self, UUID):
        try:
            return SystemACL.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    def get(self, request, UUID, format=None):
        SystemACL = self.get_object(UUID)
        serializer = SystemACLSerializer(SystemACL)
        return Response(serializer.data)

    @swagger_auto_schema( request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
            'users': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.TYPE_STRING, description='List of user UUID'),
            'public': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Make viable to all users'),
        }
    ))
    def put(self, request, UUID, format=None):
        SystemACL = self.get_object(UUID)
        serializer = SystemACLSerializer(SystemACL, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, UUID, format=None):
        SystemACL = self.get_object(UUID)
        SystemACL.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SystemList(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = System.objects.all()
    serializer_class = SystemSerializer


class SystemCreate(APIView):
    queryset = System.objects.all()
    serializer_class = SystemSerializer


    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] =  uuid.uuid4()

        serializer = SystemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemView(APIView):
    queryset = System.objects.all()
    serializer_class = SystemSerializer

    def get_object(self, UUID):
        try:
            return System.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    def get_ACL(self, UUID):
        try:
            return SystemACL.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    def get(self, request, UUID, format=None):
        System = self.get_object(UUID)
        serializer = SystemSerializer(System)
        return Response(serializer.data)

    @swagger_auto_schema( request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
            'systemACL': openapi.Schema(type=openapi.TYPE_STRING, description='System ACL UUID'),
        }
    ))
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)        
        System = self.get_object(UUID)        
        serializer = SystemSerializer(System, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, UUID, format=None):
        System = self.get_object(UUID)
        System.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SystemForwarderList(generics.ListAPIView):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer

class SystemForwarderCreate(APIView):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer


    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] =  uuid.uuid4()

        serializer = SystemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SystemForwarderView(APIView):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer

    def get_object(self, UUID):
        try:
            return SystemForwarder.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    def get(self, request, UUID, format=None):
        SystemForwarder = self.get_object(UUID)
        serializer = SystemForwarderSerializer(SystemForwarder)
        return Response(serializer.data)

    @swagger_auto_schema( request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Forwarder Name'),
            'enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='enabled'),
        }
    ))
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)        
        SystemForwarder = self.get_object(UUID)
        if "feedKey" in data:
            del data["feedKey"]
        serializer = SystemForwarderSerializer(SystemForwarder, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, UUID, format=None):
        SystemForwarder = self.get_object(UUID)
        SystemForwarder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CityList(generics.ListAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

class CityCreate(APIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer


    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] =  uuid.uuid4()

        serializer = CitySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CityView(APIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

    def get_object(self, UUID):
        try:
            return City.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    def get(self, request, UUID, format=None):
        City = self.get_object(UUID)
        serializer = CitySerializer(City)
        return Response(serializer.data)

    @swagger_auto_schema( request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='City Name'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='description'),
        }
    ))
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)        
        City = self.get_object(UUID)
        serializer = CitySerializer(City, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, UUID, format=None):
        City = self.get_object(UUID)
        City.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AgencyList(generics.ListAPIView):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer

class AgencyCreate(APIView):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer


    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] =  uuid.uuid4()

        serializer = AgencySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AgencyView(APIView):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer

    def get_object(self, UUID):
        try:
            return Agency.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    def get(self, request, UUID, format=None):
        Agency = self.get_object(UUID)
        serializer = AgencySerializer(Agency)
        return Response(serializer.data)

    @swagger_auto_schema( request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Agency Name'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='description'),
            'city': openapi.Schema(type=openapi.TYPE_STRING, description='City UUID'),
        }
    ))
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)        
        Agency = self.get_object(UUID)
        serializer = AgencySerializer(Agency, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, UUID, format=None):
        Agency = self.get_object(UUID)
        Agency.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TalkGroupView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView  ):
    queryset = TalkGroup.objects.all()
    serializer_class = TalkGroupSerializer

class SystemRecorderView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer

class UnitView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

class TransmissionUnitView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = TransmissionUnit.objects.all()
    serializer_class = TransmissionUnitSerializer

class TransmissionView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer

class IncidentView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

class TalkGroupACLView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = TalkGroupACL.objects.all()
    serializer_class = TalkGroupACLSerializer

class ScanListView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = ScanList.objects.all()
    serializer_class = ScanListSerializer

class GlobalScanListView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = GlobalScanList.objects.all()
    serializer_class = GlobalScanListSerializer

class GlobalAnnouncementView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = GlobalAnnouncement.objects.all()
    serializer_class = GlobalAnnouncementSerializer

class GlobalEmailTemplateView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = GlobalEmailTemplate.objects.all()
    serializer_class = GlobalEmailTemplateSerializer

class SystemReciveRateView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = SystemReciveRate.objects.all()
    serializer_class = SystemReciveRateSerializer

class CallView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = Call.objects.all()
    serializer_class = CallSerializer

class SystemRecorderMetricsView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = SystemRecorderMetrics.objects.all()
    serializer_class = SystemRecorderMetricsSerializer





