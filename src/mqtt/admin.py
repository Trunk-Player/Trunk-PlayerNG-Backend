from django.contrib import admin

from mqtt.models import (
   MqttServer
)


# pylint: disable=unused-argument
@admin.action(description="Enable")
def enable_clients(modeladmin, request, queryset):
    """
    Bulk Enables Servers
    """
    queryset.update(enabled=True)

# pylint: disable=unused-argument
@admin.action(description="Disable")
def disable_clients(modeladmin, request, queryset):
    """
    Bulk Disables Servers
    """
    queryset.update(enabled=False)

@admin.register(MqttServer)
class MqttServerAdmin(admin.ModelAdmin):
    list_display = ("name", "enabled", "host", "port", "keepalive", "username")
    list_filter = ("enabled", "host", "username")

    actions = [
        enable_clients,
        disable_clients
    ]