"""
The article rendering contract (module 04, CLAUDE.md invariant 4).

``resolve_article_products(body)`` runs once from ``ArticlePage.get_context()``,
before any body block renders. It collects every product card in order, resolves
the products, their renderable offers, images and normalised specs in a constant
number of queries, and attaches the result to each card as ``card.resolved``.
Quick picks, product cards and comparison tables then read only that: nothing in a
template queries per card.

The query budget does not depend on the number of cards:
  1. products (with brands)      — loaded by ``ProductChooserBlock.bulk_to_python``
  2. evidence photos             — loaded by the image chooser's bulk load
  3. renderable offers + merchants
  4. product and evidence images, and 5. their renditions (prefetched)
"""

from collections import defaultdict
from dataclasses import dataclass, field

from wagtail.images.models import Image

from catalog.models import MerchantOffer
from catalog.specs import SpecRow, spec_rows

# Rendition filter specs used by the product card template. They must match the
# `{% image ... %}` tags there so the prefetched renditions are the ones used.
PRODUCT_IMAGE_SPEC = "width-400"
EVIDENCE_IMAGE_SPEC = "width-640"

MISSING = "—"  # em dash shown for a spec a product does not record


@dataclass
class ProductEntry:
    """One resolved product card of one article."""

    block_id: str
    position: int  # 1-based among ALL cards, as an editor counts them
    product: object  # catalog.Product, brand and image already loaded
    card: object  # the ProductCardBlock value: verdict, pros, cons, evidence...
    offers: list = field(default_factory=list)  # renderable offers only
    spec_rows: list = field(default_factory=list)

    @property
    def anchor(self):
        return f"product-{self.block_id}"

    @property
    def spec_map(self):
        return {row.key: row for row in self.spec_rows}


@dataclass
class ArticleProducts:
    entries: list = field(default_factory=list)
    has_active_offers: bool = False
    first_cta_block_id: str | None = None


def resolve_article_products(body):
    """Resolve every product card in ``body`` (a StreamValue). See module docstring."""
    cards = []
    position = 0
    for child in body:
        if child.block_type != "product_card":
            continue
        position += 1
        # The first ``.value`` access loads ALL cards' products in one query.
        cards.append((position, str(child.id), child.value))

    # A product deleted after the card was saved resolves to None: that card renders
    # nothing for readers (and is left out of tables), instead of breaking the page.
    resolved = [(pos, bid, card) for pos, bid, card in cards if card["product"]]
    if not resolved:
        return ArticleProducts()

    products = {card["product"].pk: card["product"] for _, _, card in resolved}

    offers_by_product = defaultdict(list)
    offers = (
        MerchantOffer.objects.renderable()
        .filter(product_id__in=products)
        .select_related("merchant")
        .order_by("sort_order", "pk")
    )
    for offer in offers:
        # Hand the offer its product so ``is_renderable`` needs no query.
        offer.product = products[offer.product_id]
        if offer.is_renderable:
            offers_by_product[offer.product_id].append(offer)

    _attach_images(resolved)

    entries = []
    for pos, block_id, card in resolved:
        product = card["product"]
        entry = ProductEntry(
            block_id=block_id,
            position=pos,
            product=product,
            card=card,
            offers=offers_by_product.get(product.pk, []),
            spec_rows=spec_rows(product.product_type, product.key_specs),
        )
        card.resolved = entry  # what the product card template reads
        entries.append(entry)

    first_cta = next((e for e in entries if e.offers), None)
    return ArticleProducts(
        entries=entries,
        has_active_offers=first_cta is not None,
        first_cta_block_id=first_cta.block_id if first_cta else None,
    )


def _attach_images(resolved):
    """Load every product and evidence image once, with their renditions prefetched."""
    image_ids = set()
    for _, _, card in resolved:
        if card["product"].image_id:
            image_ids.add(card["product"].image_id)
        if card["evidence_media"]:
            image_ids.add(card["evidence_media"].pk)
    if not image_ids:
        return
    images = {
        image.pk: image
        for image in Image.objects.filter(pk__in=image_ids).prefetch_renditions(
            PRODUCT_IMAGE_SPEC, EVIDENCE_IMAGE_SPEC
        )
    }
    for _, _, card in resolved:
        product = card["product"]
        if product.image_id:
            product.image = images.get(product.image_id)
        if card["evidence_media"]:
            card["evidence_media"] = images.get(card["evidence_media"].pk)


def build_comparison_table(entries, positions, spec_keys):
    """
    Rows and columns for a comparison table, from already-resolved entries.

    - ``positions``: which cards to include, in the editor's order. Empty means all.
      A position with no matching card is skipped, never an error at render time
      (the card may have been removed since the table was saved).
    - ``spec_keys``: which columns. Empty means every comparable spec. Either way, a
      column no included product records is left out.
    A spec a product does not record shows as an em dash; nothing is guessed.
    Returns ``None`` when there is nothing meaningful to compare (fewer than two
    products or no columns), so the template renders nothing.
    """
    by_position = {entry.position: entry for entry in entries}
    if positions:
        chosen, seen = [], set()
        for position in positions:
            entry = by_position.get(int(position))
            if entry is not None and position not in seen:
                chosen.append(entry)
                seen.add(position)
    else:
        chosen = list(entries)
    if len(chosen) < 2:
        return None

    labels = {}
    for entry in chosen:
        for row in entry.spec_rows:
            if row.comparable:
                labels.setdefault(row.key, row.label)

    # Only columns at least one included product actually records. A column of dashes
    # tells readers nothing, so it is dropped even when an editor listed it.
    recorded = {
        key
        for entry in chosen
        for key, row in entry.spec_map.items()
        if row.comparable and row.display_value != ""
    }
    wanted = spec_keys or list(labels)
    columns = [key for key in wanted if key in labels and key in recorded]
    if not columns:
        return None

    rows = []
    for entry in chosen:
        spec_map = entry.spec_map
        cells = []
        for key in columns:
            row = spec_map.get(key)
            cells.append(row.display_value if row and row.display_value else MISSING)
        rows.append({"entry": entry, "cells": cells})

    return {
        "columns": [{"key": key, "label": labels[key]} for key in columns],
        "rows": rows,
    }


__all__ = [
    "ArticleProducts",
    "ProductEntry",
    "SpecRow",
    "build_comparison_table",
    "resolve_article_products",
]
