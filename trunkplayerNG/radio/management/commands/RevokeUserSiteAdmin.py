from django.core.management.base import BaseCommand, CommandError
from users.models import CustomUser
from radio.models import UserProfile


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        parser.add_argument("UserEmail", type=str)

    def handle(self, *args, **options):
        if CustomUser.objects.filter(email=options["UserEmail"]):
            User: CustomUser = CustomUser.objects.get(email=options["UserEmail"])

            if not User.userProfile.site_admin:
                self.stdout.write(
                    self.style.WARNING(f"{options['UserEmail']} is Not a Site Admin")
                )
            else:
                User.userProfile.site_admin = False
                User.userProfile.save()
                User.save()

                self.stdout.write(
                    self.style.ERROR(
                        f"{options['UserEmail']} is no longer a Site Admin"
                    )
                )
