from pathlib import Path
from datetime import timedelta

from decouple import config, Csv
import dj_database_url

from corsheaders.defaults import default_headers


# =============================================================================
# BASE CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-change-this-in-production-xyz123",
)

DEBUG = config(
    "DEBUG",
    default=False,
    cast=bool,
)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="dailypakistanzindabadbackend-5r6naj6n.b4a.run,localhost,127.0.0.1",
    cast=Csv(),
)


# =============================================================================
# INSTALLED APPS
# =============================================================================

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "django_celery_beat",

    # Local
    "accounts",
    "articles",
]


# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    # CORS middleware MUST be before CommonMiddleware
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =============================================================================
# URL / WSGI
# =============================================================================

ROOT_URLCONF = "pzn_news.urls"

WSGI_APPLICATION = "pzn_news.wsgi.application"


# =============================================================================
# TEMPLATES
# =============================================================================

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


# =============================================================================
# DATABASE
# =============================================================================

DATABASE_URL = config("DATABASE_URL", default="")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

    if DATABASES["default"].get("ENGINE", "").endswith("postgresql"):
        DATABASES["default"]["OPTIONS"] = {
            "sslmode": "require",
        }

else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "ur"

TIME_ZONE = "Asia/Karachi"

USE_I18N = True
USE_TZ = True


# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)


# =============================================================================
# MEDIA FILES
# =============================================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =============================================================================
# DEFAULT MODEL FIELD
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =============================================================================
# CUSTOM USER MODEL
# =============================================================================

AUTH_USER_MODEL = "accounts.User"


# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],

    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],

    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),

    "PAGE_SIZE": 20,
}


# =============================================================================
# SIMPLE JWT
# =============================================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=6),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
}


# =============================================================================
# CORS CONFIGURATION
# =============================================================================
#
# IMPORTANT:
# The production Vercel URL is explicitly included here.
# Do NOT depend on DEBUG for production CORS.
#

CORS_ALLOWED_ORIGINS = [
    "https://dailypakistanzindabad.vercel.app",

    # Local development
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]


# =============================================================================
# CSRF
# =============================================================================

CSRF_TRUSTED_ORIGINS = [
    "https://dailypakistanzindabad.vercel.app",
]


# =============================================================================
# URL CONFIGURATION
# =============================================================================

APPEND_SLASH = True


# =============================================================================
# CELERY
# =============================================================================

REDIS_URL = config(
    "REDIS_URL",
    default="redis://localhost:6379/0",
)

CELERY_BROKER_URL = REDIS_URL

CELERY_RESULT_BACKEND = REDIS_URL

CELERY_ACCEPT_CONTENT = [
    "json",
]

CELERY_TASK_SERIALIZER = "json"

CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = "Asia/Karachi"


# =============================================================================
# CELERY BEAT
# =============================================================================

from celery.schedules import crontab


CELERY_BEAT_SCHEDULE = {
    "refresh-rss-all": {
        "task": "articles.tasks.refresh_rss_category",
        "schedule": 300.0,
        "args": ("all",),
    },

    "refresh-rss-pakistan": {
        "task": "articles.tasks.refresh_rss_category",
        "schedule": 300.0,
        "args": ("pakistan",),
    },

    "refresh-rss-politics": {
        "task": "articles.tasks.refresh_rss_category",
        "schedule": 300.0,
        "args": ("politics",),
    },

    "refresh-rss-sports": {
        "task": "articles.tasks.refresh_rss_category",
        "schedule": 300.0,
        "args": ("sports",),
    },

    "refresh-rss-business": {
        "task": "articles.tasks.refresh_rss_category",
        "schedule": 300.0,
        "args": ("business",),
    },

    "refresh-rss-technology": {
        "task": "articles.tasks.refresh_rss_category",
        "schedule": 300.0,
        "args": ("technology",),
    },

    "refresh-rss-international": {
        "task": "articles.tasks.refresh_rss_category",
        "schedule": 300.0,
        "args": ("international",),
    },
}