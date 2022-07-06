import json
import uuid

from django.urls import reverse

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import  SystemACL
from radio.serializers import SystemACLSerializer
from radio.views.api.system_acl import Create, List, View
from radio.helpers.utils import UUIDEncoder
from users.models import CustomUser


class APISystemACLTests(APITestCase):
    """
    Tests the System ACL API EP
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

        self.system_acl1: SystemACL = SystemACL.objects.create(
            name="Default",
            public=True
        )
        self.system_acl1.save()

        self.system_acl2: SystemACL = SystemACL.objects.create(
            name="Super top secret",
            public=False
        )
        self.system_acl2.save()
        self.system_acl2.users.add(self.user.userProfile)
        self.system_acl2.save()

        self.system_acl3: SystemACL = SystemACL.objects.create(
            name="Extra Super top secret",
            public=False
        )
        self.system_acl3.save()

    def test_api_system_acl_list(self):
        '''Test for the System ACL List EP'''
        view = List.as_view()

        serializer = SystemACLSerializer(
            SystemACL.objects.all(),
            many=True
        )
        endpoint = reverse('systemacl_list')

        admin_request = self.factory.get(endpoint)
        force_authenticate(admin_request, user=self.privilaged_user)
        admin_response = view(admin_request)
        admin_response = admin_response.render()

        un_privilaged_request = self.factory.get(endpoint)
        force_authenticate(un_privilaged_request, user=self.user2)
        un_privilaged_response = view(un_privilaged_request)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.get(endpoint)
        force_authenticate(request, user=self.user)
        response = view(request)
        response = response.render()

        admin_data = json.loads(admin_response.content)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_data["count"], 3)
        self.assertEqual(json.dumps(admin_data["results"]), json.dumps(serializer.data,cls=UUIDEncoder))

    def test_api_system_acl_create(self):
        '''Test for the System ACL Create EP'''
        view = Create.as_view()

        to_create: SystemACL = SystemACL(
            name="Everyone but greg",
            public=True
        )
        payload = SystemACLSerializer(
            to_create
        ).data

        endpoint = reverse('systemacl_create')

        un_privilaged_request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request)
        response = response.render()

        data = json.loads(response.content)
        system_acls = SystemACL.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(system_acls, 4)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_system_acl_get(self):
        '''Test for the System ACL Get EP'''
        view = View.as_view()

        systemacl: SystemACL = SystemACL.objects.get(
            name="Default",
        )
        payload = SystemACLSerializer(systemacl).data
        endpoint = reverse('systemacl_view',  kwargs={'request_uuid': systemacl.UUID})

        admin_request = self.factory.get(endpoint)
        force_authenticate(admin_request, user=self.privilaged_user)
        admin_response = view(admin_request, request_uuid=systemacl.UUID)
        admin_response = admin_response.render()

        user1_request = self.factory.get(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=systemacl.UUID)
        user1_response = user1_response.render()

        user2_request = self.factory.get(endpoint)
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request, request_uuid=systemacl.UUID)
        user2_response = user2_response.render()

        restricted_systemacl: SystemACL = SystemACL.objects.get(
            name="Super top secret",
        )
        restricted_payload = SystemACLSerializer(restricted_systemacl).data
        endpoint = reverse('systemacl_view',  kwargs={'request_uuid': restricted_systemacl.UUID})

        admin_restricted_request = self.factory.get(endpoint)
        force_authenticate(admin_restricted_request, user=self.privilaged_user)
        admin_restricted_response = view(admin_restricted_request, request_uuid=restricted_systemacl.UUID)
        admin_restricted_response = admin_restricted_response.render()

        user1_restricted_request = self.factory.get(endpoint)
        force_authenticate(user1_restricted_request, user=self.user)
        user1_restricted_response = view(user1_restricted_request, request_uuid=restricted_systemacl.UUID)
        user1_restricted_response = user1_restricted_response.render()

        user2_restricted_request = self.factory.get(endpoint)
        force_authenticate(user2_restricted_request, user=self.user2)
        user2_restricted_response = view(user2_restricted_request, request_uuid=restricted_systemacl.UUID)
        user2_restricted_response = user2_restricted_response.render()

        data = json.loads(admin_response.content)
        restricted_data = json.loads(admin_restricted_response.content)

        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(admin_restricted_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(restricted_data), json.dumps(restricted_payload, cls=UUIDEncoder))

    def test_api_system_acl_update(self):
        '''Test for the City Update EP'''
        view = View.as_view()

        to_update: SystemACL = SystemACL.objects.get(
            name="Default"
        )
        payload = SystemACLSerializer(
            to_update
        ).data
        payload["name"] = "Default New"

        endpoint = reverse('systemacl_view',  kwargs={'request_uuid': to_update.UUID})

        un_privilaged_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request, request_uuid=to_update.UUID)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=to_update.UUID)
        response = response.render()

        data = json.loads(response.content)
        system_acls = SystemACL.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(system_acls, 3)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_system_acl_delete(self):
        '''Test for the city Delete EP'''
        view = View.as_view()

        to_delete: SystemACL = SystemACL.objects.get(
            name="Extra Super top secret"
        )

        endpoint = reverse('systemacl_view',  kwargs={'request_uuid': to_delete.UUID})

        un_privilaged_request = self.factory.delete(endpoint)
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request, request_uuid=to_delete.UUID)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.delete(endpoint)
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=to_delete.UUID)
        response = response.render()

        system_acls = SystemACL.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(system_acls, 2)
