# CLAUDE.md — Agent Rules

Read this file at the start of every session before writing any code.

## What we are building
MyBestPicks.in: an editorial site for shoppers in India. It publishes buying guides,
comparisons and explainers, starting with the **Developer Setup** hub. The audience
comes first: no revenue target for the first 90 days. Affiliate links (Cuelinks for
Flipkart, and Amazon later) are optional and never block publishing. The site is not
a shop, has no checkout, and never claims hands-on testing it did not do.

Source of truth for scope: [docs/mybestpicks_plan_v4.md](docs/mybestpicks_plan_v4.md)
(v4 baseline, 1 Nov 2026; the architecture is frozen).

Key docs:
- [docs/modules/README.md](docs/modules/README.md): status board and module specs
- [docs/dev-setup.md](docs/dev-setup.md): local setup on Windows
- [docs/deployment.md](docs/deployment.md): VPS runbook, backups and rollback
- [docs/editorial-workflow.md](docs/editorial-workflow.md): evidence, images, prices, hubs
- [docs/telegram-distribution.md](docs/telegram-distribution.md): manual posts and UTMs
- [docs/launch-checklist.md](docs/launch-checklist.md): launch gates and MVP definition of done

## Locked tech stack — do not deviate
- Python 3.x (a supported stable release, pinned), Django at a version compatible
  with the pinned Wagtail release, and a stable Wagtail release, also pinned.
  Record the exact versions in README.md. Never use an unpinned `latest`.
- DB: PostgreSQL (a current supported major version). Search uses Wagtail's
  database search backend on PostgreSQL. **No Elasticsearch.**
- Presentation: server-rendered Django templates, Bootstrap 5 and as little
  JavaScript as possible. **No React, no SPA, no separate API (DRF) in the MVP.**
- Layout: the native `wagtail start mybestpicks` layout, with the repo root as the
  project root (`manage.py`, `mybestpicks/settings/{base,dev,production}.py`). The
  top-level apps are `home/`, `editorial/`, `catalog/` and `seo/`; `seo/` holds thin
  JSON-LD and template-tag helpers only. Do not move the apps under `apps/` after the
  first migration.
- Prefer Wagtail built-ins: `wagtail.contrib.sitemaps`, `wagtail.contrib.redirects`
  and `wagtail.contrib.settings`. Use `RoutablePageMixin` only when a page truly
  needs its own routes.
- Serving: Gunicorn and Nginx on **one VPS, run with Docker Compose**, with Cloudflare
  as an optional DNS/proxy. WhiteNoise serves static files. Media lives in a
  persistent named volume. The DB and media are both backed up to an off-box
  destination every night. Runbook: [docs/deployment.md](docs/deployment.md).
- Local development uses a Python venv on Windows, with PostgreSQL in Docker Compose.
  Gunicorn is for Linux production only.
- CI: GitHub Actions running Ruff, tests, Django/Wagtail checks and a migration check.
  **Do not enable Dependabot** (no `.github/dependabot.yml`, no repo-setting alerts;
  owner decision 2026-11-02). Dependency updates are reviewed and pinned by hand.
- Analytics: Google Search Console, plus self-hosted Umami after a privacy review.
  GA4 is optional and runs only behind consent.

## 10 Non-negotiable invariants

1. SERVER-RENDERED CONTENT. The full article text, headings, tables and links are
   in the HTML response. No essential SEO content may depend on client-side JS.

2. PRICES ONLY AS DATED EDITORIAL TEXT (owner decision 2026-11-04, relaxing the
   original "no prices"). A price may appear only as editor-supplied text inside an
   article, with an "as of <date>" stamp next to it (for example "₹1,499 as of
   4 Nov 2026"). Still no price fields on `Product` or `MerchantOffer`, no price
   columns or widgets driven by data, and no scraped or fetched prices. Buttons and
   CTAs never show a price. Price text older than 30 days is re-verified or removed.
   A title that depends on price ("under ₹1,000") needs a recent `last_verified_at`
   and a re-verification task (default 30 days). Rewrite the title if it is not
   verified.

3. ONE SOURCE OF EDITORIAL JUDGEMENT. Product facts (`Product` snippet) are
   global and reusable. Verdicts, pros and cons, ranking, labels and evidence for
   one article live **only** in that article's `ProductCardBlock` StreamField
   values. There is no `ArticleProduct` model. A `ComparisonTableBlock` derives its
   products from the article's product cards and never re-selects products.

4. PRECOMPUTED RENDERING CONTEXT. `ArticlePage.get_context()` collects every
   `ProductCardBlock` in order, then resolves products, active offers and
   normalised specs once, before any block renders. The result is passed as
   `article_products`. Product cards must not query the DB one card at a time.

5. DISCOVERY IS `discovery_mode` ONLY. `CategoryPage.discovery_mode` takes
   `force_hide` (the default), `auto` (3 or more live direct `ArticlePage`
   children) or `force_show`. It is the single rule for navigation, homepage
   tiles, category directories and the sitemap. `show_in_menus` is secondary,
   and nothing hard-codes a category list. A hub that is not discoverable stays
   live, but the hub page is `noindex,follow` and is left out of the sitemap; its
   articles stay indexable. Adding an editorial category needs no code change.

6. AFFILIATE LINKS ARE OPTIONAL AND STRICT.
   - Offers must use `https://`.
   - The *tracking-link* hostname must be in `Merchant.allowed_link_domains`.
   - Store `network` (Direct/Cuelinks) separately from `destination_domain`.
   - Never resolve redirects on the server (SSRF risk).
   - Never load the Cuelinks auto-convert JavaScript, and never use cloaked redirects.
   - Every outbound affiliate anchor carries `rel="sponsored nofollow noopener"`.
   - CTAs read "View at Flipkart" or "Check price at Amazon".

7. DISCLOSURE ONLY WHEN TRUE. The in-article affiliate disclosure renders only
   when `article_products` contains an active offer that will render, and it
   appears before the first CTA. Never claim Amazon Associate status before the
   account is actually accepted.

8. HONEST EVIDENCE AND IMAGES.
   - When `tested_by_editor=True`, evidence notes or media are required, enforced
     in `ProductCardBlock.clean()` with tests for both valid and invalid input.
   - Every product image records its provenance (`owned_original`,
     `manufacturer_licensed`, `other_licensed` or `permitted_program_content`)
     with evidence or credit.
   - Never use retailer listing photos, reviews, ratings or descriptions.

9. PRIVACY BY DEFAULT. There is no `AffiliateClickEvent` table and no server-side
   click log. Telegram subscriber data is never imported. Collect as little email
   data as possible, with clear consent and a way to unsubscribe. Any GA4 event
   (such as `affiliate_click`) fires only after consent. Cookieless analytics does
   not mean the consent rules do not apply.

10. SECRETS IN ENV ONLY, AND CONFIG BEFORE CODE.
    - `SECRET_KEY`, DB credentials and the Telegram bot token live only in env or
      the host's secret store. Never put them in Wagtail settings, source code or
      the repo.
    - Store the Telegram channel URL and label in Wagtail site settings, and render
      nothing when they are unset. Never invent a URL.
    - Telegram posting always needs a human to approve it. There is no automatic
      on-publish hook.

## Build order — strict dependency sequence
Module numbers match the plan's MBP tickets. The build order is the dependency
order, not the numeric order. The status board is
[docs/modules/README.md](docs/modules/README.md).

01 scaffold → 03 page-models → 02 base-layout → 05 product-catalog
→ 04 editorial-blocks → 06 trust-privacy-seo → 08 search → 10 editorial-qa
→ 07 release-pipeline → 09 metrics
→ (P2, only after launch: 14 telegram-posting, 13 amazon-eligibility,
12 adsense, 11 merchant-api)

**NO DEPLOYMENT until development is finished** (owner decision 2026-11-02). This
overrides the plan's "minimal production deploy in week 2". Do not provision a
server, change DNS, push images or deploy anywhere, and do not start module 07,
until the owner says development is complete. Local development and CI are fine.
Module 07 stays last among the P0/P1 modules; module 09 follows it because Search
Console and Umami need a live site.

## Per-task workflow
1. Read this file and the relevant `docs/modules/<nn>-*.md` spec.
2. Check that every dependency is ✅ in docs/modules/README.md.
3. Implement in this order: model/snippet/block → migration → Wagtail panels and
   admin → template → tests.
4. Write a test for every business rule in the spec, covering both the valid and
   the invalid case where validation is involved.
5. For any model or schema change:
   a. `python manage.py makemigrations`
   b. `python manage.py migrate`, and confirm it applies cleanly
   c. `python manage.py makemigrations --check --dry-run`, which must be clean
      (CI runs this too)
6. Run `ruff check .`, `ruff format --check .`, `python manage.py check` and
   `python manage.py test` before you call the task done. Before any deploy, also
   run `python manage.py check --deploy --settings=mybestpicks.settings.production`.
7. Update the module spec so it matches what was actually built, in the same commit.
8. Update the status in docs/modules/README.md.
9. Record every judgement call in the module spec under "Decisions", with a date.

## When to stop and ask (do not guess)
- The plan is silent or ambiguous about affiliate, disclosure, privacy/consent or
  image-rights behaviour.
- A task needs a new dependency, a new service (Redis, Celery, object storage,
  Elasticsearch) or a change to the stack above.
- A task adds price fields or stored price data, click logging, scraping, user
  accounts or comments. All of these are out of scope. (Dated prices written as
  article text are allowed; see invariant 2.)
- A new `product_type` is needed (it requires `catalog/specs.py` and tests).
  Confirm the spec keys first.
- Any deploy, or any change to production DNS, the existing `mybestpicks.in`
  content or the Telegram channel (see the no-deploy rule above). Inspect first and
  never overwrite.
- Applying to an affiliate program or AdSense, or showing affiliate status on the site.
