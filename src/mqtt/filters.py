import django_filters

from django_filters import rest_framework as filters
from django_filters.filters import OrderingFilter


from mqtt.models import (
    MqttServer,
   
)

class MqttServerFilter(filters.FilterSet):
    order_by_field = 'ordering'

    system_name = django_filters.CharFilter(field_name='systems__name', lookup_expr='exact')
    system_uuid= django_filters.CharFilter(field_name='systems__UUID', lookup_expr='exact')

    ordering = OrderingFilter(
        fields=(
            ('name', 'name'),
        )
    )

    class Meta:
        model = MqttServer
        fields = [
            "UUID",
            "name",
            "host",
            "port",
            "keepalive",
            "enabled"
        ]
