from django.shortcuts import render
from rest_framework.views import APIView
from django.http import Http404
from rest_framework.response import Response
from radio.models import *
from radio.serializers import *
from rest_framework import generics
from rest_framework.parsers import JSONParser
from rest_framework.parsers import FileUploadParser
from rest_framework import status
import json
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from radio.transmission import new_transmission_handler

class UserProfileList(APIView):    
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    
    @swagger_auto_schema(tags=['UserProfile'])
    def get(self, request, format=None):
        userProfile = UserProfile.objects.all()
        serializer = UserProfileSerializer(userProfile)
        return Response(serializer.data)
    


class UserProfileView(APIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def get_object(self, UUID):
        try:
            return UserProfile.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=['UserProfile'])
    def get(self, request, UUID, format=None):
        userProfile = self.get_object(UUID)
        serializer = UserProfileSerializer(userProfile)
        return Response(serializer.data)


    @swagger_auto_schema(tags=['UserProfile'], request_body=openapi.Schema(
        
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
        serializer = UserProfileSerializer(userProfile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['UserProfile'])
    def delete(self, request, UUID, format=None):
        userProfile = self.get_object(UUID)
        userProfile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemACLList(APIView):
    queryset = SystemACL.objects.all()
    serializer_class = SystemACLSerializer
    
    @swagger_auto_schema(tags=['SystemACL'])
    def get(self, request, format=None):
        SystemACLs = SystemACL.objects.all()
        serializer = SystemACLSerializer(SystemACLs)
        return Response(serializer.data)

class SystemACLCreate(APIView):
    queryset = SystemACL.objects.all()
    serializer_class = SystemACLSerializer

    @swagger_auto_schema(tags=['SystemACL'])
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

    @swagger_auto_schema(tags=['SystemACL'])
    def get(self, request, UUID, format=None):
        SystemACL = self.get_object(UUID)
        serializer = SystemACLSerializer(SystemACL)
        return Response(serializer.data)

    @swagger_auto_schema(tags=['SystemACL'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
            'users': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='List of user UUID'),
            'public': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Make viable to all users'),
        }
    ))
    def put(self, request, UUID, format=None):
        SystemACL = self.get_object(UUID)
        serializer = SystemACLSerializer(SystemACL, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['SystemACL'])
    def delete(self, request, UUID, format=None):
        SystemACL = self.get_object(UUID)
        SystemACL.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SystemList(APIView):
    queryset = System.objects.all()
    serializer_class = SystemSerializer

    @swagger_auto_schema(tags=['System'])
    def get(self, request, format=None):
        Systems = System.objects.all()
        serializer = SystemSerializer(Systems)
        return Response(serializer.data)


class SystemCreate(APIView):
    queryset = System.objects.all()
    serializer_class = SystemSerializer

    @swagger_auto_schema(tags=['System'])
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
    @swagger_auto_schema(tags=['System'])
    def get(self, request, UUID, format=None):
        System = self.get_object(UUID)
        serializer = SystemSerializer(System)
        return Response(serializer.data)

    @swagger_auto_schema(tags=['System'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
            'systemACL': openapi.Schema(type=openapi.TYPE_STRING, description='System ACL UUID'),
        }
    ))
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)        
        System = self.get_object(UUID)        
        serializer = SystemSerializer(System, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['System'])
    def delete(self, request, UUID, format=None):
        System = self.get_object(UUID)
        System.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SystemForwarderList(APIView):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer

    @swagger_auto_schema(tags=['SystemForwarder'])
    def get(self, request, format=None):
        SystemForwarders = SystemForwarder.objects.all()
        serializer = SystemForwarderSerializer(SystemForwarders)
        return Response(serializer.data)


class SystemForwarderCreate(APIView):
    queryset = SystemForwarder.objects.all()
    serializer_class = SystemForwarderSerializer

    @swagger_auto_schema(tags=['SystemForwarder'])
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

    @swagger_auto_schema(tags=['SystemForwarder'])
    def get(self, request, UUID, format=None):
        SystemForwarder = self.get_object(UUID)
        serializer = SystemForwarderSerializer(SystemForwarder)
        return Response(serializer.data)

    @swagger_auto_schema(tags=['SystemForwarder'], request_body=openapi.Schema(
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
        serializer = SystemForwarderSerializer(SystemForwarder, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['SystemForwarder'])
    def delete(self, request, UUID, format=None):
        SystemForwarder = self.get_object(UUID)
        SystemForwarder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CityList(APIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

    @swagger_auto_schema(tags=['City'])
    def get(self, request, format=None):
        Citys = City.objects.all()
        serializer = CitySerializer(Citys)
        return Response(serializer.data)

class CityCreate(APIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

    @swagger_auto_schema(tags=['City'])
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

    @swagger_auto_schema(tags=['City'])
    def get(self, request, UUID, format=None):
        City = self.get_object(UUID)
        serializer = CitySerializer(City)
        return Response(serializer.data)

    @swagger_auto_schema(tags=['City'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='City Name'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='description'),
        }
    ))
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)        
        City = self.get_object(UUID)
        serializer = CitySerializer(City, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['City'])
    def delete(self, request, UUID, format=None):
        City = self.get_object(UUID)
        City.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AgencyList(APIView):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer

    @swagger_auto_schema(tags=['Agency'])
    def get(self, request, format=None):
        Agencys = Agency.objects.all()
        serializer = AgencySerializer(Agencys)
        return Response(serializer.data)

class AgencyCreate(APIView):
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer

    @swagger_auto_schema(tags=['Agency'])
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

    @swagger_auto_schema(tags=['Agency'])
    def get(self, request, UUID, format=None):
        Agency = self.get_object(UUID)
        serializer = AgencySerializer(Agency)
        return Response(serializer.data)

    @swagger_auto_schema(tags=['Agency'], request_body=openapi.Schema(
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
        serializer = AgencySerializer(Agency, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Agency'])
    def delete(self, request, UUID, format=None):
        Agency = self.get_object(UUID)
        Agency.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TalkGroupList(APIView):
    queryset = TalkGroup.objects.all()
    serializer_class = TalkGroupSerializer

    @swagger_auto_schema(tags=['TalkGroup'])
    def get(self, request, format=None):
        TalkGroups = TalkGroup.objects.all()
        serializer = TalkGroupSerializer(TalkGroups)
        return Response(serializer.data)

class TalkGroupCreate(APIView):
    queryset = TalkGroup.objects.all()
    serializer_class = TalkGroupSerializer

    @swagger_auto_schema(tags=['TalkGroup'])
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] =  uuid.uuid4()

        serializer = TalkGroupSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TalkGroupView(APIView):
    queryset = TalkGroup.objects.all()
    serializer_class = TalkGroupSerializer

    def get_object(self, UUID):
        try:
            return TalkGroup.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=['TalkGroup'])
    def get(self, request, UUID, format=None):
        TalkGroup = self.get_object(UUID)
        serializer = TalkGroupSerializer(TalkGroup)
        return Response(serializer.data)

    @swagger_auto_schema(tags=['TalkGroup'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            #'system': openapi.Schema(type=openapi.TYPE_STRING, description='System UUID'),
            #'decimalID': openapi.Schema(type=openapi.TYPE_STRING, description='decimalID'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='decimalID'),
            'alphaTag': openapi.Schema(type=openapi.TYPE_STRING, description='alphaTag'),
            'encrypted': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='encrypted'),
            'agency': openapi.Schema(type=openapi.TYPE_STRING, description='Agency UUID'),
        }
    ))
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)        
        TalkGroup = self.get_object(UUID)
        serializer = TalkGroupSerializer(TalkGroup, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['TalkGroup'])
    def delete(self, request, UUID, format=None):
        TalkGroup = self.get_object(UUID)
        TalkGroup.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SystemRecorderList(APIView):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer

    @swagger_auto_schema(tags=['SystemRecorder'])
    def get(self, request, format=None):
        SystemRecorders = SystemRecorder.objects.all()
        serializer = SystemRecorderSerializer(SystemRecorders)
        return Response(serializer.data)

class SystemRecorderCreate(APIView):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer

    @swagger_auto_schema(tags=['SystemRecorder'])
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] =  uuid.uuid4()

        serializer = SystemRecorderSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SystemRecorderView(APIView):
    queryset = SystemRecorder.objects.all()
    serializer_class = SystemRecorderSerializer

    def get_object(self, UUID):
        try:
            return SystemRecorder.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=['SystemRecorder'])
    def get(self, request, UUID, format=None):
        SystemRecorder = self.get_object(UUID)
        serializer = SystemRecorderSerializer(SystemRecorder)
        return Response(serializer.data)

    @swagger_auto_schema(tags=['SystemRecorder'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            #'system': openapi.Schema(type=openapi.TYPE_STRING, description='System UUID'),
            'siteID': openapi.Schema(type=openapi.TYPE_STRING, description='Site ID'),
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Name'),
            'enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Enabled'),
            #'user': openapi.Schema(type=openapi.TYPE_STRING, description='User UUID'),
            'talkgroupsAllowed': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='Talkgroups Allowed UUIDs'),
            'talkgroupsDenyed': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='Talkgroups Allowed UUIDs'),
        }
    ))
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)        
        SystemRecorder = self.get_object(UUID)
        serializer = SystemRecorderSerializer(SystemRecorder, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['SystemRecorder'])
    def delete(self, request, UUID, format=None):
        SystemRecorder = self.get_object(UUID)
        SystemRecorder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UnitList(APIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

    @swagger_auto_schema(tags=['Unit'])
    def get(self, request, format=None):
        Units = Unit.objects.all()
        serializer = UnitSerializer(Units)
        return Response(serializer.data)

class UnitCreate(APIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

    @swagger_auto_schema(tags=['Unit'])
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] =  uuid.uuid4()

        serializer = UnitSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UnitView(APIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

    def get_object(self, UUID):
        try:
            return Unit.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=['Unit'])
    def get(self, request, UUID, format=None):
        Unit = self.get_object(UUID)
        serializer = UnitSerializer(Unit)
        return Response(serializer.data)

    @swagger_auto_schema(tags=['Unit'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description'),
        }
    ))
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)        
        Unit = self.get_object(UUID)
        serializer = UnitSerializer(Unit, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Unit'])
    def delete(self, request, UUID, format=None):
        Unit = self.get_object(UUID)
        Unit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TransmissionUnitList(APIView):
    queryset = TransmissionUnit.objects.all()
    serializer_class = TransmissionUnitSerializer

    @swagger_auto_schema(tags=['TransmissionUnit'])
    def get(self, request, format=None):
        TransmissionUnits = TransmissionUnit.objects.all()
        serializer = TransmissionUnitSerializer(TransmissionUnits)
        return Response(serializer.data)

# class TransmissionUnitCreate(APIView):
#     queryset = TransmissionUnit.objects.all()
#     serializer_class = TransmissionUnitSerializer

#     @swagger_auto_schema(tags=['TransmissionUnit'])
#     def post(self, request, format=None):
#         data = JSONParser().parse(request)

#         if not "UUID" in data:
#             data["UUID"] =  uuid.uuid4()

#         serializer = TransmissionUnitSerializer(data=data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransmissionUnitView(APIView):
    queryset = TransmissionUnit.objects.all()
    serializer_class = TransmissionUnitSerializer

    def get_object(self, UUID):
        try:
            return TransmissionUnit.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=['TransmissionUnit'])
    def get(self, request, UUID, format=None):
        TransmissionUnit = self.get_object(UUID)
        serializer = TransmissionUnitSerializer(TransmissionUnit)
        return Response(serializer.data)

    # @swagger_auto_schema(tags=['TransmissionUnit'], request_body=openapi.Schema(
    #     type=openapi.TYPE_OBJECT, 
    #     properties={
    #         'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description'),
    #     }
    # ))
    # def put(self, request, UUID, format=None):
    #     data = JSONParser().parse(request)        
    #     TransmissionUnit = self.get_object(UUID)
    #     serializer = TransmissionUnitSerializer(TransmissionUnit, data=data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @swagger_auto_schema(tags=['TransmissionUnit'])
    # def delete(self, request, UUID, format=None):
    #     TransmissionUnit = self.get_object(UUID)
    #     TransmissionUnit.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class TransmissionList(APIView):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer

    @swagger_auto_schema(tags=['Transmission'])
    def get(self, request, format=None):
        Transmissions = Transmission.objects.all()
        serializer = TransmissionSerializer(Transmissions)
        return Response(serializer.data)

class TransmissionCreate(APIView):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer

    @swagger_auto_schema(tags=['Transmission'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={            
            'system': openapi.Schema(type=openapi.TYPE_STRING, description='System UUID'),
            'recorder': openapi.Schema(type=openapi.TYPE_STRING, description='Recorder UUID'),
            'json': openapi.Schema(type=openapi.TYPE_STRING, description='Trunk-Recorder JSON'),    
            'audio': openapi.Schema(type=openapi.TYPE_STRING, description='M4A Base64')            
        }
    ))
    def post(self, request, filename, format=None):
        data = JSONParser().parse(request)

        try:
            Callback = new_transmission_handler(data)
            return Response(Callback)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

class TransmissionView(APIView):
    queryset = Transmission.objects.all()
    serializer_class = TransmissionSerializer

    def get_object(self, UUID):
        try:
            return Transmission.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=['Transmission'])
    def get(self, request, UUID, format=None):
        Transmission = self.get_object(UUID)
        serializer = TransmissionSerializer(Transmission)
        return Response(serializer.data)

    # @swagger_auto_schema(tags=['Transmission'], request_body=openapi.Schema(
    #     type=openapi.TYPE_OBJECT, 
    #     properties={
    #         'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description'),
    #     }
    # ))
    # def put(self, request, UUID, format=None):
    #     data = JSONParser().parse(request)        
    #     Transmission = self.get_object(UUID)
    #     serializer = TransmissionSerializer(Transmission, data=data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Transmission'])
    def delete(self, request, UUID, format=None):
        Transmission = self.get_object(UUID)
        Transmission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class IncidentView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView ):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

class IncidentList(APIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

    @swagger_auto_schema(tags=['Incident'])
    def get(self, request, format=None):
        Incidents = Incident.objects.all()
        serializer = IncidentSerializer(Incidents)
        return Response(serializer.data)

class IncidentCreate(APIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

    @swagger_auto_schema(tags=['Incident'])
    def post(self, request, format=None):
        data = JSONParser().parse(request)

        if not "UUID" in data:
            data["UUID"] =  uuid.uuid4()

        serializer = IncidentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IncidentView(APIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

    def get_object(self, UUID):
        try:
            return Incident.objects.get(UUID=UUID)
        except UserProfile.DoesNotExist:
            raise Http404

    @swagger_auto_schema(tags=['Incident'])
    def get(self, request, UUID, format=None):
        Incident = self.get_object(UUID)
        serializer = IncidentSerializer(Incident)
        return Response(serializer.data)

    @swagger_auto_schema(tags=['Incident'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT, 
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Description'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description'),
            'agency': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='Agency UUIDs'),
        }
    ))
    def put(self, request, UUID, format=None):
        data = JSONParser().parse(request)        
        Incident = self.get_object(UUID)
        serializer = IncidentSerializer(Incident, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Incident'])
    def delete(self, request, UUID, format=None):
        Incident = self.get_object(UUID)
        Incident.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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





