from django.core.management.base import BaseCommand, CommandError
from users.models import CustomUser
from radio.models import UserProfile


class Command(BaseCommand):
    help = "Makes user a feed provider"

    def add_arguments(self, parser):
        parser.add_argument("UserEmail", type=str)

    def handle(self, *args, **options):
        if CustomUser.objects.filter(email=options["UserEmail"]):
            User: CustomUser = CustomUser.objects.get(email=options["UserEmail"])

            if User.userProfile.feedAllowed:
                self.stdout.write(
                    self.style.WARNING(
                        f"{options['UserEmail']} is Already a Feed Provider"
                    )
                )
            else:
                User.userProfile.feedAllowed = True
                User.userProfile.save()
                User.save()

                self.stdout.write(
                    self.style.SUCCESS(f"{options['UserEmail']} is now a Feed Provider")
                )
