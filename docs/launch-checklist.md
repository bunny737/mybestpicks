# Launch Gates & MVP Definition of Done

Plan reference: [mybestpicks_plan_v4.md §13, §14](mybestpicks_plan_v4.md). Tick
items here as they are verified, adding the date and who checked.

## Before public launch
- [ ] Wagtail login and editorial workflow (draft, preview, schedule, publish, revise)
- [ ] PostgreSQL in production, with backups running
- [ ] Category parent URLs resolve; breadcrumbs are correct
- [ ] At least one useful, reviewed article published
- [ ] SEO metadata on every page type; sitemap; robots.txt; RSS at `/feed/`
- [ ] Search Console property verified and sitemap submitted
- [ ] HTTPS with an apex canonical redirect (`www` → apex, http → https)
- [ ] Legal pages published: About, Contact, Editorial Policy, Affiliate Disclosure,
      Privacy Policy, Terms
- [ ] Mobile usability checked at 320px
- [ ] Off-box DB and media backups configured

**Not blockers:** Telegram bot automation, Amazon approval, Cuelinks acceptance,
affiliate CTAs, AdSense, custom click tracking, or reaching 30 posts.

## Before revealing a new hub
- [ ] A meaningful introduction and real editorial depth
- [ ] Links and breadcrumbs work; metadata is unique
- [ ] A deliberate choice of `auto` or `force_show` (recorded with the date)
- [ ] Tested end to end: nav, sitemap inclusion, robots meta (no longer `noindex`)
      and structured data

## MVP definition of done
- [ ] `mybestpicks.in` resolves to the new deployment with valid TLS and the
      canonical apex redirect
- [ ] Editors can create, preview, revise, schedule and publish guides in Wagtail
- [ ] Categories and articles have correct URLs, responsive layouts, breadcrumbs
      and SEO metadata
- [ ] Reusable product snippets; one canonical StreamField product-card source for
      verdicts and comparison-table membership; optional merchant links render with
      `rel="sponsored nofollow noopener"` and clear disclosures **when present**
- [ ] When affiliate links are present, disclosures and attributes are correct and
      links and images pass a program compliance review (**not a blocker when absent**)
- [ ] About, Contact, Editorial Policy, Affiliate Disclosure and Privacy Policy published
- [ ] Sitemap, robots, schema and Search Console verified
- [ ] The Telegram link can be set in Wagtail settings and shows only when a verified
      URL is set; manual sharing uses the UTM convention
- [ ] Basic search, RSS, a minimal opt-in email signup (double opt-in if available),
      privacy-respecting analytics with suitable consent controls, off-box DB and
      media backups, logging and monitoring
- [ ] Deployment and rollback documented; a backup restored successfully in a test
- [ ] Minimal site live by week 2 with one reviewed article; 4–6 substantive
      articles by the end of week 4; 12–18 as the 90-day goal

## Must verify before monetization (owner)
Cuelinks Flipkart eligibility, tracking hostnames, commission and attribution ·
Amazon account status and site eligibility · product image permissions · DNS and
hosting rights · privacy and consent obligations (DPDP has phased commencement
dates, so do not assume every provision was in force on 1 Nov 2026).
