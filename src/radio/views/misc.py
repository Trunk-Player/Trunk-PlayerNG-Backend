from django.conf import settings
from django.http import ( Http404, HttpResponse )

from radio.helpers.utils import user_allowed_to_download_transmission

from radio.models import Transmission

if settings.SEND_TELEMETRY:
    import sentry_sdk

class PaginationMixin(object):
    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination
        is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given
        output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)


def transmission_download(request, transmission_uuid):
    """
    Handles Transmission download URL
    """
    import requests

    try:
        transmission: Transmission = Transmission.objects.get(UUID=transmission_uuid)
    except Transmission.DoesNotExist:
        raise Http404 from Transmission.DoesNotExist

    user = request.user.userProfile
    if not user.site_admin:
        if not user_allowed_to_download_transmission(transmission, user.UUID):
            return HttpResponse("UNAUTHORIZED", status=401)

    file_url = transmission.audio_file.url
    # file_size = transmission.audio_file.size

    if not settings.USE_S3:
        file_url = f"{settings.AUDIO_DOWNLOAD_HOST}{file_url}"

    audio_type = f'audio/{file_url.split(".")[-1].strip()}'
    filename = f'{str(transmission.talkgroup.decimal_id)}_{str(transmission.start_time.isoformat())}_{str(transmission.UUID)}.{file_url.split(".")[-1].strip()}'

    response = HttpResponse(content_type=audio_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    data = requests.get(file_url, verify=False)
    response.write(data.content)

    return response
