from django.db import models
import uuid
from django.db.models.base import ModelBase
from django.db.models.enums import Choices
from datetime import datetime
from trunkplayerNG.storage_backends import PrivateMediaStorage


class UserProfile(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    siteAdmin = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    siteTheme = models.TextField(blank=True, null=True)
    # feedAllowed = models.BooleanField(default=False)
    # feedAllowedSystems = models.ManyToManyField()

    def __str__(self):
        return f"{self.UUID}"


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
    enableTalkGroupACLs = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class SystemForwarder(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=100, db_index=True, unique=True)
    enabled = models.BooleanField(default=False)
    feedKey = models.UUIDField(default=uuid.uuid4, unique=True)

    def __str__(self):
        return self.name

    def webhook(self):
        pass
        # add forward logic


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
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class TalkGroup(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    decimalID = models.IntegerField(db_index=True)
    alphaTag = models.CharField(max_length=30, blank=True)
    description = models.CharField(max_length=100, blank=True, null=True)
    encrypted = models.BooleanField(default=True, blank=True)
    agency = models.ManyToManyField(Agency, blank=True, null=True)

    def __str__(self):
        return self.alphaTag


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
        return self.name


class Unit(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    decimalID = models.IntegerField(db_index=True)
    description = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return str(self.decimalID)


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
        return f"[{self.talkgroup}][{self.startTime}] {self.UUID}"


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
        return f"[{self.talkgroup}][{self.startTime}] {self.UUID}"


class Transmission(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    recorder = models.ForeignKey(SystemRecorder, on_delete=models.CASCADE)
    startTime = models.DateTimeField()
    endTime = models.DateTimeField(null=True, blank=True)
    audioFile = models.FileField()
    talkgroup = models.ForeignKey(TalkGroup, on_delete=models.CASCADE)
    encrypted = models.BooleanField(default=False, db_index=True)
    emergency = models.BooleanField(default=False, db_index=True)
    units = models.ManyToManyField(TransmissionUnit)
    frequencys = models.ManyToManyField(TransmissionFreq)
    frequency = models.FloatField(default=0.0)
    length = models.FloatField(default=0.0)

    def __str__(self):
        return f"[{self.talkgroup}][{self.startTime}] {self.UUID}"


class Incident(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    transmission = models.ManyToManyField(Transmission, blank=True)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True, null=True)
    agency = models.ManyToManyField(Agency, blank=True)

    def __str__(self):
        return self.name


class TalkGroupACL(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=30)
    users = models.ManyToManyField(UserProfile)
    allowedTalkgroups = models.ManyToManyField(TalkGroup)
    defaultNewUsers = models.BooleanField(default=True)
    defaultNewTalkgroups = models.BooleanField(default=True)

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


class SystemReciveRate(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    ),
    recorder = models.ForeignKey(SystemRecorder, on_delete=models.CASCADE)
    time = models.DateTimeField(default=datetime.now())
    rate = models.FloatField()

    def __str__(self):
        return f'{self.time.strftime("%c")} - {str(self.rate)}'


class Call(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    trunkRecorderID = models.CharField(max_length=30, unique=True)
    startTime = models.DateTimeField(db_index=True)
    endTime = models.DateTimeField(null=True, blank=True)
    units = models.ManyToManyField(Unit, related_name="TG_UNITS")
    active = models.BooleanField(default=True)
    emergency = models.BooleanField(default=True)
    encrypted = models.BooleanField(default=True)
    frequency = models.FloatField()
    phase2 = models.CharField(max_length=30)
    talkgroup = models.ForeignKey(TalkGroup, on_delete=models.CASCADE)
    recorder =  models.ForeignKey(SystemRecorder, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.time.strftime("%c")} - {str(self.rate)}'


