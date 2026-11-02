# Module: Editorial QA tooling

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Done
**Priority:** P1
**Ticket:** MBP-010
**Plan reference:** docs/mybestpicks_plan_v4.md §4 (safeguards), §7 (editorial standards, image sourcing), §10 (weekly workflow)
**Depends on:** 04, 05
**Blocks:** 13

## Purpose
Tools that keep published claims true over time: price-dependent headline
re-verification, image provenance and license checks, source tracking, link audits
and test fixtures. The human process is in
[../editorial-workflow.md](../editorial-workflow.md).

## Design (as built)
- All read-only logic lives in `editorial/audits.py`; each management command is a
  thin wrapper that prints findings and exits non-zero when there are any (rule 3).
- `python manage.py editorial_audit` (optional `--days` to override the threshold
  for one run) runs `run_editorial_audit()`, which does one pass over
  `ArticlePage.objects.live()` (using `resolve_article_products()` from module 04,
  so it shares the exact rendering contract rather than re-parsing StreamField data)
  plus the catalog, and reports:
  - `stale-priced-article`: a live article's title or excerpt matches
    `PRICE_PATTERN` (`₹`, "under", "below", "budget", case-insensitive) and a
    product its cards reference has `last_verified_at` unset or older than
    `settings.EDITORIAL_AUDIT_STALE_DAYS` (default 30)
  - `missing-image-evidence`: a `Product` fails `catalog.provenance
    .validate_image_provenance` (the same check `Product.clean()` runs) — this is a
    sanity check for rows that bypassed `full_clean()`, since normal admin saves
    already enforce it
  - `unavailable-product-reference`: a live article's card references a `Product`
    whose `status` is not `active`
  - `stale-offer`: an active `MerchantOffer` with `last_checked_at` older than the
    threshold
  - `untested-evidence-claim`: a card has `tested_by_editor=True` with no
    `editorial_evidence` text and no `evidence_media` (mirrors
    `ProductCardBlock.clean()`, again as a sanity check on data that bypassed it)
- `python manage.py check_internal_links` runs `find_broken_internal_links()`,
  which walks every live, public page's `RichTextField`s and any `RichText` nested
  in its StreamField body (struct/stream/list blocks, arbitrarily nested) and
  checks every `<a>` tag:
  - `linktype="page" id="N"` → the target page must exist and be live
  - `linktype="document" id="N"` → the target document must exist
  - any other same-site `href` (by netloc against `SITE_URL`) → resolved with an
    in-process `django.test.Client` request (not a real network call) and flagged
    if it returns 400+; `mailto:`/`tel:`/`javascript:` links and pure fragments are
    skipped; a different-domain `href` is never requested at all
  - it also flags `RelatedArticlesBlock` picks and `CategoryFeaturedGuide` rows
    whose target article is no longer live (the template already hides these from
    readers, so nothing breaks publicly, but the stale pick is worth an editor's
    attention)
- Fixtures and factories for HomePage → CategoryPage → ArticlePage trees, plus
  products and offers, already existed from modules 04/05
  (`editorial/tests/helpers.py`, `catalog/tests/helpers.py`) and are reused as-is;
  no new fixture module was needed.

## Hooks from module 05
- `Product.status` and `last_verified_at`, and `MerchantOffer.last_checked_at`, are
  plain fields (dates) to compare with the configurable threshold.
- `MerchantOffer.is_renderable` and `.objects.renderable()` identify offers that
  currently show. A discontinued product's offers already stop rendering; this module
  reports the *articles* that still reference it.
- `ArticleSource` rows (accessed dates, types) feed the research audit.

## Hooks from module 04
- Product cards store `tested_by_editor`, `editorial_evidence` and `evidence_media`; the
  block already blocks saving an unsupported claim, so the audit only needs to check
  old data.
- To find the articles that use a product, ask Wagtail's reference index
  (`ReferenceIndex.get_references_to(product)`), as `ReferenceIndexTests` does.

## Business rules
1. The audit never edits content by itself. It only reports.
2. The thresholds come from settings, not constants spread through the code.
3. The audit exits non-zero when there are findings, so CI or cron can alert.

## Open questions / Decisions
- [OPEN] Run the audit on a schedule (cron in the Compose host) or by hand during
  the weekly review? Both commands are safe either way (read-only, rule 1); this is
  purely about cadence. Module 07 (release pipeline) is the natural place to wire
  a cron job if the owner wants one.

## Changelog
- 2026-11-02  Created stub from plan v4.
- 2026-11-02  Built `editorial/audits.py` plus the `editorial_audit` and
  `check_internal_links` management commands. Added
  `EDITORIAL_AUDIT_STALE_DAYS` (default 30) to settings and `.env.example`.
  Added `editorial/tests/test_editorial_audit.py` and
  `test_check_internal_links.py` covering every finding category (both the
  flagged and the not-flagged case) and a read-only check that the audit never
  mutates product/offer rows. Referenced both commands from
  docs/editorial-workflow.md step 7.
