from .base import *  # noqa: F403
from .base import DATABASES, MIDDLEWARE, STORAGES, env

DEBUG = False

# Required: no default, so a missing secret fails loudly at startup.
SECRET_KEY = env("SECRET_KEY")

# Example: ALLOWED_HOSTS=mybestpicks.in,www.mybestpicks.in
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
# Example: CSRF_TRUSTED_ORIGINS=https://mybestpicks.in
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# WhiteNoise serves static files; the manifest storage fingerprints file names so
# a Wagtail upgrade never leaves outdated JS/CSS in browser caches.
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STORAGES["staticfiles"]["BACKEND"] = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

# Reuse database connections between requests.
DATABASES["default"]["CONN_MAX_AGE"] = 60

# HTTPS. Nginx terminates TLS and sends X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS is set by Django (not Nginx), so there is one place to change it. It starts
# short; raise SECURE_HSTS_SECONDS (for example to 31536000) once HTTPS and the
# apex/www redirects are verified. Subdomains and preload stay off on purpose.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
# These two are deliberately off (see above); silence only them so `check --deploy`
# stays clean and any new warning is noticed.
SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W021"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
    },
}
