from datetime import datetime, timedelta
import uuid
from xml.dom.pulldom import default_bufsize
from django.core.management.base import BaseCommand, CommandError

from gevent import monkey
import requests

monkey.patch_all()


from radio.models import (
    SystemACL,
    System,
    City,
    Agency,
    TalkGroup,
    SystemForwarder,
    SystemRecorder,
    Transmission,
    Incident,
    TalkGroupACL,
    ScanList,
    Scanner,
    GlobalAnnouncement,
    GlobalEmailTemplate,
    UserAlert
)

from users.models import CustomUser


#############################################################
# Main Command
#############################################################
class Command(BaseCommand):
    help = "Generates/Removes Junk data for api testing"

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action='store_true', help="Confirm this is really what you want todo", required=True)
        parser.add_argument("--rr_username", required=True)
        parser.add_argument("--rr_password", required=True)

    def handle(self, *args, **options):
        from radio.helpers.radioreference import RR

        #############################################################
        # Users
        #############################################################
        
        
        user1_pass = str(uuid.uuid4())
        user1_email = "admin@trunkplayer.io"
        user2_pass = str(uuid.uuid4())
        user2_email = "user2@trunkplayer.io"
        user3_pass = str(uuid.uuid4())
        user3_email = "user3@trunkplayer.io"
        user4_pass = str(uuid.uuid4())
        user4_email = "user4@trunkplayer.io"

        # Superuser Account
        user1:CustomUser = CustomUser.objects.create_user(
            email=user1_email, password=user1_pass
        )
        user1.is_superuser = True
        user1.is_active = True
        user1.userProfile.site_admin = True
        user1.save()

        # Site Admin Account
        user2:CustomUser = CustomUser.objects.create_user(
            email=user2_email, password=user2_pass
        )
        user2.is_superuser = False
        user2.is_active = True
        user2.userProfile.site_admin = True
        user2.save()

        # Standard Account
        user3:CustomUser = CustomUser.objects.create_user(
            email=user3_email, password=user3_pass
        )
        user3.is_superuser = False
        user3.is_active = True
        user3.userProfile.site_admin = False
        user3.save()

        # Standard Account
        user4:CustomUser = CustomUser.objects.create_user(
            email=user4_email, password=user4_pass
        )
        user4.is_superuser = False
        user4.is_active = True
        user4.userProfile.site_admin = False
        user4.save()

        self.stdout.write(
            self.style.SUCCESS(f"""
API USER LOGINS:
    User 1 (SuperUser): 
        Email: {user1_email}
        Pass: {user1_pass}
    User 2 (Site Admin): 
        Email: {user2_email}
        Pass: {user2_pass}
    User 3 (Standard User) [Access to Restriced System ACL]: 
        Email: {user3_email}
        Pass: {user3_pass}
    User 4 (Standard User): 
        Email: {user4_email}
        Pass: {user4_pass}
            """)
        )

        #############################################################
        # System ACLs
        #############################################################
        # All access public ACL
        default_acl: SystemACL = SystemACL.objects.create(
            UUID=uuid.uuid4(),
            name='Default2', public=True
        )
        default_acl.save()
        self.stdout.write(self.style.SUCCESS("[+] Created Default System ACL"))

        # Restriced access ACL (Granted to User3)
        restricted_acl: SystemACL = SystemACL.objects.create(
            UUID=uuid.uuid4(),
            name='restricted', public=False
        )
        restricted_acl.save()
        restricted_acl.users.add(user3.userProfile)
        restricted_acl.save()
        self.stdout.write(self.style.SUCCESS("[+] Created Restricted System ACL"))

        #############################################################
        # Systems
        #############################################################

        system1: System = System.objects.create(
            UUID=uuid.uuid4(),
            name = "Nebraska State Radio System",
            systemACL = default_acl,
            rr_system_id = "6699",
            enable_talkgroup_acls = True,
            prune_transmissions = False,
            notes = '# System Notes\n**Markdown Ready**'
        )
        system1.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created System - {system1.name}"))

        system2: System = System.objects.create(
            UUID=uuid.uuid4(),
            name = "Lancaster County",
            systemACL = restricted_acl,
            rr_system_id = "12040",
            enable_talkgroup_acls = True,
            prune_transmissions = False,
            notes = '# System Notes\n**Markdown Ready**'
        )
        system2.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created System - {system2.name}"))

        system3: System = System.objects.create(
            UUID=uuid.uuid4(),
            name = "Omaha Regional Interoperability Network",
            systemACL = restricted_acl,
            rr_system_id = "2361",
            enable_talkgroup_acls = False,
            prune_transmissions = False,
            notes = '# System Notes\n**Markdown Ready**'
        )
        system3.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created System - {system3.name}"))

        #############################################################
        # Cities
        #############################################################

        city1: City = City.objects.create(
            UUID=uuid.uuid4(),
            name = "Lincoln",
            description = "Lincoln, Nebraska"
        )
        city1.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created City - {city1.name}"))

        city2: City = City.objects.create(
            UUID=uuid.uuid4(),
            name = "Omaha",
            description = "Omaha, Nebraska"
        )
        city2.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created City - {city2.name}"))

        city3: City = City.objects.create(
            UUID=uuid.uuid4(),
            name = "Waverly",
            description = "Waverly, Nebraska"
        )
        city3.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created City - {city3.name}"))

        #############################################################
        # Agencies
        #############################################################

        agency1: Agency = Agency.objects.create(
            UUID=uuid.uuid4(),
            name = "LFR",
            description = "Lincoln Fire Rescue"
        )
        agency1.save()
        agency1.city.add(city1)
        agency1.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created Agency - {agency1.name}"))

        agency2: Agency = Agency.objects.create(
            UUID=uuid.uuid4(),
            name = "OPD",
            description = "Omhah Police Department"
        )
        agency2.save()
        agency2.city.add(city2)
        self.stdout.write(self.style.SUCCESS(f"[+] Created Agency - {agency2.name}"))

        agency3: Agency = Agency.objects.create(
            UUID=uuid.uuid4(),
            name = "NSP",
            description = "Nebraska State Patrol"
        )
        agency3.save()
        agency3.city.add(city1, city2, city3)
        agency3.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created Agency - {agency3.name}"))

        agency4: Agency = Agency.objects.create(
            UUID=uuid.uuid4(),
            name = "LES",
            description = "Lincoln Eletric Systems"
        )
        agency4.save()
        agency4.city.add(city1, city3)
        agency4.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created Agency - {agency4.name}"))

        #############################################################
        # Talkgroups (Import here because im lazy)
        #############################################################

        system1_rr = RR(system1.rr_system_id, options["rr_username"], options["rr_password"])
        system2_rr = RR(system2.rr_system_id,  options["rr_username"], options["rr_password"])
        system3_rr = RR(system3.rr_system_id,  options["rr_username"], options["rr_password"])

        system1_rr.load_system(system1.UUID)
        self.stdout.write(self.style.SUCCESS(f"[+] Importing Talkgroups for - {system1.name}"))
        system2_rr.load_system(system2.UUID)
        self.stdout.write(self.style.SUCCESS(f"[+] Importing Talkgroups for - {system2.name}"))
        system3_rr.load_system(system3.UUID)
        self.stdout.write(self.style.SUCCESS(f"[+] Importing Talkgroups for - {system3.name}"))
        
        # Add some agencies to talkgoups
        LFR: TalkGroup = TalkGroup.objects.filter(alpha_tag__icontains="Lincoln FD")
        for tg in LFR:
            tg.agency.add(agency1)
            tg.save()

        NSP: TalkGroup = TalkGroup.objects.filter(alpha_tag__icontains="Troop")
        for tg in NSP:
            tg.agency.add(agency3)
            tg.save()


        #############################################################
        # System Forwarders
        #############################################################

        system_forwarder1: SystemForwarder = SystemForwarder.objects.create(
            name = "example1.io Forwarder",
            enabled=False,
            recorder_key=uuid.uuid4(),
            remote_url="https://example1.io/apiv1/",
            forward_incidents = True
        )
        system_forwarder1.save()
        system_forwarder1.forwarded_systems.add(system1, system3)
        system_forwarder1.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created System Forwarder - {system_forwarder1.name}"))

        system_forwarder2: SystemForwarder = SystemForwarder.objects.create(
            name = "example2.io Forwarder",
            enabled=False,
            recorder_key=uuid.uuid4(),
            remote_url="https://example2.io/apiv1/",
            forward_incidents = False
        )
        system_forwarder2.save()
        system_forwarder2.forwarded_systems.add(system1, system2)
        system_forwarder2.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created System Forwarder - {system_forwarder2.name}"))

        #############################################################
        # System Recorders
        #############################################################

        system_recorder1_api_key = uuid.uuid4()
        system_recorder1: SystemRecorder = SystemRecorder.objects.create(
            system = system1,
            name = "Lincoln South Site",
            site_id = '23549',
            enabled=True,
            user=user2.userProfile,
            api_key=system_recorder1_api_key
        )
        system_recorder1.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created System Recorder - {system_recorder1.name}"))

        system_recorder2_api_key = uuid.uuid4()
        system_recorder2: SystemRecorder = SystemRecorder.objects.create(
            system = system2,
            name = "Lancaster County Simulcast",
            site_id = '41074',
            enabled=True,
            user=user3.userProfile,
            api_key=system_recorder2_api_key
        )
        system_recorder2.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created System Recorder - {system_recorder2.name}"))

        system_recorder3_api_key = uuid.uuid4()
        system_recorder3: SystemRecorder = SystemRecorder.objects.create(
            system = system3,
            name = "Douglas County Simulcast",
            site_id = '8306',
            enabled=True,
            user=user4.userProfile,
            api_key=system_recorder3_api_key
        )
        system_recorder3.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created System Recorder - {system_recorder3.name}"))

        self.stdout.write(
            self.style.SUCCESS(f"""
System Recorder API Keys:
    System Recorder 1: 
        API KEY: {system_recorder1_api_key}
    System Recorder 2: 
        API KEY: {system_recorder2_api_key}
    System Recorder 3: 
        API KEY: {system_recorder3_api_key}
            """)
        )

        #############################################################
        # Transmissions
        #############################################################
        from radio.helpers.transmission import _new_transmission_handler

        transmission1_payload = {
            "recorder": system_recorder2_api_key,
            "json": {
                "freq": 859212500,
                "start_time": 1654886359,
                "stop_time": 1654886361,
                "emergency": 0,
                "encrypted": 0,
                "call_length": 2,
                "talkgroup": 12502,
                "talkgroup_tag": "Lincoln FD 2 Tac",
                "talkgroup_description": "Fire 2 Tac",
                "talkgroup_group_tag": "Fire-Tac",
                "talkgroup_group": "Lincoln",
                "audio_type": "digital tdma",
                "short_name": "nesr",
                "freqList": [
                    {
                    "freq": 859212500,
                    "time": 1654886359,
                    "pos": 0,
                    "len": 1.8,
                    "error_count": "0",
                    "spike_count": "0"
                    }
                ],
                "play_length": 1.8,
                "source": 0,
                "srcList": [
                    {
                    "src": 203616,
                    "time": 1654886359,
                    "pos": 0,
                    "emergency": 0,
                    "signal_system": "",
                    "tag": ""
                    }
                ]
                },
            "audio_file": "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S0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS7/8QpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpd+EIUtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS8=",
            "UUID": uuid.uuid4(),
            "name": "tx1.m4a",
        }
        transmission1 = _new_transmission_handler(transmission1_payload)
        transmission1: Transmission = Transmission.objects.get(UUID=transmission1["UUID"])
        self.stdout.write(self.style.SUCCESS(f"[+] Created Transmission - {str(transmission1)}"))

        transmission2_payload = {
            "recorder": system_recorder2_api_key,
            "json": {
                "freq": 857712500,
                "start_time": 1654872894,
                "stop_time": 1654872934,
                "emergency": 0,
                "encrypted": 0,
                "call_length": 40,
                "talkgroup": 12841,
                "talkgroup_tag": "Bryan Med West",
                "talkgroup_description": "Bryan Medical Center West",
                "talkgroup_group_tag": "Hospital",
                "talkgroup_group": "Lincoln",
                "audio_type": "digital tdma",
                "short_name": "nesr",
                "freqList": [
                    {
                    "freq": 857712500,
                    "time": 1654872894,
                    "pos": 0,
                    "len": 39.84,
                    "error_count": "0",
                    "spike_count": "0"
                    }
                ],
                "play_length": 39.84,
                "source": 0,
                "srcList": [
                    {
                    "src": 231780,
                    "time": 1654872894,
                    "pos": 0,
                    "emergency": 0,
                    "signal_system": "",
                    "tag": ""
                    }
                ]
                },
            "audio_file": "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S0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS7/8QpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpd+EIUtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS8=",
            "UUID": uuid.uuid4(),
            "name": "tx2.m4a"
        }
        transmission2 = _new_transmission_handler(transmission2_payload)
        transmission2: Transmission = Transmission.objects.get(UUID=transmission2["UUID"])
        self.stdout.write(self.style.SUCCESS(f"[+] Created Transmission - {str(transmission2)}"))

        transmission3_payload = {
            "recorder": system_recorder1_api_key,
            "name": "tx3.m4a",
            "json": {
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
                },
            "audio_file": "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S0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS7/8QpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpaWlpd+EIUtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS8=",
            "UUID": uuid.uuid4()
        }
        transmission3 = _new_transmission_handler(transmission3_payload)
        transmission3: Transmission = Transmission.objects.get(UUID=transmission3["UUID"])
        self.stdout.write(self.style.SUCCESS(f"[+] Created Transmission - {str(transmission3)}"))


        #############################################################
        # Incidents
        #############################################################
        incident1_time = datetime.now()-timedelta(days=5)
        incident1: Incident = Incident.objects.create(
            active=False,
            time=incident1_time,
            system=system1,
            name = "Major I80 Accident",
            description="**Markdown Valid**"
        )
        incident1.save()
        incident1.transmission.add(transmission1, transmission3)
        incident1.agency.add(agency1, agency3)
        incident1.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created Incident - {incident1.name}"))

        incident2_time = datetime.now()-timedelta(minutes=5)
        incident2: Incident = Incident.objects.create(
            active=True,
            time=incident2_time,
            system=system1,
            name = "Transformer at substation blew",
            description="**Markdown Valid**"
        )
        incident2.save()
        incident2.transmission.add(transmission2)
        incident2.agency.add(agency4)
        incident2.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created Incident - {incident2.name}"))

        incident3_time = datetime.now()-timedelta(minutes=15)
        incident3: Incident = Incident.objects.create(
            active=True,
            time=incident3_time,
            system=system2,
            name = "Drug Bust",
            description="**Markdown Valid**"
        )
        incident3.save()
        incident3.agency.add(agency2)
        incident3.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created Incident - {incident3.name}"))

        #############################################################
        # TalkGroup ACLs
        #############################################################

        default_talkgroup_acl: TalkGroupACL = TalkGroupACL.objects.create(
            name="Default TG ACL",
            default_new_talkgroups = True,
            default_new_users = True,
            download_allowed=False,
            transcript_allowed = False
        )
        default_talkgroup_acl.save()
        default_talkgroup_acl.users.add(user1.userProfile, user2.userProfile, user3.userProfile, user4.userProfile)
        default_talkgroup_acl.allowed_talkgroups.add(*TalkGroup.objects.filter(system=system1))
        default_talkgroup_acl.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created Talkgroup ACL - {default_talkgroup_acl.name}"))

        restricted_talkgroup_acl: TalkGroupACL = TalkGroupACL.objects.create(
            name="Default TG ACL",
            default_new_talkgroups = True,
            default_new_users = False,
            download_allowed=False,
            transcript_allowed = False
        )
        restricted_talkgroup_acl.save()
        restricted_talkgroup_acl.users.add(user1.userProfile, user2.userProfile, user3.userProfile)
        restricted_talkgroup_acl.allowed_talkgroups.add(*TalkGroup.objects.filter(system=system2))
        restricted_talkgroup_acl.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created Talkgroup ACL - {restricted_talkgroup_acl.name}"))

        #############################################################
        # Scanlists
        #############################################################

        default_scanlist: ScanList = ScanList.objects.create(
            owner=user1.userProfile,
            name="Default",
            description="**MARKDOWN READY**",
            public=True,
            community_shared = False,
            notes = "**MARKDOWN READY**"
        )
        default_scanlist.save()
        default_scanlist.talkgroups.add(*TalkGroup.objects.all())
        default_scanlist.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created scanlist - {default_scanlist.name}"))

        scanlist2: ScanList = ScanList.objects.create(
            owner=user2.userProfile,
            name="User2's Shared",
            description="**MARKDOWN READY**",
            public=False,
            community_shared = True,
            notes = "**MARKDOWN READY**"
        )
        scanlist2.save()
        scanlist2.talkgroups.add(*TalkGroup.objects.filter(system=system1))
        scanlist2.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created scanlist - {scanlist2.name}"))

        scanlist3: ScanList = ScanList.objects.create(
            owner=user3.userProfile,
            name="User3's LFR Scanlist",
            description="**MARKDOWN READY**",
            public=False,
            community_shared = False,
            notes = "**MARKDOWN READY**"
        )
        scanlist3.save()
        scanlist3.talkgroups.add(*TalkGroup.objects.filter(alpha_tag__icontains="Lincoln FD"))
        scanlist3.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created scanlist - {scanlist3.name}"))

        scanlist4: ScanList = ScanList.objects.create(
            owner=user2.userProfile,
            name="NSP",
            description="**MARKDOWN READY**",
            public=True,
            community_shared = False,
            notes = "**MARKDOWN READY**"
        )
        scanlist4.save()
        scanlist4.talkgroups.add(*TalkGroup.objects.filter(alpha_tag__icontains="Troop"))
        scanlist4.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created scanlist - {scanlist4.name}"))

        #############################################################
        # Scanners
        #############################################################
        scanner1: Scanner = Scanner.objects.create(
            owner=user1.userProfile,
            name="NSP/LFR",
            description="**MARKDOWN READY**",
            public=True,
            community_shared = False,
            notes = "**MARKDOWN READY**"
        )
        scanner1.save()
        scanner1.scanlists.add(scanlist3,scanlist4)
        scanner1.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created scanner - {scanner1.name}"))

        scanner2: Scanner = Scanner.objects.create(
            owner=user1.userProfile,
            name="Kitchen Sink",
            description="**MARKDOWN READY**",
            public=True,
            community_shared = False,
            notes = "**MARKDOWN READY**"
        )
        scanner2.save()
        scanner2.scanlists.add(default_scanlist, scanlist2, scanlist3,scanlist4)
        scanner2.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created scanner - {scanner2.name}"))

        #############################################################
        # Global Announcements
        #############################################################
        
        global_announcement1: GlobalAnnouncement = GlobalAnnouncement.objects.create(
            name = "THIS IS AN ANNOUNCEMENT",
            enabled=True,
            description="**MARKDOWN READY**"
        )
        global_announcement1.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created global announcement - {global_announcement1.name}"))

        global_announcement2: GlobalAnnouncement = GlobalAnnouncement.objects.create(
            name = "THIS IS AN DISABLED ANNOUNCEMENT",
            enabled=False,
            description="**MARKDOWN READY**"
        )
        global_announcement2.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created global announcement - {global_announcement2.name}"))

        #############################################################
        # User Alerts
        #############################################################
        
        user_alert1: UserAlert = UserAlert.objects.create(
            user=user1.userProfile,
            name="NSP Activity",
            enabled = True,
            description="**MARKDOWN READY**",
            web_notification=True,
            app_rise_notification=False,
            app_rise_urls="<URL>,<URL>,<URL>",
            emergency_only = False,
            count = 1,
            trigger_time = 10,
            title="New Activity Alert for NSP",
            body="New Activity on %T - %I"
        )   
        user_alert1.save()
        user_alert1.talkgroups.add(*TalkGroup.objects.filter(alpha_tag__icontains="Troop"))
        user_alert1.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created user alert - {user_alert1.name}"))

        user_alert2: UserAlert = UserAlert.objects.create(
            user=user3.userProfile,
            name="LFR Activity",
            enabled = True,
            description="**MARKDOWN READY**",
            web_notification=True,
            app_rise_notification=False,
            app_rise_urls="<URL>,<URL>,<URL>",
            emergency_only = False,
            count = 1,
            trigger_time = 10,
            title="New Activity Alert for NSP",
            body="New Activity on %T - %I"
        )   
        user_alert2.save()
        user_alert2.talkgroups.add(*TalkGroup.objects.filter(alpha_tag__icontains="Lincoln FD"))
        user_alert2.save()
        self.stdout.write(self.style.SUCCESS(f"[+] Created user alert - {user_alert2.name}"))
