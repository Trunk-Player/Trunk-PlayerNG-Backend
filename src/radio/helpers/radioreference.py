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
    """
    Radio Refrence interface library
    """
    def __init__(self, rr_system_id: str, username: str, password: str) -> None:
        """
        Radio Refrence interface library
        """
        self.rr_system_id = rr_system_id
        self.rr_user = username
        self.rr_pass = password

    def fetch_system_talkgroups(self) -> list[dict]:
        """
        Radio Refrence interface library
        """
        # radio reference authentication
        client = Client("http://api.radioreference.com/soap2/?wsdl&v=15&s=rpc")
        auth_type = client.get_type("ns0:authInfo")
        my_auth_info = auth_type(
            username=self.rr_user,
            password=self.rr_pass,
            appKey="c820a9fd-7488-11ec-ba68-0ecc8ab9ccec",
            version="15",
            style="rpc",
        )

        # prompt user for system ID
        sysName = client.service.getTrsDetails(self.rr_system_id, my_auth_info).sName
        sysresult = client.service.getTrsDetails(self.rr_system_id, my_auth_info).sysid
        sysid = sysresult[0].sysid

        # Read Talkgroup Data for given System ID
        talkgroups_type = client.get_type("ns0:Talkgroups")
        result = talkgroups_type(
            client.service.getTrsTalkgroups(self.rr_system_id, 0, 0, 0, my_auth_info)
        )
        return result

    def get_system(self, system_uuid) -> System:
        """
        Gets System ORM Object via UUID
        """
        system = System.objects.get(UUID=system_uuid)
        return system

    def load_system(self, system_uuid: str) -> list[TalkGroup]:
        """
        Downloads and stores RR talkgroups
        """
        rr_tg_ids = self.fetch_system_talkgroups()
        system: System = self.get_system(system_uuid)

        talkgroups = []

        mode_types = {"D": "digital", "A": "analog", "T": "tdma", "M": "mixed"}

        for talkgroup in rr_tg_ids:
            encrypted = True if talkgroup["enc"] > 0 else False
            mode = mode_types[talkgroup["tgMode"].upper()]
            try:
                tg_uuid = uuid.uuid5(
                    uuid.NAMESPACE_DNS, f"{system_uuid}+{str(talkgroup['tgDec'])}"
                )
                tg_object, created = TalkGroup.objects.get_or_create(
                    UUID=tg_uuid,
                    system=system,
                    decimal_id=int(talkgroup["tgDec"]),
                    alpha_tag=talkgroup["tgAlpha"],
                    description=talkgroup["tgDescr"][:250],
                    encrypted=encrypted,
                    mode=mode,
                )

                tg_object.save()
                talkgroups.append(tg_object)
                if created:
                    logger.info(
                        f"[+] IMPORTED TALKGROUP - [{str(talkgroup['tgDec'])}] {talkgroup['tgAlpha']}"
                    )
                else:
                    logger.info(
                        f"[+] UPDATED TALKGROUP - [{str(talkgroup['tgDec'])}] {talkgroup['tgAlpha']}"
                    )
            except IntegrityError as error:
                if settings.SEND_TELEMETRY:
                    capture_exception(error)
                continue
        return talkgroups
