import json
import uuid

from django.urls import reverse

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import Agency, City
from radio.serializers import AgencySerializer, AgencyViewListSerializer
from radio.views.api.agency import Create, List, View
from radio.helpers.utils import UUIDEncoder
from users.models import CustomUser


class APIAgencyTests(APITestCase):
    """
    Tests the Agency API EP
    """
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = CustomUser.objects.create_user(email='test@trunkplayer.io', password=str(uuid.uuid4()))
        self.privilaged_user:CustomUser = CustomUser.objects.create_user(email='test-priv@trunkplayer.io', password=str(uuid.uuid4()))
        self.privilaged_user.is_superuser = True
        self.privilaged_user.userProfile.site_admin = True
        self.privilaged_user.userProfile.save()
        self.privilaged_user.save()

        self.city: City = City.objects.create(
            name="Dimsdale",
            description="Home to the Dimsdale Dimmadome"
        )

        self.agency: Agency = Agency.objects.create(
            name="Ghostbusters",
            description="Who Ya gonna call"

        )
        self.agency.save()
        self.agency.city.add(self.city)
        self.agency.save()

        self.agency2: Agency = Agency.objects.create(
            name="LAPD",
            description="LAPD"
        )
        self.agency2.save()
        self.agency2.city.add(self.city)
        self.agency2.save()

    def test_api_agency_list(self):
        '''Test for the Agency List EP'''
        view = List.as_view()

        agency_serializer = AgencyViewListSerializer(
            Agency.objects.all(),
            many=True
        )
        endpoint = reverse('agency_list')

        request = self.factory.get(endpoint, None)
        force_authenticate(request, user=self.user)
        response = view(request)
        response = response.render()

        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["results"], agency_serializer.data)

    def test_api_agency_create(self):
        '''Test for the Agency Create EP'''
        view = Create.as_view()

        agency_to_create: Agency = Agency(
            name="Bacon Boys",
            description="Bacon Boys"
        )
        payload = AgencySerializer(
            agency_to_create
        ).data
        del payload["UUID"]
        payload["city"].append(self.city.UUID)

        endpoint = reverse('agency_create')

        un_privilaged_request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request)
        response = response.render()


        malformed_payload = AgencySerializer(
            agency_to_create
        ).data
        del malformed_payload["UUID"]
        malformed_payload["city"] = "Bacon Boys"
        malformed_request = self.factory.post(endpoint, malformed_payload, format='json')
        force_authenticate(malformed_request, user=self.privilaged_user)
        malformed_response = view(malformed_request)
        malformed_response = malformed_response.render()

        data = json.loads(response.content)
        del data["UUID"]
        agencies = Agency.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(malformed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(agencies, 3)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_agency_get(self):
        '''Test for the Agency Get EP'''
        view = View.as_view()

        agency: Agency = Agency.objects.get(
            name="Ghostbusters",
        )
        payload = AgencyViewListSerializer(agency).data
        endpoint = reverse('agency_view',  kwargs={'request_uuid': agency.UUID})

        request = self.factory.get(endpoint)
        force_authenticate(request, user=self.user)
        response = view(request, request_uuid=agency.UUID)
        response = response.render()

        nonexistent_request = self.factory.get(endpoint)
        force_authenticate(nonexistent_request, user=self.user)
        nonexistent_response = view(nonexistent_request, request_uuid=uuid.uuid4())
        nonexistent_response = nonexistent_response.render()

        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(nonexistent_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_agency_update(self):
        '''Test for the Agency Update EP'''
        view = View.as_view()

        agency_to_update: Agency = Agency.objects.get(
            name="Ghostbusters"
        )
        payload = AgencySerializer(
            agency_to_update
        ).data
        payload["name"] = "Ghost Busters"

        endpoint = reverse('agency_view',  kwargs={'request_uuid': agency_to_update.UUID})

        un_privilaged_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request, request_uuid=agency_to_update.UUID)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=agency_to_update.UUID)
        response = response.render()

        malformed_payload = AgencySerializer(
            agency_to_update
        ).data
        del malformed_payload["UUID"]
        malformed_payload["city"] = "SOMETHING SNARKY"
        malformed_request = self.factory.put(endpoint, malformed_payload, format='json')
        force_authenticate(malformed_request, user=self.privilaged_user)
        malformed_response = view(malformed_request, request_uuid=agency_to_update.UUID)
        malformed_response = malformed_response.render()

        data = json.loads(response.content)
        agencies = Agency.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(malformed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(agencies, 2)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_agency_delete(self):
        '''Test for the Agency Delete EP'''
        view = View.as_view()

        agency_to_delete: Agency = Agency.objects.get(
            name="LAPD"
        )

        endpoint = reverse('agency_view',  kwargs={'request_uuid': agency_to_delete.UUID})

        un_privilaged_request = self.factory.delete(endpoint)
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request, request_uuid=agency_to_delete.UUID)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.delete(endpoint)
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=agency_to_delete.UUID)
        response = response.render()

        agencies = Agency.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(agencies, 1)
