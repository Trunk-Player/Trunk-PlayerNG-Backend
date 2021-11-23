from datetime import datetime


class TransmissionSrc:
    def __init__(self, payload):
        self.src = payload.get("src")
        self.pos = payload.get("pos")
        self.emergency = payload.get("emergency") in ("true", "1", "t")
        self.signal_system = payload.get("signal_system")
        self.tag = payload.get("tag")

        time = payload.get("time")
        if time:
            self.time = datetime.fromtimestamp(time)
        else:
            self.time = None

    def _to_json(self):
        payload = {
            "unit": self.src,
            "time": self.pos,
            "emergency": self.emergency,
            "signal_system": self.signal_system,
            "tag": self.tag,
            "length": self.length,
        }
        return payload


class TransmissionFrequency:
    def __init__(self, payload):
        self.freq = payload.get("freq")
        self.pos = payload.get("pos")
        self.len = payload.get("len")
        self.error_count = payload.get("error_count")
        self.spike_count = payload.get("spike_count")

        time = payload.get("time")
        if time:
            self.time = datetime.fromtimestamp(time)
        else:
            self.time = None

    def _to_json(self):
        payload = {
            "freq": self.freq,
            "pos": self.pos,
            "len": self.len,
            "error_count": self.error_count,
            "spike_count": self.spike_count,
        }
        return payload


class TransmissionDetails:
    def __init__(self, payload):
        self.freq = payload.get("freq")
        self.call_length = payload.get("call_length")
        self.talkgroup = payload.get("talkgroup")
        self.talkgroup_tag = payload.get("talkgroup_tag")
        self.play_length = payload.get("play_length")
        self.source = payload.get("source")

        self.start_time = payload.get("start_time")
        self.stop_time = payload.get("stop_time")

        self.emergency = payload.get("emergency") in ("true", "1", "t")
        self.encrypted = payload.get("encrypted") in ("true", "1", "t")

        self.freqList = []
        if "Freq" in payload:
            for freq in payload["freqList"]:
                self.freqList.append(TransmissionFrequency(freq))

        self.srcList = []
        if "srcList" in payload:
            for src in payload["srcList"]:
                self.srcList.append(TransmissionSrc(src))

    def _to_json(self):
        payload = {
            "startTime": self.start_time,
            "endTime": self.stop_time,
            "talkgroup": self.talkgroup,
            "encrypted": self.encrypted,
            "emergency": self.emergency,
            "units": [],
            "frequencys": [],
            "frequency": self.freq,
            "length": self.call_length,
        }

        for unit in self.srcList:
            unit: TransmissionSrc
            payload["units"].append(unit._to_json())

        for Freq in self.freqList:
            Freq: TransmissionSrc
            payload["frequencys"].append(Freq._to_json())

        return payload
