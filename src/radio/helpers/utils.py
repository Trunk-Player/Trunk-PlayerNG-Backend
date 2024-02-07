import hashlib
import uuid
import logging
import json

from django.utils import timezone
from django.db.models import Q


from radio.models import (
    System,
    SystemACL,
    SystemRecorder,
    TalkGroup,
    TalkGroupACL,
    Transmission,
    Unit,
    UserProfile,
)
from radio.serializers import UnitSerializer

logger = logging.getLogger(__name__)

class UUIDEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, uuid.UUID):
            return str(o)
        return json.JSONEncoder.default(self, o)

class TransmissionDetails:
    def __init__(self, payload) -> None:
        """
        Transmission Details object
        """
        self.system:System = System.objects.get(UUID=payload.get("system"))
        self.freq = payload.get("freq")
        self.audio_type = payload.get("audio_type")
        self.call_length = payload.get("call_length")
        self.talkgroup = payload.get("talkgroup")
        self.talkgroup_tag = payload.get("talkgroup_tag", str(self.talkgroup))
        self.source = payload.get("source")

        self.start_time = timezone.datetime.fromtimestamp(
            payload.get("start_time")
        ).isoformat()
        self.stop_time = timezone.datetime.fromtimestamp(
            payload.get("stop_time")
        ).isoformat()

        self.emergency = payload.get("emergency") in ("true", "1", "t")
        self.encrypted = payload.get("encrypted") in ("true", "1", "t")

        self.freq_list =  payload["freqList"]
        
        self.src_list = payload["srcList"]

        for src in self.src_list:
            unit, created = Unit.objects.get_or_create(
                system=self.system, decimal_id=int(src["src"])
            )
            unit.save()

            src["decimal_id"] = src["src"]
            src["UUID"] = str(uuid.uuid5(
                uuid.NAMESPACE_DNS,
                hashlib.blake2b(json.dumps(src).encode()).hexdigest()
            ))
            unit_serializer = UnitSerializer(unit)
            src["unit"] = json.loads(json.dumps(unit_serializer.data, cls=UUIDEncoder))

            print(src)
       

    def to_json(self) -> dict:
        """
        Convert Transmission Details object to dict
        """
        system: System = self.system

        if self.talkgroup_tag == "-":
            alphatag = self.talkgroup
        else:
            alphatag = self.talkgroup_tag

        if TalkGroup.objects.filter(decimal_id=self.talkgroup, system=system):
            talkgroup = TalkGroup.objects.get(decimal_id=self.talkgroup, system=system)
            created = False
        else:
            talkgroup, created = TalkGroup.objects.get_or_create(
                decimal_id=self.talkgroup, system=system, alpha_tag=alphatag
            )
            talkgroup.save()

        if created:
            for acl in TalkGroupACL.objects.filter(default_new_users=True):
                acl: TalkGroupACL
                acl.allowed_talkgroups.add(talkgroup)
                acl.save()

        payload = {
            "audio_type": self.audio_type,
            "start_time": self.start_time,
            "end_time": self.stop_time,
            "talkgroup": str(talkgroup.UUID),
            "encrypted": self.encrypted,
            "emergency": self.emergency,
            "units": [],
            "frequencys": [],
            "frequency": self.freq,
            "length": self.call_length,
        }

        payload["units"] = self.src_list
        payload["frequencys"] = self.freq_list

        return payload

    def validate_upload(self, recorder_uuid: str) -> bool:
        """
        Validate that user is allowed to post TG
        """
        recorder: SystemRecorder = SystemRecorder.objects.get(
            api_key=recorder_uuid
        )

        talkgroups_allowed = recorder.talkgroups_allowed.all()
        talkgroups_denyed = recorder.talkgroups_denyed.all()
        talkgroup = TalkGroup.objects.filter(UUID=self.talkgroup)

        if (
            len(talkgroups_allowed) > 0
            and len(talkgroups_denyed) == 0
        ):
            if talkgroup in talkgroups_allowed:
                return True
            else:
                return False
        elif (
            len(talkgroups_allowed) == 0
            and len(talkgroups_denyed) > 0
        ):
            if talkgroup in talkgroups_denyed:
                return False
            else:
                return True
        elif (
            len(talkgroups_allowed) > 0
            and len(talkgroups_denyed) > 0
        ):
            if talkgroup in talkgroups_denyed:
                return False
            else:
                if talkgroup in talkgroups_allowed:
                    return True
                else:
                    return False
        elif (
            len(talkgroups_allowed) == 0
            and len(talkgroups_denyed) == 0
        ):
            return True


def get_user_allowed_systems(user_uuid: str) -> tuple[list, list]:
    """
    Gets the systems that the user is allowed to access
    """
    user_acls = SystemACL.objects.filter(Q(users__UUID=user_uuid) | Q(public=True))
    systems = System.objects.filter(systemACL__in=user_acls)
    system_uuids = list(systems.values_list("UUID", flat=True))
    return system_uuids, systems


def get_user_allowed_talkgroups(system: System, user_uuid: str) -> list:
    """
    Gets the talkgroups that the user is allowed to access
    """
    if not system.enable_talkgroup_acls:
        return TalkGroup.objects.filter(system=system)

    acls = TalkGroupACL.objects.filter(users__UUID=user_uuid)
    allowed = list(acls.values_list("allowed_talkgroups__UUID", flat=True))
    allowed_talkgropups = TalkGroup.objects.filter(UUID__in=allowed)

    return allowed_talkgropups

def get_user_allowed_talkgroups_for_systems(systems: list[System], user_uuid: str) -> list:
    """
    Gets the talkgroups that the user is allowed to access
    """
    non_acl_talkgroups = TalkGroup.objects.filter(system__in=systems, system__enable_talkgroup_acls=False)
    acls = TalkGroupACL.objects.filter(users__UUID=user_uuid)
    allowed = list(acls.values_list("allowed_talkgroups__UUID", flat=True))
    acl_talkgroups = TalkGroup.objects.filter(UUID__in=allowed)

    return non_acl_talkgroups | acl_talkgroups


def user_allowed_to_access_transmission(
    transmission: Transmission, user_uuid: str
) -> list:
    """
    Returs bool if user can access Transmission
    """

    user:UserProfile = UserProfile.objects.get(UUID=user_uuid)
    if user.site_admin:
        return True

    allowed_tgs = get_user_allowed_talkgroups(transmission.system, user_uuid=user_uuid)

    if transmission.talkgroup in allowed_tgs:
        return True

    return False


def get_user_allowed_download_talkgroups(system: System, user_uuid: str) -> list:
    """
    Returns talkgroups user can download
    """
    if not system.enable_talkgroup_acls:
        return TalkGroup.objects.filter(system=system)

    acls = TalkGroupACL.objects.filter(users__UUID=user_uuid, download_allowed=True)
    allowed = list(acls.values_list("allowed_talkgroups__UUID", flat=True))
    allowed_talkgropups = TalkGroup.objects.filter(UUID__in=allowed)

    return allowed_talkgropups


def user_allowed_to_download_transmission(
    transmission: Transmission, user_uuid: str
) -> list:
    """
    Returns whether a user can download a transmission
    """
    allowed_tgs = get_user_allowed_download_talkgroups(
        transmission.system, user_uuid=user_uuid
    )

    if transmission.talkgroup in allowed_tgs:
        return True

    return False

def get_user_allowed_transmissions(user_uuid: str) -> list:
    system_uuids, systems = get_user_allowed_systems(user_uuid)
    del system_uuids
    allowed_transmissions_non_acl = Transmission.objects.none()
    allowed_transmissions_acl = Transmission.objects.none()

    for system in systems:
        system: System
        if system.enable_talkgroup_acls:
            talkgroups_allowed = get_user_allowed_talkgroups(system, user_uuid)
            allowed_transmissions_acl = allowed_transmissions_acl | Transmission.objects.filter(
                    system=system, talkgroup__in=talkgroups_allowed
                )
        else:
            allowed_transmissions_non_acl = allowed_transmissions_non_acl | Transmission.objects.filter(system=system)
    allowed_transmissions = allowed_transmissions_acl | allowed_transmissions_non_acl 

    return allowed_transmissions

def validate_upload(talkgroup_decimalid: str, recorder: SystemRecorder) -> bool:
    """
    Validate that user is allowed to post TG
    """

    talkgroups_allowed = recorder.talkgroups_allowed.all().count()
    talkgroups_denyed = recorder.talkgroups_denyed.all().count()
    talkgroup = TalkGroup.objects.filter(decimal_id=talkgroup_decimalid, system=recorder.system)

    if (
        talkgroups_allowed > 0
        and talkgroups_denyed == 0
    ):
        if talkgroup in talkgroups_allowed:
            return True
        else:
            return False
    elif (
        talkgroups_allowed == 0
        and talkgroups_denyed > 0
    ):
        if talkgroup in talkgroups_denyed:
            return False
        else:
            return True
    elif (
        talkgroups_allowed > 0
        and talkgroups_denyed > 0
    ):
        if talkgroup in talkgroups_denyed:
            return False
        else:
            if talkgroup in talkgroups_allowed:
                return True
            else:
                return False
    elif (
        talkgroups_allowed == 0
        and talkgroups_denyed == 0
    ):
        return True
