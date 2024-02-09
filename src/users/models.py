import uuid

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from users.managers import CustomUserManager
from radio.models import UserInbox, UserProfile, TalkGroupACL

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

    site_admin = False if instance.is_superuser and instance.is_active else True

    user_profile = UserProfile(
        UUID=uuid.uuid4(), site_admin=site_admin, description="", site_theme=""
    )
    user_profile.save()

    user_inbox = UserInbox(user=user_profile)
    user_inbox.save()

    for acl in TalkGroupACL.objects.filter(default_new_users=True):
        acl: TalkGroupACL
        acl.users.add(user_profile)
        acl.save()

    instance.userProfile = user_profile
    instance.save()
