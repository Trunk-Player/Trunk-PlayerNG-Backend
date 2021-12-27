from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

import uuid

from radio.models import UserProfile, TalkGroupACL
from users.managers import CustomUserManager


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    userProfile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.email


@receiver(post_save, sender=CustomUser)
def createUserProfile(sender, instance: CustomUser, **kwargs):
    if instance.userProfile:
        return True

    siteAdmin = False

    if instance.is_superuser and instance.is_active:
        siteAdmin = True

    UP = UserProfile(
        UUID=uuid.uuid4(), siteAdmin=siteAdmin, description="", siteTheme=""
    )

    UP.save()

    for acl in TalkGroupACL.objects.filter(defaultNewUsers=True):
        acl: TalkGroupACL
        acl.users.add(UP)
        acl.save()

    instance.userProfile = UP
    instance.save()
