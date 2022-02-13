import uuid, logging, json

from django.utils import timezone
from django.conf import settings
from django.db.models import Q

from uuid import UUID

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

if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


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

    def _to_json(self) -> dict:
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

    def _create(self, system) -> str:
        """
        Creates a new Transmission Unit
        """
        unit, created = Unit.objects.get_or_create(
            system=system, decimalID=int(self.src)
        )
        unit.save()
        TXS = TransmissionUnit(
            UUID=uuid.uuid4(),
            unit=unit,
            time=self.time,
            pos=self.pos,
            emergency=self.emergency,
            signal_system=self.signal_system,
            tag=self.tag,
        )
        TXS.save()
        return str(TXS.UUID)


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

    def _to_json(self) -> dict:
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

    def _create(self) -> str:
        """
        Create a Transission Freq
        """
        TF = TransmissionFreq(
            UUID=uuid.uuid4(),
            time=self.time,
            freq=self.freq,
            pos=self.pos,
            len=self.len,
            error_count=self.error_count,
            spike_count=self.spike_count,
        )
        TF.save()
        return str(TF.UUID)


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
        self.play_length = payload.get("play_length")
        self.source = payload.get("source")

        self.start_time = timezone.datetime.fromtimestamp(
            payload.get("start_time")
        ).isoformat()
        self.stop_time = timezone.datetime.fromtimestamp(
            payload.get("stop_time")
        ).isoformat()

        self.emergency = payload.get("emergency") in ("true", "1", "t")
        self.encrypted = payload.get("encrypted") in ("true", "1", "t")

        if "freqList" in payload:
            self.freqList = [
                TransmissionFrequency(freq) for freq in payload["freqList"]
            ]

        if "srcList" in payload:
            self.srcList = [TransmissionSrc(src) for src in payload["srcList"]]

    def _to_json(self) -> dict:
        """
        Convert Transmission Details object to dict
        """
        system: System = System.objects.get(UUID=self.system)

        if self.talkgroup_tag == "-":
            alphatag = self.talkgroup
        else:
            alphatag = self.talkgroup_tag

        if TalkGroup.objects.filter(decimalID=self.talkgroup, system=system):
            Talkgroup = TalkGroup.objects.get(decimalID=self.talkgroup, system=system)
            created = False
        else:
            Talkgroup, created = TalkGroup.objects.get_or_create(
                decimalID=self.talkgroup, system=system, alphaTag=alphatag
            )
            Talkgroup.save()

        if created:
            for acl in TalkGroupACL.objects.filter(defaultNewTalkgroups=True):
                acl: TalkGroupACL
                acl.allowedTalkgroups.add(Talkgroup)
                acl.save()

        payload = {
            "startTime": self.start_time,
            "endTime": self.stop_time,
            "talkgroup": str(Talkgroup.UUID),
            "encrypted": self.encrypted,
            "emergency": self.emergency,
            "units": [],
            "frequencys": [],
            "frequency": self.freq,
            "length": self.call_length,
        }

        payload["units"] = [unit._create(system) for unit in self.srcList]
        payload["frequencys"] = [Freq._create() for Freq in self.freqList]

        return payload

    def validate_upload(self, recorderUUID: str) -> bool:
        """
        Validate that user is allowed to post TG
        """
        system: System = System.objects.get(UUID=self.system)
        recorder: SystemRecorder = SystemRecorder.objects.get(
            forwarderWebhookUUID=recorderUUID
        )

        if (
            len(recorder.talkgroupsAllowed.all()) > 0
            and len(recorder.talkgroupsDenyed.all()) == 0
        ):
            talkgroup = TalkGroup.objects.filter(UUID=self.talkgroup)
            if talkgroup in recorder.talkgroupsAllowed.all():
                return True
            else:
                return False
        elif (
            len(recorder.talkgroupsAllowed.all()) == 0
            and len(recorder.talkgroupsDenyed.all()) > 0
        ):
            talkgroup = TalkGroup.objects.filter(UUID=self.talkgroup)
            if talkgroup in recorder.talkgroupsDenyed.all():
                return False
            else:
                return True
        elif (
            len(recorder.talkgroupsAllowed.all()) > 0
            and len(recorder.talkgroupsDenyed.all()) > 0
        ):
            talkgroup = TalkGroup.objects.filter(UUID=self.talkgroup)
            if talkgroup in recorder.talkgroupsDenyed.all():
                return False
            else:
                if talkgroup in recorder.talkgroupsAllowed.all():
                    return True
                else:
                    return False
        elif (
            len(recorder.talkgroupsAllowed.all()) == 0
            and len(recorder.talkgroupsDenyed.all()) == 0
        ):
            return True


def get_user_allowed_systems(UserUUID: str) -> tuple[list, list]:
    userACLs = SystemACL.objects.filter(Q(users__UUID=UserUUID) | Q(public=True))
    Systems = System.objects.filter(systemACL__in=userACLs)
    systemUUIDs = [system.UUID for system in Systems]
    return systemUUIDs, Systems


def get_user_allowed_talkgroups(System: System, UserUUID: str) -> list:
    if not System.enableTalkGroupACLs:
        return TalkGroup.objects.filter(system=System)

    ACLs = TalkGroupACL.objects.filter(users__UUID=UserUUID)
    Allowed = list(ACLs.values_list("allowedTalkgroups__UUID", flat=True))
    AllowedTalkgropups = TalkGroup.objects.filter(UUID__in=Allowed)

    return AllowedTalkgropups


def user_allowed_to_access_transmission(
    Transmission: Transmission, UserUUID: str
) -> list:
    allowed_tgs = get_user_allowed_talkgroups(Transmission.system, UserUUID=UserUUID)

    if Transmission.talkgroup in allowed_tgs:
        return True

    return False


def get_user_allowed_download_talkgroups(System: System, UserUUID: str) -> list:
    if not System.enableTalkGroupACLs:
        return TalkGroup.objects.filter(system=System)

    ACLs = TalkGroupACL.objects.filter(users__UUID=UserUUID, downloadAllowed=True)
    Allowed = list(ACLs.values_list("allowedTalkgroups__UUID", flat=True))
    AllowedTalkgropups = TalkGroup.objects.filter(UUID__in=Allowed)

    return AllowedTalkgropups


def user_allowed_to_download_transmission(
    Transmission: Transmission, UserUUID: str
) -> list:
    allowed_tgs = get_user_allowed_download_talkgroups(
        Transmission.system, UserUUID=UserUUID
    )

    if Transmission.talkgroup in allowed_tgs:
        return True

    return False
