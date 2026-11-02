# Module: Trust, privacy and SEO

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started
**Priority:** P0
**Ticket:** MBP-006
**Plan reference:** docs/mybestpicks_plan_v4.md §5, §6 (compliance), §7, §11 (RSS, email, Telegram MVP)
**Depends on:** 02, 03, 04
**Blocks:** 09, 12, 14

## Purpose
Everything that makes the site trustworthy to readers and crawlable by search
engines: policy pages, site settings, sitemap, robots, redirects, canonical URLs,
JSON-LD, RSS, the configurable Telegram link, privacy-respecting email signup and
consent controls.

## Data model (as planned; update to as-built)
```
Model: SiteSettings (BaseSiteSetting)   app: home
  telegram_channel_url     URL, blank; validated https://t.me/…; nothing renders when blank
  telegram_channel_label   optional, default "Join on Telegram"
  contact_email
  social links (LinkedIn, …)
  analytics_enabled / umami_website_id   nonsecret, used by module 09
  NO secrets (no bot token, no API keys)

Model: EmailSubscriber   app: home   (only if consent/unsubscribe can be operated; see Decisions)
  email, consented_at, consent_text_version, confirmed_at (double opt-in), unsubscribe_token
```

## Pages, URLs
```
/sitemap.xml        wagtail.contrib.sitemaps, live, canonical, indexable pages only
/robots.txt         allows production, references the sitemap, blocks /admin/ and /search/
/feed/              RSS of live ArticlePages (newest first), linked in <head> and the footer
/search/            module 08
/admin/             Wagtail admin (access controls: module 07)
StandardPages       About, Contact, Editorial Policy, Affiliate Disclosure, Privacy Policy, Terms
```

## Business rules
1. Every page has its own `<title>`, meta description, canonical URL (apex
   `https://mybestpicks.in/…`) and exactly one H1.
2. The sitemap leaves out undiscoverable hubs (module 03, rule 4), drafts, and
   non-indexable utility pages.
3. Staging sends `X-Robots-Tag: noindex` or requires authentication. Production does
   not block articles.
4. JSON-LD: `Article`/`BlogPosting` on articles and `BreadcrumbList` on articles and
   hubs. No `Review`/`AggregateRating` unless it is genuinely eligible and
   truthful, and never invented ratings. Test that the output is valid JSON.
5. The Telegram CTA (`components/telegram_cta.html`) renders on the homepage, in the
   footer and on relevant articles **only when `telegram_channel_url` is set**. It is
   never a popup and never covers content.
6. RSS item links are canonical URLs, not UTM-tagged.
7. The Affiliate Disclosure page may say links "may be used in future" while none
   are active. Nothing on the site claims Amazon Associate status before acceptance.
8. Email signup, if built, stores only the email and consent metadata, uses double
   opt-in if possible, puts an unsubscribe link in every send, and links to the
   privacy notice next to the form.
9. Analytics or ads scripts that need consent load only after consent is given.
10. Images: WebP/AVIF renditions where practical, alt text required, width and height set.

## Technical SEO checklist (verify before public launch)
- [ ] Full article text is in the server HTML
- [ ] Titles, descriptions, canonicals, a single H1 and correct HTTP status on every page type
- [ ] Sitemap submitted to Search Console; robots.txt is correct
- [ ] `www` → apex 301; http → https 301
- [ ] JSON-LD validates (Rich Results Test)
- [ ] LCP/CLS checked on mobile; no mixed content
- [ ] No critical broken internal links

## Open questions / Decisions
- [OPEN] Will email signup ship at launch? The plan makes RSS the required baseline
  and email the first enhancement after launch, unless consent and unsubscribe can
  be run properly from day one.
- [OPEN] Is a consent banner needed? Decide after the privacy review of the Umami
  setup, hosting region and DPDP phase dates.
- [OPEN] Policy page text needs owner review (and professional advice where needed,
  per plan §6: ASCI, DPDP, tax).

## Changelog
- 2026-11-02  Created stub from plan v4.
