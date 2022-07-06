import json
import uuid

from django.urls import reverse

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import System, SystemACL
from radio.serializers import SystemSerializer
from radio.views.api.system import Create, List, View
from radio.helpers.utils import UUIDEncoder
from users.models import CustomUser


class APISystemTests(APITestCase):
    """
    Tests the System API EP
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

        self.system1: System = System.objects.create(
            name="System1",
            systemACL=self.system_acl1,
            rr_system_id="555",
            enable_talkgroup_acls=True,
            prune_transmissions=False,
            notes=""
        )
        self.system1.save()

        self.system2: System = System.objects.create(
            name="System2",
            systemACL=self.system_acl2,
            rr_system_id="555",
            enable_talkgroup_acls=True,
            prune_transmissions=False,
            notes=""
        )
        self.system2.save()


        self.system3: System = System.objects.create(
            name="System3",
            systemACL=self.system_acl3,
            rr_system_id="555",
            enable_talkgroup_acls=True,
            prune_transmissions=False,
            notes=""
        )
        self.system3.save()

    def test_api_system_list(self):
        '''Test for the System List EP'''
        view = List.as_view()

        serializer = SystemSerializer(
            System.objects.all(),
            many=True
        )
        endpoint = reverse('system_list')

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
        self.assertEqual(user1_data["count"], 2)
        self.assertEqual(user2_data["count"], 1)
        self.assertEqual(admin_data["count"], 3)
        self.assertEqual(json.dumps(admin_data["results"]), json.dumps(serializer.data,cls=UUIDEncoder))

    def test_api_system_create(self):
        '''Test for the System Create EP'''
        view = Create.as_view()

        to_create: System = System(
            name="System4",
            systemACL=self.system_acl3,
            rr_system_id="555",
            enable_talkgroup_acls=True,
            prune_transmissions=False,
            notes=""
        )
        payload = SystemSerializer(
            to_create
        ).data

        endpoint = reverse('system_create')

        un_privilaged_request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request)
        response = response.render()

        data = json.loads(response.content)
        systems = System.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(systems, 4)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_system_get(self):
        '''Test for the System Get EP'''
        view = View.as_view()

        system: System = System.objects.get(
            name="system1",
        )
        payload = SystemSerializer(system).data
        endpoint = reverse('system_view',  kwargs={'request_uuid': system.UUID})

        admin_request = self.factory.get(endpoint)
        force_authenticate(admin_request, user=self.privilaged_user)
        admin_response = view(admin_request, request_uuid=system.UUID)
        admin_response = admin_response.render()

        user1_request = self.factory.get(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=system.UUID)
        user1_response = user1_response.render()

        user2_request = self.factory.get(endpoint)
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request, request_uuid=system.UUID)
        user2_response = user2_response.render()

        restricted_system: System = System.objects.get(
            name="System2",
        )
        restricted_payload = SystemSerializer(restricted_system).data
        endpoint = reverse('system_view',  kwargs={'request_uuid': restricted_system.UUID})

        admin_restricted_request = self.factory.get(endpoint)
        force_authenticate(admin_restricted_request, user=self.privilaged_user)
        admin_restricted_response = view(admin_restricted_request, request_uuid=restricted_system.UUID)
        admin_restricted_response = admin_restricted_response.render()

        user1_restricted_request = self.factory.get(endpoint)
        force_authenticate(user1_restricted_request, user=self.user)
        user1_restricted_response = view(user1_restricted_request, request_uuid=restricted_system.UUID)
        user1_restricted_response = user1_restricted_response.render()

        user2_restricted_request = self.factory.get(endpoint)
        force_authenticate(user2_restricted_request, user=self.user2)
        user2_restricted_response = view(user2_restricted_request, request_uuid=restricted_system.UUID)
        user2_restricted_response = user2_restricted_response.render()

        restricted2_system: System = System.objects.get(
            name="System3",
        )
        restricted2_payload = SystemSerializer(restricted2_system).data
        endpoint = reverse('system_view',  kwargs={'request_uuid': restricted2_system.UUID})

        admin_restricted2_request = self.factory.get(endpoint)
        force_authenticate(admin_restricted2_request, user=self.privilaged_user)
        admin_restricted2_response = view(admin_restricted2_request, request_uuid=restricted2_system.UUID)
        admin_restricted2_response = admin_restricted2_response.render()

        user1_restricted2_request = self.factory.get(endpoint)
        force_authenticate(user1_restricted2_request, user=self.user)
        user1_restricted2_response = view(user1_restricted2_request, request_uuid=restricted2_system.UUID)
        user1_restricted2_response = user1_restricted2_response.render()

        user2_restricted2_request = self.factory.get(endpoint)
        force_authenticate(user2_restricted2_request, user=self.user2)
        user2_restricted2_response = view(user2_restricted2_request, request_uuid=restricted2_system.UUID)
        user2_restricted2_response = user2_restricted2_response.render()

        data = json.loads(admin_response.content)
        user1_data = json.loads(user1_response.content)
        restricted_data = json.loads(admin_restricted_response.content)
        user1_restricted_data = json.loads(user1_restricted_response.content)

        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_restricted_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_restricted_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(admin_restricted2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_restricted2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_restricted2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data), json.dumps(payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(restricted_data), json.dumps(restricted_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_restricted_data), json.dumps(restricted_payload, cls=UUIDEncoder))

    def test_api_system_update(self):
        '''Test for the System Update EP'''
        view = View.as_view()

        to_update: System = System.objects.get(
            name="System1"
        )
        payload = SystemSerializer(
            to_update
        ).data
        payload["notes"] = "NEW NOTES"

        endpoint = reverse('system_view',  kwargs={'request_uuid': to_update.UUID})

        un_privilaged_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request, request_uuid=to_update.UUID)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=to_update.UUID)
        response = response.render()

        data = json.loads(response.content)
        systems = System.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(systems, 3)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_system_delete(self):
        '''Test for the System Delete EP'''
        view = View.as_view()

        to_delete: System = System.objects.get(
            name="System3"
        )

        endpoint = reverse('system_view',  kwargs={'request_uuid': to_delete.UUID})

        un_privilaged_request = self.factory.delete(endpoint)
        force_authenticate(un_privilaged_request, user=self.user)
        un_privilaged_response = view(un_privilaged_request, request_uuid=to_delete.UUID)
        un_privilaged_response = un_privilaged_response.render()

        request = self.factory.delete(endpoint)
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=to_delete.UUID)
        response = response.render()

        systems = System.objects.all().count()

        self.assertEqual(un_privilaged_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(systems, 2)
