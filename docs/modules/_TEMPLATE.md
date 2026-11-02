# Module: <NAME>

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started | In Progress | Done
**Priority:** P0 | P1 | P2
**Ticket:** MBP-0xx
**Plan reference:** docs/mybestpicks_plan_v4.md §<n>
**Depends on:** <modules>
**Blocks:** <modules>

## Purpose
What does this module let an editor or reader do?

## Data model (as-built)
Document models as actually built, not as first planned. Mark whether each is a
Wagtail Page, a snippet, a setting or a plain Django model.

```
Model: <Name>   (Page | snippet | BaseSiteSetting | model)   app: <app>
  field           type            notes
  ...
```

## Pages, URLs and templates
```
URL / page type          template                         notes
```

## Wagtail admin
Panels, choosers, snippet viewsets, and which editor actions are available.

## Business rules
Each rule maps to a test.
1.
2.

## Edge cases handled
-

## Open questions / Decisions
- [DECISION 2026-11-xx] what was decided and why
- [OPEN] unresolved, needs input

## Changelog
- 2026-11-xx  Created stub.
