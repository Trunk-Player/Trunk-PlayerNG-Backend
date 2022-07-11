import json
import uuid

from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import  UserInbox, UserMessage
from radio.serializers import UserInboxSerializer
from radio.views.api.user_inbox import DirectView, View, List
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

    def test_api_user_inbox_list(self):
        '''Test for the User Inbox List EP'''
        view = List.as_view()

        admin_serializer = UserInboxSerializer(
            UserInbox.objects.all(),
            many=True
        )
        user1_serializer = UserInboxSerializer(
            UserInbox.objects.filter(user=self.user.userProfile),
            many=True
        )
        user2_serializer = UserInboxSerializer(
            UserInbox.objects.filter(user=self.user2.userProfile),
            many=True
        )
        endpoint = reverse('users_inbox_list')

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


    def test_api_user_inbox_direct_get(self):
        '''Test for the User Inbox Direct Get EP'''
        view = DirectView.as_view()

        user1_inbox_payload = UserInboxSerializer(UserInbox.objects.get(user=self.user.userProfile)).data
        endpoint = reverse('users_inbox_direct_view',  kwargs={'request_uuid': self.user.userProfile.UUID})

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

        nonexistent_uuid = uuid.uuid4()
        endpoint = reverse('users_inbox_direct_view',  kwargs={'request_uuid': nonexistent_uuid})
        nonexistent_request = self.factory.get(endpoint)
        force_authenticate(nonexistent_request, user=self.user2)
        nonexistent_response = view(nonexistent_request, request_uuid=nonexistent_uuid)
        nonexistent_response = nonexistent_response.render()

        data = json.loads(admin_response.content)
        user1_data = json.loads(user1_response.content)

        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(nonexistent_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(json.dumps(data), json.dumps(user1_inbox_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data), json.dumps(user1_inbox_payload, cls=UUIDEncoder))


    def test_api_user_inbox_get(self):
        '''Test for the User Inbox Get EP'''
        view = View.as_view()

        user1_inbox = UserInbox.objects.get(user=self.user.userProfile)
        user1_inbox_payload = UserInboxSerializer(user1_inbox).data
        inbox_uuid = user1_inbox.UUID
        endpoint = reverse('users_inbox_view',  kwargs={'request_uuid': inbox_uuid})

        admin_request = self.factory.get(endpoint)
        force_authenticate(admin_request, user=self.privilaged_user)
        admin_response = view(admin_request, request_uuid=inbox_uuid)
        admin_response = admin_response.render()

        user1_request = self.factory.get(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=inbox_uuid)
        user1_response = user1_response.render()

        user2_request = self.factory.get(endpoint)
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request, request_uuid=inbox_uuid)
        user2_response = user2_response.render()
    
        nonexistent_uuid = uuid.uuid4()
        endpoint = reverse('users_inbox_view',  kwargs={'request_uuid': nonexistent_uuid})
        nonexistent_request = self.factory.get(endpoint)
        force_authenticate(nonexistent_request, user=self.user2)
        nonexistent_response = view(nonexistent_request, request_uuid=nonexistent_uuid)
        nonexistent_response = nonexistent_response.render()


        data = json.loads(admin_response.content)
        user1_data = json.loads(user1_response.content)

        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(nonexistent_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(json.dumps(data), json.dumps(user1_inbox_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data), json.dumps(user1_inbox_payload, cls=UUIDEncoder))
