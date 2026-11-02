# Module: Base layout and dynamic navigation

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started
**Priority:** P0
**Ticket:** MBP-002
**Plan reference:** docs/mybestpicks_plan_v4.md §5 (homepage and article hierarchy), §7 (performance and accessibility)
**Depends on:** 01, 03
**Blocks:** 06, 07, 08

## Purpose
The Bootstrap 5 base template, header and footer, homepage and article layouts.
Navigation is built from discoverable categories. The layout must work on mobile
down to 320px.

## Templates (as planned; update to as-built)
Wagtail gives the admin, routing and template tags, but no public theme. The
starter's `base.html` is a bare skeleton, and its welcome page is a placeholder that
is deleted here. Page templates follow Wagtail's naming convention,
`<app>/<model_snake_case>.html`.

```
mybestpicks/templates/base.html                 head metadata slots, header nav, search box, footer, RSS <link>
mybestpicks/templates/404.html · 500.html       restyled starter pages
home/templates/home/home_page.html              hierarchy below (replaces the starter welcome page)
editorial/templates/editorial/category_page.html
editorial/templates/editorial/article_page.html
editorial/templates/editorial/author_page.html
editorial/templates/editorial/standard_page.html
mybestpicks/templates/components/{product_card,comparison_table,affiliate_disclosure,breadcrumbs,telegram_cta}.html
```

**Homepage order:** logo, nav and search → hero → cards for discoverable categories
→ featured guides → latest comparisons and recently updated articles → budget
collections (only if re-verified) → "How We Choose" → footer (legal pages, contact,
RSS, social/Telegram).

**Article order:** breadcrumb, H1, author and reviewed dates → short answer and
methodology → affiliate disclosure (only if an active offer renders) → quick picks
→ comparison table → product discussions → buying advice, FAQ, sources → related
guides and the final update date.

## Business rules
1. Header nav, homepage category cards and category directories list only hubs that
   are **live and `is_discoverable`**. There is no hard-coded category list and no
   separate article-count rule.
2. Navigation runs a bounded number of queries, whatever the number of hubs (test
   with `assertNumQueries`).
3. The nav cache, if used, is invalidated on page publish, unpublish, move and delete,
   and when `discovery_mode` changes.
4. Each page has exactly one `<h1>`.
5. At a 320px viewport: the mobile nav works, cards stack, and comparison tables
   scroll horizontally inside their own container (the page does not scroll
   sideways).
6. Focus states are visible, links have meaningful labels and colours meet contrast.
7. Images carry width and height; images below the fold are lazy-loaded.
8. JavaScript is limited to Bootstrap's bundle and small progressive enhancements.
   With JS off, the page is still fully readable.

## Open questions / Decisions
- [OPEN] Brand assets (logo, favicon, colours) are not supplied yet.
- [OPEN] Load Bootstrap from a vendored static copy or a CDN? A vendored copy suits
  WhiteNoise and privacy.

## Changelog
- 2026-11-02  Created stub from plan v4.
