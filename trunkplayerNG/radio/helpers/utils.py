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
    TransmissionFreq,
    Unit,
    TransmissionUnit,
    UserProfile,
)

logger = logging.getLogger(__name__)


class UUIDEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, uuid.UUID):
            return str(o)
        return json.JSONEncoder.default(self, o)


class TransmissionSrc:
    def __init__(self, payload) -> None:
        """
        Transmission Unit Object
        """
        self.src = payload.get("src")
        self.pos = payload.get("pos")
        self.emergency = payload.get("emergency") in ("true", "1", "t")
        self.signal_system = payload.get("signal_system")
        self.tag = payload.get("tag")
        self.time = timezone.datetime.fromtimestamp(payload.get("time")).isoformat()

    def to_json(self) -> dict:
        """
        Return Transission Unit as a dict
        """
        payload = {
            "UUID": uuid.uuid4(),
            "unit": self.src,
            "time": self.time,
            "emergency": self.emergency,
            "signal_system": self.signal_system,
            "tag": self.tag,
        }
        return payload

    def create(self, system) -> str:
        """
        Creates a new Transmission Unit
        """
        unit, created = Unit.objects.get_or_create(
            system=system, decimal_id=int(self.src)
        )
        del created
        unit.save()
        transmission = TransmissionUnit(
            UUID=uuid.uuid4(),
            unit=unit,
            time=self.time,
            pos=self.pos,
            emergency=self.emergency,
            signal_system=self.signal_system,
            tag=self.tag,
        )
        transmission.save()
        return str(transmission.UUID)


class TransmissionFrequency:
    def __init__(self, payload: dict) -> None:
        """
        Transmission Freq Object
        """
        self.freq = payload.get("freq")
        self.pos = payload.get("pos")
        self.len = payload.get("len")
        self.error_count = payload.get("error_count")
        self.spike_count = payload.get("spike_count")
        self.time = timezone.datetime.fromtimestamp(payload.get("time"))

    def to_json(self) -> dict:
        """
        Return Transission Freq as a dict
        """
        payload = {
            "UUID": uuid.uuid4(),
            "freq": self.freq,
            "pos": self.pos,
            "len": self.len,
            "error_count": self.error_count,
            "spike_count": self.spike_count,
            "time": self.time,
        }

        return payload

    def create(self) -> str:
        """
        Create a Transission Freq
        """
        transmission_freq = TransmissionFreq(
            UUID=uuid.uuid4(),
            time=self.time,
            freq=self.freq,
            pos=self.pos,
            len=self.len,
            error_count=self.error_count,
            spike_count=self.spike_count,
        )
        transmission_freq.save()
        return str(transmission_freq.UUID)


class TransmissionDetails:
    def __init__(self, payload) -> None:
        """
        Transmission Details object
        """
        self.system = payload.get("system")
        self.freq = payload.get("freq")
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

        self.freq_list = []
        if "freqList" in payload:
            self.freq_list = [
                TransmissionFrequency(freq) for freq in payload["freqList"]
            ]

        self.src_list = []
        if "srcList" in payload:
            self.src_list = [TransmissionSrc(src) for src in payload["srcList"]]

    def to_json(self) -> dict:
        """
        Convert Transmission Details object to dict
        """
        system: System = System.objects.get(UUID=self.system)

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

        payload["units"] = [unit.create(system) for unit in self.src_list]
        payload["frequencys"] = [Freq.create() for Freq in self.freq_list]

        return payload

    def validate_upload(self, recorder_uuid: str) -> bool:
        """
        Validate that user is allowed to post TG
        """
        recorder: SystemRecorder = SystemRecorder.objects.get(
            api_key=recorder_uuid
        )

        if (
            len(recorder.talkgroups_allowed.all()) > 0
            and len(recorder.talkgroups_denyed.all()) == 0
        ):
            talkgroup = TalkGroup.objects.filter(UUID=self.talkgroup)
            if talkgroup in recorder.talkgroups_allowed.all():
                return True
            else:
                return False
        elif (
            len(recorder.talkgroups_allowed.all()) == 0
            and len(recorder.talkgroups_denyed.all()) > 0
        ):
            talkgroup = TalkGroup.objects.filter(UUID=self.talkgroup)
            if talkgroup in recorder.talkgroups_denyed.all():
                return False
            else:
                return True
        elif (
            len(recorder.talkgroups_allowed.all()) > 0
            and len(recorder.talkgroups_denyed.all()) > 0
        ):
            talkgroup = TalkGroup.objects.filter(UUID=self.talkgroup)
            if talkgroup in recorder.talkgroups_denyed.all():
                return False
            else:
                if talkgroup in recorder.talkgroups_allowed.all():
                    return True
                else:
                    return False
        elif (
            len(recorder.talkgroups_allowed.all()) == 0
            and len(recorder.talkgroups_denyed.all()) == 0
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
