import logging
from django.conf import settings
from rest_framework import permissions

if settings.SEND_TELEMETRY:
    from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


class IsSAOrReadOnly(permissions.BasePermission):
    """
    Custom permission - Site admin or Read Only
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_anonymous:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.userProfile.site_admin and request.user.is_authenticated


class IsSAOrUser(permissions.BasePermission):
    """
    Custom permission - Site admin or User
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_anonymous:
            return False

        if (
            request.user.userProfile.site_admin
            or request.user.userProfile.UUID == obj.UUID
        ):
            return True

        return False


class IsUser(permissions.BasePermission):
    """
    Custom permission - Is a user
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_anonymous:
            return False

        return True


class IsSiteAdmin(permissions.BasePermission):
    """
    Custom permission - Site admin
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.userProfile.site_admin


class Feeder(permissions.BasePermission):
    """
    Custom permission - Authenticated feed
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        return True


class FeederFree(permissions.BasePermission):
    """
    Custom permission - Token only feed
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return True
