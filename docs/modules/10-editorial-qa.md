# Module: Editorial QA tooling

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started
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

## Design (as planned; update to as-built)
- A management command, `editorial_audit`, reports:
  - live articles whose title or excerpt matches a price pattern (`₹`, "under",
    "below", "budget") and whose referenced products have a `last_verified_at` older
    than the threshold (default 30 days, configurable in settings)
  - products with images that are missing provenance or license evidence
  - live articles that reference `discontinued` or `unavailable` products
  - offers whose `last_checked_at` is older than the threshold
  - `tested_by_editor` cards without evidence (a sanity check on old data)
- A management command, `check_internal_links`, finds broken internal links in live
  pages. External offer URLs are **not** fetched (no SSRF, and it respects merchant
  terms).
- Fixtures and factories for HomePage → CategoryPage → ArticlePage trees, plus
  products and offers, for use in tests across modules.

## Business rules
1. The audit never edits content by itself. It only reports.
2. The thresholds come from settings, not constants spread through the code.
3. The audit exits non-zero when there are findings, so CI or cron can alert.

## Open questions / Decisions
- [OPEN] Run the audit on a schedule (cron in the Compose host) or by hand during
  the weekly review?

## Changelog
- 2026-11-02  Created stub from plan v4.
