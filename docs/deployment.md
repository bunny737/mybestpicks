# Deployment — single VPS production (mybestpicks.in)

Plan reference: [mybestpicks_plan_v4.md §9](mybestpicks_plan_v4.md). Module spec:
[modules/07-release-pipeline.md](modules/07-release-pipeline.md).

Status: **live** at https://mybestpicks.in (owner lifted the deployment hold on
2026-11-02). Backups for the app VM's media volume, uptime/error monitoring, a
restore rehearsal and a repeatable deploy script are still open — see the
module 07 spec for details and as-built specifics (exact resource names, IPs,
decisions). This file is being corrected to match the as-built deploy as that
work continues.

## 1. Architecture

```
mybestpicks.in, www.mybestpicks.in  → GCP static IP 35.234.223.110 (GoDaddy DNS)

mybestpicks-app VM (GCP e2-micro, asia-south1-a, project pglive-prod, Docker Compose)
  nginx    :80 → 301 https · :443 TLS (Let's Encrypt, certbot --webroot on the
           host) · www → apex 301 · /media/ served directly · everything else
           proxied to app
  app      gunicorn + Django/Wagtail (production settings, WhiteNoise for
           static, baked into the image at build time)
           media    volume: media   (originals + Wagtail renditions)
later: umami (own service, own DB/user), module 09

Shared Cloud SQL instance pglive-pg-prod (Postgres 16, asia-south1-c, project
pglive-prod) — also hosts pglive.in and mytravelplanner.in's databases.
  mybestpicks has its own database + role on this instance — never a shared
  schema/role with the other sites. Connection is public IP + password auth +
  sslmode=require, locked to the app VM's IP via Cloud SQL authorized networks.
  backup   Cloud SQL's own automated backups (already enabled on this
           instance: 14 retained, point-in-time recovery) — nothing extra
           needed on the DB side. The media volume above has no backup yet.
```

Object storage for media is deferred until it is needed.

## 2. Before the first deploy (do not skip)
1. **Back up and inspect** the current `mybestpicks.in` DNS records and any existing
   site. Make sure no important content or email (MX) records get overwritten.
2. Confirm domain control and registrar access.
3. Choose a provider and size for the mybestpicks **app** VPS. Do not pick a vendor
   on a teaser price alone (plan budget: about ₹3,000–8,000 for the first 90 days
   in total).
4. On the **shared Postgres instance** (the pglive.in/mytravelplanner.in DB host),
   create a dedicated `mybestpicks` database and a dedicated role with its own
   password — not reused from another site. Open the DB port's firewall /
   `pg_hba.conf` to the new app VPS's IP specifically.

## 3. Deployment sequence
1. Provision the app VPS: OS updates, a non-root deploy user, SSH keys only, a
   firewall (22/80/443), and Docker with Compose. **No local Postgres container** —
   the DB lives on the shared instance.
2. Create the env/secret file on the host (never in git): `SECRET_KEY`,
   `DATABASE_URL` (pointing at the shared DB host, `sslmode=require`),
   `ALLOWED_HOSTS=mybestpicks.in,www.mybestpicks.in`,
   `CSRF_TRUSTED_ORIGINS=https://mybestpicks.in`,
   `WAGTAILADMIN_BASE_URL=https://mybestpicks.in`,
   `SITE_URL=https://mybestpicks.in`, and
   `DJANGO_SETTINGS_MODULE=mybestpicks.settings.production`.
3. Confirm the app VPS can reach the shared DB host over TLS on the DB port, then
   deploy the pinned app image.
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
As built, every deploy so far has been run by hand over SSH (no repeatable
script yet — see module 07's open questions):
```bash
# locally: package the repo (excluding .venv, .git, media, __pycache__) and
# scp the tarball to the VM, keeping the existing .env.production in place.
cd ~/mybestpicks
docker-compose -f compose.prod.yaml build app
docker-compose -f compose.prod.yaml run --rm app python manage.py migrate
docker-compose -f compose.prod.yaml up -d app nginx
# smoke test (step 8), then run update_index if search_fields changed (module 08)
```
Note: this VM has `docker-compose` (classic v1), not the `docker compose` v2
plugin — Debian 12 doesn't package the v2 plugin (see module 07 Decisions).
If a future VM has v2, swap in `docker compose`.

## 5. Backups and restore
- **DB:** already covered by Cloud SQL's own automated backups on
  `pglive-pg-prod` (14 retained, point-in-time recovery) — nothing extra to run.
- **Media (not done yet):** needs a nightly tar of the app VM's `media` volume
  copied to an off-box destination, with a retention policy (for example 7
  daily and 4 weekly; decide and record it).
- **Restore rehearsal (not done yet):** restore both into a clean environment,
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
