import os
import logging

from pathlib import Path
from datetime import timedelta

from kombu import Queue
from kombu.entity import Exchange

BASE_DIR = Path(__file__).resolve().parent.parent

SEND_TELEMETRY = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ""

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

CELERY_BROKER_URL = "ampq://user:pass@host/"

AUDIO_DOWNLOAD_HOST = "example.com"
ALLOWED_HOSTS = ['example.com']

CORS_ALLOWED_ORIGINS = [
    "http://example.com",
    "https://example.com",
]
CORS_ALLOW_ALL_ORIGINS = True

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "3306",
    }
}


TIME_ZONE = "America/Los_Angeles"


#SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

USE_S3 = False
if USE_S3:
    # aws settings
    AWS_ACCESS_KEY_ID = ""
    AWS_SECRET_ACCESS_KEY = ""
    AWS_STORAGE_BUCKET_NAME = ""
    AWS_S3_ENDPOINT_URL = ""
    AWS_DEFAULT_ACL = None
    AWS_S3_CUSTOM_DOMAIN = "https://S3.US-WEST-1.AMAZONAWS.COM"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}

    # s3 static settings
    STATIC_LOCATION = "static"
    STATIC_URL = (
        f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_STORAGE_BUCKET_NAME}/{STATIC_LOCATION}/"
    )
    STATICFILES_STORAGE = "trunkplayer_ng.storage_backends.StaticStorage"

    # s3 public media settings
    PUBLIC_MEDIA_LOCATION = "media"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_STORAGE_BUCKET_NAME}/{PUBLIC_MEDIA_LOCATION}/"
    # s3 private media settings
    PRIVATE_MEDIA_LOCATION = "private"
    PRIVATE_FILE_STORAGE = "trunkplayer_ng.storage_backends.PrivateMediaStorage"

    DEFAULT_FILE_STORAGE = "trunkplayer_ng.storage_backends.PrivateMediaStorage"
else:
    STATIC_URL = "/static/"
    STATIC_ROOT = os.path.join(BASE_DIR, "static")
    MEDIA_URL = "/mediafiles/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")
