import json
import uuid

from django.urls import reverse

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import GlobalAnnouncement
from radio.serializers import GlobalAnnouncementSerializer
from radio.views.api.global_announcement import Create, List, View
from radio.helpers.utils import UUIDEncoder
from users.models import CustomUser


class APIGlobalAnnouncmentTests(APITestCase):
    """
    Tests the Global Announcment API EP
    """
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = CustomUser.objects.create_user(email='test@trunkplayer.io', password=str(uuid.uuid4()))
        self.privilaged_user:CustomUser = CustomUser.objects.create_user(email='test-priv@trunkplayer.io', password=str(uuid.uuid4()))
        self.privilaged_user.is_superuser = True
        self.privilaged_user.userProfile.site_admin = True
        self.privilaged_user.userProfile.save()
        self.privilaged_user.save()

        self.ga1: GlobalAnnouncement = GlobalAnnouncement.objects.create(
            name="Site maitinace",
            description="we broke a thing",
            enabled=False
        )
        self.ga1.save()

        self.ga2: GlobalAnnouncement = GlobalAnnouncement.objects.create(
            name="panik",
            description="Aliens have landed",
            enabled=True
        )
        self.ga2.save()
 

    def test_api_global_announcment_list(self):
        '''Test for the Global Announcement List EP'''
        view = List.as_view()

        serializer = GlobalAnnouncementSerializer(
            GlobalAnnouncement.objects.all(),
            many=True
        )
        endpoint = reverse('globalannouncement_list')

        un_privilaged_request = self.factory.get(endpoint)
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.get(endpoint)
        force_authenticate(request, user=self.privilaged_user)
        response = view(request)
        response = response.render()

        un_privilaged_data = json.loads(un_privilaged_response.content)
        data = json.loads(response.content)
    
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(un_privilaged_response.status_code, status.HTTP_200_OK)
        self.assertEqual(un_privilaged_data["count"], 1)
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["results"], serializer.data)

    def test_api_global_announcment_create(self):
        '''Test for the Global Announcement Create EP'''
        view = Create.as_view()

        to_create: GlobalAnnouncement = GlobalAnnouncement(
            name="New System",
            description="New system was added",
            enabled=True
        )
        payload = GlobalAnnouncementSerializer(
            to_create
        ).data
        del payload["UUID"]
        endpoint = reverse('globalannouncement_create')

        un_privilaged_request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request)
        response = response.render()

        malformed_payload = GlobalAnnouncementSerializer(
            to_create
        ).data
        malformed_payload["name"] = True
        malformed_request = self.factory.post(endpoint, malformed_payload, format='json')
        force_authenticate(malformed_request, user=self.privilaged_user)
        malformed_response = view(malformed_request)
        malformed_response = malformed_response.render()

        data = json.loads(response.content)
        del data["UUID"]
        global_announcements = GlobalAnnouncement.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(malformed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(global_announcements, 3)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_global_announcment_get(self):
        '''Test for the Global Announcement Get EP'''
        view = View.as_view()

        global_announcement: GlobalAnnouncement = GlobalAnnouncement.objects.get(
            name="panik",
        )
        payload = GlobalAnnouncementSerializer(global_announcement).data
        endpoint = reverse('globalannouncement_view',  kwargs={'request_uuid': global_announcement.UUID})

        request = self.factory.get(endpoint)
        force_authenticate(request, user=self.user)
        response = view(request, request_uuid=global_announcement.UUID)
        response = response.render()

        disabled_request = self.factory.get(endpoint)
        force_authenticate(disabled_request, user=self.user)
        disabled_response = view(disabled_request, request_uuid=self.ga1.UUID)
        disabled_response = disabled_response.render()

        nonexistent_request = self.factory.get(endpoint)
        force_authenticate(nonexistent_request, user=self.user)
        nonexistent_response = view(nonexistent_request, request_uuid=uuid.uuid4())
        nonexistent_response = nonexistent_response.render()

        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(disabled_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(nonexistent_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_global_announcment_update(self):
        '''Test for the Global Announcment Update EP'''
        view = View.as_view()

        to_update: GlobalAnnouncement = GlobalAnnouncement.objects.get(
            name="panik"
        )
        payload = GlobalAnnouncementSerializer(
            to_update
        ).data
        payload["description"] = "Wait aliens are friendly"

        endpoint = reverse('globalannouncement_view',  kwargs={'request_uuid': to_update.UUID})

        un_privilaged_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request, request_uuid=to_update.UUID)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=to_update.UUID)
        response = response.render()

        malformed_payload = GlobalAnnouncementSerializer(
            to_update
        ).data
        malformed_payload["name"] = True
        malformed_request = self.factory.put(endpoint, malformed_payload, format='json')
        force_authenticate(malformed_request, user=self.privilaged_user)
        malformed_response = view(malformed_request, request_uuid=to_update.UUID)
        malformed_response = malformed_response.render()


        data = json.loads(response.content)
        global_announcements = GlobalAnnouncement.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(malformed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(global_announcements, 2)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_global_announcment_delete(self):
        '''Test for the Global Announcment Delete EP'''
        view = View.as_view()

        to_delete: GlobalAnnouncement = GlobalAnnouncement.objects.get(
            name="panik"
        )

        endpoint = reverse('globalannouncement_view',  kwargs={'request_uuid': to_delete.UUID})

        un_privilaged_request = self.factory.delete(endpoint)
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request, request_uuid=to_delete.UUID)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.delete(endpoint)
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=to_delete.UUID)
        response = response.render()

        global_announcements = GlobalAnnouncement.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(global_announcements, 1)
