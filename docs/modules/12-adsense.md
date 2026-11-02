# Module: AdSense readiness

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started (do not apply without owner approval)
**Priority:** P2
**Ticket:** MBP-012
**Plan reference:** docs/mybestpicks_plan_v4.md §11 (Phase 2)
**Depends on:** 06, 09
**Blocks:** none

## Purpose
Assess readiness for Google AdSense once there is enough useful public content.
There is no fixed week for submitting. No universal minimum number of posts or
views guarantees approval.

## Readiness checklist
- [ ] Original, substantive content across the discoverable hubs
- [ ] Clear navigation; About, Contact and Privacy pages published
- [ ] Mobile usability passes
- [ ] The privacy notice and consent setup cover advertising cookies and certified CMP integration
- [ ] The planned ad placements do not crowd or imitate product CTAs
- [ ] Validated Google publisher ID and ad-unit slot IDs configured
- [ ] Exclude search, 404/500 errors, legal policies, drafts, and preview states from advertising
- [ ] Verified ads.txt entries at /ads.txt

## Constraints
- The ads script loads only after consent where that is required (CLAUDE.md invariant 9).
- No excessive ads around recommendation buttons, and no layout that could confuse readers.
- Never claim active monetization or program acceptance until accounts are officially approved.
- Ad units require explicit ad unit slot IDs and must never display broken empty placements.

## Changelog
- 2026-11-02  Configured strict publisher and slot ID validation, ads.txt endpoint, and consent-gated template hooks. Module remains Not Started pending launch, CMP implementation, and traffic maturation.
