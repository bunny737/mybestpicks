# Module: Merchant API evaluation

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started (evaluation only. Do not build without owner approval)
**Priority:** P2
**Ticket:** MBP-011
**Plan reference:** docs/mybestpicks_plan_v4.md §6 (implementation stages)
**Depends on:** 05, 13
**Blocks:** none

## Purpose
Decide whether merchant product APIs are worth using. Consider them only after the
program terms, approved access, credentials, product and media rights, and cache
lifetimes are all verified.

## Constraints to respect
- Do not mix Amazon-sourced restricted API content with promotion of competitors in
  any way the Amazon license forbids. A compliance review must happen before any
  integration.
- No scraping, ever.
- Any API-sourced price data would break CLAUDE.md invariant 2. That needs an
  explicit owner decision and a documented cache/refresh design first.

## Open questions / Decisions
- [OPEN] All. Evaluate after Amazon eligibility (13) and Cuelinks approval are settled.

## Changelog
- 2026-11-02  Created stub from plan v4.
