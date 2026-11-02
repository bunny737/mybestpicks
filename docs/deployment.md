# Deployment — single VPS production (mybestpicks.in)

Plan reference: [mybestpicks_plan_v4.md §9](mybestpicks_plan_v4.md). Module spec:
[modules/07-release-pipeline.md](modules/07-release-pipeline.md).

Status: **not deployed**. The provider, backup destination and monitoring tool are
still open (see the module 07 spec). Treat the first run as a test of this runbook,
and correct this file afterwards.

## 1. Architecture

```
(optional) Cloudflare DNS/proxy
  mybestpicks.in        → VPS
  www.mybestpicks.in    → VPS → 301 → https://mybestpicks.in/   (apex is canonical)
VPS (Docker Compose)
  nginx    :80 → 301 https · :443 TLS · static/media · /admin/ hardening
  app      gunicorn + Django/Wagtail (production settings, WhiteNoise)
  db       PostgreSQL           volume: pgdata
           media                volume: media   (originals + Wagtail renditions)
  backup   nightly pg_dump + media archive → off-box destination
later: umami (own service, own DB/user), module 09
```

Object storage for media is deferred until it is needed.

## 2. Before the first deploy (do not skip)
1. **Back up and inspect** the current `mybestpicks.in` DNS records and any existing
   site. Make sure no important content or email (MX) records get overwritten.
2. Confirm domain control and registrar access.
3. Choose a provider and size. Do not pick a vendor on a teaser price alone (plan
   budget: about ₹3,000–8,000 for the first 90 days in total).

## 3. Deployment sequence
1. Provision the VPS: OS updates, a non-root deploy user, SSH keys only, a firewall
   (22/80/443), and Docker with Compose.
2. Create the env/secret file on the host (never in git): `SECRET_KEY`,
   `DATABASE_URL`, `ALLOWED_HOSTS=mybestpicks.in,www.mybestpicks.in`,
   `CSRF_TRUSTED_ORIGINS=https://mybestpicks.in`,
   `WAGTAILADMIN_BASE_URL=https://mybestpicks.in`,
   `SITE_URL=https://mybestpicks.in`, and
   `DJANGO_SETTINGS_MODULE=mybestpicks.settings.production`.
3. Start `db`, then deploy the pinned app image.
4. `python manage.py migrate` → `python manage.py collectstatic --noinput` →
   `python manage.py check --deploy`.
5. Check that the media volume persists: upload an image, render a rendition, restart
   the containers and confirm both survive.
6. In Wagtail Settings → Sites, set the hostname to `mybestpicks.in`, the port to
   `443` and the root page to the HomePage.
7. Issue TLS (Let's Encrypt, or Cloudflare origin certificates), redirect
   http → https and www → apex, then cut over DNS.
8. Smoke-test `/`, `/admin/`, `/robots.txt`, `/sitemap.xml`, `/feed/`, `/search/?q=test`,
   an article preview and (if any exist) an affiliate CTA's `rel` attributes.
9. Connect Search Console (DNS TXT), submit the sitemap and check that the site can
   be crawled.
10. Set up nightly DB and media backups, uptime alerts and the rollback procedure
    (below), then rehearse a restore.

## 4. Routine deploy
```bash
git pull                      # or pull the tagged image
docker compose -f compose.yaml -f compose.prod.yaml build app
docker compose ... run --rm app python manage.py migrate
docker compose ... run --rm app python manage.py collectstatic --noinput
docker compose ... up -d app nginx
# smoke test (step 8), then run update_index if search_fields changed (module 08)
```
Update the file names above to the real ones once module 07 exists.

## 5. Backups and restore
- **Nightly:** `pg_dump -Fc` plus a tar of the media volume, copied to an off-box
  destination. Keep a retention policy (for example 7 daily and 4 weekly; decide
  and record it).
- **Restore rehearsal** (target: week 8): restore both into a clean environment,
  then confirm pages, images and admin login work. Record the date in module 07.

## 6. Rollback
1. Redeploy the previous image or tag.
2. If a migration ran and is not backward-compatible, restore the DB from the
   pre-deploy dump. Take a dump **before** every migration-bearing deploy.
3. Write up what happened in module 07 under Decisions.

## 7. Security
- Admin: strong unique passwords and MFA where available. Optionally restrict
  `/admin/` by IP or Cloudflare Access.
- Keep the OS, Docker images and pinned dependencies patched. Review and bump
  dependencies by hand; Dependabot stays off (owner decision 2026-11-02,
  [modules/01-scaffold.md](modules/01-scaffold.md)).
- HTTPS everywhere, with no mixed content.
- Staging (if any): authentication or `X-Robots-Tag: noindex`, never indexable.
