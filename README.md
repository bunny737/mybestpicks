# MyBestPicks.in

Editorial buying guides and comparisons for shoppers in India, starting with the
Developer Setup hub. Audience first: no revenue target in the first 90 days, and
affiliate links are optional.

- Scope and architecture: [docs/mybestpicks_plan_v4.md](docs/mybestpicks_plan_v4.md)
- Agent and contributor rules: [CLAUDE.md](CLAUDE.md)
- Module status board: [docs/modules/README.md](docs/modules/README.md)
- Local setup: [docs/dev-setup.md](docs/dev-setup.md)

## Stack and pinned versions

| Layer | Version |
|---|---|
| Python | 3.14 |
| Django | 6.1.2 |
| Wagtail | 8.0.1 |
| PostgreSQL | 18 (Docker image `postgres:18`) |
| psycopg | 3.3.6 |
| Ruff | 0.17.3 |
| Bootstrap (vendored) | 5.3.8 |

Wagtail 8.0.1 lists Python 3.14 and Django 6.1 as supported. Verified on
2 November 2026 (module 01). Bump versions by hand and update this table.

## Quick start (Windows PowerShell)

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements/dev.txt -c requirements/constraints.txt
copy .env.example .env
docker compose up -d db
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://localhost:8000/ and http://localhost:8000/admin/.

## Dependencies

- `requirements/base.txt`, `production.txt` and `dev.txt` list **direct**
  dependencies, each pinned with `==`.
- `Markdown` renders the article body's Markdown block (see
  `docs/modules/04-editorial-blocks.md`).
- `requirements/constraints.txt` pins the full resolved set, including
  transitive packages. Install with `-c requirements/constraints.txt`.
- Dependabot is **off** by owner decision. To update by hand: change the pins in
  the requirements files, install in a clean venv, run the checks below, then
  regenerate the constraints:
  `pip freeze > requirements/constraints.txt` (keep the comment header and make sure
  `ruff` stays in the list).

## Checks (also run in CI)

```powershell
ruff check .
ruff format --check .
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Before a deploy, also run `python manage.py check --deploy` with
`DJANGO_SETTINGS_MODULE=mybestpicks.settings.production` and production env values.
