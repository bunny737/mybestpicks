# Module: Release pipeline

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started. **HELD: do not start or run anything until the owner says
development is finished** (decision 2026-11-02)
**Priority:** P0
**Ticket:** MBP-007
**Plan reference:** docs/mybestpicks_plan_v4.md §9, §12 (hosting and security risks), §13
**Depends on:** 01-06, 08, 10 (all development modules; see the hold above)
**Blocks:** 09

## Purpose
Deploy the site to one small VPS with Docker Compose (Nginx → Gunicorn/Django/Wagtail
→ PostgreSQL), with HTTPS, a canonical apex redirect, nightly off-box backups of the
DB and media, a tested restore and a documented rollback. The step-by-step runbook
is [../deployment.md](../deployment.md).

## Components (as planned; update to as-built)
```
compose (production):
  nginx      TLS, www → apex 301, http → https, static/media passthrough, /admin/ hardening
  app        gunicorn mybestpicks.wsgi, production settings, WhiteNoise
  db         postgres (named volume: pgdata)
  volumes    pgdata, media
  backup     nightly pg_dump + media archive → off-box destination (retention policy)
optional:   Cloudflare DNS/proxy in front of nginx
later:      umami (module 09) as its own service with its own DB/user
```

## Business rules
1. A deploy runs, in order: pull the pinned image → `migrate` → `collectstatic` →
   restart → smoke-test `/`, `/admin/login/`, `/sitemap.xml`, `/robots.txt`,
   `/feed/`.
2. The Wagtail `Site` hostname and port are set to `mybestpicks.in:443`, and
   `WAGTAILADMIN_BASE_URL` matches.
3. Backups cover **both** the DB and the media volume, go to an off-box location,
   and are kept under a stated retention policy.
4. A restore into a clean environment is rehearsed (target: week 8) and the date is
   recorded here.
5. Admin hardening: strong passwords, MFA where available, and optionally an IP
   allowlist or Cloudflare Access. Keep the host OS and images patched.
6. Uptime and error monitoring alert the owner.
7. The existing `mybestpicks.in` DNS and any current site are backed up and
   inspected **before** DNS is cut over.

## Open questions / Decisions
- [DECISION 2026-11-02] The owner has put deployment on hold until development is
  finished, replacing the plan's week-2 minimal deploy. Nothing in this module (no
  `compose.prod.yaml`, Nginx config, backup scripts or server) is built until then.
  The first deploy will already have the sitemap, RSS, legal pages and search, so the
  old "public or hidden early deploy" question is moot. Decide staging versus
  straight-to-production when this module starts.
- [OPEN] VPS provider, region and size.
- [OPEN] Off-box backup destination and retention.
- [OPEN] Error monitoring tool (for example Sentry's free tier, or logs plus an
  uptime monitor).
- [OPEN] Deploy trigger: manual SSH script, or a GitHub Actions deploy gated on CI.

## Changelog
- 2026-11-02  Created stub from plan v4.
- 2026-11-02  Put on hold by the owner: no deployment until development is finished.
