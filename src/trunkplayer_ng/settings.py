import os
import logging

from pathlib import Path
from datetime import timedelta

from kombu import Queue
from kombu.entity import Exchange

import pymysql
pymysql.install_as_MySQLdb()

SEND_TELEMETRY = os.getenv("SEND_TELEMETRY", "False").lower() in ("true", "1", "t")


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()

# Splunk settings
USE_SPLUNK = os.getenv("USE_SPLUNK_LOGGING", "False").lower() in ("true", "1", "t")
SPLUNK_HOST = os.getenv('SPLUNK_HOST')
SPLUNK_PORT = int(os.getenv('SPLUNK_PORT', '8080'))
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN')
SPLUNK_INDEX = os.getenv('SPLUNK_INDEX')

# Greylog settings
USE_GREYLOG = os.getenv("USE_GREYLOG_LOGGING", "False").lower() in ("true", "1", "t")
GREYLOG_HOST = os.getenv('GREYLOG_HOST')
GREYLOG_PORT = int(os.getenv('GREYLOG_PORT', '12201'))


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(created)f %(exc_info)s %(filename)s %(funcName)s %(levelname)s %(levelno)s %(lineno)d %(module)s %(message)s %(pathname)s %(process)s %(processName)s %(relativeCreated)d %(thread)s %(threadName)s'
        }
    },
    'handlers': {        
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': LOG_LEVEL
        }
    }
}

if USE_SPLUNK:
    LOGGING['handlers']['splunk'] = {
            'level': LOG_LEVEL,
            'class': 'splunk_handler.SplunkHandler',
            'formatter': 'json',
            'host': SPLUNK_HOST,
            'port': SPLUNK_PORT,
            'token': SPLUNK_TOKEN,
            'index': SPLUNK_INDEX,
            'sourcetype': 'json',
        },
    LOGGING['loggers']['']['handlers'].append('splunk')

if USE_GREYLOG:
    LOGGING['handlers']['graypy'] = {
            'level': LOG_LEVEL,
            'class': 'graypy.GELFUDPHandler',
            'host': GREYLOG_HOST,
            'port': GREYLOG_PORT
        },
    LOGGING['loggers']['']['handlers'].append('graypy')

AUDIO_DOWNLOAD_HOST = os.environ.get("AUDIO_DOWNLOAD_HOST", default="example.com")
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", default="*").split(" ")

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

INSTALLED_APPS = [
    "radio",
    "users",
    "corsheaders",
    'django_celery_results',
    "django_celery_beat",
    "rest_framework_simplejwt",
    "rest_framework",
    "rest_framework.authtoken",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth.registration",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "drf_yasg",
    'django_filters',
    "dj_rest_auth",
    # "rest_framework_simplejwt.token_blacklist",
    "storages",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "trunkplayer_ng.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "trunkplayer_ng.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.mysql"),
        "NAME": os.environ.get("MYSQL_DATABASE", "TrunkPlayer"),
        "USER": os.environ.get("MYSQL_USER", "TrunkPlayer"),
        "PASSWORD": os.environ.get("MYSQL_PASSWORD", "s3CuRiTy"),
        "HOST": os.environ.get("MYSQL_HOST", "localhost"),
        "PORT": os.environ.get("MYSQL_PORT", "3306"),
    }
}


AUTH_USER_MODEL = "users.CustomUser"

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = str(os.getenv("TZ", "America/Los_Angeles"))

USE_I18N = True

USE_L10N = True

USE_TZ = True


if os.getenv("FORCE_SECURE", "False").lower() in ("true", "1", "t"):
    # Honor the 'X-Forwarded-Proto' header for request.is_secure()
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

USE_S3 = os.getenv("USE_S3", "False").lower() in ("true", "1", "t")

if USE_S3:
    # aws settings
    AWS_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
    AWS_DEFAULT_ACL = None
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_S3_ENDPOINT_URL.replace('https://','')}"
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


STATICFILES_DIRS = (os.path.join(BASE_DIR, "staticfiles"),)


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "trunkplayer_ng.auth.TokenAuthSupportCookie",
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    )
}
REST_USE_JWT = True
JWT_AUTH_HTTPONLY = True
JWT_AUTH_SECURE = True
JWT_AUTH_SAMESITE = "None"
JWT_AUTH_COOKIE = "TPNG-app-auth"
JWT_AUTH_REFRESH_COOKIE = "refresh-token"
JWT_AUTH_RETURN_EXPIRATION=True
ACCOUNT_LOGOUT_ON_GET = True

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}


REST_AUTH_SERIALIZERS = {
    "USER_DETAILS_SERIALIZER": "users.serializers.UserSerializer",
}


SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
    }
}


## DJANGO ALL AUTH
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = "/?verification=1"
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/?verification=1"

SITE_ID = 1
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = os.getenv("EMAIL_PORT", "")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() in ("true", "1", "t")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() in ("true", "1", "t")
EMAIL_SUBJECT_PREFIX = ""
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")

# CELERY_ALWAYS_EAGER = True
CELERY_TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'
CELERY_TASK_RESULT_EXPIRES = 120  # 1 mins
CELERYD_MAX_TASKS_PER_CHILD = 1500
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_CREATE_MISSING_QUEUES = True
CELERY_ACKS_LATE = False
CELERY_DISABLE_RATE_LIMITS = True

CELERY_QUEUES = (
    Queue("default", Exchange("default"), routing_key="default"),
    Queue(
        "transmission_ingest",
        Exchange("transmission_ingest"),
        routing_key="transmission_ingest",
        queue_arguments={"x-max-priority": 10},
    ),
    Queue(
        "transmission_forwarding",
        Exchange("transmission_forwarding"),
        routing_key="transmission_forwarding",
        queue_arguments={"x-max-priority": 5},
    ),
    Queue(
        "radio_alerts",
        Exchange("radio_alerts"),
        routing_key="radio_alerts",
        queue_arguments={"x-max-priority": 8},
    ),
    Queue(
        "tranmission_push",
        Exchange("tranmission_push"),
        routing_key="tranmission_push",
        queue_arguments={"x-max-priority": 10},
    ),
    Queue(
        "radio_refrence",
        Exchange("radio_refrence"),
        routing_key="radio_refrence",
        queue_arguments={"x-max-priority": 1},
    ),
)
CELERY_TASK_ROUTES = {
    "radio.tasks.new_transmission_handler": {"queue": "transmission_ingest"},
    "radio.tasks.forward_Transmission": {"queue": "transmission_forwarding"},
    "radio.tasks.send_transmission": {"queue": "transmission_forwarding"},
    "radio.tasks.forward_Incident": {"queue": "transmission_forwarding"},
    "radio.tasks.send_Incident": {"queue": "transmission_forwarding"},
    "radio.tasks.import_radio_refrence": {"queue": "radio_refrence"},
    "radio.tasks.send_tx_notifications": {"queue": "radio_alerts"},
    "radio.tasks.publish_user_notification": {"queue": "radio_alerts"},
    "radio.tasks.dispatch_web_notification": {"queue": "radio_alerts"},
    "radio.tasks.broadcast_transmission": {"queue": "tranmission_push"},
}
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_DEFAULT_EXCHANGE = "default"


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "ampq://user:pass@127.0.0.1/")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TIMEZONE = str(os.getenv("TZ", "America/Chicago"))
CELERY_IMPORTS = ("radio.tasks",)
# Application definition


CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_HOSTS", default="https://dev.trunkplayer.io https://trunk-player-frontend.vercel.app https://localhost:3000 http://localhost:3000 https://localhost:3001 http://localhost:3001").split(" ")
# [
#     "http://localhost:3000",
#     "https://localhost:3000",
#     "http://127.0.0.1:3000",
#     "https://127.0.0.1:3000",
#     "http://localhost:3001",
#     "https://localhost:3001",
#     "http://127.0.0.1:3001",
#     "https://127.0.0.1:3001",
#     "https://dev.trunkplayer.io",
#     "https://trunk-player-frontend.vercel.app",
# ]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = True
CSRF_HEADER_NAME="HTTP_CSRFTOKEN"


# Load our local settings 
try:
    LOCAL_SETTINGS
except NameError:
    try:
        from trunkplayer_ng.settings_local import *
        logging.info("Initalized local settings", extra={"foo","bar"})
    except ImportError:
        logging.info("Local settings not initalized", extra={"foo","bar"})
        pass

if SEND_TELEMETRY:
    import sentry_sdk

    sentry_sdk.init(
        os.getenv(
            "SENTRY_DSN",
            "https://d83fa527e0044728b20de7dab246ea6f@bigbrother.weathermelon.io/2",
        ),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
    )
logging.info("Initalized settings", extra={"foo","bar"})