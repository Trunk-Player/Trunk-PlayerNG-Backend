import uuid

from datetime import datetime

from django.db import models
from django.dispatch import receiver
from django.utils import timezone


class UserProfile(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    site_admin = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    site_theme = models.TextField(blank=True, null=True)

    def __str__(self):
        try:
            from users.models import CustomUser

            parent: CustomUser = CustomUser.objects.get(userProfile=self)

            return f"{parent.email}"
        except Exception: # pylint: disable=broad-except
            return str(self.UUID)

class UserMessage(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    urgent = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    time = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=255,blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.title)

class UserInbox(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    messages = models.ManyToManyField(UserMessage)

    def number_unread(self):
        '''Gets the number of unread messages'''
        return len(self.messages.filter(read=False))

    def __str__(self):
        try:
            parent: UserProfile = UserProfile.objects.get(userProfile=self.user)
            return f"{str(parent)}"
        except Exception: # pylint: disable=broad-except
            return str(self.UUID)

class SystemACL(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=100, db_index=True, unique=True)
    users = models.ManyToManyField(UserProfile, blank=True)
    public = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def to_json(self):
        """
        Converts to json
        """
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
    rr_system_id = models.CharField(max_length=100, blank=True, null=True)
    enable_talkgroup_acls = models.BooleanField("Enable Talkgroup ACLs", default=False)
    prune_transmissions = models.BooleanField(
        "Enable Pruneing Transmissions", default=False
    )
    prune_transmissions_after_days = models.IntegerField(
        "Days to keep Transmissions (Prune)", default=365
    )

    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return self.name

class City(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True, default="")

    def __str__(self):
        return self.name

class Agency(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True, default="")
    city = models.ManyToManyField(City, blank=True)

    def __str__(self):
        return self.name

class TalkGroup(models.Model):
    MODE_OPTS = (
        ("digital", "Digital"),
        ("analog", "Analog"),
        ("tdma", "TDMA"),
        ("mixed", "Mixed"),
    )

    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    decimal_id = models.IntegerField(db_index=True)
    alpha_tag = models.CharField(max_length=30, blank=True, default="")
    description = models.CharField(max_length=250, blank=True, null=True)
    mode = models.CharField(max_length=250, default="digital", choices=MODE_OPTS)
    encrypted = models.BooleanField(default=False, blank=True)
    agency = models.ManyToManyField(Agency, blank=True)

    notes = models.TextField(blank=True, default="")

    @property
    def transmission_count(self):
       return Transmission.objects.filter(talkgroup=self).count() 

    def __str__(self):
        return f"[{self.system.name}] {self.alpha_tag}"


 # pylint: disable=unused-argument

@receiver(models.signals.post_save, sender=TalkGroup)
def execute_talkgroup_dedup_check(sender, instance, created, *args, **kwargs):
    """
    Removes Duplicate talkgroups
    """
    system = instance.system

    if created:
        if instance.alpha_tag != "":
            talkgroups = TalkGroup.objects.filter(
                system=system, decimal_id=instance.decimal_id
            ).exclude(UUID=instance.UUID)
            talkgroups.delete()
            talkgroup_acls = TalkGroupACL.objects.filter(default_new_talkgroups=True)
            for acl in talkgroup_acls:
                acl:TalkGroupACL
                acl.allowed_talkgroups.add(instance)
        else:
            if TalkGroup.objects.filter(
                system=system, decimal_id=instance.decimal_id
            ).exclude(alpha_tag=""):
                instance.delete()

class SystemForwarder(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=100, unique=True)
    enabled = models.BooleanField(default=False)
    recorder_key = models.UUIDField()
    remote_url = models.CharField(max_length=250)

    forward_incidents = models.BooleanField(default=False)
    forwarded_systems = models.ManyToManyField(System)
    talkgroup_filter = models.ManyToManyField(TalkGroup, blank=True)

    def __str__(self):
        return self.name

class SystemRecorder(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    site_id = models.CharField(max_length=100, blank=True, null=True)
    enabled = models.BooleanField(default=False)
    user = models.ForeignKey(
        UserProfile, null=True, blank=True, on_delete=models.CASCADE
    )
    talkgroups_allowed = models.ManyToManyField(
        TalkGroup, blank=True, related_name="SRTGAllow"
    )
    talkgroups_denyed = models.ManyToManyField(
        TalkGroup, blank=True, related_name="SRTGDeny"
    )
    api_key = models.UUIDField(default=uuid.uuid4, db_index=True)

    def __str__(self):
        return f"[{self.system.name}] {self.name}"

class Unit(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    decimal_id = models.IntegerField(db_index=True)
    description = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"[{self.system.name}] {str(self.decimal_id)}"

# pylint: disable=unused-argument
@receiver(models.signals.post_save, sender=Unit)
def execute_unit_dedup_check(sender, instance, created, *args, **kwargs):
    """
    Makes sure Units are deduped on save hook
    """

    system = instance.system

    if created:
        if instance.description != "":
            units = Unit.objects.filter(
                system=system, decimal_id=instance.decimal_id
            ).exclude(UUID=instance.UUID)
            units.delete()
        else:
            if Unit.objects.filter(system=system, decimal_id=instance.decimal_id).exclude(
                description=""
            ):
                instance.delete()

def get_audio_path(instance, filename):
    time_str = datetime.now().strftime('%Y/%m/%d')
    safe_alpha_tag = "".join([c for c in instance.talkgroup.alpha_tag if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    return f"audio/{time_str}/{instance.talkgroup.system.name}_{str(instance.talkgroup.decimal_id)}_{safe_alpha_tag.replace(' ', '-')}/{filename}"

class Transmission(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    system = models.ForeignKey(System, on_delete=models.CASCADE, db_index=True)
    recorder = models.ForeignKey(SystemRecorder, on_delete=models.CASCADE)
    audio_type = models.CharField(max_length=50, null=True, default=None)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    audio_file = models.FileField(upload_to=get_audio_path, max_length=250)
    talkgroup = models.ForeignKey(TalkGroup, on_delete=models.CASCADE, db_index=True)
    encrypted = models.BooleanField(default=False, db_index=True)
    emergency = models.BooleanField(default=False, db_index=True)
    units = models.JSONField(default=list, blank=True)
    frequencys = models.JSONField(default=list, blank=True)
    frequency = models.FloatField(default=0.0)
    length = models.FloatField(default=0.0, null=True)

    locked = models.BooleanField(default=False, db_index=True)
    transcript = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self):
        return f"[{self.system.name}][{self.talkgroup.alpha_tag}][{self.start_time}] {self.UUID}"

@receiver(models.signals.post_delete, sender=Transmission)
def auto_delete_file_on_delete(sender, instance:Transmission, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    import os
    from pathlib import Path
    if instance.audio_file:
        audio_path = Path(instance.audio_file.path)
        parent:Path = audio_path.parent

        if audio_path.exists():
            os.remove(instance.audio_file.path)

        if not any(Path(parent).iterdir()):
            os.rmdir(parent)

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

# pylint: disable=unused-argument
@receiver(models.signals.post_save, sender=Incident)
def execute_after_save(sender, instance, created, *args, **kwargs):
    """
    Handles Incident Forwarding
    """
    from radio.tasks import forward_incidents
    from radio.serializers import IncidentSerializer

    # Used for Incident forwarding

    incident_data = IncidentSerializer(instance)
    forward_incidents.delay(incident_data.data, created)

class TalkGroupACL(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=30)
    users = models.ManyToManyField(UserProfile)
    allowed_talkgroups = models.ManyToManyField(TalkGroup)
    default_new_talkgroups = models.BooleanField(default=True)
    default_new_users = models.BooleanField(default=True)
    download_allowed = models.BooleanField(default=True)
    transcript_allowed = models.BooleanField(default=True)

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
    community_shared = models.BooleanField(default=True)
    talkgroups = models.ManyToManyField(TalkGroup)

    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return self.name

 # pylint: disable=unused-argument

@receiver(models.signals.post_save, sender=ScanList)
def exec_scanlist_mutation_notification(sender, instance, created, *args, **kwargs):
    """
    Send mutations to webui
    """
    from radio.tasks import send_new_parental_mutation

    e_type = 'created' if created else 'updated'
    i_type = 'scanlist'
    s_uuid = instance.UUID

    send_new_parental_mutation.delay(
        s_uuid,
        i_type,
        e_type,
    )

 # pylint: disable=unused-argument

@receiver(models.signals.post_delete, sender=ScanList)
def exec_scanlist_mutation_notification_delete(sender, instance, created, *args, **kwargs):
    """
    Send mutations to webui
    """
    from radio.tasks import send_new_parental_mutation

    e_type = 'eject_into_the_void'
    i_type = 'scanlist'
    s_uuid = instance.UUID

    send_new_parental_mutation.delay(
        s_uuid,
        i_type,
        e_type,
    )

class Scanner(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True, null=True)
    public = models.BooleanField(default=True)
    community_shared = models.BooleanField(default=True)
    scanlists = models.ManyToManyField(ScanList)

    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return self.name

 # pylint: disable=unused-argument

@receiver(models.signals.post_save, sender=Scanner)
def exec_scanner_mutation_notification(sender, instance, created, *args, **kwargs):
    """
    Send mutations to webui
    """
    from radio.tasks import send_new_parental_mutation

    e_type = 'created' if created else 'updated'
    i_type = 'scanner'
    s_uuid = instance.UUID

    send_new_parental_mutation.delay(
        s_uuid,
        i_type,
        e_type,
    )

 # pylint: disable=unused-argument

@receiver(models.signals.post_delete, sender=Scanner)
def exec_scanner_mutation_notification_delete(sender, instance, created, *args, **kwargs):
    """
    Send mutations to webui
    """
    from radio.tasks import send_new_parental_mutation
    
    e_type = 'eject_into_the_void'
    i_type = 'scanner'
    s_uuid = instance.UUID

    send_new_parental_mutation.delay(
        s_uuid,
        i_type,
        e_type,
    )

class GlobalAnnouncement(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(max_length=80)
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
    template_type = models.CharField(max_length=30, unique=True, choices=mailTypes)
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
    web_notification = models.BooleanField(default=False)
    app_rise_notification = models.BooleanField(default=False)
    app_rise_urls = models.TextField(", Seperated AppriseURL(s)", blank=True, default="")
    talkgroups = models.ManyToManyField(TalkGroup, blank=True)
    emergency_only = models.BooleanField(default=False)
    units = models.ManyToManyField(Unit, blank=True)
    count = models.IntegerField('Number of Transmissions over trigger time to alert', default=1)
    trigger_time = models.IntegerField('trigger time', default=10)
    title = models.CharField(max_length=255, default="New Activity Alert")
    body = models.TextField(default="New Activity on %T - %I")

    def __str__(self):
        return f"{self.name}"
