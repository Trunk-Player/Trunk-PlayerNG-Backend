import logging

from django.db.models import Q


from radio.models import (
    System,
    SystemACL,
    TalkGroup,
    TalkGroupACL,
    Transmission
)

logger = logging.getLogger(__name__)

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
