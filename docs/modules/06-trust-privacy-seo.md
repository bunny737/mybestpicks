# Module: Trust, privacy and SEO

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Done (consent-banner decision explicitly deferred to module 09's
privacy review, per plan §11 and the Decisions below; nothing here blocks on it)
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

## Data model (as built)
```
Model: SiteSettings (BaseSiteSetting, per Wagtail Site)   app: home
  contact_email            blank EmailField; nothing renders when blank, never invented
  telegram_channel_url     URL, blank; validated https://t.me/…; nothing renders when blank
  telegram_channel_label   optional, default "Join on Telegram"
  social links             deferred; no current requirement to render them
  analytics fields         deferred to module 09/privacy review
  (adsense_* fields: module 12, built ahead of sequence, see README.md)
  NO secrets (no bot token, no API keys)

Model: EmailSubscriber   app: home
  email (unique), consented_at (auto_now_add), consent_text_version,
  confirmed_at (null until the confirm link is clicked), unsubscribe_token
  (opaque, doubles as the confirm token; generated in save())
```

## Pages, URLs
```
/sitemap.xml        Wagtail sitemap, canonical SITE_URL origin; hidden hubs/drafts/private pages omitted
/robots.txt         allows content, references sitemap; blocks /admin/, /django-admin/, /search/, /subscribe/
/feed/              RSS 2.0 of the 20 newest live public ArticlePages; canonical item links
/search/            module 08
/subscribe/         POST only: email signup (home.views.subscribe)
/subscribe/confirm/<token>/       GET: double opt-in confirmation
/subscribe/unsubscribe/<token>/   GET shows a confirm page; POST deletes the subscriber
/admin/             Wagtail admin (access controls: module 07)
StandardPages       About, Contact, Editorial Policy, Affiliate Disclosure, Privacy Policy, Terms
                    (seeded as unpublished drafts by editorial/migrations/0004_seed_policy_pages.py;
                    the owner reviews and publishes each one)
```

## Hooks left by module 02
`mybestpicks/templates/base.html` already has an empty `{% block extra_head %}` for the
canonical tag, JSON-LD and the RSS `<link>`, and a marked spot in the footer for the
RSS and Telegram links. Do not add either link until `/feed/` and the Telegram
setting exist. `robots.txt` should disallow `/search/` (it is a `?query=` URL).

## Hooks left by module 04
- The affiliate disclosure (`components/affiliate_disclosure.html`) links to the
  Affiliate Disclosure page via `ArticlePage.get_context()`'s
  `affiliate_disclosure_page` lookup (slug `affiliate-disclosure`, live and
  public). It renders nothing extra until that page is published.
- FAQ blocks render visible headings and text; add `FAQPage` JSON-LD only if it is
  genuinely eligible. `ArticlePage.get_context()` exposes `article_products` and
  `has_active_offers`, which JSON-LD can reuse without new queries.

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
8. Email signup stores only the email and consent metadata (no name, nothing
   imported from Telegram), uses double opt-in (the confirmation email, sent via
   `home.views._send_confirmation_email`), puts an unsubscribe link in every send,
   and the footer form links to the privacy notice next to it (when published).
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
- [DECISION 2026-11-02] Article pages emit truthful `BlogPosting` JSON-LD plus
  `BreadcrumbList`; category hubs emit `BreadcrumbList`. FAQ rich-result markup is
  omitted because this general shopping publication is not eligible under Google's
  current FAQ rich-result restrictions. No review or rating markup is generated.
- [DECISION 2026-11-02] `BLOCK_SEARCH_INDEXING=True` adds an
  `X-Robots-Tag: noindex, nofollow` header to every staging/review response. It is
  false by default so production articles are never blocked accidentally.
- [DECISION 2026-11-02] Canonical, sitemap, robots and RSS origins use the
  environment-backed `SITE_URL`. Query strings are stripped from canonical URLs;
  RSS item URLs never carry campaign parameters.
- [DECISION 2026-11-02] Telegram is a per-site Wagtail setting. Only public
  `https://t.me/<channel>` URLs are accepted. The CTA appears on the homepage,
  article pages and footer only when configured; no channel URL is seeded or guessed.
- [DECISION 2026-11-02] The required RSS baseline is implemented independently of
  email signup.
- [DECISION 2026-11-02] Email signup ships now rather than deferring to
  post-launch (owner). Double opt-in and an unsubscribe link can be run properly
  from day one (Django's `send_mail`, console backend in dev), so the plan's
  "defer unless this is true" condition is met. `EmailSubscriber` collects only
  email + consent metadata; unsubscribing deletes the row outright. Deciding
  whether to actually promote the signup form (vs. just having it available) is
  an editorial call, not a code one.
- [DECISION 2026-11-02] `unsubscribe_token` doubles as the confirmation token
  (one opaque value, not two) since both actions are equally low-stakes to
  guess-proof. Confirming is a single GET (standard practice); unsubscribing is
  GET-to-confirm + POST-to-delete, since deleting data deserves the extra step
  a reversible opt-in doesn't.
- [DECISION 2026-11-02] The six policy pages (About, Contact, Editorial Policy,
  Affiliate Disclosure, Privacy Policy, Terms) are seeded as **unpublished**
  `StandardPage` drafts by a data migration
  (`editorial/migrations/0004_seed_policy_pages.py`), with placeholder-but-real
  draft copy and a "needs owner/legal review" notice at the top of each. Nothing
  is published automatically: the owner reviews and hits publish per page.
  `SiteSettings.contact_email` (new field) is blank by default and renders
  nothing — and the Contact page template shows no mailto link — until the owner
  sets it; never invented.
- [OPEN] Is a consent banner needed? Decide after the privacy review of the Umami
  setup, hosting region and DPDP phase dates (module 09). This is independent of
  everything else in this module and does not block its completion.
- [OPEN] The seeded policy page copy still needs the owner's review and sign-off
  before publishing (and professional advice for the Privacy Policy specifically,
  per plan §6: DPDP) — it is draft text, not vetted legal copy.

## Changelog
- 2026-11-02  Created stub from plan v4.
- 2026-11-02  Added sitemap, robots.txt, canonical/feed discovery links, RSS and
  the validated Telegram site setting/CTAs. Policy pages, JSON-LD and optional
  email signup remain for later slices.
- 2026-11-02  Added article/category JSON-LD, metadata fallbacks, explicit search
  noindex, environment-wide staging noindex protection and conditional linking
  from the in-article notice to a live Affiliate Disclosure page. Policy copy,
  email signup and the consent decision remain open.
- 2026-11-02  Shipped email signup (`EmailSubscriber`, `home/forms.py`,
  `home/views.py`, `/subscribe/...` URLs, footer form, three confirm/unsubscribe
  templates, `EMAIL_*`/`EMAIL_CONSENT_TEXT_VERSION` settings). Added
  `SiteSettings.contact_email` and wired it into the Contact `StandardPage`
  template. Seeded all six policy pages as unpublished drafts via a data
  migration, cross-linked to each other, with a review notice. Added
  `Disallow: /subscribe/` to robots.txt and a site-wide Django-messages display
  in `base.html`. Tests: `home/tests/test_email_signup.py`,
  `editorial/tests/test_policy_pages.py`.
