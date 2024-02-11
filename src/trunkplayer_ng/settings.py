import os
import uuid
import socket

import hashlib
import logging

from pathlib import Path
from datetime import timedelta

from kombu import Queue
from kombu.entity import Exchange

SHITS_VALID_YO = ['t', '1', 'yeet', 'true', 'yee', 'yes', 'duh', 'yesdaddy', 'ok']

LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(level=LOG_LEVEL)

######################################################################
# 🌶️ SPICY WARNING ‼️
# SENTRY TELEMETRY (OPT IN)
######################################################################
SEND_TELEMETRY = os.getenv("SEND_TELEMETRY", "False").lower() in SHITS_VALID_YO

if SEND_TELEMETRY:
    import sentry_sdk

    SENTRY_DSN = os.getenv("SENTRY_DSN")
    if not SENTRY_DSN:
        raise ValueError("Must set SENTRY_DSN if using SEND_TELEMETRY")

    SENTRY_SAMPLE_RATE = float(os.getenv("SENTRY_SAMPLE_RATE", "1.0"))

    sentry_sdk.init(
        SENTRY_DSN,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=SENTRY_SAMPLE_RATE,
    )

######################################################################
# BASE_DIR
# Build paths inside the project like this: BASE_DIR / 'subdir'.
# https://docs.djangoproject.com/en/5.0/ref/settings/#std:setting-BASE_DIR
######################################################################
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

######################################################################
# DEBUG
# SECURITY WARNING: keep the secret key used in production secret!
# https://docs.djangoproject.com/en/5.0/ref/settings/#std:setting-SECRET_KEY
######################################################################
SECRET_KEY = os.getenv('SECRET_KEY', hashlib.blake2b(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname()).bytes).hexdigest())

######################################################################
# DEBUG
# SECURITY WARNING: don't run with debug turned on in production!
# https://docs.djangoproject.com/en/5.0/ref/settings/#std:setting-DEBUG
######################################################################
DEBUG = os.getenv("DEBUG", "False").lower() in SHITS_VALID_YO

######################################################################
# ROOT_URLCONF
# https://docs.djangoproject.com/en/5.0/ref/settings/#std:setting-ROOT_URLCONF
######################################################################
ROOT_URLCONF = "trunkplayer_ng.urls"

######################################################################
# ROOT_URLCONF
# https://docs.djangoproject.com/en/5.0/ref/settings/#std:setting-WSGI_APPLICATION
######################################################################
WSGI_APPLICATION = "trunkplayer_ng.wsgi.application"

######################################################################
# Custom Auth Model
# https://docs.djangoproject.com/en/5.0/topics/auth/customizing/#substituting-a-custom-user-model
######################################################################
AUTH_USER_MODEL = "users.CustomUser"

######################################################################
# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
######################################################################
LANGUAGE_CODE = "en-us"
USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = os.getenv("TZ", "America/Los_Angeles")

######################################################################
# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
######################################################################
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

######################################################################
# SESSION TIME OUT SETTINGS
# https://github.com/LabD/django-session-timeout
######################################################################
# Session will expire X in seconds
SESSION_EXPIRE_SECONDS = int(
    os.getenv(
        'SESSION_EXPIRE_SECONDS',
        str(
            int(
                timedelta(minutes=30).total_seconds()
            )
        )
    )
)

# By default, the session will expire X seconds after the start of the session.
# To expire the session X seconds after the last activity, use the following setting
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_EXPIRE_AFTER_LAST_ACTIVITY_GRACE_PERIOD = 60 # MIN

# To redirect to a custom URL define the following setting:
SESSION_TIMEOUT_REDIRECT = '/'

######################################################################
# DJANGO CORS HEADERS
# https://github.com/adamchainz/django-cors-headers
######################################################################
# https://github.com/adamchainz/django-cors-headers?tab=readme-ov-file#cors_allowed_origins-sequencestr
CORS_ALLOWED_ORIGINS =              os.getenv("CORS_ALLOWED_HOSTS", "https://localhost").split(" ")

# https://github.com/adamchainz/django-cors-headers?tab=readme-ov-file#cors_allowed_origins-sequencestr
CORS_ALLOW_ALL_ORIGINS =            False

# https://github.com/adamchainz/django-cors-headers?tab=readme-ov-file#cors_allow_all_origins-bool
CORS_ALLOW_CREDENTIALS =            True

# https://github.com/adamchainz/django-cors-headers?tab=readme-ov-file#cors_allow_methods-sequencestr
CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)

######################################################################
# DJANGO SECURITY CONFIG
# DONT LET THE HAKORS WIN
######################################################################

# https://docs.djangoproject.com/en/5.0/ref/settings/#ALLOWED_HOSTS
ALLOWED_HOSTS =                     os.getenv('ALLOWED_HOSTS', '').split(' ')

# https://docs.djangoproject.com/en/5.0/ref/settings/#SESSION_COOKIE_SECURE
SESSION_COOKIE_SECURE =             True

# https://docs.djangoproject.com/en/5.0/ref/settings/#SESSION_COOKIE_SAMESITE
SESSION_COOKIE_SAMESITE =           None

# https://docs.djangoproject.com/en/5.0/ref/settings/#DJANGO_WEB_MAX_REQUESTS
DJANGO_WEB_MAX_REQUESTS =           300

# https://docs.djangoproject.com/en/5.0/ref/settings/#DATA_UPLOAD_MAX_NUMBER_FIELDS
DATA_UPLOAD_MAX_NUMBER_FIELDS =     10000

# https://docs.djangoproject.com/en/5.0/ref/settings/#SECURE_PROXY_SSL_HEADER
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# https://docs.djangoproject.com/en/5.0/ref/settings/#CSRF_COOKIE_SAMESITE
CSRF_TRUSTED_ORIGINS =              CORS_ALLOWED_ORIGINS

# https://docs.djangoproject.com/en/5.0/ref/settings/#CSRF_COOKIE_SAMESITE
CSRF_COOKIE_SAMESITE =              'None'

# https://docs.djangoproject.com/en/5.0/ref/settings/#CSRF_COOKIE_SECURE
CSRF_COOKIE_SECURE =                True

# https://docs.djangoproject.com/en/5.0/ref/settings/#CSRF_COOKIE_HTTPONLY
CSRF_COOKIE_HTTPONLY =              True

# https://docs.djangoproject.com/en/5.0/ref/settings/#CSRF_HEADER_NAME
CSRF_HEADER_NAME =                  "HTTP_CSRFTOKEN"

# https://docs.djangoproject.com/en/5.0/ref/settings/#CSRF_USE_SESSIONS
CSRF_USE_SESSIONS =                 False


######################################################################
# DEBUG OVERIDES
# Do stupid things to make life easier* DONT USE IN PROD
# DONT BE AN ID10T GREG
######################################################################
if DEBUG:
    # DJANGO 
    ALLOWED_HOSTS =                     ["*"]               # Yes
    SECURE_PROXY_SSL_HEADER =           None                # CRED THEF / WEB HAK HAZARD ⚠️
    SESSION_COOKIE_SECURE =             False               # CRED THEF / WEB HAK HAZARD ⚠️
    SESSION_COOKIE_SAMESITE =           None                # CRED THEF / WEB HAK HAZARD ⚠️
    DJANGO_WEB_MAX_REQUESTS =           3000                # DOS HAZARD ⚠️
    DATA_UPLOAD_MAX_NUMBER_FIELDS =     1000000             # DOS HAZARD ⚠️

    # CORS
    CORS_ALLOWED_ORIGINS =              ["*"]               # PHISH / WEB HAK HAZARD ⚠️
    CORS_ALLOW_ALL_ORIGINS =            True                # PHISH / WEB HAK HAZARD ⚠️
    CORS_ALLOW_CREDENTIALS =            True                # PHISH / WEB HAK HAZARD ⚠️
    
    # CSRF
    CSRF_COOKIE_SAMESITE =              'None'              # CRED THEF / WEB HAK HAZARD ⚠️
    CSRF_COOKIE_SECURE =                False               # CRED THEF / WEB HAK HAZARD ⚠️
    CSRF_COOKIE_HTTPONLY =              False               # CRED THEF / WEB HAK HAZARD ⚠️
    CSRF_HEADER_NAME =                  "HTTP_CSRFTOKEN"

    # SESSION EXPIRE
    SESSION_EXPIRE_SECONDS =             timedelta(hours=48).total_seconds()
    SESSION_EXPIRE_AFTER_LAST_ACTIVITY = False

######################################################################
# Application references
# https://docs.djangoproject.com/en/5.0/ref/settings/#std:setting-INSTALLED_APPS
######################################################################
INSTALLED_APPS = [
    "radio",
    "users",
    "mqtt",
    "corsheaders",
    # "django.contrib.sites",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django_celery_results',
    "django_celery_beat",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "drf_yasg",
    'django_filters',
    "storages",
]

######################################################################
# MIDDLEWARE
# https://docs.djangoproject.com/en/5.0/ref/settings/#std:setting-MIDDLEWARE
######################################################################
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    'django_session_timeout.middleware.SessionTimeoutMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

######################################################################
# TEMPLATES
# https://docs.djangoproject.com/en/5.0/ref/settings/#std:setting-TEMPLATES
######################################################################
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

######################################################################
# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
######################################################################
DATABASES = {
    "default": {
        "ENGINE": "django_db_geventpool.backends.postgresql_psycopg2",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASS"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        "ATOMIC_REQUESTS": False,
        "CONN_MAX_AGE": 0,
        'OPTIONS': {
            'MAX_CONNS': 20,
            'REUSE_CONNS': 10
        }
    }
}

######################################################################
# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
######################################################################
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

######################################################################
# LOGGING
# https://docs.djangoproject.com/en/5.0/topics/logging/#configuring-logging
######################################################################
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

######################################################################
# SPLUNK LOGGING
# https://github.com/zach-taylor/splunk_handler
######################################################################
USE_SPLUNK = os.getenv("USE_SPLUNK_LOGGING", "False").lower() in SHITS_VALID_YO
SPLUNK_HOST = os.getenv('SPLUNK_HOST')
SPLUNK_PORT = int(os.getenv('SPLUNK_PORT', '8080'))
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN')
SPLUNK_INDEX = os.getenv('SPLUNK_INDEX')

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

###########################################################
# STATIC FILE STUFFZ
# (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
###########################################################
USE_S3 = os.getenv("USE_S3", "False").lower() in SHITS_VALID_YO
STATICFILES_DIRS = (os.path.join(BASE_DIR, "staticfiles"),)

if USE_S3:
    ######################################################################
    # DJANGO STORAGES
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
    ######################################################################
    AWS_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")

    # Use this to set an ACL on your file such as public-read. If not set the file will be private per Amazon’s default. 
    # If the ACL parameter is set in object_parameters, then this setting is ignored.
    # Defaule: None
    AWS_DEFAULT_ACL = None

    AWS_S3_CUSTOM_DOMAIN = os.getenv("S3_CUSTOM_DOMAIN", f"{AWS_S3_ENDPOINT_URL.replace('https://','')}")
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}

    ######################################################################
    # STATIC FILES
    # https://docs.djangoproject.com/en/5.0/howto/static-files/
    ######################################################################

    # https://docs.djangoproject.com/en/5.0/ref/settings/#std-setting-STATIC_LOCATION
    STATIC_LOCATION = "static"

    # https://docs.djangoproject.com/en/5.0/ref/settings/#std-setting-STATIC_LOCATION
    STATIC_URL = (
        f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_STORAGE_BUCKET_NAME}/{STATIC_LOCATION}/"
    )

    # https://docs.djangoproject.com/en/5.0/ref/settings/#std-setting-STATICFILES_STORAGE
    STATICFILES_STORAGE = "trunkplayer_ng.storage_backends.StaticStorage"

    ######################################################################
    # MEDIA FILES
    # https://docs.djangoproject.com/en/5.0/topics/files/
    ######################################################################
    PUBLIC_MEDIA_LOCATION = "media"
    PRIVATE_MEDIA_LOCATION = "private"
    PRIVATE_FILE_STORAGE = "trunkplayer_ng.storage_backends.PrivateMediaStorage"
    DEFAULT_FILE_STORAGE = "trunkplayer_ng.storage_backends.PrivateMediaStorage"

    # https://docs.djangoproject.com/en/5.0/ref/settings/#media-url
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_STORAGE_BUCKET_NAME}/{PUBLIC_MEDIA_LOCATION}/"
else:
    ######################################################################
    # STATIC FILES
    # https://docs.djangoproject.com/en/5.0/howto/static-files/
    ######################################################################
    STATIC_URL = "/static/"
    STATIC_ROOT = os.path.join(BASE_DIR, "static")
    ######################################################################
    # MEDIA FILES
    # https://docs.djangoproject.com/en/5.0/topics/files/
    ######################################################################
    MEDIA_URL = "/mediafiles/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")

######################################################################
# DRF REST_FRAMEWORK Settings
# https://www.django-rest-framework.org/#installation
######################################################################
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        'rest_framework.authentication.SessionAuthentication',
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "trunkplayer_ng.auth.TokenAuthSupportCookie"
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    )
}

REST_AUTH_SERIALIZERS = {
    "USER_DETAILS_SERIALIZER": "users.serializers.UserSerializer",
}

######################################################################
# DRFYASG SWAGGER Settings
# https://drf-yasg.readthedocs.io/en/stable/settings.html
######################################################################
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
    }
}

######################################################################
# Simple JWT
# https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html
######################################################################
REST_USE_JWT = True
JWT_AUTH_HTTPONLY = True
JWT_AUTH_SECURE = True
JWT_AUTH_SAMESITE = "None"
JWT_AUTH_COOKIE = "TPNG-app-auth"
JWT_AUTH_REFRESH_COOKIE = "refresh-token"
JWT_AUTH_RETURN_EXPIRATION=True
ACCOUNT_LOGOUT_ON_GET = True

SIMPLE_JWT = {
    # Duration before the access token expires
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),

    # Duration before the refresh token expires
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),

    # Whether to create a new token each time a token is refreshed
    "ROTATE_REFRESH_TOKENS": False,

    # Whether to blacklist the token after rotation
    "BLACKLIST_AFTER_ROTATION": False,

    # Update the user's last login time when the token is issued
    "UPDATE_LAST_LOGIN": False,

    # Algorithm used to sign the token
    "ALGORITHM": "HS256",

    # Key used to sign the token
    "SIGNING_KEY": SECRET_KEY,

    # Key used to verify the token signature. Leave blank for symmetric algorithms like HS256
    "VERIFYING_KEY": "",

    # Intended recipient of the token
    "AUDIENCE": None,

    # Issuer of the token
    "ISSUER": None,

    # JSON encoder class to use when encoding the token
    "JSON_ENCODER": None,

    # URL to retrieve the JSON Web Key Set for token verification
    "JWK_URL": None,

    # Leeway in validating "exp" and "nbf" claims in seconds
    "LEEWAY": 0,

    # Types of authorization headers that are accepted (e.g., Bearer)
    "AUTH_HEADER_TYPES": ("Bearer",),

    # Name of the header where the token will be found
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",

    # Field in the User model that is used as the unique identifier in the token payload
    "USER_ID_FIELD": "id",

    # Claim in the token that maps to the user's unique identifier
    "USER_ID_CLAIM": "user_id",

    # Rule to determine if a user should be authenticated
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    # Classes of tokens that the application can issue
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),

    # Claim in the token that indicates the type of the token
    "TOKEN_TYPE_CLAIM": "token_type",

    # Class used for representing a token user
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    # JWT ID claim name
    "JTI_CLAIM": "jti",

    # Claim name for the expiration time of a sliding token
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",

    # Duration before a sliding token expires
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),

    # Duration before a sliding refresh token expires
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    # Serializer class for token obtainment
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",

    # Serializer class for token refresh
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",

    # Serializer class for token verification
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",

    # Serializer class for token blacklisting
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",

    # Serializer class for obtaining a sliding token
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",

    # Serializer class for refreshing a sliding token
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}

######################################################################
# SMTP SETTINGS
# https://docs.djangoproject.com/en/5.0/topics/email/
######################################################################

# SET TO CONSOLE IN DEBUG
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# EMAIL CONFIG
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
EMAIL_SUBJECT_PREFIX = os.getenv("EMAIL_SUBJECT_PREFIX")

# SMTP AUTH
EMAIL_HOST = os.getenv("SMTP_HOST", "")
EMAIL_PORT = os.getenv("SMTP_PORT", "")
EMAIL_HOST_USER = os.getenv("SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("SMTP_PASS", "")

# SMTP SSL/TLS
EMAIL_USE_TLS = os.getenv("SMTP_USE_TLS", "False").lower() in SHITS_VALID_YO
EMAIL_USE_SSL = os.getenv("SMTP_USE_SSL", "False").lower() in SHITS_VALID_YO

######################################################################
# CELRY SETTINGS
# https://docs.djangoproject.com/en/5.0/topics/email/
######################################################################

# Custom test runner class for use with Celery and Django.
CELERY_TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'

# Specifies the scheduler to use for periodic tasks with Celery Beat.
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# URL for the message broker. Environment variable 'CELERY_BROKER_URL' is used to configure this.
# The message broker is a service used to queue and distribute tasks.
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")

# Maximum number of tasks a worker will process before it's killed and replaced.
# This helps in releasing memory and refreshing the worker.
CELERYD_MAX_TASKS_PER_CHILD = 1500

# The number of tasks a worker will prefetch to improve performance.
# A value of 1 means the worker will only take a task when it's free.
CELERYD_PREFETCH_MULTIPLIER = 1

# If False, tasks are acknowledged before they are executed. 
# If True, tasks are acknowledged after their execution, providing fail-over.
CELERY_ACKS_LATE = False

# If True, store additional information about the task in the result backend.
CELERY_RESULT_EXTENDED = True

# If True, disables rate limits set on tasks. 
# Rate limits can limit the number of tasks processed per time unit.
CELERY_DISABLE_RATE_LIMITS = True

# The time (in seconds) after which the task result expires. 
# Here, it's set to 120 seconds (2 minutes), not 1 minute.
CELERY_TASK_RESULT_EXPIRES = 120

# If True, Celery will emit task-sent events that can be captured by monitors.
CELERY_SEND_SENT_EVENT = True
CELERY_TASK_TRACK_STARTED = True

# Automatically create missing queues when sending tasks.
# Useful when dynamically adding tasks and you don't want to set up queues manually.
CELERY_CREATE_MISSING_QUEUES = True

# Default queue used when no custom queue is specified for a task.
CELERY_TASK_DEFAULT_QUEUE = "default"

# Default exchange used when no custom exchange is specified for a task.
CELERY_TASK_DEFAULT_EXCHANGE = "default"

# Specifies the content types Celery workers should accept. Here, only 'application/json' is accepted.
# This setting ensures that the workers will only accept tasks with JSON content.
CELERY_ACCEPT_CONTENT = ["application/json"]

# Serialization format for task requests. Set to 'json', which means task inputs will be serialized in JSON format.
# JSON is a lightweight data-interchange format and is easy for humans to read and write.
CELERY_TASK_SERIALIZER = "json"

# Serialization format for task results. Also set to 'json', making the output consistent with the task input.
# This ensures that the results of tasks are also in JSON format.
CELERY_RESULT_SERIALIZER = "json"

# Backend used to store task results. Here, it's set to use Django's database.
# The 'django-db' backend stores task results in the Django project's database.
CELERY_RESULT_BACKEND = 'django-db'

# Timezone configuration for Celery. It uses the 'TIME_ZONE' variable from your settings.
# This setting ensures that all datetime information in Celery (like task timestamps) will use this timezone.
CELERY_TIMEZONE = TIME_ZONE

# Modules to import when Celery starts. This is where Celery will look for defined tasks.
# In this case, it's importing the 'radio.tasks' module to find task definitions.
CELERY_IMPORTS = ("radio.tasks",)

# Configuration of Celery queues with priorities.
CELERY_QUEUES = (
    Queue(
        "default",
        Exchange("default"),
        routing_key="default",
        max_priority=0,
        message_ttl=timedelta(minutes=30).total_seconds()
    ),
    Queue(
        "transmission_ingest",
        Exchange("transmission_ingest"),
        routing_key="transmission_ingest",
        max_priority=10,
        message_ttl=timedelta(hours=48).total_seconds()
    ),
    Queue(
        "transmission_forwarding",
        Exchange("transmission_forwarding"),
        routing_key="transmission_forwarding",
        max_priority=5,
        message_ttl=timedelta(hours=24).total_seconds()
    ),
    Queue(
        "radio_alerts",
        Exchange("radio_alerts"),
        routing_key="radio_alerts",
        max_priority=8,
        message_ttl=timedelta(minutes=30).total_seconds()
    ),
    Queue(
        "tranmission_push",
        Exchange("tranmission_push",),
        routing_key="tranmission_push",
        max_priority=10,
        message_ttl=timedelta(minutes=60).total_seconds()
    ),
    Queue(
        "radio_refrence",
        Exchange("radio_refrence"),
        routing_key="radio_refrence",
        max_priority=1,
        message_ttl=timedelta(minutes=60).total_seconds()
    ),
)

# Defines custom routing of tasks to queues.
CELERY_TASK_ROUTES = {
    "radio.tasks.new_transmission_handler": {
        "queue": "transmission_ingest"
    },
    "radio.tasks.forward_Transmission": {
        "queue": "transmission_forwarding"
    },
    "radio.tasks.send_transmission": {
        "queue": "transmission_forwarding"
    },
    "radio.tasks.forward_Incident": {
        "queue": "transmission_forwarding"
    },
    "radio.tasks.send_Incident": {
        "queue": "transmission_forwarding"
    },
    "radio.tasks.import_radio_refrence": {
        "queue": "radio_refrence"
    },
    "radio.tasks.send_tx_notifications": {
        "queue": "radio_alerts"
    },
    "radio.tasks.publish_user_notification": {
        "queue": "radio_alerts"
    },
    "radio.tasks.dispatch_web_notification": {
        "queue": "radio_alerts"
    },
    "radio.tasks.broadcast_transmission": {
        "queue": "tranmission_push"
    },
    "radio.tasks.send_transmission_signal": {
        "queue": "tranmission_push"
    },
}

REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'jwt-auth',
}

MQTT_AMQP_QUQUE = "tpng_mqtt"

# URL for the message broker. Environment variable 'CELERY_BROKER_URL' is used to configure this.
# The message broker is a service used to queue and distribute tasks.
SOCKETS_BROKER_URL = os.getenv("CELERY_BROKER_URL") #+ '/sockets'

logging.info("Initalized settings")
# YOU THINK YOU DID SOMETHING STUPID... Youre proably right 🫰👉
try:
    LOCAL_SETTINGS
except NameError:
    try: 
       from trunkplayer_ng.settings_local import *
       logging.info("Initalized local settings")
    except ImportError:
        pass
