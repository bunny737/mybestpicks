# Module: Product catalog

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started
**Priority:** P0
**Ticket:** MBP-005
**Plan reference:** docs/mybestpicks_plan_v4.md §4 (product and merchant models, validation), §6, §7 (image sourcing)
**Depends on:** 01
**Blocks:** 04, 10, 11

## Purpose
Reusable editorial product facts (brands, products, normalised specs) and
**optional** merchant offers, kept apart from per-article judgement. An article can
launch with no merchant links at all.

## Data model (as planned; update to as-built)
```
Model: Brand   (snippet)   app: catalog
  name, slug (unique), website (optional, https)

Model: Product   (snippet)   app: catalog
  brand            FK → Brand (PROTECT)
  name
  model_number
  product_type     choices from PRODUCT_SPEC_SCHEMAS keys (keyboard, usb_c_hub, laptop_stand, …)
  key_specs        JSONField, validated by Product.clean() against the product_type schema
  image            FK → wagtailimages (optional)
  image_provenance owned_original | manufacturer_licensed | other_licensed | permitted_program_content
  image_license_evidence / image_credit
  status           active | discontinued | unavailable
  last_verified_at
  NO price fields

Model: Merchant   (snippet)   app: catalog
  name                 display label, e.g. "Flipkart"
  destination_domain   e.g. flipkart.com
  network              direct | cuelinks
  allowed_link_domains list of exact hostnames that tracking links may use
  enabled
  disclosure_notes

Model: MerchantOffer   app: catalog (snippet or inline under Product)
  product                  FK → Product (CASCADE)
  merchant                 FK → Merchant (PROTECT)
  affiliate_url            https, tracking hostname ∈ merchant.allowed_link_domains
  destination_product_url  optional, for human review only
  last_checked_at
  active
  campaign_notes
  NO price fields

Model: EditorialSource   app: catalog (or editorial)
  article (FK → ArticlePage), source_name, url, accessed_on, source_type
```

There is **no `ArticleProduct`** model and **no `AffiliateClickEvent`** model.

## Spec schemas: `catalog/specs.py`
A versioned Python mapping `PRODUCT_SPEC_SCHEMAS[product_type]`, where each spec has:
`key` (canonical), `label`, `unit`, `value_type` (int/decimal/bool/str/choice),
`comparable`, `required` and `display_order`. For example `power_watts` →
`Power (W)`. There is no admin model and no migration for schema changes. Product
type is independent of the editorial hub: a USB-C hub can appear in Developer
Setup and in Gadgets.

## Business rules
1. `Product.clean()` rejects missing required spec keys, unknown keys and values of
   the wrong type for the product's `product_type`.
2. A product with an image must have `image_provenance` set and, unless the image is
   `owned_original`, license evidence or credit.
3. `MerchantOffer.affiliate_url` must be `https://`, with no userinfo
   (`user:pass@`), no non-default port and no unsupported scheme, and its parsed
   **hostname** must exactly match an entry in `merchant.allowed_link_domains`. The
   destination retailer domain alone is not enough.
4. URLs are validated by parsing only. Never fetch or follow redirects on the server
   (SSRF).
5. An offer is renderable only when `active` is true, `merchant.enabled` is true and
   the product is not `discontinued`.
6. Adding a new `product_type` changes `specs.py`, the choices and the tests, and
   then needs a deploy. A new editorial category needs no code.

## Edge cases handled
- A Cuelinks tracking link for Flipkart: `network=cuelinks`,
  `destination_domain=flipkart.com`, and the allowlist holds the Cuelinks hostnames
  actually issued to this account. The display label is still "View on Flipkart".
- A product is referenced by articles and then marked discontinued: its offers stop
  rendering, and editorial QA (module 10) flags the articles.

## Open questions / Decisions
- [OPEN] The exact Cuelinks tracking hostnames for this account. Take them from
  verified links in the signed-in dashboard, never guess them.
- [OPEN] The first product types and their spec keys (keyboard, laptop_stand,
  usb_c_hub, monitor_arm, …). Confirm before writing `specs.py`.
- [OPEN] Is `EditorialSource` a model, or an `orderable` inline on `ArticlePage`?

## Changelog
- 2026-11-02  Created stub from plan v4.
