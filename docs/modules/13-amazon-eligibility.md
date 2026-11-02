# Module: Amazon eligibility check

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started (an owner/business task. No code until accepted)
**Priority:** P2
**Ticket:** MBP-013
**Plan reference:** docs/mybestpicks_plan_v4.md §6 (program timing)
**Depends on:** at least 10 substantive public articles
**Blocks:** 11

## Purpose
Decide when to apply to Amazon Associates India, based on the **actual** account
status rather than assumptions.

## Facts from the plan (re-verify at the official links before acting)
- Amazon India reviews an application after **at least 3 qualifying sales in the
  first 180 days**, not counting personal orders.
- Amazon describes **at least 10 publicly accessible original posts** as a useful
  benchmark.
- Do not apply automatically in week 1, 2 or 4. Apply when there are 10 or more
  substantive public articles and a plausible path to qualifying sales.
- If an account already exists, check its real application, approval and 180-day
  clock status.
- References: https://affiliate-program.amazon.in/help/node/topic/G8TW5AE9XL2VX9VM ·
  https://affiliate-program.amazon.in/help/node/topic/G7MJTPEP9NC3YKMG

## Code impact once accepted
- Add an Amazon `Merchant` with verified `allowed_link_domains`.
- Show Amazon's required identification statement in the right place on the site,
  and **only after acceptance** (CLAUDE.md invariant 7).
- CTA label: "Check price at Amazon".

## Changelog
- 2026-11-02  Created stub from plan v4.
