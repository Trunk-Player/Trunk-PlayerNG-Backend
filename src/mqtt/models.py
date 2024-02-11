import uuid
from django.db import models
from radio.models import System, Agency

class MqttServer(models.Model):
    UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, db_index=True, unique=True
    )
    name = models.CharField(null=True, blank=True, max_length=255)
    host = models.CharField(max_length=255)
    port = models.IntegerField(default=1883)
    keepalive = models.IntegerField(default=60)

    enabled = models.BooleanField(default=True)

    systems = models.ManyToManyField(System, blank=True)
    agencies = models.ManyToManyField(Agency, blank=True)

    username = models.CharField(null=True, blank=True, max_length=255)
    password = models.CharField(null=True, blank=True, max_length=255)
    
    def __str__(self):
        if self.name:
            return self.name
        else:
            return f"{self.host}:{self.port}"
