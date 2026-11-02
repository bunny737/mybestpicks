# Module: Internal search

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Done
**Priority:** P1
**Ticket:** MBP-008
**Plan reference:** docs/mybestpicks_plan_v4.md §3, §14
**Depends on:** 02, 03
**Blocks:** none

## Purpose
Site search at `/search/`, using Wagtail's database search backend on PostgreSQL.
No Elasticsearch.

## Design (as planned; update to as-built)
- Start from the `search/` app that `wagtail start` generates (its view and
  `search/templates/search/search.html`). Extend it rather than building a new one.
- `django.contrib.postgres` must be in `INSTALLED_APPS` (already added in module 01);
  the backend fails `manage.py check` without it.
- The URL parameter is `?query=` (the starter's, and what the header form in module
  02 sends). Keep it; do not switch to `q`. The search template is already restyled.
- `WAGTAILSEARCH_BACKENDS = {"default": {"BACKEND": "wagtail.search.backends.database"}}`
- `ArticlePage.search_fields` indexes the title, excerpt, body text, tags and the
  author name. `CategoryPage` indexes its title and introduction.
- `/search/?query=` returns only live, public pages and is paginated.
- The search box in the header (module 02) is a plain GET form that works without JS.

## Business rules
1. Drafts, private pages and unpublished pages never appear in results.
2. Search result pages carry `noindex,follow` and are disallowed in robots.txt.
3. An empty or whitespace-only `q` shows a helpful empty state and runs no query.
4. Run `update_index` after deploys that change `search_fields`. Document this in
   deployment.md.

## Open questions / Decisions
- [DECISION 2026-11-02] Undiscoverable hubs' articles are included in results:
  `search()` runs against `Page.objects.live().public()` with no `discovery_mode`
  filter, since those articles are live and indexable on their own.
- [DECISION 2026-11-02] Search is not restricted to specific page types; any live,
  public page (home, hubs, articles, authors, standard pages) can match. The site
  is small enough that this needs no extra filtering yet.

## Changelog
- 2026-11-02  Created stub from plan v4.
- 2026-11-02  Added `search_fields` to `ArticlePage` (excerpt, body, methodology,
  tags via a `tags_text` property, related author title) and `CategoryPage`
  (introduction). Extended the starter `search/views.py` to add `.public()`
  (excludes view-restricted pages) alongside `.live()`, and to strip
  whitespace-only queries so rule 3 (no query run, helpful empty state) holds.
  Added an empty-state message for the no-query case. The `noindex,follow` meta,
  `/search/?query=` param, and `/search/` disallow in robots.txt were already in
  place from module 02/06. Added `search/tests/test_search.py` covering drafts,
  view-restricted pages, empty/whitespace queries, pagination, noindex meta, and
  that excerpt/body/tags/introduction are indexed.
