import json
import uuid
from radio.serializers import AgencySerializer

from users.models import CustomUser

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import Agency
from radio.views.api.agency import List

class APIAgencyTests(APITestCase):
    """
    Test that only user 1 can see the Test TG 1 TalkGroup when access control is on
    """
    def setUp(self):
        self.factory = APIRequestFactory()
        
        self.user = CustomUser.objects.create_user(email='test@trunkplayer.io', password=str(uuid.uuid4()))
        self.agency: Agency = Agency.objects.create(name="Ghostbusters")
        self.agency.save()

        self.agency2: Agency = Agency.objects.create(name="LAPD")
        self.agency2.save()


    def test_api_agency_list(self):
        view = List.as_view()

        agency_serializer = AgencySerializer(Agency.objects.all(), many=True)

        request = self.factory.get('/apiv1/radio/agency/list', None)
        force_authenticate(request, user=self.user)
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json["count"]), 1)
        self.assertEqual(response["results"], agency_serializer.data)


