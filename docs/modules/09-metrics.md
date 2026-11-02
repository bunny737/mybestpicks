# Module: Metrics

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started
**Priority:** P1
**Ticket:** MBP-009
**Plan reference:** docs/mybestpicks_plan_v4.md §1 (measurement), §11 (analytics, reporting dashboard)
**Depends on:** 06, 07
**Blocks:** 12, 14

## Purpose
Measure what matters for an audience-first site: search indexing and impressions,
referral sources (including Telegram UTMs), and RSS and email acquisition. It
must never build a server-side click log.

## Design (as planned; update to as-built)
- **Search Console:** a domain or apex property, verified by DNS TXT, with the
  sitemap submitted. It is the authoritative source for Google search performance.
- **Umami (self-hosted):** a separate Compose service with its own DB and user, on
  its own subdomain or path, behind HTTPS. The tracking snippet loads only when
  `SiteSettings.analytics_enabled` is true and, if the privacy review requires it,
  only after consent.
- **UTM convention:** see [../telegram-distribution.md](../telegram-distribution.md#utm-convention).
- **GA4:** optional and off by default. If it is enabled later, it loads only after
  consent. An optional `affiliate_click` event uses the `data-merchant`,
  `data-product` and `data-article` attributes on CTA anchors.

## Business rules
1. There is no `AffiliateClickEvent` model and no endpoint that records clicks on
   the server.
2. No analytics script loads before applicable consent, and none loads when
   analytics is disabled.
3. CTA anchors may carry the `data-merchant`, `data-product` and `data-article`
   attributes, but no inline tracking JS that delays navigation or breaks merchant
   attribution.
4. Merchant dashboards are the source of truth for orders and commissions. Site
   clicks are never reported as sales.

## Weekly review (internal dashboard)
Live article count by category and type · Search Console indexed pages,
impressions, clicks, queries and CTR · Umami visits, top pages and referrals,
including `utm_source=telegram` · RSS and email opt-ins · hosting cost and
editorial time.

## Open questions / Decisions
- [OPEN] Umami hosting: the same VPS (simplest) or separate. A privacy review is
  needed either way.

## Changelog
- 2026-11-02  Created stub from plan v4.
