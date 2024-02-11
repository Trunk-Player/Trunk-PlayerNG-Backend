from django.urls import path
from mqtt.views.api import (
    server
)

urlpatterns = [
    path(
        "server/list",
        server.List.as_view(),
        name="mqtt_server_list",
    ),
    path(
        "server/create",
        server.Create.as_view(),
        name="mqtt_server_create",
    ),
    path(
        "server/<uuid:request_uuid>",
        server.View.as_view(),
        name="users_alerts_view",
    )
]
