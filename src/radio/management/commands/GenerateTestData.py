from django.core.management.base import BaseCommand, CommandError

from radio.models import (
    UserProfile,
    SystemACL,
    System,
    City,
    Agency,
    TalkGroup,
    SystemForwarder,
    SystemRecorder,
    Unit,
    TransmissionUnit,
    TransmissionFreq,
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

class Command(BaseCommand):
    help = "Generates Junk data for api testing"

    # def add_arguments(self, parser):
    #     parser.add_argument("UserEmail", type=str)

    def handle(self, *args, **options):
        user1 = CustomUser.objects.create_user


        default_acl = SystemACL.objects.create(name='Default', public=True)