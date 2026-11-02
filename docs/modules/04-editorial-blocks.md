# Module: Editorial blocks

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started
**Priority:** P0
**Ticket:** MBP-004
**Plan reference:** docs/mybestpicks_plan_v4.md §4 (StreamField blocks, rendering contract, safeguards), §6 (link rendering)
**Depends on:** 03, 05
**Blocks:** 06, 10

## Purpose
The StreamField blocks used to write articles. Product cards are the **only**
source of per-article verdicts. Comparison tables are built from those cards and
never re-select products.

## Blocks (as planned; update to as-built)
```
RichTextBlock, HeadingBlock
ImageBlock            image, caption, license attribution
KeyTakeawaysBlock, BuyingCriteriaBlock
ProductCardBlock      product (SnippetChooserBlock → Product)
                      recommendation_label, verdict, pros[], cons[]
                      best_for, editorial_evidence, evidence_media (optional image)
                      tested_by_editor (bool)
ComparisonTableBlock  card_ids (optional subset of this article's product cards, in order)
                      spec_keys (optional canonical spec keys to show)
                      NO product chooser
FAQBlock, SourceNoteBlock, RelatedArticlesBlock
```

## What module 05 provides for this module
- `Product.spec_rows` / `catalog.specs.spec_rows()`: ordered, labelled, unit-aware
  rows, with `value=None` for unrecorded specs (show a dash). Use `comparable` to pick
  comparison columns.
- `MerchantOffer.objects.renderable().select_related("merchant", "product")` for the
  batch query, then keep only offers whose `is_renderable` is true (it re-checks the
  link host against the merchant's current allowlist and costs no query).
- `Merchant.cta_label` for the button text ("View at Flipkart", or the merchant's own
  text). Offers render as `rel="sponsored nofollow noopener"` in the same tab.
- `Product.image_provenance` and `image_credit`, for credit lines.

## Rendering contract (CLAUDE.md invariant 4)
`ArticlePage.get_context()`:
1. Walks `body` and collects every `ProductCardBlock`, in order, with its block id.
2. Batch-loads the referenced products with `select_related("brand")`, and their
   renderable offers with merchants, in a bounded number of queries.
3. Validates and normalises each product's specs once against `catalog/specs.py`.
4. Exposes `article_products` (ordered, keyed by block id), plus
   `has_active_offers` and `first_cta_block_id`.

Quick picks, comparison tables and card templates read only from
`article_products`. A table may appear above the cards because the context is
precomputed.

## Business rules
1. `ProductCardBlock.clean()` raises `ValidationError` when `tested_by_editor=True`
   and both `editorial_evidence` and `evidence_media` are empty. Test the valid and
   invalid cases.
2. When a card is not tested, the template never uses hands-on wording ("we
   tested", "in our testing").
3. `ComparisonTableBlock` shows all of the article's cards by default, or the
   chosen `card_ids` subset in order. An id that does not match a card is a
   validation error and must not break rendering.
4. Only `comparable` spec keys can be columns. A missing value shows as "—" and is
   never guessed.
5. A merchant CTA renders only for a renderable offer, as an
   `<a rel="sponsored nofollow noopener">` in the same tab, labelled
   "View at <Merchant>" or "Check price at <Merchant>". It never shows a price.
6. `affiliate_disclosure.html` renders once, before the first CTA, and only when
   `has_active_offers` is true.
7. Rendering an article with N product cards uses a constant number of queries
   (test with `assertNumQueries`).
8. Wagtail's reference index finds the articles that use a given `Product`. Verify
   this for the chosen chooser block, and test what happens when a product is
   swapped.

## Edge cases handled
- A card's product is deleted: blocked by PROTECT, or the card renders a safe
  placeholder. Decide which and test it.
- An article has no cards: there are no tables, no disclosure and no CTA queries.

## Open questions / Decisions
- [OPEN] Is "quick picks" its own block, or a template section built from the
  cards' `recommendation_label`?

## Changelog
- 2026-11-02  Created stub from plan v4.
