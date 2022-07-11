import json
import uuid

from django.urls import reverse

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import City
from radio.serializers import CitySerializer
from radio.views.api.city import Create, List, View
from radio.helpers.utils import UUIDEncoder
from users.models import CustomUser


class APICityTests(APITestCase):
    """
    Tests the City API EP
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

        self.city: City = City.objects.create(
            name="Gotham",
            description="Batman or something"
        )

        self.city: City = City.objects.create(
            name="Atlantis",
            description="Why cant max be an id10t? the world may never know"
        )

 

    def test_api_city_list(self):
        '''Test for the City List EP'''
        view = List.as_view()

        serializer = CitySerializer(
            City.objects.all(),
            many=True
        )
        endpoint = reverse('city_list')

        request = self.factory.get(endpoint, None)
        force_authenticate(request, user=self.user)
        response = view(request)
        response = response.render()

        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 3)
        self.assertEqual(data["results"], serializer.data)

    def test_api_city_create(self):
        '''Test for the City Create EP'''
        view = Create.as_view()

        to_create: City = City(
            name="Las Vegas",
            description="Las Vegas, NV"
        )
        payload = CitySerializer(
            to_create
        ).data
        del payload["UUID"]
        endpoint = reverse('city_create')

        un_privilaged_request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request)
        response = response.render()


        malformed_payload = CitySerializer(
            to_create
        ).data
        malformed_payload["name"] = True
        malformed_request = self.factory.post(endpoint, malformed_payload, format='json')
        force_authenticate(malformed_request, user=self.privilaged_user)
        malformed_response = view(malformed_request)
        malformed_response = malformed_response.render()

        data = json.loads(response.content)
        del data["UUID"]
        cities = City.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(malformed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(cities, 4)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_city_get(self):
        '''Test for the City Get EP'''
        view = View.as_view()

        city: City = City.objects.get(
            name="Dimsdale",
        )
        payload = CitySerializer(city).data
        endpoint = reverse('city_view',  kwargs={'request_uuid': city.UUID})

        request = self.factory.get(endpoint)
        force_authenticate(request, user=self.user)
        response = view(request, request_uuid=city.UUID)
        response = response.render()

        nonexistent_uuid = uuid.uuid4()
        endpoint = reverse('city_view',  kwargs={'request_uuid': nonexistent_uuid})
        nonexistent_request = self.factory.get(endpoint)
        force_authenticate(nonexistent_request, user=self.user)
        nonexistent_response = view(nonexistent_request, request_uuid=nonexistent_uuid)
        nonexistent_response = nonexistent_response.render()

        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(nonexistent_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_city_update(self):
        '''Test for the City Update EP'''
        view = View.as_view()

        to_update: City = City.objects.get(
            name="Gotham"
        )
        payload = CitySerializer(
            to_update
        ).data
        payload["name"] = "Joker was here"

        endpoint = reverse('city_view',  kwargs={'request_uuid': to_update.UUID})

        un_privilaged_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request, request_uuid=to_update.UUID)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=to_update.UUID)
        response = response.render()

        malformed_payload = CitySerializer(
            to_update
        ).data
        malformed_payload["name"] = "THIS IS GOING TO BE A LOT LONGER THAN 30 CHARS... ALSO AHHH WHY IS THIS SO HARD TO TEST"
        malformed_request = self.factory.put(endpoint, malformed_payload, format='json')
        force_authenticate(malformed_request, user=self.privilaged_user)
        malformed_response = view(malformed_request, request_uuid=to_update.UUID)
        malformed_response = malformed_response.render()

        data = json.loads(response.content)
        cities = City.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(malformed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(cities, 3)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_city_delete(self):
        '''Test for the city Delete EP'''
        view = View.as_view()

        to_delete: City = City.objects.get(
            name="Atlantis"
        )

        endpoint = reverse('city_view',  kwargs={'request_uuid': to_delete.UUID})

        un_privilaged_request = self.factory.delete(endpoint)
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request, request_uuid=to_delete.UUID)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.delete(endpoint)
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=to_delete.UUID)
        response = response.render()

        cities = City.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(cities, 2)
