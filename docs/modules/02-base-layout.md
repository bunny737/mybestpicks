# Module: Base layout and dynamic navigation

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Done (2026-11-02)
**Priority:** P0
**Ticket:** MBP-002
**Plan reference:** docs/mybestpicks_plan_v4.md §5 (homepage and article hierarchy), §7 (performance and accessibility)
**Depends on:** 01, 03
**Blocks:** 06, 07, 08

## Purpose
The Bootstrap 5 base template, header and footer, homepage and article layouts.
Navigation is built from discoverable categories. The layout must work on mobile
down to 320px.

## As-built
Wagtail gives the admin, routing and template tags, but no public theme, so this
module wrote it. Page templates follow Wagtail's naming convention,
`<app>/<model_snake_case>.html`.

```
mybestpicks/templates/base.html                  skip link, header + Primary nav, search form, footer
mybestpicks/templates/404.html                   extends base.html
mybestpicks/templates/500.html                   STANDALONE (no base, no database access)
mybestpicks/templates/components/breadcrumbs.html
mybestpicks/templates/components/article_card.html
home/templates/home/home_page.html
editorial/templates/editorial/{category,article,author,author_index,standard}_page.html
editorial/templates/editorial/blocks/heading_block.html
search/templates/search/search.html              restyled starter template (module 08 owns the logic)
mybestpicks/static/vendor/bootstrap/             Bootstrap 5.3.8, vendored (see its README.md)
mybestpicks/static/css/mybestpicks.css           theme and small helpers
home/context_processors.py                       nav_categories, footer_pages (lazy)
home/templatetags/layout_tags.py                 {% breadcrumbs %}
```

- **Navigation:** `nav_categories` is `CategoryPage.objects.child_of(site root).discoverable()`
  in page-tree order (editors drag pages to reorder the menu). The current section
  gets `active` and `aria-current="page"`.
- **Footer:** repeats the categories, so navigation still works with JavaScript off
  (the mobile menu needs Bootstrap's JS), plus `StandardPage`s ticked "show in menus".
  Category hubs are never taken from `show_in_menus`.
- **Lazy context:** both context-processor values are `SimpleLazyObject`s, so the
  Wagtail admin and other pages that do not use them run no navigation queries.
- **Homepage** (plan §5): hero → category cards → featured guides → latest
  comparisons (3) → recently updated (6) → "How we choose". Every section is omitted
  when empty, so there is never an empty grid.
- **Article** (plan §5): breadcrumb → kind, H1, author and dates → excerpt as the
  short answer → hero image (not lazy, `fetchpriority="high"`, credit caption when
  set) → methodology in a collapsible `<details>` (the text is in the server HTML) →
  body → tags and last-reviewed date → related guides (up to 3 live siblings from
  `ArticlePage.get_context()`). Module 04 inserts the disclosure, quick picks and
  comparison table between methodology and body.
- **Cards** use a 16:9 image area with width and height attributes and
  `loading="lazy"`. A hub with no articles shows a "coming soon" card.
- **Accessibility:** skip link and `<main id="main-content">`, `lang="en-IN"`,
  `aria-label`ed `Primary` / `Breadcrumb` / footer navs, a visible 3px focus outline,
  a label on the search input.
- **`base.html` blocks:** `title`, `title_suffix`, `extra_css`, `extra_head`,
  `body_class`, `content`, `extra_js`. `robots_meta` from the page context prints
  `<meta name="robots">` (used by `CategoryPage`, module 03).

## Business rules
Each rule maps to a test in `home/tests/test_layout.py` unless noted.
1. Header nav, homepage category cards and category directories list only hubs that
   are **live, public and `is_discoverable`**. There is no hard-coded category list
   and no separate article-count rule. `show_in_menus` never reveals a hidden hub.
2. Navigation runs a bounded number of queries, whatever the number of hubs: the
   request's query count is identical with 1 hub and with 8, and the admin pages run
   no navigation query at all.
3. There is no navigation cache yet (see Decisions), so nothing needs invalidating.
   If one is added it must be invalidated on publish, unpublish, move and delete, and
   when `discovery_mode` changes.
4. Each page has exactly one `<h1>` (home, category, article, author, authors index,
   standard page, search).
5. At a true 320px viewport the mobile menu button is visible and no page scrolls
   sideways. **Verified by hand** in headless Edge (pages inside a 320px iframe; no
   automated test). Comparison tables scroll inside `.table-scroll` once module 04
   adds them.
6. Focus states are visible, links have meaningful labels and colours meet contrast.
   Contrast was checked by eye against Bootstrap's defaults and the accent `#0a5c70`
   on white; run an automated audit (for example Lighthouse) before launch.
7. Images carry width and height; hero images are eager, card images lazy.
8. JavaScript is only Bootstrap's bundle. With JS off the pages are fully readable
   and navigable through the footer.
9. The 500 page renders without the database, because the base layout queries it.

## Open questions / Decisions
- [DECISION 2026-11-02] Bootstrap 5.3.8 is **vendored** (own domain, WhiteNoise,
  no third-party requests, no SRI to maintain), with checksums recorded in
  `mybestpicks/static/vendor/bootstrap/README.md`. The `sourceMappingURL` comments
  were stripped, because `ManifestStaticFilesStorage` fails on a missing map. The
  Docker build's `collectstatic` was verified with these files.
- [DECISION 2026-11-02] No navigation cache for launch: it costs two small queries
  per uncached page and Cloudflare/page caching sits in front. Revisit with real
  performance data (module 07 / week 6 performance work).
- [DECISION 2026-11-02] The wordmark "MyBestPicks" is plain text in the accent colour
  until a logo exists.
- [DECISION 2026-11-02] Footer pages come from `show_in_menus` on `StandardPage`
  (answers the earlier "do standard pages go in the nav" question: footer only).
- [DECISION 2026-11-02] The search form uses the starter's `?query=` parameter, so
  `/search/?query=...` is the URL. Earlier docs said `?q=`; module 08 should keep
  `query`.
- [DECISION 2026-11-02] The 500 template is standalone so a database failure still
  yields a styled error page.
- [OPEN] RSS `<link>` / footer link and the Telegram CTA are **not** here: `/feed/`
  and the Telegram setting do not exist until module 06, and a link to a missing URL
  is worse than none. `base.html` has comments marking where they go.
- [OPEN] Brand assets (logo, favicon, final colours) are not supplied yet.
- [DECISION 2026-11-05] Footer blurb reworded. "We verify specs, test where
  possible" implied hands-on testing that live articles disclaim (invariant 8), and
  "never recommend products solely for commission" implied commission partly
  decides picks. It now reads: "We date our facts, say clearly when we have not
  tested a product ourselves, and never let commission decide what we recommend."
- [OPEN] Budget-buying collections on the home page (plan §5 item 6) are skipped
  until price bounds can be re-verified; there is no price data in the MVP.
- [OPEN] An automated 320px check (for example Playwright in CI) would replace the
  manual one; not added because it needs a browser dependency (ask first).

## Changelog
- 2026-11-02  Created stub from plan v4.
- 2026-11-02  Built: Bootstrap layout, lazy navigation context, breadcrumbs, article
  cards and every page template, 404/500, search template. 22 new tests (69 in total).
  Visual check at 320px and 1280px in headless Edge.
