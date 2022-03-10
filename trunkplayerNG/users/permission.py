from rest_framework import permissions


class IsSAOrUser(permissions.BasePermission):
    """
    Is site admin or User
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_anonymous:
            return False

        if request.user.userProfile.site_admin or request.user.UUID == obj.UUID:
            return True

        return False


class IsSiteAdmin(permissions.BasePermission):
    """
    Is site admin
    """

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.userProfile.site_admin
