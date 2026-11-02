# Module Index & Status Board

Build in the dependency order below, which is **not** numeric order. Do not start a
module until every module it depends on is ✅. Module numbers are the plan's
MBP-0xx ticket numbers ([../mybestpicks_plan_v4.md §14](../mybestpicks_plan_v4.md)).

## Status
⬜ Not Started · 🟨 In Progress · ✅ Done

| Order | # | Module | Spec file | Priority | Depends on | Target week | Status |
|---|---|--------|-----------|---|---|---|---|
| 1 | 01 | Project scaffold | 01-scaffold.md | P0 | none | 1 (Nov 1–7) | ✅ |
| 2 | 03 | Page models (Home, Category, Article, Author, Standard) | 03-page-models.md | P0 | 01 | 1–2 | ⬜ |
| 3 | 02 | Base layout and dynamic navigation | 02-base-layout.md | P0 | 01, 03 | 2 (Nov 8–14) | ⬜ |
| 4 | 07 | Release pipeline (VPS, Compose, Nginx, backups) | 07-release-pipeline.md | P0 | 01, 02, 03 | 2 (minimal deploy) · 8 (restore rehearsal) | ⬜ |
| 5 | 05 | Product catalog (Brand, Product, Merchant, Offer, specs) | 05-product-catalog.md | P0 | 01 | 3 (Nov 15–21) | ⬜ |
| 6 | 04 | Editorial blocks (ProductCard, ComparisonTable, …) | 04-editorial-blocks.md | P0 | 03, 05 | 3–5 | ⬜ |
| 7 | 06 | Trust, privacy and SEO | 06-trust-privacy-seo.md | P0 | 02, 03, 04 | 2 (legal pages) · 4 (sitemap, RSS, Telegram link) | ⬜ |
| 8 | 08 | Internal search | 08-search.md | P1 | 02, 03 | 7 | ⬜ |
| 9 | 09 | Metrics (Search Console, Umami, UTMs) | 09-metrics.md | P1 | 06, 07 | 4, reviewed weekly | ⬜ |
| 10 | 10 | Editorial QA tooling | 10-editorial-qa.md | P1 | 04, 05 | 6–8 | ⬜ |
| 11 | 14 | Telegram posting integration (optional) | 14-telegram-posting.md | P2 | 03, 06, 09 | post-launch | ⬜ |
| 12 | 13 | Amazon eligibility check | 13-amazon-eligibility.md | P2 | 10 live articles | post-launch | ⬜ |
| 13 | 12 | AdSense readiness | 12-adsense.md | P2 | 06, 09 | post-launch | ⬜ |
| 14 | 11 | Merchant API evaluation | 11-merchant-api.md | P2 | 05, 13 | post-launch | ⬜ |

## Cross-cutting (enforced in every module, not built once)
- Server-rendered content (CLAUDE.md invariant 1)
- No price fields anywhere (invariant 2)
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
- [OPEN] Week 2's "minimal production deploy" comes before module 06 is finished
  (sitemap, RSS and Search Console are due in week 4). Is the week-2 deploy public
  and indexable, or behind `noindex`/auth until the public-launch gate passes? The
  plan's launch gates suggest the latter, but this is not explicit.
- [OPEN] VPS provider and off-box backup destination are not chosen yet.
- [OPEN] The existing Telegram channel URL, topic and audience are not reviewed yet
  (plan §11).
