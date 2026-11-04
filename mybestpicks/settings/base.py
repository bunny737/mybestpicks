"""
Base settings for mybestpicks.in, shared by dev and production.

Configuration comes from environment variables (see .env.example). Nothing
secret lives in this file. SECRET_KEY is set in dev.py and production.py only,
so production can never silently fall back to a development key.
"""

from pathlib import Path

import environ
from django.contrib.messages import constants as messages_constants

PROJECT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = PROJECT_DIR.parent

env = environ.Env()
# A local .env file is optional; real environment variables always win.
environ.Env.read_env(BASE_DIR / ".env")


# Application definition

INSTALLED_APPS = [
    "home",
    "editorial",
    "catalog",
    "seo",
    "search",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.settings",
    "wagtail.contrib.sitemaps",
    "wagtail.contrib.table_block",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "taggit",
    "django_filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.postgres",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "seo.middleware.SearchIndexingProtectionMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "mybestpicks.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            PROJECT_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
                "home.context_processors.site_navigation",
                "seo.context_processors.seo_defaults",
            ],
        },
    },
]

WSGI_APPLICATION = "mybestpicks.wsgi.application"


# Database: PostgreSQL only, configured through DATABASE_URL.
# For a provider that requires TLS, add ?sslmode=require to the URL.

DATABASES = {"default": env.db("DATABASE_URL")}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
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


# Internationalization: English-language content for India.

LANGUAGE_CODE = "en-in"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# Static files and media

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STATICFILES_DIRS = [
    PROJECT_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "static"
STATIC_URL = "/static/"

# In production MEDIA_ROOT points at the persistent Docker volume.
MEDIA_ROOT = env.path("MEDIA_ROOT", default=str(BASE_DIR / "media"))
MEDIA_URL = "/media/"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Django limits a form to 1000 fields by default, but complex page models can
# exceed that in Wagtail's page editor.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000


# Wagtail settings

WAGTAIL_SITE_NAME = "MyBestPicks"

# Search: Wagtail's database backend on PostgreSQL. No Elasticsearch.
# https://docs.wagtail.org/en/stable/topics/search/backends.html
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}

# Base URL for full URLs in the Wagtail admin (e.g. notification emails).
# No '/admin' and no trailing slash.
WAGTAILADMIN_BASE_URL = env("WAGTAILADMIN_BASE_URL", default="http://localhost:8000")

# Public site URL, for canonical links, feeds and structured data.
SITE_URL = env("SITE_URL", default="http://localhost:8000")

# Set true for any public staging or review environment. Production remains
# indexable unless explicitly configured otherwise.
BLOCK_SEARCH_INDEXING = env.bool("BLOCK_SEARCH_INDEXING", default=False)

# Editorial QA audit (module 10): a product's last fact-check, or an offer's last
# manual link check, counts as stale after this many days.
EDITORIAL_AUDIT_STALE_DAYS = env.int("EDITORIAL_AUDIT_STALE_DAYS", default=30)

# Bootstrap has no "alert-error" class; map Django's ERROR level to "danger" so
# django.contrib.messages renders with the right alert colour out of the box.
MESSAGE_TAGS = {messages_constants.ERROR: "danger"}

# Email (module 06 opt-in signup: confirmation and unsubscribe links). The
# console backend in dev.py prints these instead of sending them.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@mybestpicks.in")

# Recorded against each subscriber as the consent text they agreed to. Bump this
# whenever the signup form's consent copy changes materially.
EMAIL_CONSENT_TEXT_VERSION = env("EMAIL_CONSENT_TEXT_VERSION", default="2026-11-02")

# Allowed file extensions for documents in the document library.
# See https://docs.wagtail.org/en/stable/advanced_topics/deploying.html#user-uploaded-files
WAGTAILDOCS_EXTENSIONS = [
    "csv",
    "docx",
    "key",
    "odt",
    "pdf",
    "pptx",
    "rtf",
    "txt",
    "xlsx",
    "zip",
]

# Maximum upload size for documents in bytes.
WAGTAILDOCS_MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


# Google AdSense defaults (Module 12, P2/post-launch; disabled by default)
ADSENSE_PUBLISHER_ID = env("ADSENSE_PUBLISHER_ID", default="")
ADSENSE_ENABLED = env.bool("ADSENSE_ENABLED", default=False)
ADSENSE_AUTO_ADS = env.bool("ADSENSE_AUTO_ADS", default=False)
ADSENSE_IN_ARTICLE_SLOT_ID = env("ADSENSE_IN_ARTICLE_SLOT_ID", default="")
ADSENSE_FEED_SLOT_ID = env("ADSENSE_FEED_SLOT_ID", default="")
