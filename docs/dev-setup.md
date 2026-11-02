# Local Dev Setup (Windows-first)

Module 01 (scaffold) is built, so these are the real commands. The exact versions
are in [../README.md](../README.md).

## 1. Prerequisites
- Python 3.14 (use the `py` launcher: plain `python` is not on PATH here)
- Docker Desktop, used for local PostgreSQL only
- Git

## 2. First-time setup
```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements/dev.txt -c requirements/constraints.txt
copy .env.example .env
docker compose up -d db
python manage.py migrate
python manage.py createsuperuser
```

The project was created with `wagtail start mybestpicks .`; you do not run that
again. Layout and settings details: [modules/01-scaffold.md](modules/01-scaffold.md).

## 3. Daily workflow
```powershell
.venv\Scripts\Activate.ps1
docker compose up -d db                 # local PostgreSQL 18 on host port 5433
python manage.py migrate
python manage.py runserver              # http://localhost:8000, admin at /admin/
```

Gunicorn does not run on Windows and is used only in Linux production.

## 4. Environment variables
`.env` is git-ignored. Copy it from `.env.example`, which documents every variable:

```dotenv
SECRET_KEY=replace-with-generated-secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://mybestpicks:password@127.0.0.1:5433/mybestpicks
WAGTAILADMIN_BASE_URL=http://localhost:8000
SITE_URL=http://localhost:8000
POSTGRES_DB=mybestpicks
POSTGRES_USER=mybestpicks
POSTGRES_PASSWORD=password
POSTGRES_PORT=5433
# Optional, post-launch (module 14). Never commit a real value:
# TELEGRAM_BOT_TOKEN=
```

- **Use `127.0.0.1`, not `localhost`, for the database host.** `localhost` tries IPv6
  first and every new connection stalls for seconds.
- Port 5433 is used because Windows had reserved 5432 on this machine.
- `manage.py` uses `mybestpicks.settings.dev`; `wsgi.py` (Gunicorn) uses
  `mybestpicks.settings.production`. A `DJANGO_SETTINGS_MODULE` inside `.env` has no
  effect on `manage.py`; set it in the shell if you need another module.

Production values live in the host's secret store, not in a file in git. Production
also needs `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, the live `SITE_URL`, a real
`SECRET_KEY` and a persistent `MEDIA_ROOT`; add `?sslmode=require` to `DATABASE_URL`
if the DB provider requires TLS.

## 5. Checks to run before committing
```powershell
ruff check .
ruff format --check .
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Before a deploy, also run `python manage.py check --deploy` with
`DJANGO_SETTINGS_MODULE=mybestpicks.settings.production` and production env values.

## 6. Updating dependencies (Dependabot is off)
Change the pins in `requirements/*.txt`, install in a clean venv, run the checks
above, then regenerate `requirements/constraints.txt` (see [../README.md](../README.md)).

## 7. Seeding a local content tree
Once module 03 exists:
1. In Wagtail Admin, open Pages → Home → Add child → **Category Page** "Developer
   Setup" (slug `developer-setup`), keep `discovery_mode=force_hide` and publish it.
2. Add **Article Page** children under it. Set `discovery_mode` to `force_show` or
   `auto` to check the nav, sitemap and robots behaviour.
3. Under Settings → **Site settings**, leave `telegram_channel_url` blank to confirm
   that no Telegram CTA renders, then set a test value.

Module 10 adds fixtures and factories for tests.
