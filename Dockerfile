# Production image: Django + Wagtail served by Gunicorn. Nginx, PostgreSQL and the
# volumes are defined in compose.prod.yaml (module 07).
FROM python:3.14-slim-bookworm

# psycopg[binary] and Pillow ship wheels with their own native libraries, so no
# system build packages are needed.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=mybestpicks.settings.production \
    PORT=8000

RUN useradd --create-home wagtail
WORKDIR /app

# Dependencies first, so this layer is cached until the requirements change.
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt \
    -c requirements/constraints.txt

COPY --chown=wagtail:wagtail . .

# MEDIA_ROOT should be a mounted volume in production (see .env.example).
RUN mkdir -p /app/media /app/static && chown wagtail:wagtail /app/media /app/static

USER wagtail

# Build-time collectstatic needs settings to load but never touches the database,
# so these values are throwaway placeholders.
RUN SECRET_KEY=build-only ALLOWED_HOSTS=localhost \
    DATABASE_URL=postgresql://build:build@localhost/build \
    python manage.py collectstatic --noinput

EXPOSE 8000

# Migrations are NOT run here: the deploy runs `manage.py migrate` explicitly.
CMD ["sh", "-c", "exec gunicorn mybestpicks.wsgi:application --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY:-3}"]
