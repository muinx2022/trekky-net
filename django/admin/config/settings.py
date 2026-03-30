import os
import sys
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

SETTINGS_DIR = Path(__file__).resolve().parent
BASE_DIR = SETTINGS_DIR.parent

_project_root_candidates = [
    BASE_DIR.parent.parent,
    BASE_DIR.parent,
    BASE_DIR,
]
PROJECT_ROOT = next(
    (
        candidate
        for candidate in _project_root_candidates
        if (candidate / "web").exists() or (candidate / ".env").exists()
    ),
    BASE_DIR,
)
ADMIN_APP_DIR = next(
    (
        candidate
        for candidate in (
            BASE_DIR / "admin-app",
            BASE_DIR.parent / "admin-app",
        )
        if candidate.exists()
    ),
    BASE_DIR / "admin-app",
)
WEB_DIR = PROJECT_ROOT / "web"

for dotenv_path in (PROJECT_ROOT / ".env", BASE_DIR / ".env"):
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
        break
UPLOAD_PROVIDER = os.getenv("UPLOAD_PROVIDER", "local").lower()
USE_CLOUDINARY = UPLOAD_PROVIDER == "cloudinary"

if str(ADMIN_APP_DIR) not in sys.path:
    sys.path.insert(0, str(ADMIN_APP_DIR))

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret-key-at-least-32-bytes-long")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if host]
CORS_ALLOW_ALL_ORIGINS = os.getenv("DJANGO_CORS_ALLOW_ALL", "true").lower() == "true"
CORS_ALLOWED_ORIGINS = [origin for origin in os.getenv("DJANGO_CORS_ALLOWED_ORIGINS", "").split(",") if origin]
CSRF_TRUSTED_ORIGINS = [origin for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "trekky_apps.common",
    "trekky_apps.accounts",
    "trekky_apps.taxonomy",
    "trekky_apps.content",
    "trekky_apps.engagement",
    "trekky_apps.moderation",
    "trekky_apps.integrations",
    "admin_app",
]

if USE_CLOUDINARY:
    INSTALLED_APPS.extend(
        [
            "cloudinary_storage",
            "cloudinary",
        ]
    )

INSTALLED_APPS.append("django.contrib.staticfiles")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            ADMIN_APP_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "vi"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "Asia/Ho_Chi_Minh")

USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [ADMIN_APP_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/admin-app/login/"
LOGIN_REDIRECT_URL = "/admin-app/"
LOGOUT_REDIRECT_URL = "/admin-app/login/"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback/")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

SPECTACULAR_SETTINGS = {
    "TITLE": "Trekky API",
    "DESCRIPTION": "Django backend for Trekky admin, web, and moderation flows.",
    "VERSION": "1.0.0",
}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_BEAT_SCHEDULE = {
    "run-due-ai-automation-every-minute": {
        "task": "trekky_apps.integrations.tasks.run_due_ai_automation_task",
        "schedule": 60.0,
    },
}
MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
MEILISEARCH_API_KEY = os.getenv("MEILISEARCH_API_KEY", "")

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
DEFAULT_FILE_STORAGE = STORAGES["default"]["BACKEND"]
STATICFILES_STORAGE = STORAGES["staticfiles"]["BACKEND"]

if USE_CLOUDINARY:
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": os.getenv("CLOUDINARY_NAME", ""),
        "API_KEY": os.getenv("CLOUDINARY_KEY", ""),
        "API_SECRET": os.getenv("CLOUDINARY_SECRET", ""),
        "SECURE": os.getenv("CLOUDINARY_SECURE", "true").lower() == "true",
    }
    STORAGES["default"] = {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    }
    DEFAULT_FILE_STORAGE = STORAGES["default"]["BACKEND"]
    MEDIA_URL = os.getenv(
        "CLOUDINARY_MEDIA_URL",
        f"https://res.cloudinary.com/{CLOUDINARY_STORAGE['CLOUD_NAME']}/",
    )
