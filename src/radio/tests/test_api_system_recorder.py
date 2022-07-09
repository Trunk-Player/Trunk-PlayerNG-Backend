import json
import uuid

from django.urls import reverse

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import SystemACL, SystemRecorder, TalkGroup, System
from radio.serializers import SystemForwarderSerializer, SystemRecorderSerializer
from radio.views.api.system_recorder import Create, List, View
from radio.helpers.utils import UUIDEncoder
from users.models import CustomUser


class APISystemRecorderTests(APITestCase):
    """
    Tests the System Recorder API EP
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


        self.system_recorder1: SystemRecorder = SystemRecorder.objects.create(
            system=self.system1,
            name="System Recorder 1",
            site_id="123",
            enabled=False,
            api_key=uuid.uuid4()
        )
        self.system_recorder1.save()
        self.system_recorder1.talkgroups_allowed.add(self.tg1)
        self.system_recorder1.talkgroups_denyed.add(self.tg3)
        self.system_recorder1.save()

        self.system_recorder2: SystemRecorder = SystemRecorder.objects.create(
            system=self.system1,
            name="System Recorder 2",
            site_id="124",
            enabled=True,
            user=self.user2.userProfile,
            api_key=uuid.uuid4()
        )
        self.system_recorder2.save()
        self.system_recorder2.talkgroups_allowed.add(self.tg1)
        self.system_recorder2.talkgroups_denyed.add(self.tg3)
        self.system_recorder2.save()

        self.system_recorder3: SystemRecorder = SystemRecorder.objects.create(
            system=self.system2,
            name="System Recorder 3",
            site_id="245",
            enabled=True,
            user=self.privilaged_user.userProfile,
            api_key=uuid.uuid4()
        )
        self.system_recorder2.save()
        self.system_recorder2.talkgroups_allowed.add(self.tg2)
        self.system_recorder2.talkgroups_denyed.add(self.tg1)
        self.system_recorder2.save()

        

    def test_api_system_recorder_list(self):
        '''Test for the System Recorder List EP'''
        view = List.as_view()

        admin_serializer = SystemRecorderSerializer(
            SystemRecorder.objects.all(),
            many=True
        )
       
        user1_allowed_system_recorders = SystemRecorder.objects.filter(user=self.user.userProfile)
        user1_serializer = SystemRecorderSerializer(
            user1_allowed_system_recorders,
            many=True
        )
        
        user2_allowed_system_recorders = SystemRecorder.objects.filter(user=self.user2.userProfile)
        user2_serializer = SystemRecorderSerializer(
            user2_allowed_system_recorders,
            many=True
        )

        endpoint = reverse('systemrecorder_list')

        admin_request = self.factory.get(endpoint)
        force_authenticate(admin_request, user=self.privilaged_user)
        admin_response = view(admin_request)
        admin_response = admin_response.render()

        user1_request = self.factory.get(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request)
        user1_response = user1_response.render()

        user2_request = self.factory.get(endpoint)
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request)
        user2_response = user2_response.render()

        admin_data = json.loads(admin_response.content)
        user1_data = json.loads(user1_response.content)
        user2_data = json.loads(user2_response.content)

        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_data["count"], 3)
        self.assertEqual(user1_data["count"], 0)
        self.assertEqual(user2_data["count"], 1)
        self.assertEqual(json.dumps(admin_data["results"]), json.dumps(admin_serializer.data,cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data["results"]), json.dumps(user1_serializer.data,cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_data["results"]), json.dumps(user2_serializer.data,cls=UUIDEncoder))

    def test_api_system_recorder_create(self):
        '''Test for the System Recorder Create EP'''
        view = Create.as_view()

        to_create: SystemRecorder = SystemRecorder(
            system=self.system2,
            name="System Recorder 4",
            site_id="777",
            enabled=True,
            api_key=uuid.uuid4()
        )
        payload = SystemRecorderSerializer(
            to_create
        ).data

        payload["talkgroups_allowed"] = [self.tg1.UUID]
        payload["talkgroups_denyed"] = [self.tg2.UUID]

        endpoint = reverse('systemrecorder_create')

        user1_request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request)
        user1_response = user1_response.render()

        request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request)
        response = response.render()

        data = json.loads(response.content)
        total = SystemRecorder.objects.all().count()

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(total, 4)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_system_recorder_get(self):
        '''Test for the System Recorder Get EP'''
        view = View.as_view()

        system_recorder1_payload = SystemRecorderSerializer(self.system_recorder1).data
        system_recorder2_payload = SystemRecorderSerializer(self.system_recorder2).data
        endpoint = reverse('systemrecorder_view',  kwargs={'request_uuid': self.tg1.UUID})

        admin_system_recorder1_request = self.factory.get(endpoint)
        force_authenticate(admin_system_recorder1_request, user=self.privilaged_user)
        admin_system_recorder1_response = view(admin_system_recorder1_request, request_uuid=self.system_recorder1.UUID)
        admin_system_recorder1_response = admin_system_recorder1_response.render()

        user1_system_recorder1_request = self.factory.get(endpoint)
        force_authenticate(user1_system_recorder1_request, user=self.user)
        user1_system_recorder1_response = view(user1_system_recorder1_request, request_uuid=self.system_recorder1.UUID)
        user1_system_recorder1_response = user1_system_recorder1_response.render()

        user2_system_recorder1_request = self.factory.get(endpoint)
        force_authenticate(user2_system_recorder1_request, user=self.user2)
        user2_system_recorder1_response = view(user2_system_recorder1_request, request_uuid=self.system_recorder1.UUID)
        user2_system_recorder1_response = user2_system_recorder1_response.render()


        admin_system_recorder2_request = self.factory.get(endpoint)
        force_authenticate(admin_system_recorder2_request, user=self.privilaged_user)
        admin_system_recorder2_response = view(admin_system_recorder2_request, request_uuid=self.system_recorder2.UUID)
        admin_system_recorder2_response = admin_system_recorder2_response.render()

        user1_system_recorder2_request = self.factory.get(endpoint)
        force_authenticate(user1_system_recorder2_request, user=self.user)
        user1_system_recorder2_response = view(user1_system_recorder2_request, request_uuid=self.system_recorder2.UUID)
        user1_system_recorder2_response = user1_system_recorder2_response.render()

        user2_system_recorder2_request = self.factory.get(endpoint)
        force_authenticate(user2_system_recorder2_request, user=self.user2)
        user2_system_recorder2_response = view(user2_system_recorder2_request, request_uuid=self.system_recorder2.UUID)
        user2_system_recorder2_response = user2_system_recorder2_response.render()


        admin_system_recorder1_data = json.loads(user2_system_recorder1_response.content)
        # user1_system_recorder1_data = json.loads(user2_system_recorder1_response.content)
        user2_system_recorder1_data = json.loads(user2_system_recorder1_response.content)

        admin_system_recorder2_data = json.loads(admin_system_recorder2_response.content)
        # user1_system_recorder2_data = json.loads(user1_system_recorder2_response.content)
        # user2_system_recorder2_data = json.loads(user2_system_recorder2_response.content)

        self.assertEqual(admin_system_recorder1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_system_recorder1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_system_recorder1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(admin_system_recorder2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_system_recorder2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_system_recorder2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.dumps(admin_system_recorder1_data), json.dumps(system_recorder1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_system_recorder1_data), json.dumps(system_recorder1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(admin_system_recorder2_data), json.dumps(system_recorder2_payload, cls=UUIDEncoder))


    def test_api_system_recorder_update(self):
        '''Test for the System Recorder Update EP'''
        view = View.as_view()

        payload = SystemRecorderSerializer(
            self.system_recorder2
        ).data
        payload["enabled"] = False

        endpoint = reverse('systemrecorder_view',  kwargs={'request_uuid': self.system_recorder2.UUID})

        user1_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.system_recorder2.UUID)
        user1_response = user1_response.render()

        request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.system_recorder2.UUID)
        response = response.render()


        data = json.loads(response.content)

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_system_recorder_delete(self):
        '''Test for the System Recorder Delete EP'''
        view = View.as_view()

        endpoint = reverse('systemrecorder_view',  kwargs={'request_uuid': self.system_recorder3.UUID})

        user1_request = self.factory.delete(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.system_recorder3.UUID)
        user1_response = user1_response.render()

        request = self.factory.delete(endpoint)
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.system_recorder3.UUID)
        response = response.render()


        total = SystemRecorder.objects.all().count()

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(total,2)
