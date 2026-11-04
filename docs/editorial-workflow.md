# Editorial Workflow & Standards

Plan reference: [mybestpicks_plan_v4.md §4, §5A, §7, §10](mybestpicks_plan_v4.md).
Tooling support: [modules/10-editorial-qa.md](modules/10-editorial-qa.md).

## 1. Every recommendation explains
**Selection criteria · evidence · who it fits · limitations · alternatives · research date.**
Never present a list based only on research as a hands-on review.

## 2. Weekly workflow
1. Check search intent in India: pick one specific, useful reader decision.
2. Note what the editor owns or can test, and keep firsthand testing separate from
   desk research.
3. Get licensed or owned images and keep the provenance evidence (section 4).
4. Normalise specs against the product-type schema (`catalog/specs.py`) and check
   availability. Add merchant links only where they genuinely help and are approved.
5. Draft with clear evidence, limitations, practical use cases and the disclosure
   where it applies.
6. Review on mobile, then publish once it is live. Update internal links and check
   indexing.
7. Audit existing claims, especially headlines that depend on price, against their
   verification dates: run `python manage.py editorial_audit` (stale price claims,
   missing image evidence, discontinued-product references, stale offer checks,
   unsupported hands-on claims) and `python manage.py check_internal_links`
   (broken page/document links, dead hrefs, stale related-article and
   featured-guide picks). Both only report; neither edits content.
8. Share one useful Telegram summary with a tracked link where it is relevant
   ([telegram-distribution.md](telegram-distribution.md)), and collect reader
   questions for the next guide.

Cadence: 1–2 substantive pieces a week after the initial build. Baseline is 12–18
in 12 weeks; 30 is a stretch goal. Do not write filler to reach it.

## 3. Hands-on claims
- Tick `tested_by_editor` only with evidence notes or media. The CMS enforces this.
- Do not imply hands-on experience in any other case.

## 4. Product images
Do **not** download Amazon or Flipkart listing photos just because they are public.
Choose in this order:
1. `owned_original`: your own photos of equipment you own or tested
2. `manufacturer_licensed`: written permission or licensed press media
3. `other_licensed`: another license, with the evidence stored
4. `permitted_program_content`: only where the affiliate program's terms allow it

If no legal image exists, use a text and spec card. Plan image sourcing into each
article's research time.

## 5. Prices
- A price may appear only as text in an article, with an "as of <date>" stamp beside it
  (for example "₹1,499 as of 4 Nov 2026"). The date is the day you checked the price
  yourself. Never copy a price without checking it, and never put one in a button,
  widget or catalog field.
- Re-check or delete any price older than 30 days. Check the Amazon and Flipkart
  programme terms on showing prices before relying on this.
- A title like "under ₹1,000" needs a recent `last_verified_at` on the products it
  references. Re-verify every 30 days, or sooner for volatile categories. If it is
  unverified, rewrite the title so it is price-neutral.
- CTAs use price-neutral labels: "View at Flipkart" or "Check price at Amazon".

## 6. Categories (hubs)
- **Create a hub only when its first article is ready.** Publish the hub
  (`force_hide`) before its first child article, so breadcrumbs and URLs resolve.
- Each article has one primary hub. Use tags, related articles and internal links
  for cross-topic discovery, and never duplicate an article under two hubs.
- Reveal a hub (`auto` or `force_show`) only after the new-hub gate in
  [launch-checklist.md](launch-checklist.md#before-revealing-a-new-hub) passes.
- Order: Developer Setup first, then Home & Kitchen (about week 10). Car
  Accessories, Gadgets & Tech and Home Office stay off the public nav until each
  has three useful articles.
- A new hub needs no code. A new **product type** needs a developer
  (`catalog/specs.py`).

## 7. Affiliate links (optional)
- Create Cuelinks deeplinks by hand in the dashboard and store them as
  `MerchantOffer.affiliate_url`. Check the real destination by hand before
  activating an offer.
- Never paste in Cuelinks auto-convert JS, and never use link shorteners or
  cloakers.
- Do not claim Amazon Associate status until the account is accepted.

## 8. Planned launch content (Developer Setup)
From plan §10: an ergonomic coding desk and laptop-stand guide · a USB-C hub
compatibility explainer · mechanical vs membrane keyboards · a coding keyboard
buying guide · USB-C hubs for developers · monitor arms or keyboard ergonomics ·
desk cable management · home-office lighting · a small-space desk setup.
