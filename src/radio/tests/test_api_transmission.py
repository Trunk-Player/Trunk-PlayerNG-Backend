import json
from time import sleep
import uuid

from django.urls import reverse
from django.utils import timezone
from django.core.files.base import ContentFile

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status

from users.models import CustomUser
from radio.models import (
    Agency,
    City,
    SystemACL,
    SystemRecorder,
    TalkGroupACL,
    TransmissionFreq,
    TransmissionUnit,
    Unit,
    Transmission,
    TalkGroup,
    System
)

from radio.serializers import (
    TransmissionListSerializer,
    TransmissionSerializer
)

from radio.views.api.transmission import (
    Create,
    List,
    View
)

from radio.helpers.utils import (
    UUIDEncoder,
    get_user_allowed_transmissions
)



class APITransmissionTests(APITestCase):
    """
    Tests the Transmission API EP
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
            enable_talkgroup_acls=True,
            prune_transmissions=False,
            notes=""
        )
        self.system4.save()

        self.system5: System = System.objects.create(
            name="System5",
            systemACL=self.system_acl2,
            rr_system_id="558",
            enable_talkgroup_acls=False,
            prune_transmissions=False,
            notes=""
        )
        self.system5.save()

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
        self.tg2.agency.add(self.agency)
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

        self.tg7: TalkGroup = TalkGroup.objects.create(
            system=self.system4,
            decimal_id=7,
            alpha_tag="tg7",
            description="Talk group 7",
            mode="tdma",
            encrypted=False,
            notes=""
        )
        self.tg7.save()
        self.tg7.agency.add(self.agency)
        self.tg7.save()

        self.tg8: TalkGroup = TalkGroup.objects.create(
            system=self.system5,
            decimal_id=8,
            alpha_tag="tg8",
            description="Talk group 8",
            mode="tdma",
            encrypted=False,
            notes=""
        )
        self.tg8.save()
        self.tg8.agency.add(self.agency)
        self.tg8.save()

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
        self.talkgroup_acl2.allowed_talkgroups.add(self.tg2, self.tg4, self.tg6)
        self.talkgroup_acl2.save()

        self.talkgroup_acl3: TalkGroupACL = TalkGroupACL.objects.create(
            name="System4 user1 access",
            default_new_talkgroups=False,
            default_new_users=False,
            download_allowed=True,
            transcript_allowed=False
        )
        self.talkgroup_acl3.save()
        self.talkgroup_acl3.users.add(self.user.userProfile)
        self.talkgroup_acl3.allowed_talkgroups.add(self.tg7)
        self.talkgroup_acl3.save()

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

        self.api_key1 = uuid.uuid4()
        self.recorder1: SystemRecorder = SystemRecorder.objects.create(
            system=self.system1,
            name="Site 1",
            site_id="1",
            enabled=True,
            api_key=self.api_key1
        )
        self.recorder1.save()

        self.api_key2 = uuid.uuid4()
        self.recorder2: SystemRecorder = SystemRecorder.objects.create(
            system=self.system2,
            name="Site 2",
            site_id="2",
            enabled=True,
            api_key=self.api_key2
        )
        self.recorder2.save()

        self.transmission_frequency1: TransmissionFreq = TransmissionFreq.objects.create(
            time=timezone.now(),
            freq=856.2125,
            pos=1,
            len=5.0,
            error_count=0,
            spike_count=1
        )
        self.transmission_frequency1.save()

        self.transmission_unit1: TransmissionUnit = TransmissionUnit.objects.create(
            time=timezone.now(),
            unit=self.unit1,
            pos=1,
            emergency=False,
            signal_system="",
            tag="",
            length=1.2
        )
        self.transmission_unit1.save()

        self.transmission_unit2: TransmissionUnit = TransmissionUnit.objects.create(
            time=timezone.now(),
            unit=self.unit2,
            pos=2,
            emergency=False,
            signal_system="",
            tag="",
            length=3.8
        )
        self.transmission_unit2.save()

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
        self.transmission1.units.add(self.transmission_unit2)
        self.transmission1.frequencys.add(self.transmission_frequency1)
        self.transmission1.save()

        self.transmission_frequency2: TransmissionFreq = TransmissionFreq.objects.create(
            time=timezone.now(),
            freq=867.5309,
            pos=1,
            len=5.0,
            error_count=0,
            spike_count=1
        )
        self.transmission_frequency2.save()

        self.transmission_unit3: TransmissionUnit = TransmissionUnit.objects.create(
            time=timezone.now(),
            unit=self.unit3,
            pos=1,
            emergency=False,
            signal_system="",
            tag="",
            length=1.2
        )
        self.transmission_unit3.save()

        self.transmission_unit4: TransmissionUnit = TransmissionUnit.objects.create(
            time=timezone.now(),
            unit=self.unit1,
            pos=2,
            emergency=False,
            signal_system="",
            tag="",
            length=3.8
        )
        self.transmission_unit4.save()

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
        self.transmission2.units.add(self.transmission_unit3)
        self.transmission2.frequencys.add(self.transmission_frequency2)
        self.transmission2.save()

        self.transmission_frequency3: TransmissionFreq = TransmissionFreq.objects.create(
            time=timezone.now(),
            freq=867.5309,
            pos=1,
            len=5.0,
            error_count=0,
            spike_count=1
        )
        self.transmission_frequency3.save()

        self.transmission_unit5: TransmissionUnit = TransmissionUnit.objects.create(
            time=timezone.now(),
            unit=self.unit3,
            pos=1,
            emergency=False,
            signal_system="",
            tag="",
            length=1.2
        )
        self.transmission_unit5.save()

        self.transmission_unit6: TransmissionUnit = TransmissionUnit.objects.create(
            time=timezone.now(),
            unit=self.unit1,
            pos=2,
            emergency=False,
            signal_system="",
            tag="",
            length=3.8
        )
        self.transmission_unit6.save()

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
        self.transmission3.units.add(self.transmission_unit4)
        self.transmission3.frequencys.add(self.transmission_frequency3)
        self.transmission3.save()

        self.transmission_frequency4: TransmissionFreq = TransmissionFreq.objects.create(
            time=timezone.now(),
            freq=867.5309,
            pos=1,
            len=5.0,
            error_count=0,
            spike_count=1
        )
        self.transmission_frequency4.save()

        self.transmission_unit7: TransmissionUnit = TransmissionUnit.objects.create(
            time=timezone.now(),
            unit=self.unit3,
            pos=1,
            emergency=False,
            signal_system="",
            tag="",
            length=1.2
        )
        self.transmission_unit7.save()

        self.transmission_unit8: TransmissionUnit = TransmissionUnit.objects.create(
            time=timezone.now(),
            unit=self.unit1,
            pos=2,
            emergency=False,
            signal_system="",
            tag="",
            length=3.8
        )
        self.transmission_unit8.save()

        self.transmission4: Transmission = Transmission.objects.create(
            system=self.system4,
            recorder=self.recorder2,
            audio_type="m4a",
            start_time=timezone.now(),
            end_time=timezone.now(),
            audio_file=ContentFile("Junk data"),
            talkgroup=self.tg6,
            encrypted=False,
            emergency=False,
            frequency=867.5309,
            length=5.0,
            locked=False,
            transcript=""
        )
        self.transmission4.save()
        self.transmission4.units.add(self.transmission_unit6)
        self.transmission4.frequencys.add(self.transmission_frequency3)
        self.transmission4.save()

        self.transmission_frequency5: TransmissionFreq = TransmissionFreq.objects.create(
            time=timezone.now(),
            freq=867.5309,
            pos=1,
            len=5.0,
            error_count=0,
            spike_count=1
        )
        self.transmission_frequency5.save()

        self.transmission_unit8: TransmissionUnit = TransmissionUnit.objects.create(
            time=timezone.now(),
            unit=self.unit3,
            pos=1,
            emergency=False,
            signal_system="",
            tag="",
            length=1.2
        )
        self.transmission_unit8.save()

        self.transmission_unit9: TransmissionUnit = TransmissionUnit.objects.create(
            time=timezone.now(),
            unit=self.unit1,
            pos=2,
            emergency=False,
            signal_system="",
            tag="",
            length=3.8
        )
        self.transmission_unit9.save()

        self.transmission5: Transmission = Transmission.objects.create(
            system=self.system4,
            recorder=self.recorder2,
            audio_type="m4a",
            start_time=timezone.now(),
            end_time=timezone.now(),
            audio_file=ContentFile("Junk data"),
            talkgroup=self.tg7,
            encrypted=False,
            emergency=False,
            frequency=867.5309,
            length=5.0,
            locked=False,
            transcript=""
        )
        self.transmission5.save()
        self.transmission5.units.add(self.transmission_unit8)
        self.transmission5.frequencys.add(self.transmission_frequency5)
        self.transmission5.save()

        self.transmission_frequency6: TransmissionFreq = TransmissionFreq.objects.create(
            time=timezone.now(),
            freq=867.5309,
            pos=1,
            len=5.0,
            error_count=0,
            spike_count=1
        )
        self.transmission_frequency5.save()

        self.transmission_unit10: TransmissionUnit = TransmissionUnit.objects.create(
            time=timezone.now(),
            unit=self.unit3,
            pos=1,
            emergency=False,
            signal_system="",
            tag="",
            length=1.2
        )
        self.transmission_unit10.save()

        self.transmission_unit11: TransmissionUnit = TransmissionUnit.objects.create(
            time=timezone.now(),
            unit=self.unit1,
            pos=2,
            emergency=False,
            signal_system="",
            tag="",
            length=3.8
        )
        self.transmission_unit11.save()

        self.transmission6: Transmission = Transmission.objects.create(
            system=self.system5,
            recorder=self.recorder2,
            audio_type="m4a",
            start_time=timezone.now(),
            end_time=timezone.now(),
            audio_file=ContentFile("Junk data"),
            talkgroup=self.tg8,
            encrypted=False,
            emergency=False,
            frequency=867.5309,
            length=5.0,
            locked=False,
            transcript=""
        )
        self.transmission6.save()
        self.transmission6.units.add(self.transmission_unit10)
        self.transmission6.frequencys.add(self.transmission_frequency6)
        self.transmission6.save()

        self.sample_json = {
  "freq": 854187500,
  "start_time": 1652817155,
  "stop_time": 1652817172,
  "emergency": 0,
  "encrypted": 0,
  "call_length": 8,
  "talkgroup": 3071,
  "talkgroup_tag": "Troop HQ Disp 1",
  "audio_type": "digital",
  "short_name": "nesr",
  "freqList": [
    {
      "freq": 854187500,
      "time": 1652817155,
      "pos": 0,
      "len": 8,
      "error_count": 0,
      "spike_count": 0
    }
  ],
  "srcList": [
    {
      "src": 32526,
      "time": 1652817155,
      "pos": 0,
      "emergency": 0,
      "signal_system": "",
      "tag": ""
    },
    {
      "src": 32526,
      "time": 1652817156,
      "pos": 0,
      "emergency": 0,
      "signal_system": "",
      "tag": ""
    },
    {
      "src": 40033,
      "time": 1652817157,
      "pos": 1,
      "emergency": 0,
      "signal_system": "",
      "tag": ""
    },
    {
      "src": 40033,
      "time": 1652817164,
      "pos": 5,
      "emergency": 0,
      "signal_system": "",
      "tag": ""
    },
    {
      "src": 31526,
      "time": 1652817165,
      "pos": 6,
      "emergency": 0,
      "signal_system": "",
      "tag": ""
    },
    {
      "src": 31526,
      "time": 1652817171,
      "pos": 8,
      "emergency": 0,
      "signal_system": "",
      "tag": ""
    }
  ]
}

    def test_api_transmission_list(self):
        '''Test for the Transmission List EP'''
        view = List.as_view()

        admin_serializer = TransmissionListSerializer(
            Transmission.objects.all(),
            many=True
        )

        user1_allowed_talkgroups = get_user_allowed_transmissions(
            self.user.userProfile.UUID
        )
        user1_serializer = TransmissionListSerializer(
            user1_allowed_talkgroups,
            many=True
        )
        
        user2_allowed_talkgroups = get_user_allowed_transmissions(
            self.user2.userProfile.UUID
        )
        user2_serializer = TransmissionListSerializer(
            user2_allowed_talkgroups,
            many=True
        )

        endpoint = reverse('transmission_list')

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
        self.assertEqual(user2_data["count"], 2)
        self.assertEqual(json.dumps(admin_data["results"]), json.dumps(admin_serializer.data,cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data["results"]), json.dumps(user1_serializer.data,cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_data["results"]), json.dumps(user2_serializer.data,cls=UUIDEncoder))

    def test_api_transmission_create(self):
        '''Test for the Transmission Create EP'''
        view = Create.as_view()

        to_create = {
            "recorder": self.api_key1,
            "json": self.sample_json,
            "audio_file": "LITERLAY ANSY ARBATRARY STRING",
            "name": "audio.wav"
        }

        endpoint = reverse('transmission_create')

        authorized_request = self.factory.post(endpoint, to_create, format='json')
        authorized_response = view(authorized_request)
        authorized_response = authorized_response.render()

        to_create2 = {
            "recorder": uuid.uuid4(),
            "json": self.sample_json,
            "audio_file": "ANY ARBATRARY STRING",
            "name": "audio.wav"
        }
        unauthorized_request = self.factory.post(endpoint, to_create2, format='json')
        unauthorized_response = view(unauthorized_request)
        unauthorized_response = unauthorized_response.render()

        data = json.loads(authorized_response.content)
        # user1_data = json.loads(user1_response.content)
        
        # total = Transmission.objects.all().count()

        self.assertEqual(authorized_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(unauthorized_response.status_code, status.HTTP_401_UNAUTHORIZED)
        # self.assertEqual(total, 7)
        # self.assertEqual(json.dumps(data), json.dumps(to_create, cls=UUIDEncoder))

    def test_api_transmission_get(self):
        '''Test for the Transmsion Get EP'''
        view = View.as_view()

        transmission1_payload = TransmissionSerializer(self.transmission1).data
        transmission2_payload = TransmissionSerializer(self.transmission2).data
        endpoint = reverse('transmission_view',  kwargs={'request_uuid': self.transmission1.UUID})

        admin_tx1_request = self.factory.get(endpoint)
        force_authenticate(admin_tx1_request, user=self.privilaged_user)
        admin_tx1_response = view(admin_tx1_request, request_uuid=self.transmission1.UUID)
        admin_tx1_response = admin_tx1_response.render()

        user1_tx1_request = self.factory.get(endpoint)
        force_authenticate(user1_tx1_request, user=self.user)
        user1_tx1_response = view(user1_tx1_request, request_uuid=self.transmission1.UUID)
        user1_tx1_response = user1_tx1_response.render()

        user2_tx1_request = self.factory.get(endpoint)
        force_authenticate(user2_tx1_request, user=self.user2)
        user2_tx1_response = view(user2_tx1_request, request_uuid=self.transmission1.UUID)
        user2_tx1_response = user2_tx1_response.render()


        admin_tx2_request = self.factory.get(endpoint)
        force_authenticate(admin_tx2_request, user=self.privilaged_user)
        admin_tx2_response = view(admin_tx2_request, request_uuid=self.transmission2.UUID)
        admin_tx2_response = admin_tx2_response.render()

        user1_tx2_request = self.factory.get(endpoint)
        force_authenticate(user1_tx2_request, user=self.user)
        user1_tx2_response = view(user1_tx2_request, request_uuid=self.transmission2.UUID)
        user1_tx2_response = user1_tx2_response.render()

        user2_tx2_request = self.factory.get(endpoint)
        force_authenticate(user2_tx2_request, user=self.user2)
        user2_tx2_response = view(user2_tx2_request, request_uuid=self.transmission2.UUID)
        user2_tx2_response = user2_tx2_response.render()


        admin_tx1_data = json.loads(admin_tx1_response.content)
        user1_tx1_data = json.loads(user1_tx1_response.content)
        # user2_tx1_data = json.loads(user2_tx1_response.content)

        admin_tx2_data = json.loads(admin_tx2_response.content)
        # user1_tx2_data = json.loads(user1_tx2_response.content)
        user2_tx2_data = json.loads(user2_tx2_response.content)

        self.assertEqual(admin_tx1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_tx1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_tx1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(admin_tx2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_tx2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_tx2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.dumps(admin_tx1_data), json.dumps(transmission1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_tx1_data), json.dumps(transmission1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(admin_tx2_data), json.dumps(transmission2_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_tx2_data), json.dumps(transmission2_payload, cls=UUIDEncoder))

    def test_api_taransmission_delete(self):
        '''Test for the Transmission Delete EP'''
        view = View.as_view()

        endpoint = reverse('transmission_view',  kwargs={'request_uuid': self.tg2.UUID})

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
        self.assertEqual(total,4)

    # def test_api_talkgroup_transmission_list(self):
    #     '''Test for the Talkgroup Transmission List EP'''
    #     view = TransmissionList.as_view()

    #     talkgroup1_payload = TransmissionListSerializer(
    #         Transmission.objects.filter(talkgroup=self.tg1),
    #         many=True
    #     ).data
    #     talkgroup2_payload = TransmissionListSerializer(
    #         Transmission.objects.filter(talkgroup=self.tg2),
    #         many=True
    #     ).data
    #     talkgroup4_payload = TransmissionListSerializer(
    #         Transmission.objects.filter(talkgroup=self.tg4),
    #         many=True
    #     ).data
    #     endpoint = reverse('talkgroup_transmissions',  kwargs={'request_uuid': self.tg1.UUID})

    #     admin_tg1_request = self.factory.get(endpoint)
    #     force_authenticate(admin_tg1_request, user=self.privilaged_user)
    #     admin_tg1_response = view(admin_tg1_request, request_uuid=self.tg1.UUID)
    #     admin_tg1_response = admin_tg1_response.render()

    #     user1_tg1_request = self.factory.get(endpoint)
    #     force_authenticate(user1_tg1_request, user=self.user)
    #     user1_tg1_response = view(user1_tg1_request, request_uuid=self.tg1.UUID)
    #     user1_tg1_response = user1_tg1_response.render()

    #     user2_tg1_request = self.factory.get(endpoint)
    #     force_authenticate(user2_tg1_request, user=self.user2)
    #     user2_tg1_response = view(user2_tg1_request, request_uuid=self.tg1.UUID)
    #     user2_tg1_response = user2_tg1_response.render()


    #     admin_tg2_request = self.factory.get(endpoint)
    #     force_authenticate(admin_tg2_request, user=self.privilaged_user)
    #     admin_tg2_response = view(admin_tg2_request, request_uuid=self.tg2.UUID)
    #     admin_tg2_response = admin_tg2_response.render()

    #     user1_tg2_request = self.factory.get(endpoint)
    #     force_authenticate(user1_tg2_request, user=self.user)
    #     user1_tg2_response = view(user1_tg2_request, request_uuid=self.tg2.UUID)
    #     user1_tg2_response = user1_tg2_response.render()

    #     user2_tg2_request = self.factory.get(endpoint)
    #     force_authenticate(user2_tg2_request, user=self.user2)
    #     user2_tg2_response = view(user2_tg2_request, request_uuid=self.tg2.UUID)
    #     user2_tg2_response = user2_tg2_response.render()


    #     admin_tg4_request = self.factory.get(endpoint)
    #     force_authenticate(admin_tg4_request, user=self.privilaged_user)
    #     admin_tg4_response = view(admin_tg4_request, request_uuid=self.tg4.UUID)
    #     admin_tg4_response = admin_tg4_response.render()

    #     user1_tg4_request = self.factory.get(endpoint)
    #     force_authenticate(user1_tg4_request, user=self.user)
    #     user1_tg4_response = view(user1_tg4_request, request_uuid=self.tg4.UUID)
    #     user1_tg4_response = user1_tg4_response.render()

    #     user2_tg4_request = self.factory.get(endpoint)
    #     force_authenticate(user2_tg4_request, user=self.user2)
    #     user2_tg4_response = view(user2_tg4_request, request_uuid=self.tg4.UUID)
    #     user2_tg4_response = user2_tg4_response.render()


    #     admin_tg1_data = json.loads(admin_tg1_response.content)
    #     user1_tg1_data = json.loads(user1_tg1_response.content)
    #     # user2_tg1_data = json.loads(user2_tg1_response.content)


    #     admin_tg2_data = json.loads(admin_tg2_response.content)
    #     # user1_tg2_data = json.loads(user1_tg2_response.content)
    #     user2_tg2_data = json.loads(user2_tg2_response.content)

    #     admin_tg4_data = json.loads(admin_tg4_response.content)
    #     # user1_tg2_data = json.loads(user1_tg2_response.content)
    #     user2_tg4_data = json.loads(user2_tg4_response.content)

    #     self.assertEqual(admin_tg1_response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(user1_tg1_response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(user2_tg1_response.status_code, status.HTTP_403_FORBIDDEN)
    #     self.assertEqual(admin_tg2_response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(user1_tg2_response.status_code, status.HTTP_403_FORBIDDEN)
    #     self.assertEqual(user2_tg2_response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(admin_tg4_response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(user1_tg4_response.status_code, status.HTTP_403_FORBIDDEN)
    #     self.assertEqual(user2_tg4_response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(json.dumps(admin_tg1_data["results"]), json.dumps(talkgroup1_payload, cls=UUIDEncoder))
    #     self.assertEqual(json.dumps(user1_tg1_data["results"]), json.dumps(talkgroup1_payload, cls=UUIDEncoder))
    #     self.assertEqual(json.dumps(admin_tg2_data["results"]), json.dumps(talkgroup2_payload, cls=UUIDEncoder))
    #     self.assertEqual(json.dumps(user2_tg2_data["results"]), json.dumps(talkgroup2_payload, cls=UUIDEncoder))
    #     self.assertEqual(json.dumps(admin_tg4_data["results"]), json.dumps(talkgroup4_payload, cls=UUIDEncoder))
    #     self.assertEqual(json.dumps(user2_tg4_data["results"]), json.dumps(talkgroup4_payload, cls=UUIDEncoder))
