# Module Index & Status Board

Build in the dependency order below, which is **not** numeric order. Do not start a
module until every module it depends on is ✅. Module numbers are the plan's
MBP-0xx ticket numbers ([../mybestpicks_plan_v4.md §14](../mybestpicks_plan_v4.md)).

## Status
⬜ Not Started · 🟨 In Progress · ✅ Done

| Order | # | Module | Spec file | Priority | Depends on | Target week | Status |
|---|---|--------|-----------|---|---|---|---|
| 1 | 01 | Project scaffold | 01-scaffold.md | P0 | none | 1 (Nov 1–7) | ✅ |
| 2 | 03 | Page models (Home, Category, Article, Author, Standard) | 03-page-models.md | P0 | 01 | 1–2 | ✅ |
| 3 | 02 | Base layout and dynamic navigation | 02-base-layout.md | P0 | 01, 03 | 2 (Nov 8–14) | ✅ |
| 4 | 05 | Product catalog (Brand, Product, Merchant, Offer, specs; product types provisional) | 05-product-catalog.md | P0 | 01 | 3 (Nov 15–21) | ✅ |
| 5 | 04 | Editorial blocks (ProductCard, ComparisonTable, …) | 04-editorial-blocks.md | P0 | 03, 05 | 3–5 | ✅ |
| 6 | 06 | Trust, privacy and SEO | 06-trust-privacy-seo.md | P0 | 02, 03, 04 | 2 (legal pages) · 4 (sitemap, RSS, Telegram link) | ✅ |
| 7 | 08 | Internal search | 08-search.md | P1 | 02, 03 | 7 | ✅ |
| 8 | 10 | Editorial QA tooling | 10-editorial-qa.md | P1 | 04, 05 | 6–8 | ✅ |
| 9 | 07 | Release pipeline (VPS, Compose, Nginx, backups). **Hold lifted (owner, 2026-11-02): live at mybestpicks.in. Backups/monitoring/restore rehearsal still open.** | 07-release-pipeline.md | P0 | 01–06, 08, 10 | after development (plan had week 2) | 🟨 |
| 10 | 09 | Metrics (Search Console, Umami, UTMs; needs a live site) | 09-metrics.md | P1 | 06, 07 | after 07 | ⬜ |
| 11 | 14 | Telegram posting integration (optional) | 14-telegram-posting.md | P2 | 03, 06, 09 | post-launch | ⬜ |
| 12 | 13 | Amazon eligibility check | 13-amazon-eligibility.md | P2 | 10 live articles | post-launch | ⬜ |
| 13 | 12 | AdSense readiness | 12-adsense.md | P2 | 06, 09 | post-launch | ⬜ |
| 14 | 11 | Merchant API evaluation | 11-merchant-api.md | P2 | 05, 13 | post-launch | ⬜ |

## Cross-cutting (enforced in every module, not built once)
- Server-rendered content (CLAUDE.md invariant 1)
- No price fields anywhere; prices only as dated article text (invariant 2, relaxed 2026-11-04)
- Article judgement only in StreamField product cards (invariants 3 and 4)
- `discovery_mode` is the only rule for visibility (invariant 5)
- Affiliate link and disclosure rules apply whenever an offer renders (invariants 6 and 7)
- Image provenance and evidence for hands-on claims (invariant 8)
- Privacy-friendly defaults and secrets only in env (invariants 9 and 10)
- Mobile layouts work at 320px, pages are keyboard accessible and HTTPS-only

## Launch gates
See [../launch-checklist.md](../launch-checklist.md) for the public-launch gate, the
new-hub reveal gate and the MVP definition of done.

## Open questions
- [DECISION 2026-11-02] **No deployment until development is finished** (owner).
  The plan's week-2 "minimal production deploy" is dropped, so module 07 now comes
  after 08 and 10, and module 09 after 07. This also settles the question of whether
  an early deploy would be public or hidden: there is no early deploy. The plan's
  timeline and its "live by week 2 / 4–6 articles by week 4" targets no longer
  apply; the schedule needs a re-plan once development is done.
- [DECISION 2026-11-02] mybestpicks will deploy on its **own** VPS (app + nginx),
  but use the **same shared Postgres instance** that already hosts pglive.in and
  mytravelplanner.in, in its own database and role (never a shared schema/role).
  Details and the security requirements this adds (TLS, firewall allowlist,
  per-site credentials) are recorded in
  [07-release-pipeline.md](07-release-pipeline.md). Still open: the app VPS
  provider/region/size, and the off-box backup destination.
- [OPEN] The existing Telegram channel URL, topic and audience are not reviewed yet
  (plan §11).
- [DECISION 2026-11-02] Module 12 (AdSense) infrastructure (ad slot component,
  consent-gated script tag, publisher/slot ID validation, `/ads.txt`) was built
  ahead of the strict build order, which lists 12 as P2/post-launch depending on
  06 and 09 (neither done). Owner reviewed and chose to keep the code rather than
  revert it: it is disabled by default (`ADSENSE_ENABLED=False`), renders nothing,
  and claims no program acceptance. Module 12's status stays "Not Started" and it
  is not to be enabled or extended until 06 and 09 are actually done. Do not treat
  this as license to build other P2 modules early.
