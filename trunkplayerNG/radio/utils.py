from datetime import datetime
import decimal
import uuid
from radio.models import (
    System,
    SystemACL,
    SystemRecorder,
    TalkGroup,
    TransmissionFreq,
    Unit,
    TransmissionUnit,
    UserProfile,
)


class TransmissionSrc:
    def __init__(self, payload):
        self.src = payload.get("src")
        self.pos = payload.get("pos")
        self.emergency = payload.get("emergency") in ("true", "1", "t")
        self.signal_system = payload.get("signal_system")
        self.tag = payload.get("tag")
        self.time = datetime.fromtimestamp(payload.get("time")).isoformat()

    def _to_json(self):
        payload = {
            "UUID": uuid.uuid4(),
            "unit": self.src,
            "time": self.time,
            "emergency": self.emergency,
            "signal_system": self.signal_system,
            "tag": self.tag,
        }
        return payload

    def _create(self, system):
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
    def __init__(self, payload):
        self.freq = payload.get("freq")
        self.pos = payload.get("pos")
        self.len = payload.get("len")
        self.error_count = payload.get("error_count")
        self.spike_count = payload.get("spike_count")
        self.time = datetime.fromtimestamp(payload.get("time"))

    def _to_json(self):
        payload = {
            "UUID": uuid.uuid4(),
            "freq": self.freq,
            "pos": self.pos,
            "len": self.len,
            "error_count": self.error_count,
            "spike_count": self.spike_count,
        }

        return payload

    def _create(self):
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
    def __init__(self, payload):
        self.system = payload.get("system")
        self.freq = payload.get("freq")
        self.call_length = payload.get("call_length")
        self.talkgroup = payload.get("talkgroup")
        self.talkgroup_tag = payload.get("talkgroup_tag")
        self.play_length = payload.get("play_length")
        self.source = payload.get("source")

        self.start_time = datetime.fromtimestamp(payload.get("start_time")).isoformat()
        self.stop_time = datetime.fromtimestamp(payload.get("stop_time")).isoformat()

        self.emergency = payload.get("emergency") in ("true", "1", "t")
        self.encrypted = payload.get("encrypted") in ("true", "1", "t")

        self.freqList = []
        if "freqList" in payload:
            for freq in payload["freqList"]:
                self.freqList.append(TransmissionFrequency(freq))

        self.srcList = []
        if "srcList" in payload:
            for src in payload["srcList"]:
                self.srcList.append(TransmissionSrc(src))

    def _to_json(self):
        system: System = System.objects.get(UUID=self.system)
        Talkgroup, created = TalkGroup.objects.get_or_create(
            decimalID=self.talkgroup, system=system
        )
        Talkgroup.save()

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

        for unit in self.srcList:
            unit: TransmissionSrc
            payload["units"].append(unit._create(system))

        for Freq in self.freqList:
            Freq: TransmissionFrequency
            payload["frequencys"].append(Freq._create())

        return payload

    def validate_upload(self, recorderUUID):
        system: System = System.objects.get(UUID=self.system)
        recorder: SystemRecorder = SystemRecorder.objects.get(UUID=recorderUUID)

        if len(recorder.talkgroupsAllowed) > 0 and len(recorder.talkgroupsDenyed) == 0:
            talkgroup = TalkGroup.objects.filter(UUID=self.talkgroup)
            if talkgroup in recorder.talkgroupsAllowed.objects.all():
                return True
            else:
                return False
        elif (
            len(recorder.talkgroupsAllowed) == 0 and len(recorder.talkgroupsDenyed) > 0
        ):
            talkgroup = TalkGroup.objects.filter(UUID=self.talkgroup)
            if talkgroup in recorder.talkgroupsDenyed.objects.all():
                return False
            else:
                return True
        elif len(recorder.talkgroupsAllowed) > 0 and len(recorder.talkgroupsDenyed) > 0:
            talkgroup = TalkGroup.objects.filter(UUID=self.talkgroup)
            if talkgroup in recorder.talkgroupsDenyed.objects.all():
                return False
            else:
                if talkgroup in recorder.talkgroupsAllowed.objects.all():
                    return True
                else:
                    return False
        elif (
            len(recorder.talkgroupsAllowed) == 0 and len(recorder.talkgroupsDenyed) == 0
        ):
            return True


def getUserAllowedSystems(UserUUID):
    userACLs = []
    ACLs = SystemACL.objects.all()
    for ACL in ACLs:
        ACL: SystemACL
        if ACL.users.filter(UUID=UserUUID):
            userACLs.append(ACL)
        elif ACL.public:
            userACLs.append(ACL)
    Systems = System.objects.filter(systemACL__in=userACLs)
    systemUUIDs = [system.UUID for system in Systems]
    return systemUUIDs
