# Module: Product catalog

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Done (2026-11-02). The product-type list is provisional and not a blocker (see Decisions)
**Priority:** P0
**Ticket:** MBP-005
**Plan reference:** docs/mybestpicks_plan_v4.md §4 (product and merchant models, validation), §6, §7 (image sourcing)
**Depends on:** 01
**Blocks:** 04, 10, 11

## Purpose
Reusable editorial product facts (brands, products, normalised specs) and
**optional** merchant offers, kept apart from per-article judgement. An article can
launch with no merchant links at all.

## Data model (as-built)
Code: `catalog/models.py`, `catalog/specs.py`, `catalog/validators.py`,
`catalog/provenance.py` (from module 03), `catalog/wagtail_hooks.py`. Migration
`catalog.0001_initial`. Everything is a Wagtail **snippet** under a "Catalog" admin
menu (Products, Brands, Merchants).

```
Brand
  name (unique), slug (unique; generated from the name when blank), website (https only)

Product   (ClusterableModel, searchable)
  brand            FK → Brand (PROTECT)
  name, model_number (blank allowed)
  product_type     choices from catalog/specs.py
  key_specs        JSONField, validated and normalised by Product.clean()
  image            FK → wagtailimages.Image (SET_NULL)
  image_provenance, image_credit      same rules as module 03 (catalog/provenance.py)
  status           active | discontinued | unavailable
  last_verified_at DateField, optional
  UNIQUE (brand, name, model_number)
  property spec_rows → ordered SpecRow list for display or comparison
  offers           inline MerchantOffer (edited on the product screen)

Merchant
  name (unique)    shown to readers, e.g. Flipkart
  destination_domain   where the shopper lands (flipkart.com)   ← kept SEPARATE from
  network          direct | cuelinks                              ← how it is tracked
  allowed_link_domains  one exact tracking hostname per line (normalised on clean)
  enabled (default True), cta_text (blank → "View at <name>"), disclosure_notes
  properties: allowed_hosts (set), cta_label

MerchantOffer   (Orderable under Product)
  product          ParentalKey → Product (CASCADE)
  merchant         FK → Merchant (PROTECT)
  affiliate_url    https, tracking host ∈ merchant.allowed_hosts
  destination_product_url   optional, for a human check only, never fetched
  last_checked_at  DateField; REQUIRED before an offer can be active
  active           default FALSE
  campaign_notes
  manager          MerchantOffer.objects.renderable()
  property         is_renderable

ArticleSource  (Orderable under ArticlePage; lives in the editorial app, migration
                editorial.0002)
  article, source_name, url (http/https only), accessed_on,
  source_type (manufacturer | datasheet | review | retailer | other),
  is_public (default False)
```
There is **no `ArticleProduct`** and **no `AffiliateClickEvent`** model, and no price
field on any model. Tests guard all three.

## Spec schemas: `catalog/specs.py`
`PRODUCT_SPEC_SCHEMAS[product_type]` is a `ProductTypeSchema` of `SpecDef`s with: `key`
(canonical snake_case), `label`, `unit`, `value_type` (int | decimal | bool | str |
choice), `choices`, `required`, `comparable`, `minimum` and `display_order`. For
example `power_watts` is displayed as `Power Delivery pass-through (W)`.
`SCHEMA_VERSION = 1`. No admin model, no migration when the schema changes.

Public API: `validate_key_specs(product_type, key_specs)` returns the normalised dict
or raises a `ValidationError` listing every problem; `spec_rows(product_type,
key_specs)` returns every spec in display order (unrecorded ones with `value=None`, so
a comparison table shows a dash instead of guessing).

**Provisional types** (proposed 2026-11-02; the owner names real ones when needed):
- `keyboard`: layout*, switch_type*, connectivity*, hot_swappable, backlight,
  battery_life_hours, weight_g
- `laptop_stand`: material*, adjustable_height*, min_height_cm, max_height_cm,
  max_laptop_size_in, max_load_kg, foldable, weight_g
- `usb_c_hub`: ports_usb_a*, ports_usb_c*, hdmi*, ethernet, sd_card_reader,
  power_watts, data_speed_gbps, weight_g
- `monitor_arm`: arm_count*, vesa_mount*, min_screen_in, max_screen_in, max_load_kg,
  desk_mount, gas_spring

(`*` = required.)

## Wagtail admin
- Catalog menu with list, filter (type, status, brand) and search for each snippet.
- The product screen shows a help panel listing the spec keys per product type, a
  JSON box for `key_specs`, and the merchant offers inline. Validation errors from the
  schema and from the offer URL rules appear on the form.
- The article screen has a "Research sources" inline. Public sources are listed under
  the article as "Sources" with `rel="noopener nofollow"`; private ones never render.

## Business rules
Each rule maps to a test in `catalog/tests/` or `editorial/tests/test_sources.py`.
1. `Product.clean()` rejects missing required specs, unknown keys and values of the
   wrong type for the product's `product_type`, and stores the normalised specs.
   (`test_specs`, `test_models`)
2. A product with an image needs `image_provenance`; anything except an owned
   original also needs a credit or licence evidence. (`test_models`)
3. `MerchantOffer.affiliate_url` must be `https://`, with no username or password, no
   non-default port, no whitespace, control characters or backslashes, no
   credential-like query parameter (`token`, `password`, ...), and its parsed
   **hostname** must exactly match an entry in the merchant's allowlist. The retailer
   domain alone is not enough, and subdomains or suffixes of an allowed host do not
   match. IP addresses are rejected. (`test_validators`, `test_models`, `test_admin`)
4. URLs are validated by parsing only. Nothing in `catalog` opens a connection,
   resolves a name or follows a redirect (SSRF); the tests run with the network
   patched to raise. (`test_validators`)
5. An offer is renderable only when it is `active`, its merchant is `enabled`, the
   product is not `discontinued`, **and** its link host is still in the merchant's
   current allowlist (`is_renderable`). A temporarily `unavailable` product still
   shows its offer. (`test_models`)
6. An offer can only be activated after a manual check date is recorded, and new
   offers start inactive. (`test_models`)
7. `destination_product_url` must be on the merchant's destination domain or a
   subdomain. (`test_models`, `test_validators`)
8. Adding a new `product_type` changes `specs.py` and `test_specs.py`, then needs a
   deploy. A new editorial category needs no code. (`test_specs` checks every schema is
   well formed, including that no spec is about price.)
9. A brand with products, and a merchant with offers, cannot be deleted (PROTECT).
   (`test_models`)

## Edge cases handled
- A Cuelinks-tracked Flipkart link: `network=cuelinks`, `destination_domain=flipkart.com`,
  the allowlist holds the tracker's hostnames, and the button still reads "View at
  Flipkart". (`test_models`)
- A product is marked discontinued after articles used it: its offers stop rendering at
  once. Flagging those articles is module 10.
- Removing a host from a merchant's allowlist stops existing links on that host from
  rendering without editing each offer. (`test_models`)
- Rendering N offers needs one query (with `select_related`) and no further queries
  for `is_renderable`. (`test_models`)

## Open questions / Decisions
- [DECISION 2026-11-02] The four product types above are a **provisional starting set,
  not a blocker**. The owner will name the product types when they write a post that
  needs them, so nothing has to be confirmed now. At that point add the type to
  `specs.py` and `test_specs.py` first (CLAUDE.md: confirm the spec keys before adding
  a type). An article does not need any product, so publishing is never blocked.
- [OPEN] Add a generic "Other" product type (no required specs) so any product can be
  added from the admin without a code change? Trade-off: no comparison columns until a
  proper type exists. Not built; the owner has not asked for it.
- [OPEN] The real Cuelinks tracking hostnames for this account. Take them from
  verified links in the signed-in dashboard; never guess. Tests use the reserved
  `track.example.test` host.
- [DECISION 2026-11-02] `MerchantOffer` is an **inline under Product** (an
  `Orderable`), not a separate snippet: editors manage a product's links on one screen.
- [DECISION 2026-11-02] `EditorialSource` is an inline `ArticleSource` on
  `ArticlePage` in the **editorial** app, not in `catalog`: it belongs to the article,
  and `editorial` already depends on `catalog`, so the reverse would be circular.
  It is private by default; ticking `is_public` lists it under the article.
- [DECISION 2026-11-02] New offers are **inactive by default**, and activating one
  requires `last_checked_at`. This enforces the plan's "inspect the real destination by
  hand before activation" in the data, not only in a checklist.
- [DECISION 2026-11-02] `key_specs` is edited as raw JSON with an on-screen guide of
  the keys. A per-field form would need JavaScript that reacts to the chosen type;
  revisit if editors find JSON awkward.
- [DECISION 2026-11-02] Allowlist matching is exact and the `key` query parameter is
  not on the credential denylist (too common in harmless tracking links).
- [DECISION 2026-11-02] `last_verified_at` and `last_checked_at` are dates, not
  timestamps. The staleness check (default 30 days) is module 10.
- [OPEN] `Product.offers` shows in the admin only. Public rendering of offers (button,
  `rel="sponsored nofollow noopener"`, disclosure) is module 04.

## Changelog
- 2026-11-02  Created stub from plan v4.
- 2026-11-02  Built: Brand, Product, Merchant, MerchantOffer, ArticleSource,
  `specs.py`, URL validators, Catalog admin menu, migrations `catalog.0001` and
  `editorial.0002`, 94 new tests (163 in total). Mutation-checked the allowlist and
  credential rules.
