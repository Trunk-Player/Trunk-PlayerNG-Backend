import uuid

from django.db import models
from django.db import models
from django.db.models.fields import NullBooleanField
from django.dispatch import receiver
from django.utils import timezone

from trunkplayerNG.storage_backends import PrivateMediaStorage


class UserProfile(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    siteAdmin = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    siteTheme = models.TextField(blank=True, null=True)

    def __str__(self):
        from users.models import CustomUser
        try:
            parent: CustomUser = CustomUser.objects.get(userProfile=self)

            return f"{parent.email}"
        except:
            return str(self.UUID)


class SystemACL(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=100, db_index=True, unique=True)
    users = models.ManyToManyField(UserProfile)
    public = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def to_json(self):
        data = {
            "UUID": str(self.UUID),
            "name": str(self.name),
            "public": self.public,
            "users": [],
        }

        for user in self.users.all():
            data["users"].append(user.UUID)

        return data


class System(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=100, db_index=True, unique=True)
    systemACL = models.ForeignKey(SystemACL, on_delete=models.CASCADE)
    enableTalkGroupACLs = models.BooleanField("Enable Talkgroup ACLs", default=False)
    pruneTransmissions = models.BooleanField(
        "Enable Pruneing Transmissions", default=False
    )
    pruneTransmissionsAfterDays = models.IntegerField(
        "Days to keep Transmissions (Prune)", default=365
    )

    def __str__(self):
        return self.name


class City(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class Agency(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True, null=True)
    city = models.ManyToManyField(City, blank=True)

    def __str__(self):
        return self.name


class TalkGroup(models.Model):
    MODE_OPTS = (("digital", "Digital"), ("analog", "Analog"), ("tdma", "TDMA"), ("mixed","Mixed"))

    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    decimalID = models.IntegerField(db_index=True)
    alphaTag = models.CharField(max_length=30, blank=True, default="")
    description = models.CharField(max_length=250, blank=True, null=True)
    mode = models.CharField(max_length=250, default="digital", choices=MODE_OPTS)
    encrypted = models.BooleanField(default=False, blank=True)
    agency = models.ManyToManyField(Agency, blank=True)

    def __str__(self):
        return f"[{self.system.name}] {self.alphaTag}"


@receiver(models.signals.post_save, sender=TalkGroup)
def execute_TalkGroup_dedup_check(sender, instance, created, *args, **kwargs):
    system = instance.system

    if created:
        if instance.alphaTag != "":
            TGs = TalkGroup.objects.filter(
                system=system, decimalID=instance.decimalID
            ).exclude(UUID=instance.UUID)
            TGs.delete()
        else:
            if TalkGroup.objects.filter(
                system=system, decimalID=instance.decimalID
            ).exclude(alphaTag=""):
                instance.delete()


class SystemForwarder(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=100, unique=True)
    enabled = models.BooleanField(default=False)
    recorderKey = models.UUIDField()
    remoteURL = models.CharField(max_length=250)

    forwardIncidents = models.BooleanField(default=False)
    forwardedSystems = models.ManyToManyField(System)
    talkGroupFilter = models.ManyToManyField(TalkGroup, blank=True)

    def __str__(self):
        return self.name

    def webhook(self):
        pass
        # add forward logic


class SystemRecorder(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    siteID = models.CharField(max_length=100, blank=True, null=True)
    enabled = models.BooleanField(default=False)
    user = models.ForeignKey(
        UserProfile, null=True, blank=True, on_delete=models.CASCADE
    )
    talkgroupsAllowed = models.ManyToManyField(
        TalkGroup, blank=True, related_name="SRTGAllow"
    )
    talkgroupsDenyed = models.ManyToManyField(
        TalkGroup, blank=True, related_name="SRTGDeny"
    )
    forwarderWebhookUUID = models.UUIDField(default=uuid.uuid4, db_index=True)

    def __str__(self):
        return f"[{self.system.name}] {self.name}"


class Unit(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    decimalID = models.IntegerField(db_index=True)
    description = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"[{self.system.name}] {str(self.decimalID)}"


@receiver(models.signals.post_save, sender=Unit)
def execute_unit_dedup_check(sender, instance, created, *args, **kwargs):
    system = instance.system

    if created:
        if instance.description != "":
            TGs = Unit.objects.filter(
                system=system, decimalID=instance.decimalID
            ).exclude(UUID=instance.UUID)
            TGs.delete()
        else:
            if Unit.objects.filter(system=system, decimalID=instance.decimalID).exclude(
                description=""
            ):
                instance.delete()


class TransmissionUnit(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    time = models.DateTimeField(db_index=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    pos = models.IntegerField(default=0)
    emergency = models.BooleanField(default=0)
    signal_system = models.CharField(default="", blank=True, max_length=50)
    tag = models.CharField(default="", blank=True, max_length=255)
    length = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.UUID}"


class TransmissionFreq(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    time = models.DateTimeField()
    freq = models.IntegerField(default=0, db_index=True)
    pos = models.IntegerField(default=0)
    len = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    spike_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.UUID}"


class Transmission(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE, db_index=True)
    recorder = models.ForeignKey(SystemRecorder, on_delete=models.CASCADE)
    startTime = models.DateTimeField()
    endTime = models.DateTimeField(null=True, blank=True)
    audioFile = models.FileField(upload_to="audio/%Y/%m/%d/")
    talkgroup = models.ForeignKey(TalkGroup, on_delete=models.CASCADE, db_index=True)
    encrypted = models.BooleanField(default=False, db_index=True)
    emergency = models.BooleanField(default=False, db_index=True)
    units = models.ManyToManyField(TransmissionUnit)
    frequencys = models.ManyToManyField(TransmissionFreq)
    frequency = models.FloatField(default=0.0)
    length = models.FloatField(default=0.0)

    locked = models.BooleanField(default=False, db_index=True)
    transcript = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-startTime"]

    def __str__(self):
        return f"[{self.system.name}][{self.talkgroup.alphaTag}][{self.startTime}] {self.UUID}"


class Incident(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    active = models.BooleanField(default=True)
    time = models.DateTimeField(default=timezone.now)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    transmission = models.ManyToManyField(Transmission, blank=True)
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True, null=True)
    agency = models.ManyToManyField(Agency, blank=True)

    class Meta:
        ordering = ["-time"]

    def __str__(self):
        return f"[{self.system.name}] {self.name}"


@receiver(models.signals.post_save, sender=Incident)
def execute_after_save(sender, instance, created, *args, **kwargs):
    from radio.tasks import forward_incidents
    from radio.serializers import IncidentSerializer

    # Used for Incident forwarding

    IncidentData = IncidentSerializer(instance)
    forward_incidents.delay(IncidentData.data, created)


class TalkGroupACL(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=30)
    users = models.ManyToManyField(UserProfile)
    allowedTalkgroups = models.ManyToManyField(TalkGroup)
    defaultNewUsers = models.BooleanField(default=True)
    defaultNewTalkgroups = models.BooleanField(default=True)
    downloadAllowed = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ScanList(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True, null=True)
    public = models.BooleanField(default=False)
    communityShared = models.BooleanField(default=True)
    talkgroups = models.ManyToManyField(TalkGroup)

    def __str__(self):
        return self.name


class Scanner(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True, null=True)
    public = models.BooleanField(default=True)
    communityShared = models.BooleanField(default=True)
    scanlists = models.ManyToManyField(ScanList)

    def __str__(self):
        return self.name


class GlobalAnnouncement(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=30)
    enabled = models.BooleanField(default=False)
    description = models.TextField()

    def __str__(self):
        return self.name


class GlobalEmailTemplate(models.Model):
    mailTypes = (
        ("welcome", "welcome"),
        ("alert", "alert"),
    )

    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=30)
    type = models.CharField(max_length=30, unique=True, choices=mailTypes)
    enabled = models.BooleanField(default=False)
    HTML = models.TextField()

    def __str__(self):
        return self.name


class UserAlert(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    user = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=250)
    enabled = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    webNotification = models.BooleanField(default=False)
    appRiseNotification = models.BooleanField(default=False)
    appRiseURLs = models.TextField(", Seperated AppriseURL(s)", default="")
    talkgroups = models.ManyToManyField(TalkGroup, blank=True)
    emergencyOnly = models.BooleanField(default=False)
    units = models.ManyToManyField(Unit, blank=True)
    title = models.CharField(max_length=255, default="New Activity Alert")
    body = models.TextField(default="New Activity on %T - %I")

    def __str__(self):
        return f"{self.name}"


# class SystemReciveRate(models.Model):
#     UUID = models.UUIDField(
#         primary_key=True, default=uuid.uuid4, db_index=True, unique=True
#     )

#     recorder = models.ForeignKey(SystemRecorder, on_delete=models.CASCADE)
#     time = models.DateTimeField(default=timezone.now())
#     rate = models.FloatField()

#     def __str__(self):
#         return f'{self.time.strftime("%c")} - {str(self.rate)}'


# class Call(models.Model):
#     UUID = models.UUIDField(
#         primary_key=True, default=uuid.uuid4, db_index=True, unique=True
#     )
#     trunkRecorderID = models.CharField(max_length=30, unique=True)
#     startTime = models.DateTimeField(db_index=True)
#     endTime = models.DateTimeField(null=True, blank=True)
#     units = models.ForeignKey(
#         Unit,
#         related_name="TG_UNITS",
#         blank=True,
#         null=True,
#         on_delete=models.DO_NOTHING,
#     )
#     active = models.BooleanField(default=True)
#     emergency = models.BooleanField(default=True)
#     encrypted = models.BooleanField(default=True)
#     frequency = models.FloatField()
#     phase2 = models.CharField(max_length=30)
#     talkgroup = models.ForeignKey(TalkGroup, on_delete=models.CASCADE)
#     recorder = models.ForeignKey(SystemRecorder, on_delete=models.CASCADE)

#     def __str__(self):
#         return f"{self.trunkRecorderID}"
