# Module: Page models

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started
**Priority:** P0
**Ticket:** MBP-003
**Plan reference:** docs/mybestpicks_plan_v4.md §4 (page types), §5, §5A
**Depends on:** 01
**Blocks:** 02, 04, 06, 07, 08

## Purpose
The Wagtail page tree for the site: homepage, category hubs, articles, author
pages and standard (policy) pages. Editors draft, preview, schedule, revise and
publish in Wagtail. A new category hub is created in the admin with no code change.

## Data model (as planned; update to as-built)
Use the built-in `Page` fields for the SEO title, search description, slug and live
status. Do not add duplicate SEO columns.

```
Model: HomePage (Page)   app: home
  hero_title          default "Find the Best Picks for Everyday Life."
  hero_text
  featured_guides     ordered ArticlePage choosers (hand-picked)
  trust_panel         short "How We Choose" text with a link to the editorial policy
  subpage_types       CategoryPage, StandardPage, AuthorPage (or an authors index)

Model: CategoryPage (Page)   app: editorial
  introduction        rich text
  banner              image, optional (provenance required, see 05)
  featured_guides     ordered ArticlePage choosers
  discovery_mode      CharField(16) choices force_hide | auto | force_show, default force_hide
  live_child_count    computed: count of live direct ArticlePage children (not stored)
  is_discoverable     derived (see rules 1–3)
  parent_page_types   HomePage
  subpage_types       ArticlePage

Model: ArticlePage (Page)   app: editorial
  article_kind        buying_guide | comparison | explainer | tutorial
  excerpt
  author              FK → AuthorPage (PROTECT)
  featured_image      image (provenance required)
  body                StreamField (blocks: module 04)
  published_date / reviewed_date
  methodology         rich text: selection criteria, evidence, research date
  has_affiliate_links derived from article_products at render time, not hand-set (see Decisions)
  tags                for cross-topic discovery (one primary parent only)
  parent_page_types   CategoryPage

Model: AuthorPage (Page)   app: editorial
  name, bio, expertise, research/testing experience, photo (owned)

Model: StandardPage (Page)   app: editorial
  body                rich text / simple StreamField
  used for            About, Contact, Editorial Policy, Privacy Policy,
                      Affiliate Disclosure, Terms
```

## Pages, URLs
```
/                                   HomePage
/<category-slug>/                   CategoryPage   e.g. /developer-setup/
/<category-slug>/<article-slug>/    ArticlePage    e.g. /developer-setup/best-keyboards-for-coding/
/about/ /contact/ /editorial-policy/ /affiliate-disclosure/ /privacy-policy/ /terms/   StandardPage
```

## Business rules
1. `force_show` makes a hub discoverable and `force_hide` makes it undiscoverable,
   whatever its child count.
2. `auto` makes a hub discoverable when it has **3 or more live direct `ArticlePage`
   children**. Drafts, unpublished pages and non-article children do not count.
3. A new `CategoryPage` defaults to `force_hide`.
4. An undiscoverable hub renders `<meta name="robots" content="noindex,follow">`, and
   `CategoryPage.get_sitemap_urls()` returns `[]` for it. Its live articles stay in
   the sitemap and are indexable.
5. A live hub with no live articles shows a useful introductory or "coming soon"
   state, never an empty grid.
6. `ArticlePage` can only be created under a `CategoryPage`; each article has one
   primary parent.
7. `ArticlePage.get_context()` follows the rendering contract in module 04 and
   CLAUDE.md invariant 4.
8. Changing a slug or moving a page creates a 301 redirect
   (`wagtail.contrib.redirects`). Test this.

## Edge cases handled
- A hub changes mode while cached navigation exists: the cache is invalidated on
  publish, unpublish, move and `discovery_mode` changes (module 02).
- An article moves to another hub: a redirect is created and the old hub's count drops.

## Open questions / Decisions
- [DECISION 2026-11-02] `is_discoverable` is computed, never stored, so it cannot
  drift. Navigation uses one efficient annotated queryset rather than a
  per-hub `.count()` (the plan's snippet only shows the behaviour).
- [DECISION 2026-11-02] Whether an article has affiliate links is derived from the
  active offers that will render, not from an editor flag (plan §4, "affiliate
  flags"), so the disclosure can never disagree with the page. Revisit if editors
  need a manual "no affiliate links on this article" override.
- [OPEN] Authors index page (`/authors/`), or author pages directly under home?

## Changelog
- 2026-11-02  Created stub from plan v4.
