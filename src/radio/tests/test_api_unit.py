import json
import uuid

from django.urls import reverse

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import SystemACL, Unit, System
from radio.serializers import UnitSerializer
from radio.views.api.unit import Create, List, View
from radio.helpers.utils import UUIDEncoder, get_user_allowed_systems
from users.models import CustomUser

# Ba dum tissss
class APIUnitTests(APITestCase):
    """
    Tests the Unit API EP
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
            systemACL=self.system_acl2,
            rr_system_id="555",
            enable_talkgroup_acls=True,
            prune_transmissions=False,
            notes=""
        )
        self.system2.save()

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

    def test_api_unit_list(self):
        '''Test for the Unit List EP'''
        view = List.as_view()

        admin_serializer = UnitSerializer(
            Unit.objects.all(),
            many=True
        )

        user1_system_uuids, user1_allowed_systems = get_user_allowed_systems(self.user.userProfile.UUID)
        del user1_allowed_systems
        user1_serializer = UnitSerializer(
            Unit.objects.filter(system__in=user1_system_uuids),
            many=True
        )

        user2_system_uuids, user2_allowed_systems = get_user_allowed_systems(self.user2.userProfile.UUID)
        del user2_allowed_systems
        user2_serializer = UnitSerializer(
            Unit.objects.filter(system__in=user2_system_uuids),
            many=True
        )

        endpoint = reverse('unit_list')

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
        self.assertEqual(user1_data["count"], 3)
        self.assertEqual(user2_data["count"], 2)
        self.assertEqual(json.dumps(admin_data["results"]), json.dumps(admin_serializer.data,cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data["results"]), json.dumps(user1_serializer.data,cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_data["results"]), json.dumps(user2_serializer.data,cls=UUIDEncoder))

    def test_api_unit_create(self):
        '''Test for the Unit Create EP'''
        view = Create.as_view()

        to_create: Unit = Unit(
            system=self.system2,
            decimal_id=5,
            description=""
        )
        payload = UnitSerializer(
            to_create
        ).data

        endpoint = reverse('unit_create')

        user1_request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request)
        user1_response = user1_response.render()

        request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request)
        response = response.render()

        data = json.loads(response.content)
        total = Unit.objects.all().count()

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(total, 4)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_unit_get(self):
        '''Test for the System Recorder Get EP'''
        view = View.as_view()

        unit1_payload = UnitSerializer(self.unit1).data
        unit3_payload = UnitSerializer(self.unit3).data
        endpoint = reverse('unit_view',  kwargs={'request_uuid': self.unit1.UUID})

        admin_unit1_request = self.factory.get(endpoint)
        force_authenticate(admin_unit1_request, user=self.privilaged_user)
        admin_unit1_response = view(admin_unit1_request, request_uuid=self.unit1.UUID)
        admin_unit1_response = admin_unit1_response.render()

        user1_unit1_request = self.factory.get(endpoint)
        force_authenticate(user1_unit1_request, user=self.user)
        user1_unit1_response = view(user1_unit1_request, request_uuid=self.unit1.UUID)
        user1_unit1_response = user1_unit1_response.render()

        user2_unit1_request = self.factory.get(endpoint)
        force_authenticate(user2_unit1_request, user=self.user2)
        user2_unit1_response = view(user2_unit1_request, request_uuid=self.unit1.UUID)
        user2_unit1_response = user2_unit1_response.render()


        admin_unit3_request = self.factory.get(endpoint)
        force_authenticate(admin_unit3_request, user=self.privilaged_user)
        admin_unit3_response = view(admin_unit3_request, request_uuid=self.unit3.UUID)
        admin_unit3_response = admin_unit3_response.render()

        user1_unit3_request = self.factory.get(endpoint)
        force_authenticate(user1_unit3_request, user=self.user)
        user1_unit3_response = view(user1_unit3_request, request_uuid=self.unit3.UUID)
        user1_unit3_response = user1_unit3_response.render()

        user2_unit3_request = self.factory.get(endpoint)
        force_authenticate(user2_unit3_request, user=self.user2)
        user2_unit3_response = view(user2_unit3_request, request_uuid=self.unit3.UUID)
        user2_unit3_response = user2_unit3_response.render()


        admin_unit1_data = json.loads(admin_unit1_response.content)
        user1_unit1_data = json.loads(user2_unit1_response.content)
        user2_unit1_data = json.loads(user2_unit1_response.content)

        admin_unit3_data = json.loads(admin_unit3_response.content)
        user1_unit3_data = json.loads(user1_unit3_response.content)
        # user2_unit3_data = json.loads(user2_unit3_response.content)

        self.assertEqual(admin_unit1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_unit1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_unit1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_unit3_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_unit3_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_unit3_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(json.dumps(admin_unit1_data), json.dumps(unit1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_unit1_data), json.dumps(unit1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_unit1_data), json.dumps(unit1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(admin_unit3_data), json.dumps(unit3_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_unit3_data), json.dumps(unit3_payload, cls=UUIDEncoder))

    def test_api_unit_update(self):
        '''Test for the Unit Update EP'''
        view = View.as_view()

        payload = UnitSerializer(
            Unit.objects.get(decimal_id=2)
        ).data
        payload["description"] = "Bacon"

        endpoint = reverse('unit_view',  kwargs={'request_uuid': self.unit2.UUID})

        user1_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.unit2.UUID)
        user1_response = user1_response.render()

        request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.unit2.UUID)
        response = response.render()


        data = json.loads(response.content)

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_unit_delete(self):
        '''Test for the Unit Delete EP'''
        view = View.as_view()

        endpoint = reverse('unit_view',  kwargs={'request_uuid': self.unit1.UUID})

        user1_request = self.factory.delete(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.unit1.UUID)
        user1_response = user1_response.render()

        request = self.factory.delete(endpoint)
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.unit1.UUID)
        response = response.render()


        total = Unit.objects.all().count()

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(total,2)
