import json
import uuid

from django.urls import reverse
from django.utils import timezone
from django.core.files.base import ContentFile

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import Agency, City, SystemACL, SystemRecorder, TalkGroupACL, Unit, Transmission, TalkGroup, System
from radio.serializers import TalkGroupSerializer, TalkGroupViewListSerializer, TransmissionListSerializer
from radio.views.api.talkgroup import Create, List, View
from radio.views.api.talkgroup import TransmissionList
from radio.helpers.utils import UUIDEncoder, get_user_allowed_systems, get_user_allowed_talkgroups_for_systems
from users.models import CustomUser


class APITalkgroupTests(APITestCase):
    """
    Tests the Talkgroup API EP
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
            name="Restricted",
            public=False
        )
        self.system_acl2.save()
        self.system_acl2.users.add(self.user.userProfile)
        self.system_acl2.save()

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

        self.system3: System = System.objects.create(
            name="System3",
            systemACL=self.system_acl1,
            rr_system_id="556",
            enable_talkgroup_acls=False,
            prune_transmissions=False,
            notes=""
        )
        self.system3.save()

        self.system4: System = System.objects.create(
            name="System4",
            systemACL=self.system_acl2,
            rr_system_id="557",
            enable_talkgroup_acls=False,
            prune_transmissions=False,
            notes=""
        )
        self.system4.save()

        self.city: City = City.objects.create(
            name="Dimsdale",
            description="Home to the Dimsdale Dimmadome"
        )
        self.city.save()

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
        self.tg1.agency.add(self.agency)
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
        self.tg2.agency.add(self.agency, self.agency2)
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
        self.tg3.agency.add(self.agency2)
        self.tg3.save()

        self.tg4: TalkGroup = TalkGroup.objects.create(
            system=self.system2,
            decimal_id=4,
            alpha_tag="tg4",
            description="Talk group 4",
            mode="tdma",
            encrypted=False,
            notes=""
        )
        self.tg4.save()
        self.tg4.agency.add(self.agency)
        self.tg4.save()

        self.tg5: TalkGroup = TalkGroup.objects.create(
            system=self.system3,
            decimal_id=5,
            alpha_tag="tg5",
            description="Talk group 5",
            mode="tdma",
            encrypted=False,
            notes=""
        )
        self.tg5.save()
        self.tg5.agency.add(self.agency)
        self.tg5.save()

        self.tg6: TalkGroup = TalkGroup.objects.create(
            system=self.system4,
            decimal_id=6,
            alpha_tag="tg6",
            description="Talk group 6",
            mode="tdma",
            encrypted=False,
            notes=""
        )
        self.tg6.save()
        self.tg6.agency.add(self.agency)
        self.tg6.save()

        self.talkgroup_acl1: TalkGroupACL = TalkGroupACL.objects.create(
            name="System1 user1 access",
            default_new_talkgroups=False,
            default_new_users=False,
            download_allowed=True,
            transcript_allowed=False
        )
        self.talkgroup_acl1.save()
        self.talkgroup_acl1.users.add(self.user.userProfile)
        self.talkgroup_acl1.allowed_talkgroups.add(self.tg1, self.tg3)
        self.talkgroup_acl1.save()

        self.talkgroup_acl2: TalkGroupACL = TalkGroupACL.objects.create(
            name="System1 user2 access",
            default_new_talkgroups=False,
            default_new_users=False,
            download_allowed=True,
            transcript_allowed=False
        )
        self.talkgroup_acl2.save()
        self.talkgroup_acl2.users.add(self.user2.userProfile)
        self.talkgroup_acl2.allowed_talkgroups.add(self.tg2, self.tg4)
        self.talkgroup_acl2.save()

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

        self.recorder1: SystemRecorder = SystemRecorder.objects.create(
            system=self.system1,
            name="Site 1",
            site_id="1",
            enabled=True,
            api_key=uuid.uuid4()
        )
        self.recorder1.save()

        self.recorder2: SystemRecorder = SystemRecorder.objects.create(
            system=self.system2,
            name="Site 2",
            site_id="2",
            enabled=True,
            api_key=uuid.uuid4()
        )
        self.recorder2.save()


        self.transmission1: Transmission = Transmission.objects.create(
            system=self.system1,
            recorder=self.recorder1,
            audio_type="m4a",
            start_time=timezone.now(),
            end_time=timezone.now(),
            audio_file=ContentFile("Junk data"),
            talkgroup=self.tg1,
            encrypted=False,
            emergency=False,
            frequency=856.2125,
            length=5.0,
            locked=False,
            transcript=""
        )
        self.transmission1.save()
        self.transmission1.save()

        self.transmission2: Transmission = Transmission.objects.create(
            system=self.system2,
            recorder=self.recorder2,
            audio_type="m4a",
            start_time=timezone.now(),
            end_time=timezone.now(),
            audio_file=ContentFile("Junk data"),
            talkgroup=self.tg4,
            encrypted=False,
            emergency=False,
            frequency=867.5309,
            length=5.0,
            locked=False,
            transcript=""
        )
        self.transmission2.save()
        self.transmission2.save()

    

        self.transmission3: Transmission = Transmission.objects.create(
            system=self.system3,
            recorder=self.recorder2,
            audio_type="m4a",
            start_time=timezone.now(),
            end_time=timezone.now(),
            audio_file=ContentFile("Junk data"),
            talkgroup=self.tg5,
            encrypted=False,
            emergency=False,
            frequency=867.5309,
            length=5.0,
            locked=False,
            transcript=""
        )
        self.transmission3.save()
        self.transmission3.save()

    def test_api_talkgroup_list(self):
        '''Test for the Talkgroup List EP'''
        view = List.as_view()

        admin_serializer = TalkGroupViewListSerializer(
            TalkGroup.objects.all(),
            many=True
        )
        system_uuids, user1_systems = get_user_allowed_systems(self.user.userProfile.UUID)
        user1_allowed_talkgroups = get_user_allowed_talkgroups_for_systems(
            user1_systems,
            self.user.userProfile.UUID
        )

        user1_serializer = TalkGroupViewListSerializer(
            user1_allowed_talkgroups,
            many=True
        )
        system_uuids, user2_systems = get_user_allowed_systems(self.user2.userProfile.UUID)
        user2_allowed_talkgroups = get_user_allowed_talkgroups_for_systems(
            user2_systems,
            self.user2.userProfile.UUID
        )
        user2_serializer = TalkGroupViewListSerializer(
            user2_allowed_talkgroups,
            many=True
        )
        del system_uuids

        endpoint = reverse('talkgroup_list')

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
        self.assertEqual(admin_data["count"], 6)
        self.assertEqual(user1_data["count"], 4)
        self.assertEqual(user2_data["count"], 3)
        self.assertEqual(json.dumps(admin_data["results"]), json.dumps(admin_serializer.data,cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data["results"]), json.dumps(user1_serializer.data,cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_data["results"]), json.dumps(user2_serializer.data,cls=UUIDEncoder))

    def test_api_talkgroup_create(self):
        '''Test for the Talkgroup Create EP'''
        view = Create.as_view()

        to_create: TalkGroup = TalkGroup(
            system=self.system2,
            decimal_id=6,
            alpha_tag="tg5",
            description="Talkgroup 5",
            mode="tdma",
            encrypted=False,
            notes=""
        )
        payload = TalkGroupSerializer(
            to_create
        ).data
        payload["agency"] = [self.agency2.UUID]
        del payload["UUID"]
        endpoint = reverse('talkgroup_create')

        user1_request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request)
        user1_response = user1_response.render()

        request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request)
        response = response.render()

        malformed_payload = TalkGroupSerializer(
            to_create
        ).data
        malformed_payload["encrypted"] = "no"
        malformed_payload["mode"] = 420
        malformed_request = self.factory.post(endpoint,  malformed_payload, format='json')
        force_authenticate(malformed_request, user=self.privilaged_user)
        malformed_response = view(malformed_request)
        malformed_response = malformed_response.render()

        data = json.loads(response.content)
        del data["UUID"]
        # user1_data = json.loads(user1_response.content)
        total = TalkGroup.objects.all().count()

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(malformed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(total, 7)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_talkgroup_get(self):
        '''Test for the Talkgroup Get EP'''
        view = View.as_view()

        talkgroup1_payload = TalkGroupViewListSerializer(self.tg1).data
        talkgroup2_payload = TalkGroupViewListSerializer(self.tg2).data
        endpoint = reverse('talkgroup_view',  kwargs={'request_uuid': self.tg1.UUID})

        admin_tg1_request = self.factory.get(endpoint)
        force_authenticate(admin_tg1_request, user=self.privilaged_user)
        admin_tg1_response = view(admin_tg1_request, request_uuid=self.tg1.UUID)
        admin_tg1_response = admin_tg1_response.render()

        user1_tg1_request = self.factory.get(endpoint)
        force_authenticate(user1_tg1_request, user=self.user)
        user1_tg1_response = view(user1_tg1_request, request_uuid=self.tg1.UUID)
        user1_tg1_response = user1_tg1_response.render()

        user2_tg1_request = self.factory.get(endpoint)
        force_authenticate(user2_tg1_request, user=self.user2)
        user2_tg1_response = view(user2_tg1_request, request_uuid=self.tg1.UUID)
        user2_tg1_response = user2_tg1_response.render()


        admin_tg2_request = self.factory.get(endpoint)
        force_authenticate(admin_tg2_request, user=self.privilaged_user)
        admin_tg2_response = view(admin_tg2_request, request_uuid=self.tg2.UUID)
        admin_tg2_response = admin_tg2_response.render()

        user1_tg2_request = self.factory.get(endpoint)
        force_authenticate(user1_tg2_request, user=self.user)
        user1_tg2_response = view(user1_tg2_request, request_uuid=self.tg2.UUID)
        user1_tg2_response = user1_tg2_response.render()

        user2_tg2_request = self.factory.get(endpoint)
        force_authenticate(user2_tg2_request, user=self.user2)
        user2_tg2_response = view(user2_tg2_request, request_uuid=self.tg2.UUID)
        user2_tg2_response = user2_tg2_response.render()

        nonexistent_uuid = uuid.uuid4()
        nonexistent_endpoint = reverse('talkgroup_view',  kwargs={'request_uuid': nonexistent_uuid})
        nonexistent_request = self.factory.get(nonexistent_endpoint)
        force_authenticate(nonexistent_request, user=self.privilaged_user)
        nonexistent_response = view(nonexistent_request, request_uuid=nonexistent_uuid)
        nonexistent_response = nonexistent_response.render()


        admin_tg1_data = json.loads(admin_tg1_response.content)
        user1_tg1_data = json.loads(user1_tg1_response.content)
        # user2_tg1_data = json.loads(user2_tg1_response.content)

        admin_tg2_data = json.loads(admin_tg2_response.content)
        # user1_tg2_data = json.loads(user1_tg2_response.content)
        user2_tg2_data = json.loads(user2_tg2_response.content)

        self.assertEqual(admin_tg1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_tg1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_tg1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(admin_tg2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_tg2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_tg2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(nonexistent_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(json.dumps(admin_tg1_data), json.dumps(talkgroup1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_tg1_data), json.dumps(talkgroup1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(admin_tg2_data), json.dumps(talkgroup2_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_tg2_data), json.dumps(talkgroup2_payload, cls=UUIDEncoder))

    def test_api_talkgroup_update(self):
        '''Test for the Talkgroup Update EP'''
        view = View.as_view()

        payload = TalkGroupSerializer(
            self.tg4
        ).data
        payload["mode"] = "analog"
        payload["agency"] = [self.agency.UUID]

        endpoint = reverse('talkgroup_view',  kwargs={'request_uuid': self.tg4.UUID})

        user1_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.tg4.UUID)
        user1_response = user1_response.render()

        request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.tg4.UUID)
        response = response.render()

        malformed_payload = TalkGroupSerializer(
            self.tg4
        ).data
        malformed_payload["encrypted"] = "no"
        malformed_payload["mode"] = 420
        malformed_request = self.factory.put(endpoint,  malformed_payload, format='json')
        force_authenticate(malformed_request, user=self.privilaged_user)
        malformed_response = view(malformed_request, request_uuid=self.tg4.UUID)
        malformed_response = malformed_response.render()

        data = json.loads(response.content)

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(malformed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_talkgroup_delete(self):
        '''Test for the Talkgroup Delete EP'''
        view = View.as_view()

        endpoint = reverse('talkgroup_view',  kwargs={'request_uuid': self.tg2.UUID})

        user1_request = self.factory.delete(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.tg2.UUID)
        user1_response = user1_response.render()

        request = self.factory.delete(endpoint)
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.tg2.UUID)
        response = response.render()


        total = TalkGroup.objects.all().count()

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(total,5)

    def test_api_talkgroup_transmission_list(self):
        '''Test for the Talkgroup Transmission List EP'''
        view = TransmissionList.as_view()

        talkgroup1_payload = TransmissionListSerializer(
            Transmission.objects.filter(talkgroup=self.tg1),
            many=True
        ).data
        talkgroup2_payload = TransmissionListSerializer(
            Transmission.objects.filter(talkgroup=self.tg2),
            many=True
        ).data
        talkgroup4_payload = TransmissionListSerializer(
            Transmission.objects.filter(talkgroup=self.tg4),
            many=True
        ).data
        talkgroup6_payload = TransmissionListSerializer(
            Transmission.objects.filter(talkgroup=self.tg6),
            many=True
        ).data
        endpoint = reverse('talkgroup_transmissions',  kwargs={'request_uuid': self.tg1.UUID})

        admin_tg1_request = self.factory.get(endpoint)
        force_authenticate(admin_tg1_request, user=self.privilaged_user)
        admin_tg1_response = view(admin_tg1_request, request_uuid=self.tg1.UUID)
        admin_tg1_response = admin_tg1_response.render()

        user1_tg1_request = self.factory.get(endpoint)
        force_authenticate(user1_tg1_request, user=self.user)
        user1_tg1_response = view(user1_tg1_request, request_uuid=self.tg1.UUID)
        user1_tg1_response = user1_tg1_response.render()

        user2_tg1_request = self.factory.get(endpoint)
        force_authenticate(user2_tg1_request, user=self.user2)
        user2_tg1_response = view(user2_tg1_request, request_uuid=self.tg1.UUID)
        user2_tg1_response = user2_tg1_response.render()


        admin_tg2_request = self.factory.get(endpoint)
        force_authenticate(admin_tg2_request, user=self.privilaged_user)
        admin_tg2_response = view(admin_tg2_request, request_uuid=self.tg2.UUID)
        admin_tg2_response = admin_tg2_response.render()

        user1_tg2_request = self.factory.get(endpoint)
        force_authenticate(user1_tg2_request, user=self.user)
        user1_tg2_response = view(user1_tg2_request, request_uuid=self.tg2.UUID)
        user1_tg2_response = user1_tg2_response.render()

        user2_tg2_request = self.factory.get(endpoint)
        force_authenticate(user2_tg2_request, user=self.user2)
        user2_tg2_response = view(user2_tg2_request, request_uuid=self.tg2.UUID)
        user2_tg2_response = user2_tg2_response.render()


        admin_tg4_request = self.factory.get(endpoint)
        force_authenticate(admin_tg4_request, user=self.privilaged_user)
        admin_tg4_response = view(admin_tg4_request, request_uuid=self.tg4.UUID)
        admin_tg4_response = admin_tg4_response.render()

        user1_tg4_request = self.factory.get(endpoint)
        force_authenticate(user1_tg4_request, user=self.user)
        user1_tg4_response = view(user1_tg4_request, request_uuid=self.tg4.UUID)
        user1_tg4_response = user1_tg4_response.render()

        user2_tg4_request = self.factory.get(endpoint)
        force_authenticate(user2_tg4_request, user=self.user2)
        user2_tg4_response = view(user2_tg4_request, request_uuid=self.tg4.UUID)
        user2_tg4_response = user2_tg4_response.render()


        admin_tg6_request = self.factory.get(endpoint)
        force_authenticate(admin_tg6_request, user=self.privilaged_user)
        admin_tg6_response = view(admin_tg6_request, request_uuid=self.tg6.UUID)
        admin_tg6_response = admin_tg6_response.render()

        user1_tg6_request = self.factory.get(endpoint)
        force_authenticate(user1_tg6_request, user=self.user)
        user1_tg6_response = view(user1_tg6_request, request_uuid=self.tg6.UUID)
        user1_tg6_response = user1_tg6_response.render()

        user2_tg6_request = self.factory.get(endpoint)
        force_authenticate(user2_tg6_request, user=self.user2)
        user2_tg6_response = view(user2_tg6_request, request_uuid=self.tg6.UUID)
        user2_tg6_response = user2_tg6_response.render()


        nonexistent_request = self.factory.get(endpoint)
        force_authenticate(nonexistent_request, user=self.user2)
        nonexistent_response = view(nonexistent_request, request_uuid=uuid.uuid4())
        nonexistent_response = nonexistent_response.render()


        admin_tg1_data = json.loads(admin_tg1_response.content)
        user1_tg1_data = json.loads(user1_tg1_response.content)
        # user2_tg1_data = json.loads(user2_tg1_response.content)


        admin_tg2_data = json.loads(admin_tg2_response.content)
        # user1_tg2_data = json.loads(user1_tg2_response.content)
        user2_tg2_data = json.loads(user2_tg2_response.content)

        admin_tg4_data = json.loads(admin_tg4_response.content)
        # user1_tg2_data = json.loads(user1_tg2_response.content)
        user2_tg4_data = json.loads(user2_tg4_response.content)

        admin_tg6_data = json.loads(admin_tg6_response.content)
        user1_tg6_data = json.loads(user1_tg6_response.content)
        # user2_tg6_data = json.loads(user2_tg4_response.content)

        self.assertEqual(admin_tg1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_tg1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_tg1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(admin_tg2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_tg2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_tg2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_tg4_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_tg4_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_tg4_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_tg6_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_tg6_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_tg6_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(nonexistent_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(json.dumps(admin_tg1_data["results"]), json.dumps(talkgroup1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_tg1_data["results"]), json.dumps(talkgroup1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(admin_tg2_data["results"]), json.dumps(talkgroup2_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_tg2_data["results"]), json.dumps(talkgroup2_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(admin_tg4_data["results"]), json.dumps(talkgroup4_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_tg4_data["results"]), json.dumps(talkgroup4_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(admin_tg6_data["results"]), json.dumps(talkgroup6_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_tg6_data["results"]), json.dumps(talkgroup6_payload, cls=UUIDEncoder))
