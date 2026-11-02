# Module: Page models

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Done (2026-11-02)
**Priority:** P0
**Ticket:** MBP-003
**Plan reference:** docs/mybestpicks_plan_v4.md §4 (page types), §5, §5A
**Depends on:** 01
**Blocks:** 02, 04, 06, 07, 08

## Purpose
The Wagtail page tree for the site: homepage, category hubs, articles, author
pages and standard (policy) pages. Editors draft, preview, schedule, revise and
publish in Wagtail. A new category hub is created in the admin with no code change.

## Data model (as-built)
Code: `editorial/models.py`, `home/models.py`, `catalog/provenance.py`. Wagtail's
built-in `Page` fields cover the SEO title, search description, slug and live
status; no duplicate SEO columns were added.

```
Model: HomePage (Page)   app: home        parent: wagtailcore.Page   max_count 1
  hero_title          default "Find the Best Picks for Everyday Life."
  hero_text           default: one-line description
  trust_panel         rich text, "How We Choose" with a link to the editorial policy
  featured_guides     inline HomeFeaturedGuide (Orderable) → ArticlePage
  subpage_types       CategoryPage, StandardPage, AuthorIndexPage
  context             categories = CategoryPage.objects.child_of(self).discoverable()
                      featured_articles = featured guides that are live

Model: CategoryPage (Page)   app: editorial        parent: HomePage   children: ArticlePage
  introduction        rich text
  banner              image FK (SET_NULL) + banner_provenance + banner_credit
  featured_guides     inline CategoryFeaturedGuide (Orderable) → ArticlePage
  discovery_mode      CharField(16): auto | force_show | force_hide, default force_hide
                      (Settings tab in the editor)
  live_child_count    property: live direct ArticlePage children (uses the
                      live_article_count annotation when present)
  is_discoverable     property (rules 1-3)
  robots_meta         property: "" or "noindex,follow"; also in the template context
  objects             PageManager with CategoryPageQuerySet:
                        .with_live_article_count()  annotates live_article_count
                        .discoverable()             live + public + discovery rule

Model: ArticlePage (Page)   app: editorial        parent: CategoryPage only, no children
  article_kind        buying_guide | comparison | explainer | tutorial
  excerpt             TextField(max 300), required
  author              FK → AuthorPage (PROTECT)
  featured_image      image FK (SET_NULL) + featured_image_provenance + featured_image_credit
  body                StreamField: paragraph (rich text), heading (H2/H3); module 04 adds the rest
  methodology         rich text
  reviewed_date       DateField, optional
  tags                ClusterTaggableManager (through ArticlePageTag)
  category            property: the parent CategoryPage

Model: AuthorIndexPage (Page)   app: editorial     parent: HomePage   max_count 1
  intro               rich text; lists live AuthorPages (slug authors → /authors/)

Model: AuthorPage (Page)   app: editorial          parent: AuthorIndexPage
  bio, expertise, experience (research/testing, stated honestly), photo (own photo)
  context             articles = live ArticlePages by this author

Model: StandardPage (Page)   app: editorial        parent: HomePage
  body                rich text
  used for            About, Contact, Editorial Policy, Privacy Policy,
                      Affiliate Disclosure, Terms
```

`DISCOVERY_AUTO_MIN_ARTICLES = 3` lives in `editorial/models.py`; it is the only
place the threshold is written.

Shared helper `catalog/provenance.py`: `ImageProvenance` choices and
`validate_image_provenance()`. Module 05's `Product` must use it too.

## Pages, URLs and templates
```
/                                   HomePage        home/home_page.html
/<category-slug>/                   CategoryPage    editorial/category_page.html
/<category-slug>/<article-slug>/    ArticlePage     editorial/article_page.html
/authors/ and /authors/<slug>/      AuthorIndexPage / AuthorPage
/about/ /contact/ /editorial-policy/ /affiliate-disclosure/ /privacy-policy/ /terms/
                                    StandardPage    editorial/standard_page.html
```
The templates are deliberately **plain, unstyled HTML** so every page renders and can
be tested; module 02 replaces them with the Bootstrap layout. `base.html` already
prints `<meta name="robots">` when the context has `robots_meta`. The starter's
welcome page and CSS were deleted.

## Business rules
Each rule maps to a test (`editorial/tests/`, `home/tests/`).
1. `force_show` makes a hub discoverable and `force_hide` makes it undiscoverable,
   whatever its child count. (`test_category_discovery`)
2. `auto` makes a hub discoverable at **3 or more live direct `ArticlePage`
   children**. Drafts and non-article children do not count. (`test_category_discovery`)
3. A new `CategoryPage` defaults to `force_hide`. (`test_category_discovery`)
4. An undiscoverable hub renders `<meta name="robots" content="noindex,follow">` and
   `CategoryPage.get_sitemap_urls()` returns `[]`. Its live articles stay
   indexable and keep their own sitemap entries. (`test_seo_and_pages`)
5. A live hub with no live articles shows a "coming soon" state, never an empty
   grid. The homepage hides the category section when there are no discoverable
   hubs. (`test_seo_and_pages`, `test_home_page`)
6. `ArticlePage` can only be created under a `CategoryPage`; each article has one
   primary parent. Other placement rules are tested too. (`test_seo_and_pages`)
7. `ArticlePage.get_context()` follows the rendering contract in module 04. **Not
   built here:** the contract needs the product blocks, so module 04 adds it.
8. Changing a slug or moving a page creates a 301 redirect
   (`wagtail.contrib.redirects`). (`test_seo_and_pages`)
9. `CategoryPage.objects.discoverable()` returns the same hubs as `is_discoverable`,
   excludes unpublished and private hubs, and its query count does not grow with the
   number of hubs. (`test_category_discovery`)
10. An image on an article or a banner needs provenance, and anything except an
    owned original also needs a credit or licence evidence (invariant 8).
    (`test_image_provenance`)
11. A category's featured guides must be articles of that category. (`test_home_page`)
12. An author who has articles cannot be deleted (PROTECT). (`test_seo_and_pages`)
13. The admin add/edit forms build for every page type. (`test_admin`)

## Edge cases handled
- A hub changes mode: nothing is cached yet, so there is nothing to invalidate. When
  module 02 caches navigation it must invalidate on publish, unpublish, move, delete
  and `discovery_mode` changes.
- An article moves to another hub: a redirect is created and the old hub's count
  drops.
- Article body headings are escaped in the template (tested with a `<script>` title).

## Open questions / Decisions
- [DECISION 2026-11-02] `is_discoverable` is computed, never stored, so it cannot
  drift. Navigation uses `.discoverable()`, an annotated queryset (two queries in
  total: one for the hubs and one Wagtail runs for private-page restrictions),
  instead of a per-hub `.count()`.
- [DECISION 2026-11-02] Whether an article has affiliate links is derived from the
  active offers that will render (module 04), not from an editor flag (plan §4,
  "affiliate flags"), so the disclosure can never disagree with the page. Revisit if
  editors need a manual "no affiliate links" override.
- [DECISION 2026-11-02] Authors live under an `AuthorIndexPage` at `/authors/`
  (answers the earlier open question). Author URLs stay out of the category
  namespace, and the index gives readers and crawlers a page to find all authors.
- [DECISION 2026-11-02] "Published date" is Wagtail's `first_published_at`; only
  `reviewed_date` is stored, to avoid two sources of truth.
- [DECISION 2026-11-02] The homepage has **no curated category links field**. Plan §4
  lists one, but invariant 5 says tiles come from `discovery_mode` alone.
- [DECISION 2026-11-02] Image provenance fields sit next to each image on the page
  (`featured_image_provenance`, `banner_provenance`, ...) instead of on a custom
  image model, because the images tables were already migrated by module 01 and
  swapping the image model afterwards is unsafe. The rule itself lives in
  `catalog/provenance.py` so articles and products share it.
- [DECISION 2026-11-02] Wagtail sends `page_slug_changed` in `transaction.on_commit`.
  Tests that change a slug must wrap the publish in
  `captureOnCommitCallbacks(execute=True)`.
- [DECISION 2026-11-02] The starter's `home/tests.py` was replaced by
  `home/tests/test_home_page.py`; its three checks (root page exists, home page
  exists) are covered there.
- [OPEN] `/sitemap.xml` is not wired to a URL yet (module 06), so rule 4 is tested
  through `get_sitemap_urls()`. Add an end-to-end sitemap test in module 06.
- [OPEN] `search_fields` for the new pages (module 08).
- [OPEN] Should `StandardPage` pages show up in the main navigation? Module 02.

## Changelog
- 2026-11-02  Created stub from plan v4.
- 2026-11-02  Built: all five page types plus AuthorIndexPage, migrations
  `editorial.0001` and `home.0003`, plain templates, the image-provenance helper and
  47 tests (ruff, check, makemigrations --check clean).
