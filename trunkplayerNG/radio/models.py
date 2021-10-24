from django.db import models
import uuid
from django.contrib.auth.models import User
from django.db.models.base import ModelBase
from django.db.models.enums import Choices
from datetime import datetime


# Create your models here.

class UserProfile(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False)
    siteAdmin = models.BooleanField(default=False)
    Description = models.TextField(blank=True, null=True)
    siteTheme = models.TextField(blank=True, null=True)
    feedAllowed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.first_name}" 

class SystemACL(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    name = models.CharField(max_length=100, db_index=True, unique=True)
    users = models.ManyToManyField(UserProfile)
    public = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class System(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    name = models.CharField(max_length=100, db_index=True, unique=True)
    systemACL = models.ForeignKey(SystemACL , on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class SystemForwarder(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    name = models.CharField(max_length=100, db_index=True, unique=True)
    feedKey = models.UUIDField(default=uuid.uuid4,  unique=True)
    
    def __str__(self):
        return self.name
    
    def webhook(self):
        pass 
        # add forward logic

class City(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True, null=True)   

    def __str__(self):
        return self.name

class Agency(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True, null=True)   
    city =  models.ForeignKey(City, on_delete=models.CASCADE)   

    def __str__(self):
        return self.name

class TalkGroup(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    decimalID = models.IntegerField(db_index=True)
    alphaTag = models.CharField(max_length=30)
    commonName = models.CharField(max_length=10, blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)    
    encrypted = models.BooleanField(default=True)
    agency = models.ManyToManyField(Agency)

    def __str__(self):
        return self.alphaTag

class SystemRecorder(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    siteID = models.CharField(max_length=100, blank=True, null=True)
    enabled = models.BooleanField(default=False)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    talkgroupsAllowed = models.ManyToManyField(TalkGroup, related_name='SRTGAllow')
    talkgroupsDenyed = models.ManyToManyField(TalkGroup, related_name='SRTGDeny')
    forwarderWebhookUUID = models.UUIDField(default=uuid.uuid4)

    def __str__(self):
        return self.name

class Unit(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    decimalID = models.IntegerField(db_index=True)
    description = models.CharField(max_length=100, blank=True, null=True)    
    encrypted = models.BooleanField(default=True)

    def __str__(self):
        return self.decimalID

class Transmission(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    recorder = models.ForeignKey(SystemRecorder, on_delete=models.CASCADE)
    startTime = models.DateTimeField(db_index=True)
    endTime = models.DateTimeField(null=True, blank=True)
    audioFile = models.FileField()
    talkgroup =  models.ForeignKey(TalkGroup, on_delete=models.CASCADE)
    encrypted = models.BooleanField(default=False)
    units =  models.ManyToManyField(Unit)
    frequency = models.FloatField(default=0.0)
    length =  models.FloatField(default=0.0)

    def __str__(self):
        return f"[{self.talkgroup}][{self.startTime}] {self.UUID}"

class Incident(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    transmission = models.ManyToManyField(Transmission)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True, null=True)    
    agency = models.ManyToManyField(Agency)

    def __str__(self):
        return self.name

class TalkGroupACL(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    name = models.CharField(max_length=30)
    users = models.ManyToManyField(UserProfile)
    allowedTalkgroups = models.ManyToManyField(TalkGroup)  
    defualtNewUsers = models.BooleanField(default=True)
    defualtNewTalkgroups = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ScanList(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True, null=True)
    public = models.BooleanField(default=True)
    talkgroups = models.ManyToManyField(TalkGroup)  

    def __str__(self):
        return self.name

class GlobalScanList(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    scanList = models.ForeignKey(ScanList, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class GlobalAnnouncement(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    name = models.CharField(max_length=30)
    enabled = models.BooleanField(default=False)
    Description = models.TextField()

    def __str__(self):
        return self.name

class GlobalEmailTemplate(models.Model):
    mailTypes = (
        ('welcome','welcome'),
        ('alert','alert'),
    )

    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    name = models.CharField(max_length=30)
    type = models.CharField(max_length=30, unique=True, choices=mailTypes)
    enabled = models.BooleanField(default=False)
    HTML = models.TextField()

    def __str__(self):
        return self.name

class SystemReciveRate(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    time = models.DateTimeField(default=datetime.now())
    rate = models.FloatField()    

    def __str__(self):
        return f'{self.time.strftime("%c")} - {str(self.rate)}'

class Call(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    trunkRecorderID = models.CharField(max_length=30)
    startTime = models.DateTimeField(db_index=True)
    endTime = models.DateTimeField(null=True, blank=True)
    units = models.ManyToManyField(Unit)   
    active = models.BooleanField(default=True)
    emergency = models.BooleanField(default=True)
    encrypted = models.BooleanField(default=True)
    frequency = models.FloatField()
    phase2 = models.CharField(max_length=30)
    talkgroup =  models.ForeignKey(TalkGroup, on_delete=models.CASCADE)


    def __str__(self):
        return f'{self.time.strftime("%c")} - {str(self.rate)}'

class SystemRecorderMetrics(models.Model):
    UUID = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)
    systemRecorder = models.ForeignKey(System, on_delete=models.CASCADE)
    rates = models.ManyToManyField(SystemReciveRate)   
    calls = models.ManyToManyField(Call)    

    def __str__(self):
        return f'{self.time.strftime("%c")} - {str(self.rate)}'
    
    def statusServerURL(self):
        pass
        #return 