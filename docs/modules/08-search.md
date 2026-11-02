# Module: Internal search

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started
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
- [OPEN] Include undiscoverable hubs' articles in results? Proposed yes: the
  articles are live and indexable.

## Changelog
- 2026-11-02  Created stub from plan v4.
