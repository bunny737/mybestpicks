# Module: Release pipeline

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** 🟨 In Progress. Owner confirmed development finished (2026-11-02); the
hold is lifted. First deploy is live at https://mybestpicks.in (HTTPS, real
traffic). Remaining: backups, restore rehearsal, uptime/error monitoring, admin
hardening beyond IAP-only SSH, and a repeatable deploy script (see Open
questions).
**Priority:** P0
**Ticket:** MBP-007
**Plan reference:** docs/mybestpicks_plan_v4.md §9, §12 (hosting and security risks), §13
**Depends on:** 01-06, 08, 10 (all ✅; verified with a from-scratch `manage.py test`
run before deploying — see the editorial 0004 migration fix in
[06-trust-privacy-seo.md](06-trust-privacy-seo.md))
**Blocks:** 09

## Purpose
Deploy the site to one small VPS with Docker Compose (Nginx → Gunicorn/Django/Wagtail
→ PostgreSQL), with HTTPS, a canonical apex redirect, nightly off-box backups of the
DB and media, a tested restore and a documented rollback. The step-by-step runbook
is [../deployment.md](../deployment.md).

## Components (as built)
```
mybestpicks-app VM (GCP e2-micro, asia-south1-a, project pglive-prod, Docker Compose):
  nginx      nginx:1.27-alpine. TLS via Let's Encrypt (certbot, host-installed,
             --webroot). www → apex 301, http → https 301. /media/ served
             directly from the media volume; everything else proxied to app.
  app        mybestpicks-app:latest (built from repo Dockerfile), gunicorn,
             production settings, WhiteNoise for static (baked into the image
             at build time).
  volumes    media (named volume)
  secrets    .env.production on the VM only (mode 600), never in git.
  static IP  35.234.223.110 (reserved GCE address "mybestpicks-ip")
  firewall   tag "edge" (shared pglive-prod rule, 80/443 from 0.0.0.0/0) +
             tag "mybestpicks" (new rule mybestpicks-allow-iap-ssh, 22 from
             35.235.240.0/20 only — IAP, no public SSH). No service account
             attached (--no-service-account --no-scopes): the app doesn't call
             any GCP API.
  TLS renewal certbot.timer (systemd, enabled). Deploy hook
             /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh reloads the
             nginx container after renewal (needed because nginx runs
             containerized, not as the host service certbot normally manages).
later:      umami (module 09) as its own service with its own DB/user

db: shared Cloud SQL instance pglive-pg-prod (Postgres 16, db-g1-small,
  asia-south1-c, project pglive-prod) — the same instance already hosting
  pg_platform (pglive.in) and travel_platform (mytravelplanner.in).
  mybestpicks has its own database (`mybestpicks`) and role (`mybestpicks`),
  never touching the other two. Connection is public IP + password auth +
  `sslmode=require` (the instance enforces `sslMode: ENCRYPTED_ONLY` anyway),
  locked to the app VM's /32 via Cloud SQL authorized networks (added by the
  owner; see Decisions — an IAM/Cloud-SQL-Auth-Proxy grant was attempted first
  but blocked by Claude Code's own permission classifier as a sensitive
  IAM-grant action, so the simpler password+allowlist path already documented
  below was used instead). Cloud SQL's own automated backups cover this
  instance already (verified: enabled, 14 retained, point-in-time recovery on
  — pre-existing, not something this module added) — the module's "off-box
  backup" open question below is about the **app VM's media volume**, which
  has no backup yet.
```

## Business rules
1. ✅ A deploy runs, in order: build the pinned image → `migrate` →
   `collectstatic` (baked into the image at build time) → `up -d` → smoke-test
   `/`, `/admin/login/`, `/sitemap.xml`, `/robots.txt`, `/search/`. First deploy
   done manually over SSH (see Open questions for the repeatable version).
2. ✅ The Wagtail `Site` hostname and port are set to `mybestpicks.in:443`;
   `WAGTAILADMIN_BASE_URL`/`SITE_URL`/`CSRF_TRUSTED_ORIGINS` match in
   `.env.production`.
3. ⬜ Backups cover **both** the DB and the media volume, go to an off-box
   location, and are kept under a stated retention policy. The DB side is
   already covered by Cloud SQL's existing automated backups (14 retained,
   point-in-time recovery). The app VM's media volume has **no backup yet** —
   still open.
4. ⬜ A restore into a clean environment is rehearsed and the date is recorded
   here. Not done yet.
5. 🟨 Admin hardening: SSH is IAP-only (no public port 22), OS Login enabled,
   minimal VM IAM footprint (no service account/scopes). Strong passwords/MFA
   on the Wagtail admin account and any IP allowlist/Cloudflare Access for
   `/admin/` are still open.
6. ⬜ Uptime and error monitoring alert the owner. Not set up yet.
7. ✅ The existing `mybestpicks.in` DNS was inspected before cutover: the A
   record pointed at `pglive-worker` (34.14.158.50) but nothing was actually
   being served there for that hostname (confirmed: TCP connects, no HTTP
   response) — no live content was at risk. The owner made the DNS change
   (GoDaddy, not something this session has API access to).

## Open questions / Decisions
- [DECISION 2026-11-02] The owner put deployment on hold until development was
  finished, replacing the plan's week-2 minimal deploy. The hold is now lifted
  (owner: "development is finished", 2026-11-02) — verified with a clean
  `ruff check`/`ruff format --check`/`manage.py check`/
  `makemigrations --check --dry-run`/`manage.py test` run (333 tests, from a
  fresh database) before any deploy step, which is how the editorial 0004
  migration-ordering bug above was caught. Went straight to production, no
  staging — the first deploy already has the sitemap, RSS, legal pages and
  search, so the old "public or hidden early deploy" question is moot.
- [DECISION 2026-11-02] Topology: mybestpicks runs on its **own** VPS instance
  (app + nginx only, no local Postgres container). The database runs on the
  **existing shared Postgres instance** that already hosts pglive.in and
  mytravelplanner.in, in its own database with its own role — never a shared
  schema or role with the other sites. This keeps app-level blast radius
  (deploys, Nginx, OS patching) isolated per site while consolidating DB
  operations (backups, patching, HA) on infrastructure already maintained.
  Requirements this adds, to implement when the module starts:
  - `DATABASE_URL` must use `sslmode=require` (or `verify-full` if a CA cert is
    available) since the connection crosses the network between two VPS instances.
  - The DB host's firewall/`pg_hba.conf` must allowlist the mybestpicks VPS's IP
    specifically, not `0.0.0.0/0`.
  - mybestpicks's DB credentials stay in the mybestpicks VPS's env file only
    (invariant 10); they are not reused across sites.
  - The DB host's existing nightly backup job must be extended to cover the new
    `mybestpicks` database, still landing off-box. (As built: Cloud SQL's own
    automated backup already covers the whole instance, mybestpicks included —
    nothing extra was needed on the DB side.)
  - A Postgres version bump on the shared instance is now a cross-site change —
    coordinate it against all three sites' compatibility, not just this one.
- [DECISION 2026-11-02] As-built: VPS provider is GCP, project `pglive-prod`
  (same project as `pglive-worker`, owner's choice — reuses the existing VPC/
  firewall), zone `asia-south1-a` (same as `pglive-worker`, owner's choice —
  lowest latency to the DB and to an Indian audience; e2-micro is **not** in
  GCP's free tier in this region, unlike us-west1/central1/east1, so this is a
  small real monthly cost). Instance name `mybestpicks-app`, machine type
  `e2-micro`.
- [DECISION 2026-11-02] DB connection method: `pglive-worker` connects to Cloud
  SQL via IAM (`roles/cloudsql.client` on its service account) rather than a
  network allowlist — the more secure, existing pattern. The matching setup for
  mybestpicks (a dedicated service account + IAM role binding) was attempted
  but **blocked by Claude Code's own permission classifier** as a sensitive
  IAM-grant action. Fell back to the password + `sslmode=require` +
  authorized-networks `/32` allowlist approach already planned above instead
  — Cloud SQL enforces `sslMode: ENCRYPTED_ONLY` regardless, so the connection
  is still encrypted; it's a weaker isolation model than IAM auth (a leaked
  password is reusable until rotated; a leaked IAM token is not), but
  consistent with what this module already documented before the IAM path was
  tried. Revisit the IAM/Cloud SQL Auth Proxy approach later if wanted — it
  needs the owner (or a granted PowerShell IAM permission) to run the
  `gcloud iam service-accounts create` / `add-iam-policy-binding` commands.
- [DECISION 2026-11-02] `docker-compose` (classic v1, from Debian 12's apt
  repo) is used instead of the `docker compose` v2 plugin — Debian 12 doesn't
  package `docker-compose-plugin`, and adding Docker's own apt repo felt like
  more surface than this single-VM deploy needed. Works fine for this compose
  file; revisit if a v2-only feature is ever needed.
- [DECISION 2026-11-02] Installing `python3-certbot-nginx` on Debian pulled in
  a **host-level nginx package as a dependency and auto-started it**, which
  collided with the containerized nginx on ports 80/443. Fixed by stopping and
  disabling the host nginx service; TLS issuance uses `certbot certonly
  --webroot` instead (the nginx plugin was never actually used). A deploy hook
  at `/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh` reloads the
  containerized nginx after each renewal, since certbot's webroot plugin
  doesn't know to do that itself. `certbot.timer` (systemd) handles scheduling;
  confirmed working with `certbot renew --dry-run`.
- [OPEN] Off-box backup for the app VM's **media volume** (the DB side is
  already covered — see above). Destination and retention not chosen yet.
- [OPEN] Error monitoring tool (for example Sentry's free tier, or logs plus an
  uptime monitor). Not set up.
- [OPEN] Deploy trigger: so far every deploy step was run manually over SSH
  (package the repo into a tarball locally, scp it, rebuild, migrate, restart).
  Turn this into a repeatable script, or a GitHub Actions deploy gated on CI,
  before relying on it for routine deploys.
- [OPEN] Restore rehearsal not yet done for either the DB or the media volume.
- [OPEN] Uptime/error monitoring and Wagtail admin MFA/IP-allowlisting not yet
  set up.

## Changelog
- 2026-11-02  Created stub from plan v4.
- 2026-11-02  Put on hold by the owner: no deployment until development is finished.
- 2026-11-02  Owner lifted the hold. Deployed to production: GCP e2-micro VM
  (`mybestpicks-app`, project `pglive-prod`, zone `asia-south1-a`) running
  nginx + the app in Docker Compose; database is a dedicated `mybestpicks`
  database/role on the shared `pglive-pg-prod` Cloud SQL instance (same
  instance as pglive.in/mytravelplanner.in); TLS issued via Let's Encrypt
  (certbot --webroot) with auto-renewal verified via dry run; DNS cut over by
  the owner at GoDaddy after confirming nothing was actually being served at
  the old placeholder A record. `mybestpicks.in` is live over HTTPS with the
  Wagtail `Site` record, HSTS, secure cookies and the www→apex/http→https
  redirects all verified. See Decisions for what's still open (backups,
  monitoring, a repeatable deploy script, restore rehearsal).
