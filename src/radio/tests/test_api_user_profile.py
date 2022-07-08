import json
import uuid

from django.urls import reverse

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import UserProfile
from radio.serializers import  UserProfileSerializer
from radio.views.api.user_profile import List, View
from radio.helpers.utils import UUIDEncoder
from users.models import CustomUser


class APIUserProfileTests(APITestCase):
    """
    Tests the User Profile API EP
    """
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user: CustomUser = CustomUser.objects.create_user(email='test@trunkplayer.io', password=str(uuid.uuid4()))
        self.user2: CustomUser = CustomUser.objects.create_user(email='test2@trunkplayer.io', password=str(uuid.uuid4()))
        self.privilaged_user:CustomUser = CustomUser.objects.create_user(email='test-priv@trunkplayer.io', password=str(uuid.uuid4()))
        self.privilaged_user.is_superuser = True
        self.privilaged_user.userProfile.site_admin = True
        self.privilaged_user.userProfile.save()
        self.privilaged_user.save()


    def test_api_user_alert_list(self):
        '''Test for the User Profile List EP'''
        view = List.as_view()

        admin_serializer = UserProfileSerializer(
            UserProfile.objects.all(),
            many=True
        )
        user1_serializer = UserProfileSerializer(
            UserProfile.objects.filter(UUID=self.user.userProfile.UUID),
            many=True
        )
        user2_serializer = UserProfileSerializer(
            UserProfile.objects.filter(UUID=self.user2.userProfile.UUID),
            many=True
        )
        endpoint = reverse('users_list')

        admin_request = self.factory.get(endpoint)
        force_authenticate(admin_request, user=self.privilaged_user)
        admin_response = view(admin_request)
        admin_response = admin_response.render()

        user2_request = self.factory.get(endpoint)
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request)
        user2_response = user2_response.render()

        user1_request = self.factory.get(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request)
        user1_response = user1_response.render()

        admin_data = json.loads(admin_response.content)
        user1_data = json.loads(user1_response.content)
        user2_data = json.loads(user2_response.content)

        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_data["count"], 1)
        self.assertEqual(user2_data["count"], 1)
        self.assertEqual(admin_data["count"], 3)
        self.assertEqual(json.dumps(admin_data["results"]), json.dumps(admin_serializer.data,cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data["results"]), json.dumps(user1_serializer.data,cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_data["results"]), json.dumps(user2_serializer.data,cls=UUIDEncoder))

    def test_api_user_alert_get(self):
        '''Test for the User Alert Get EP'''
        view = View.as_view()

        user1_payload = UserProfileSerializer(self.user.userProfile).data
        endpoint = reverse('users_view',  kwargs={'request_uuid': self.user.userProfile.UUID})

        admin_request = self.factory.get(endpoint)
        force_authenticate(admin_request, user=self.privilaged_user)
        admin_response = view(admin_request, request_uuid=self.user.userProfile.UUID)
        admin_response = admin_response.render()

        user1_request = self.factory.get(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.user.userProfile.UUID)
        user1_response = user1_response.render()

        user2_request = self.factory.get(endpoint)
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request, request_uuid=self.user.userProfile.UUID)
        user2_response = user2_response.render()

        admin_payload = UserProfileSerializer(self.privilaged_user.userProfile).data
        endpoint = reverse('system_view',  kwargs={'request_uuid': self.privilaged_user.userProfile.UUID})

        admin_restricted_request = self.factory.get(endpoint)
        force_authenticate(admin_restricted_request, user=self.privilaged_user)
        admin_restricted_response = view(admin_restricted_request, request_uuid=self.privilaged_user.userProfile.UUID)
        admin_restricted_response = admin_restricted_response.render()

        user1_restricted_request = self.factory.get(endpoint)
        force_authenticate(user1_restricted_request, user=self.user)
        user1_restricted_response = view(user1_restricted_request, request_uuid=self.privilaged_user.userProfile.UUID)
        user1_restricted_response = user1_restricted_response.render()

        user2_restricted_request = self.factory.get(endpoint)
        force_authenticate(user2_restricted_request, user=self.user2)
        user2_restricted_response = view(user2_restricted_request, request_uuid=self.privilaged_user.userProfile.UUID)
        user2_restricted_response = user2_restricted_response.render()


        data = json.loads(admin_response.content)
        user1_data = json.loads(user1_response.content)
        restricted_data = json.loads(admin_restricted_response.content)

        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(admin_restricted_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(json.dumps(data), json.dumps(user1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data), json.dumps(user1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(restricted_data), json.dumps(admin_payload, cls=UUIDEncoder))

    def test_api_user_alert_update(self):
        '''Test for the User Alert Update EP'''
        view = View.as_view()

        payload = UserProfileSerializer(
            self.user.userProfile
        ).data
        payload["site_theme"] = "NO"
        payload["description"] = "Ahoy"

        endpoint = reverse('users_view',  kwargs={'request_uuid': self.user.userProfile.UUID})

        user1_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.user.userProfile.UUID)
        user1_response = user1_response.render()

        user2_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request, request_uuid=self.user.userProfile.UUID)
        user2_response = user2_response.render()


        payload["description"] = "Admin overide"
        request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.user.userProfile.UUID)
        response = response.render()


        restricted_payload = UserProfileSerializer(
            self.privilaged_user.userProfile
        ).data
        restricted_payload["site_theme"] = "NOPE"
        restricted_payload["description"] = "Ahoy"

        user1_restricted_request = self.factory.put(endpoint, restricted_payload, format='json')
        force_authenticate(user1_restricted_request, user=self.user)
        user1_restricted_response = view(user1_restricted_request, request_uuid=self.privilaged_user.userProfile.UUID)
        user1_restricted_response = user1_restricted_response.render()

        user2_restricted_request = self.factory.put(endpoint, restricted_payload, format='json')
        force_authenticate(user2_restricted_request, user=self.user)
        user2_restricted_response = view(user2_restricted_request, request_uuid=self.privilaged_user.userProfile.UUID)
        user2_restricted_response = user2_restricted_response.render()

        restricted_request = self.factory.put(endpoint, restricted_payload, format='json')
        force_authenticate(restricted_request, user=self.privilaged_user)
        restricted_response = view(restricted_request, request_uuid=self.privilaged_user.userProfile.UUID)
        restricted_response = restricted_response.render()

        data = json.loads(response.content)
        restricted_data = json.loads(restricted_response.content)
        user2_data = json.loads(response.content)

        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(restricted_response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_data), json.dumps(payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(restricted_data), json.dumps(restricted_payload, cls=UUIDEncoder))
