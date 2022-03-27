from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings

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
                    raw_token = request.COOKIES.get(settings.JWT_AUTH_COOKIE).encode("utf-8")
                    validated_token = self.get_validated_token(raw_token)
                    return self.get_user(validated_token), validated_token
            else:
                raw_token = request.COOKIES.get(settings.JWT_AUTH_COOKIE).encode("utf-8")
                validated_token = self.get_validated_token(raw_token)
                return self.get_user(validated_token), validated_token