import json
import uuid

from django.urls import reverse

from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.test import force_authenticate
from rest_framework import status


from radio.models import SystemACL, Unit, UserAlert, TalkGroup, System
from radio.serializers import UserAlertSerializer
from radio.views.api.user_alert import Create, List, View
from radio.helpers.utils import UUIDEncoder
from users.models import CustomUser


class APIUserAlertTests(APITestCase):
    """
    Tests the User Alert API EP
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
            system=self.system1,
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
            system=self.system1,
            decimal_id=3,
            description=""
        )
        self.unit3.save()

        self.user1_alert1: UserAlert = UserAlert.objects.create(
            name="user1_alert1",
            user=self.user.userProfile,
            enabled=True,
            description="User 1's 'Alert 1'",
            web_notification=True,
            app_rise_notification=False,
            app_rise_urls="<URL>,<URL>",
            emergency_only=False,
            count=5,
            trigger_time=30
        )
        self.user1_alert1.save()
        self.user1_alert1.talkgroups.add(self.tg1, self.tg3)
        self.user1_alert1.units.add(self.unit3, self.unit2)
        self.user1_alert1.save()


        self.user1_alert2: UserAlert = UserAlert.objects.create(
            name="user1_alert2",
            user=self.user.userProfile,
            enabled=True,
            description="User 1's 'Alert 2'",
            web_notification=True,
            app_rise_notification=True,
            app_rise_urls="<URL>,<URL>",
            emergency_only=True,
            count=1,
            trigger_time=10
        )
        self.user1_alert2.save()
        self.user1_alert1.talkgroups.add(self.tg2, self.tg3)
        self.user1_alert1.save()

        self.user2_alert1: UserAlert = UserAlert.objects.create(
            name="user2_alert1",
            user=self.user2.userProfile,
            enabled=True,
            description="User 2's 'Alert 1'",
            web_notification=True,
            app_rise_notification=False,
            app_rise_urls="<URL>,<URL>",
            emergency_only=False,
            count=5,
            trigger_time=30
        )
        self.user2_alert1.save()
        self.user2_alert1.units.add(self.unit3, self.unit1)
        self.user2_alert1.save()

        self.admin_alert1: UserAlert = UserAlert.objects.create(
            name="admin_alert1",
            user=self.privilaged_user.userProfile,
            enabled=False,
            description="Admin's 'Alert 1'",
            web_notification=True,
            app_rise_notification=False,
            app_rise_urls="<URL>,<URL>",
            emergency_only=False,
            count=5,
            trigger_time=30
        )
        self.admin_alert1.save()
        self.user1_alert1.talkgroups.add(self.tg2, self.tg1, self.tg3)
        self.admin_alert1.units.add(self.unit3, self.unit2, self.unit1)
        self.admin_alert1.save()

        self.admin_alert2: UserAlert = UserAlert.objects.create(
            name="admin_alert2",
            user=self.privilaged_user.userProfile,
            enabled=True,
            description="Admin's 'Alert 2'",
            web_notification=True,
            app_rise_notification=False,
            app_rise_urls="<URL>,<URL>",
            emergency_only=False,
            count=5,
            trigger_time=30
        )
        self.admin_alert2.save()

    def test_api_user_alert_list(self):
        '''Test for the Useralert List EP'''
        view = List.as_view()

        admin_serializer = UserAlertSerializer(
            UserAlert.objects.all(),
            many=True
        )
        user1_serializer = UserAlertSerializer(
            UserAlert.objects.filter(user=self.user.userProfile),
            many=True
        )
        user2_serializer = UserAlertSerializer(
            UserAlert.objects.filter(user=self.user2.userProfile),
            many=True
        )
        endpoint = reverse('users_alerts_list')

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
        self.assertEqual(admin_data["count"], 5)
        self.assertEqual(json.dumps(admin_data["results"]), json.dumps(admin_serializer.data,cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data["results"]), json.dumps(user1_serializer.data,cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_data["results"]), json.dumps(user2_serializer.data,cls=UUIDEncoder))

    def test_api_user_alert_create(self):
        '''Test for the User Alert Create EP'''
        view = Create.as_view()

        to_create: UserAlert = UserAlert(
            name="Created",
            user=self.user.userProfile,
            enabled=False,
            description="Created via API",
            web_notification=True,
            app_rise_notification=False,
            app_rise_urls="<URL>,<URL>",
            emergency_only=False,
            count=5,
            trigger_time=30
        )
        payload = UserAlertSerializer(
            to_create
        ).data

        endpoint = reverse('users_alerts_create')

        user1_request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request)
        user1_response = user1_response.render()

        payload["UUID"] = uuid.uuid4()
        request = self.factory.post(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request)
        response = response.render()

        data = json.loads(response.content)
        user1_data = json.loads(user1_response.content)
        total_useralerts = UserAlert.objects.all().count()

        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(total_useralerts, 7)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data), json.dumps(payload, cls=UUIDEncoder))

    def test_api_user_alert_get(self):
        '''Test for the User Alert Get EP'''
        view = View.as_view()

        user1_alert1_payload = UserAlertSerializer(self.user1_alert1).data
        endpoint = reverse('users_alerts_view',  kwargs={'request_uuid': self.user1_alert1.UUID})

        admin_request = self.factory.get(endpoint)
        force_authenticate(admin_request, user=self.privilaged_user)
        admin_response = view(admin_request, request_uuid=self.user1_alert1.UUID)
        admin_response = admin_response.render()

        user1_request = self.factory.get(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.user1_alert1.UUID)
        user1_response = user1_response.render()

        user2_request = self.factory.get(endpoint)
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request, request_uuid=self.user1_alert1.UUID)
        user2_response = user2_response.render()

        admin_alert1_payload = UserAlertSerializer(self.admin_alert1).data
        endpoint = reverse('system_view',  kwargs={'request_uuid': self.admin_alert1.UUID})

        admin_restricted_request = self.factory.get(endpoint)
        force_authenticate(admin_restricted_request, user=self.privilaged_user)
        admin_restricted_response = view(admin_restricted_request, request_uuid=self.admin_alert1.UUID)
        admin_restricted_response = admin_restricted_response.render()

        user1_restricted_request = self.factory.get(endpoint)
        force_authenticate(user1_restricted_request, user=self.user)
        user1_restricted_response = view(user1_restricted_request, request_uuid=self.admin_alert1.UUID)
        user1_restricted_response = user1_restricted_response.render()

        user2_restricted_request = self.factory.get(endpoint)
        force_authenticate(user2_restricted_request, user=self.user2)
        user2_restricted_response = view(user2_restricted_request, request_uuid=self.admin_alert1.UUID)
        user2_restricted_response = user2_restricted_response.render()


        data = json.loads(admin_response.content)
        user1_data = json.loads(user1_response.content)
        restricted_data = json.loads(admin_restricted_response.content)

        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(admin_restricted_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(json.dumps(data), json.dumps(user1_alert1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user1_data), json.dumps(user1_alert1_payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(restricted_data), json.dumps(admin_alert1_payload, cls=UUIDEncoder))
        

    def test_api_user_alert_update(self):
        '''Test for the User Alert Update EP'''
        view = View.as_view()

        payload = UserAlertSerializer(
            self.user2_alert1
        ).data
        payload["enabled"] = False
        payload["description"] = "Ahoy"

        endpoint = reverse('system_view',  kwargs={'request_uuid': self.user2_alert1.UUID})

        user1_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.user2_alert1.UUID)
        user1_response = user1_response.render()

        user2_request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request, request_uuid=self.user2_alert1.UUID)
        user2_response = user2_response.render()


        payload["description"] = "Admin overide"
        request = self.factory.put(endpoint, payload, format='json')
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.user2_alert1.UUID)
        response = response.render()


        restricted_payload = UserAlertSerializer(
            self.admin_alert1
        ).data
        restricted_payload["enabled"] = True
        restricted_payload["description"] = "Ahoy"

        user1_restricted_request = self.factory.put(endpoint, restricted_payload, format='json')
        force_authenticate(user1_restricted_request, user=self.user)
        user1_restricted_response = view(user1_restricted_request, request_uuid=self.admin_alert1.UUID)
        user1_restricted_response = user1_restricted_response.render()

        user2_restricted_request = self.factory.put(endpoint, restricted_payload, format='json')
        force_authenticate(user2_restricted_request, user=self.user)
        user2_restricted_response = view(user2_restricted_request, request_uuid=self.admin_alert1.UUID)
        user2_restricted_response = user2_restricted_response.render()

        restricted_request = self.factory.put(endpoint, restricted_payload, format='json')
        force_authenticate(restricted_request, user=self.privilaged_user)
        restricted_response = view(restricted_request, request_uuid=self.admin_alert1.UUID)
        restricted_response = restricted_response.render()

        data = json.loads(response.content)
        restricted_data = json.loads(restricted_response.content)
        user2_data = json.loads(response.content)
        user_alerts = UserAlert.objects.all().count()

        self.assertEqual(user1_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user1_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(restricted_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user_alerts, 5)
        self.assertEqual(json.dumps(data), json.dumps(payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(user2_data), json.dumps(payload, cls=UUIDEncoder))
        self.assertEqual(json.dumps(restricted_data), json.dumps(restricted_payload, cls=UUIDEncoder))

    def test_api_user_alert_delete(self):
        '''Test for the User Alert Delete EP'''
        view = View.as_view()

        endpoint = reverse('system_view',  kwargs={'request_uuid': self.user1_alert2.UUID})

        user2_request = self.factory.delete(endpoint)
        force_authenticate(user2_request, user=self.user2)
        user2_response = view(user2_request, request_uuid=self.user1_alert2.UUID)
        user2_response = user2_response.render()

        user1_request = self.factory.delete(endpoint)
        force_authenticate(user1_request, user=self.user)
        user1_response = view(user1_request, request_uuid=self.user1_alert2.UUID)
        user1_response = user1_response.render()

        request = self.factory.delete(endpoint)
        force_authenticate(request, user=self.privilaged_user)
        response = view(request, request_uuid=self.user1_alert2.UUID)
        response = response.render()


        user1_restricted_request = self.factory.delete(endpoint)
        force_authenticate(user1_restricted_request, user=self.user)
        user1_restricted_response = view(user1_restricted_request, request_uuid=self.admin_alert1.UUID)
        user1_restricted_response = user1_restricted_response.render()

        user2_restricted_request = self.factory.delete(endpoint)
        force_authenticate(user2_restricted_request, user=self.user)
        user2_restricted_response = view(user2_restricted_request, request_uuid=self.admin_alert1.UUID)
        user2_restricted_response = user2_restricted_response.render()

        restricted_request = self.factory.delete(endpoint)
        force_authenticate(restricted_request, user=self.privilaged_user)
        restricted_response = view(restricted_request, request_uuid=self.admin_alert1.UUID)
        restricted_response = restricted_response.render()

        user_alerts = UserAlert.objects.all().count()

        self.assertEqual(user1_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(user2_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(user1_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user2_restricted_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(restricted_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(user_alerts, 3)
