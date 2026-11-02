from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DEBUG", default=True)

# Development-only default. Never used in production (see production.py).
SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-only-not-for-production")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
