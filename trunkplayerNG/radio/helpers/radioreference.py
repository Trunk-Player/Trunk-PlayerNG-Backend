import logging
import uuid

from zeep import Client
from django.db import IntegrityError
from django.conf import settings

from radio.models import TalkGroup, System

if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


class RR:
    def __init__(self, rrSystemId: str, User: str, Pass: str) -> None:
        """
        Radio Refrence interface library
        """
        self.rrSystemId = rrSystemId
        self.rrUser = User
        self.rrPass = Pass

    def fetch_system_talkgroups(self) -> list[dict]:
        """
        Radio Refrence interface library
        """
        # radio reference authentication
        client = Client("http://api.radioreference.com/soap2/?wsdl&v=15&s=rpc")
        auth_type = client.get_type("ns0:authInfo")
        myAuthInfo = auth_type(
            username=self.rrUser,
            password=self.rrPass,
            appKey="c820a9fd-7488-11ec-ba68-0ecc8ab9ccec",
            version="15",
            style="rpc",
        )

        # prompt user for system ID
        sysName = client.service.getTrsDetails(self.rrSystemId, myAuthInfo).sName
        sysresult = client.service.getTrsDetails(self.rrSystemId, myAuthInfo).sysid
        sysid = sysresult[0].sysid

        # Read Talkgroup Data for given System ID
        Talkgroups_type = client.get_type("ns0:Talkgroups")
        result = Talkgroups_type(
            client.service.getTrsTalkgroups(self.rrSystemId, 0, 0, 0, myAuthInfo)
        )
        return result

    def get_system(self, UUID) -> System:
        """
        Gets System ORM Object via UUID
        """
        systemX = System.objects.get(UUID=UUID)
        return systemX

    def load_system(self, SystemUUID: str) -> list[TalkGroup]:
        """
        Downloads and stores RR talkgroups
        """
        RR_TGs = self.fetch_system_talkgroups()
        system: System = self.get_system(SystemUUID)

        TalkGroups = []

        mode_types = {"D": "digital", "A": "analog", "T": "tdma"}

        for talkgroup in RR_TGs:
            Encrypted = True if talkgroup["enc"] > 0 else False
            Mode = mode_types[talkgroup["tgMode"].upper()]
            try:
                UUID = uuid.uuid5(
                    uuid.NAMESPACE_DNS, f"{SystemUUID}+{str(talkgroup['tgDec'])}"
                )
                tgX, created = TalkGroup.objects.get_or_create(
                    UUID=UUID,
                    system=system,
                    decimalID=int(talkgroup["tgDec"]),
                    alphaTag=talkgroup["tgAlpha"],
                    description=talkgroup["tgDescr"][:250],
                    encrypted=Encrypted,
                    mode=Mode,
                )

                tgX.save()
                TalkGroups.append(tgX)
                logger.info(
                    f"[+] IMPORTED TALKGROUP - [{str(talkgroup['tgDec'])}] {str(talkgroup['tgAlpha'])}"
                )
            except IntegrityError as e:
                if settings.SEND_TELEMETRY:
                    capture_exception(e)
                continue
        return TalkGroups
