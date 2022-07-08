import json
import uuid

from django.urls import reverse

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import SystemACL, Unit, SystemForwarder, TalkGroup, System
from radio.serializers import SystemForwarder, SystemForwarderSerializer
from radio.views.api.system_forwarder import Create, List, View
from radio.helpers.utils import UUIDEncoder
from users.models import CustomUser


class APISystemForwarderTests(APITestCase):
    """
    Tests the System Forwarder API EP
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
            systemACL=self.system_acl1,
            rr_system_id="555",
            enable_talkgroup_acls=True,
            prune_transmissions=False,
            notes=""
        )
        self.system2.save()

        self.tg1: TalkGroup = TalkGroup.objects.create(
            system=self.system1,
            decimal_id=1,
            alpha_tag="tg1",
            description="Talk group 1",
            mode="tdma",
            encrypted=False,
            notes=""
        )
        self.tg1.save()

        self.tg2: TalkGroup = TalkGroup.objects.create(
            system=self.system1,
            decimal_id=2,
            alpha_tag="tg2",
            description="Talk group 2",
            mode="tdma",
            encrypted=False,
            notes=""
        )
        self.tg2.save()

        self.tg3: TalkGroup = TalkGroup.objects.create(
            system=self.system2,
            decimal_id=3,
            alpha_tag="tg3",
            description="Talk group 3",
            mode="tdma",
            encrypted=False,
            notes=""
        )
        self.tg3.save()

        self.unit1: Unit = Unit.objects.create(
            system=self.system1,
            decimal_id=1,
            description=""
        )
        self.unit1.save()

        self.unit2: Unit = Unit.objects.create(
            system=self.system1,
            decimal_id=2,
            description=""
        )
        self.unit2.save()

        self.unit3: Unit = Unit.objects.create(
            system=self.system2,
            decimal_id=3,
            description=""
        )
        self.unit3.save()

        self.system_forwarder1: SystemForwarder = SystemForwarder.objects.create(
            name="system_forwarder1",
            enabled=True,
            recorder_key=uuid.uuid4(),
            remote_url="null.trunkplayer.io",
            forward_incidents=True
        )
        self.system_forwarder1.save()
        self.system_forwarder1.forwarded_systems.add(self.system1)
        self.system_forwarder1.save()

        self.system_forwarder2: SystemForwarder = SystemForwarder.objects.create(
            name="system_forwarder2",
            enabled=False,
            recorder_key=uuid.uuid4(),
            remote_url="null.trunkplayer.io",
            forward_incidents=True
        )
        self.system_forwarder2.save()
        self.system_forwarder2.forwarded_systems.add(self.system1, self.system2)
        self.system_forwarder2.talkgroup_filter.add(self.tg1,self.tg3)
        self.system_forwarder2.save()

        self.system_forwarder3: SystemForwarder = SystemForwarder.objects.create(
            name="system_forwarder3",
            enabled=True,
            recorder_key=uuid.uuid4(),
            remote_url="null.trunkplayer.io",
            forward_incidents=False
        )
        self.system_forwarder3.save()
        self.system_forwarder3.forwarded_systems.add(self.system2)
        self.system_forwarder2.talkgroup_filter.add(self.tg2)
        self.system_forwarder3.save()

    def test_api_system_forwarder_list(self):
        '''Test for the Useralert List EP'''
        view = List.as_view()

        admin_serializer = SystemForwarderSerializer(
            SystemForwarder.objects.all(),
            many=True
        )
       
        endpoint = reverse('systemforwarder_list')

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

        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(admin_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(admin_data["count"], 3)
        self.assertEqual(json.dumps(admin_data["results"]), json.dumps(admin_serializer.data,cls=UUIDEncoder))
      
    def test_api_system_forwarder_create(self):
        '''Test for the User Alert Create EP'''
        view = Create.as_view()

        to_create: SystemForwarder = SystemForwarder(
            name="SystemForwarder4",
            enabled=False,
            recorder_key=uuid.uuid4(),
            remote_url="https://null.trunkplayer.io",
            forward_incidents=False
        )
        payload = SystemForwarderSerializer(
            to_create
        ).data

        payload["forwarded_systems"] = [self.system1.UUID, self.system2.UUID]
        payload["talkgroup_filter"] = [self.tg2]

        endpoint = reverse('systemforwarder_create')

        user1_request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request)
        user1_response = user1_response.render()

        request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request)
        response = response.render()

        data = json.loads(response.content)
        total = SystemForwarder.objects.all().count()

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(total, 4)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))
        

    def test_api_system_forwarder_get(self):
        '''Test for the System Forwarder Get EP'''
        view = View.as_view()

        system_forwarder_payload = SystemForwarderSerializer(self.system_forwarder1).data
        endpoint = reverse('systemforwarder_view',  kwargs={'request_uuid': self.system_forwarder1.UUID})

        admin_request = self.factory.get(endpoint)
        force_authenticate(admin_request, user=self.privilaged_user)
        admin_response = view(admin_request, request_uuid=self.system_forwarder1.UUID)
        admin_response = admin_response.render()

        user1_request = self.factory.get(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.system_forwarder1.UUID)

        
        data = json.loads(admin_response.content)

        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(json.dumps(data), json.dumps(system_forwarder_payload, cls=UUIDEncoder))
 
    def test_api_system_forwarder_update(self):
        '''Test for the System Forwarder Update EP'''
        view = View.as_view()

        payload = SystemForwarderSerializer(
            self.system_forwarder2
        ).data
        payload["enabled"] = False

        endpoint = reverse('systemforwarder_view',  kwargs={'request_uuid': self.system_forwarder2.UUID})

        user1_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.system_forwarder2.UUID)
        user1_response = user1_response.render()

        request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.system_forwarder2.UUID)
        response = response.render()


        data = json.loads(response.content)
       
        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))
      
    def test_api_system_forwarder_delete(self):
        '''Test for the System Forwarder Delete EP'''
        view = View.as_view()

        endpoint = reverse('systemforwarder_view',  kwargs={'request_uuid': self.system_forwarder3.UUID})

        user1_request = self.factory.delete(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.system_forwarder3.UUID)
        user1_response = user1_response.render()

        request = self.factory.delete(endpoint)
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.system_forwarder3.UUID)
        response = response.render()


        total = SystemForwarder.objects.all().count()

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(total,2)
