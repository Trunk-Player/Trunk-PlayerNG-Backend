from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings

from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import exceptions

def enforce_csrf(request):
    """
    Enforce CSRF validation.
    """
    reason = CsrfViewMiddleware().process_view(request, None, (), {})
    if reason:
        # CSRF failed, bail with explicit error message
        raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)


class TokenAuthSupportCookie(JWTAuthentication):
    """
    Extend the TokenAuthentication class to support cookie based authentication
    """
    def authenticate(self, request):
        # Check if 'auth_token' is in the request cookies.
        # Give precedence to 'Authorization' header.
        raw_token = None
        if settings.JWT_AUTH_COOKIE in request.COOKIES and \
                        'HTTP_AUTHORIZATION' not in request.META:
            if 'HTTP_REFERER' in request.META:
                if "/auth/" not in request.META['HTTP_REFERER']:
                    enforce_csrf(request)
                    raw_token = request.COOKIES.get(settings.JWT_AUTH_COOKIE).encode("utf-8")
                    validated_token = self.get_validated_token(raw_token)

                    return self.get_user(validated_token), validated_token
            else:
                enforce_csrf(request)
                raw_token = request.COOKIES.get(settings.JWT_AUTH_COOKIE).encode("utf-8")
                validated_token = self.get_validated_token(raw_token)
                return self.get_user(validated_token), validated_token