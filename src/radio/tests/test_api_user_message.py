import json
import uuid

from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import  UserInbox, UserMessage
from radio.serializers import UserMessageSerializer
from radio.views.api.user_message import View
from radio.helpers.utils import UUIDEncoder
from users.models import CustomUser


class APIUserMessageTests(APITestCase):
    """
    Tests the User Message API EP
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

        self.user1_message1: UserMessage = UserMessage.objects.create(
            urgent=False,
            read=False,
            time=timezone.now(),
            title="THe Barn is on fire!",
            body="The dog lied",
            source="Lassie"
        )
        self.user1_message1.save()

        self.user1_message2: UserMessage = UserMessage.objects.create(
            urgent=False,
            read=False,
            time=timezone.now(),
            title="Heads Up",
            body="I picked a bad week to stop sniffing glue",
            source="Steve McCroskey"
        )
        self.user1_message2.save()
        user1_inbox: UserInbox = UserInbox.objects.get(user=self.user.userProfile)
        user1_inbox.messages.add(self.user1_message1, self.user1_message2)
        user1_inbox.save()

        self.user2_message1: UserMessage = UserMessage.objects.create(
            urgent=False,
            read=False,
            time=timezone.now(),
            title="THe Barn is on fire!",
            body="The dog lied",
            source="Lassie"
        )
        self.user2_message1.save()

        self.user2_message2: UserMessage = UserMessage.objects.create(
            urgent=False,
            read=False,
            time=timezone.now(),
            title="Heads Up",
            body="I picked a bad week to stop sniffing glue",
            source="Steve McCroskey"
        )
        self.user2_message2.save()
        user2_inbox: UserInbox = UserInbox.objects.get(user=self.user2.userProfile)
        user2_inbox.messages.add(self.user2_message1, self.user2_message2)

    def test_api_user_message_get(self):
        '''Test for the User Message Get EP'''
        view = View.as_view()

        user1_message1_payload = UserMessageSerializer(self.user1_message1).data
        endpoint = reverse('users_message_view',  kwargs={'request_uuid': self.user1_message1.UUID})

        admin_request = self.factory.get(endpoint)
        force_authenticate(admin_request, user=self.privilaged_user)
        admin_response = view(admin_request, request_uuid=self.user1_message1.UUID)
        admin_response = admin_response.render()

        user1_request = self.factory.get(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.user1_message1.UUID)
        user1_response = user1_response.render()

        user2_request = self.factory.get(endpoint)
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request, request_uuid=self.user1_message1.UUID)
        user2_response = user2_response.render()

        data = json.loads(admin_response.content)
        user1_data = json.loads(user1_response.content)

        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(json.dumps(data), json.dumps(user1_message1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data), json.dumps(user1_message1_payload, cls=UUIDEncoder))

    def test_api_user_message_update(self):
        '''Test for the User Message Update EP'''
        view = View.as_view()

        payload = UserMessageSerializer(
            self.user2_message2
        ).data
        payload["read"] = True

        endpoint = reverse('users_message_view',  kwargs={'request_uuid': self.user2_message2.UUID})

        user1_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.user2_message2.UUID)
        user1_response = user1_response.render()

        user2_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request, request_uuid=self.user2_message2.UUID)
        user2_response = user2_response.render()

        payload2 = UserMessageSerializer(
            self.user2_message2
        ).data
        payload2["read"] = False
        request = self.factory.put(endpoint, payload2, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.user2_message2.UUID)
        response = response.render()

        malformed_payload = UserMessageSerializer(
            self.user2_message2
        ).data
        malformed_payload["read"] = "Duh"
        malformed_request = self.factory.put(endpoint, malformed_payload, format='json')
        force_authenticate(malformed_request, user=self.privilaged_user)
        malformed_response = view(malformed_request, request_uuid=self.user2_message2.UUID)
        malformed_response = malformed_response.render()

        data = json.loads(response.content)
        user2_data = json.loads(user2_response.content)

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(malformed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.dumps(data), json.dumps(payload2, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_user_message_delete(self):
        '''Test for the User Message Delete EP'''
        view = View.as_view()

        endpoint = reverse('users_alerts_view',  kwargs={'request_uuid': self.user1_message2.UUID})

        user2_request = self.factory.delete(endpoint)
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request, request_uuid=self.user1_message2.UUID)
        user2_response = user2_response.render()

        user1_request = self.factory.delete(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.user1_message2.UUID)
        user1_response = user1_response.render()

        request = self.factory.delete(endpoint)
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.user1_message2.UUID)
        response = response.render()

        user_messages = UserMessage.objects.all().count()

        self.assertEqual(user1_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(user2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(user_messages, 3)
