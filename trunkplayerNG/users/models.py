import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from radio.models import UserProfile, TalkGroupACL
from users.managers import CustomUserManager


class CustomUser(AbstractUser):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    userProfile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.email

# pylint: disable=unused-argument
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance: CustomUser, **kwargs):
    """
    Creates User Profile on user create
    """
    if instance.userProfile:
        return True

    site_admin = False

    if instance.is_superuser and instance.is_active:
        site_admin = True

    user_profile = UserProfile(
        UUID=uuid.uuid4(), site_admin=site_admin, description="", site_theme=""
    )

    user_profile.save()

    for acl in TalkGroupACL.objects.filter(default_new_users=True):
        acl: TalkGroupACL
        acl.users.add(user_profile)
        acl.save()

    instance.userProfile = user_profile
    instance.save()


@receiver(pre_delete, sender=CustomUser)
def delete_user_profile(sender, instance: CustomUser, **kwargs):
    """
    Deletes Allauth User Profile on user delete
    """
    from allauth.account.models import EmailAddress

    try:
        EmailAddress.objects.get(user=instance, email=instance.email).delete()
    except EmailAddress.DoesNotExist:
        pass
