from django.contrib import admin

from radio.models import *

# Register your models here.

admin.site.register(UserProfile)
admin.site.register(SystemACL)
admin.site.register(System)
admin.site.register(SystemForwarder)
admin.site.register(City)
admin.site.register(Agency)
admin.site.register(TalkGroup)
admin.site.register(SystemRecorder)
admin.site.register(Unit)
admin.site.register(Transmission)
admin.site.register(Incident)
admin.site.register(TalkGroupACL)
admin.site.register(ScanList)
admin.site.register(Scanner)
admin.site.register(GlobalAnnouncement)
admin.site.register(GlobalEmailTemplate)
admin.site.register(SystemReciveRate)
admin.site.register(Call)
admin.site.register(SystemRecorderMetrics)
