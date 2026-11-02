# Module: Project scaffold

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Done (2026-11-02)
**Priority:** P0
**Ticket:** MBP-001
**Plan reference:** docs/mybestpicks_plan_v4.md §2, §3, §8
**Depends on:** none
**Blocks:** every other module

## Purpose
Gives the project a reproducible base: the native Wagtail starter layout,
PostgreSQL, pinned requirements, environment-based settings, Docker Compose for the
local DB, CI, and a README that records the exact versions.

## Layout (as-built)
The repo root is the project root, created with `wagtail start mybestpicks .`:

```text
manage.py · pyproject.toml (Ruff config) · compose.yaml · Dockerfile · .dockerignore
.env.example · .gitignore · README.md · .github/workflows/ci.yml
mybestpicks/settings/{base,dev,production}.py · urls.py · wsgi.py
mybestpicks/templates/{base,404,500}.html                        (starter location)
mybestpicks/static/{css,js}/                                     (starter location)
home/        HomePage (starter); templates in home/templates/home/
search/      starter search view + template, reused by module 08
editorial/   empty app (module 03)
catalog/     empty app (module 05)
seo/         empty app, JSON-LD and template-tag helpers ONLY (module 06)
tests/       empty package for cross-app tests
requirements/{base,production,dev,constraints}.txt
```

There is no `asgi.py`: the starter does not generate one and the site runs on
Gunicorn (WSGI).

## Settings and environment (as-built)
- `base.py` reads env with `django-environ` (and an optional `.env` in the repo
  root; real environment variables win). `DATABASE_URL` is required.
- `SECRET_KEY` is **not** in `base.py`. `dev.py` falls back to an obviously insecure
  key; `production.py` has no default and fails at startup when it is missing.
- `INSTALLED_APPS` adds `home, editorial, catalog, seo, search`,
  `wagtail.contrib.{redirects,settings,sitemaps}`, `django.contrib.sitemaps` and
  `django.contrib.postgres`. The last one is **required** by Wagtail's PostgreSQL
  search backend: without it `manage.py check` fails with `postgres.E005`.
- The `wagtail.contrib.settings` context processor is enabled.
- `LANGUAGE_CODE=en-in`, `TIME_ZONE=Asia/Kolkata`. `MEDIA_ROOT` comes from env
  (default `./media`; the production volume path is set in env).
- `production.py`: `DEBUG=False`, WhiteNoise middleware and manifest storage,
  `CONN_MAX_AGE=60`, `SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT`, secure
  session/CSRF cookies, HSTS set by **Django** (not Nginx), `CSRF_TRUSTED_ORIGINS`
  and `ALLOWED_HOSTS` from env, console logging. DB TLS is requested with
  `?sslmode=require` in `DATABASE_URL`.
- `wsgi.py` defaults to the **production** settings; `manage.py` defaults to dev.
- `Dockerfile`: single stage on `python:3.14-slim-bookworm` (psycopg binary and
  Pillow ship their own native libraries), installs
  `requirements/production.txt -c constraints.txt`, runs `collectstatic` at build
  with throwaway values, and starts Gunicorn. It does not run migrations.
- `compose.yaml` runs PostgreSQL 18 only (local development). The production
  compose file is module 07.

## Versions (as-built)
Python 3.14 · Django 6.1.2 · Wagtail 8.0.1 · PostgreSQL 18 · psycopg 3.3.6 ·
Ruff 0.17.3. Wagtail 8.0.1 lists Python 3.14 and Django 6.1 as supported.

## CI (GitHub Actions)
`.github/workflows/ci.yml`, on pushes to `main` and on pull requests: check that
every requirement line is pinned with `==`, install with the constraints file,
`ruff check`, `ruff format --check`, `manage.py check`,
`makemigrations --check --dry-run`, `check --deploy --fail-level WARNING` with
production settings, and `manage.py test`, against a PostgreSQL 18 service container.
Do **not** enable Dependabot (alerts, security updates or version updates); see
Decisions.

## Business rules
1. Every dependency is pinned to an exact version. CI fails on an unpinned line.
2. `makemigrations --check --dry-run` is clean on `main`.
3. `check --deploy` with production settings shows no warnings. Only
   `security.W005` and `security.W021` (HSTS subdomains and preload) are silenced,
   on purpose.
4. No secret is committed. `.env` is git-ignored and `.env.example` holds only placeholders.

## Local gotchas (Windows)
- **Use `127.0.0.1`, not `localhost`, in `DATABASE_URL`.** `localhost` resolves to
  IPv6 first, nothing listens there, and every new connection stalls for seconds
  (the test runner appeared to hang for minutes).
- PostgreSQL is published on host port **5433**: Windows had port 5432 reserved
  and Docker could not bind it.
- `python` is not on PATH in this environment; create the venv with
  `py -3.14 -m venv .venv`.

## Open questions / Decisions
- [DECISION 2026-11-02] Owner instruction: do not turn on Dependabot alerts. This
  overrides the plan §8 line "Dependabot/Renovate alerts". Do not add
  `.github/dependabot.yml` or enable Dependabot in the repo settings. Dependency
  updates are reviewed and pinned by hand. Ask the owner before adding any other
  automated dependency tool (for example Renovate).
- [DECISION 2026-11-02] The repo root is the Wagtail project root. This matches the
  plan §3 tree and avoids a nested `mybestpicks/mybestpicks/mybestpicks/`.
- [DECISION 2026-11-02] Project-wide templates and static files stay where the
  starter puts them (`mybestpicks/templates/`, `mybestpicks/static/`), not at the
  repo root as drawn in plan §3. CLAUDE.md requires the native starter layout. The
  starter's welcome page and CSS were deleted in module 03.
- [DECISION 2026-11-02] Python 3.14 (owner choice). Wagtail 8.0.1 / Django 6.1.2
  were the newest releases and officially support it.
- [DECISION 2026-11-02] Plain pinned `requirements/*.txt` (owner choice), no
  `pip-tools`. Direct dependencies live in `base/production/dev.txt`; the full
  resolved set lives in `constraints.txt` so installs (and the Docker build) are
  reproducible without another tool.
- [DECISION 2026-11-02] HSTS is set in Django and starts at 3600 seconds. Raise
  `SECURE_HSTS_SECONDS` only after HTTPS and the apex/www redirects are verified in
  production.
- [DECISION 2026-11-02] PostgreSQL 18 (`postgres:18`), the current major release.
  Its image keeps data under `/var/lib/postgresql/<major>`, so the volume is
  mounted at `/var/lib/postgresql`.
- [DECISION 2026-11-02] Git author identity was unset. Set repo-local (not global) to
  `bunny737 <bajibaba997@gmail.com>`, taken from the GitHub remote and the owner's
  account email. Change it with `git config user.name/user.email` if you want
  another name on future commits.
- [OPEN] The starter search view reads `?query=`; module 06/08 docs say `?q=`.
  Decide one parameter name in module 08.

## Changelog
- 2026-11-02  Created stub from plan v4.
- 2026-11-02  Committed and pushed to origin/main (31fdff8).
- 2026-11-02  Built: starter scaffold, split env-driven settings, PostgreSQL 18
  compose, pinned requirements, Dockerfile, CI, README. Ruff, `check`,
  `check --deploy`, `makemigrations --check` and the 4 starter tests pass.
