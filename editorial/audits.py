"""
Read-only editorial QA checks (module 10, MBP-010).

Business rule 1: an audit only reports; it never edits content. Nothing here
calls ``.save()``. Business rule 2: thresholds come from
``settings.EDITORIAL_AUDIT_STALE_DAYS``, not a constant buried in this module.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from wagtail.blocks.stream_block import StreamValue
from wagtail.documents.models import Document
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.rich_text import RichText

from catalog.models import MerchantOffer, Product, ProductStatus
from catalog.provenance import validate_image_provenance

from .models import ArticlePage, CategoryPage
from .rendering import resolve_article_products

# A title or excerpt matching this implies a price claim (CLAUDE.md invariant 2):
# such a claim needs a recent product verification or a rewrite.
PRICE_PATTERN = re.compile(r"₹|\bunder\b|\bbelow\b|\bbudget\b", re.IGNORECASE)


@dataclass
class Finding:
    category: str
    message: str

    def __str__(self):
        return f"[{self.category}] {self.message}"


def stale_cutoff(days=None):
    days = settings.EDITORIAL_AUDIT_STALE_DAYS if days is None else days
    return timezone.now().date() - timedelta(days=days)


# --- editorial_audit ----------------------------------------------------------


def run_editorial_audit(days=None):
    """
    All ``editorial_audit`` checks, in one pass over live articles plus the
    catalog. See docs/modules/10-editorial-qa.md for what each category means.
    """
    cutoff = stale_cutoff(days)
    stale_days = settings.EDITORIAL_AUDIT_STALE_DAYS if days is None else days
    findings = []

    for article in ArticlePage.objects.live().select_related("author"):
        products = resolve_article_products(article.body)
        price_claim = bool(
            PRICE_PATTERN.search(article.title) or PRICE_PATTERN.search(article.excerpt)
        )
        stale_for_price = set()

        for entry in products.entries:
            product, card = entry.product, entry.card

            if product.status != ProductStatus.ACTIVE:
                findings.append(
                    Finding(
                        "unavailable-product-reference",
                        f'"{article.title}" ({article.url}) references {product}, '
                        f"which is marked {product.get_status_display()}.",
                    )
                )

            if card["tested_by_editor"]:
                has_notes = bool((card["editorial_evidence"] or "").strip())
                if not (has_notes or card["evidence_media"]):
                    findings.append(
                        Finding(
                            "untested-evidence-claim",
                            f'"{article.title}" ({article.url}): the product card '
                            f"for {product} claims hands-on testing with no "
                            "evidence notes or photo.",
                        )
                    )

            if price_claim and (
                product.last_verified_at is None or product.last_verified_at < cutoff
            ):
                stale_for_price.add(str(product))

        if stale_for_price:
            findings.append(
                Finding(
                    "stale-priced-article",
                    f'"{article.title}" ({article.url}) makes a price claim, but '
                    f"these products were last verified over {stale_days} days ago "
                    f"or never: {', '.join(sorted(stale_for_price))}.",
                )
            )

    for product in Product.objects.select_related("brand"):
        try:
            validate_image_provenance(
                image=product.image,
                provenance=product.image_provenance,
                credit=product.image_credit,
                image_field="image",
                provenance_field="image_provenance",
                credit_field="image_credit",
            )
        except ValidationError as exc:
            message = "; ".join(exc.messages)
            findings.append(Finding("missing-image-evidence", f"{product}: {message}"))

    stale_offers = MerchantOffer.objects.filter(
        active=True, last_checked_at__lt=cutoff
    ).select_related("merchant", "product", "product__brand")
    for offer in stale_offers:
        findings.append(
            Finding(
                "stale-offer",
                f"{offer.product}'s {offer.merchant.name} offer was last checked "
                f"on {offer.last_checked_at}, over {stale_days} days ago.",
            )
        )

    return findings


# --- check_internal_links ------------------------------------------------------

_ANCHOR_TAG_RE = re.compile(r"<a\s+([^>]*)>", re.IGNORECASE)
_ATTR_RE = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)="([^"]*)"')


def _anchor_attrs(html):
    for match in _ANCHOR_TAG_RE.finditer(html or ""):
        yield dict(_ATTR_RE.findall(match.group(1)))


def _walk_richtext(value):
    """Yield raw HTML source from every ``RichText`` nested anywhere in a
    StreamField value (struct/stream/list blocks, arbitrarily nested)."""
    if isinstance(value, RichText):
        if value.source:
            yield value.source
    elif isinstance(value, StreamValue):
        for child in value:
            yield from _walk_richtext(child.value)
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _walk_richtext(item)
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for item in value:
            yield from _walk_richtext(item)


def _richtext_sources(page):
    for field in page._meta.get_fields():
        if isinstance(field, RichTextField):
            value = getattr(page, field.attname, "")
            if value:
                yield value
    body = getattr(page, "body", None)
    if body is not None:
        yield from _walk_richtext(body)


def _internal_path(href, site_netloc):
    parsed = urlsplit(href)
    if parsed.scheme in ("mailto", "tel", "javascript"):
        return None
    if parsed.netloc and parsed.netloc != site_netloc:
        return None  # an external link; never fetched (no SSRF risk, just skipped)
    if not parsed.path:
        return None  # a pure fragment like "#section"
    path = parsed.path
    if parsed.query:
        path += "?" + parsed.query
    return path


def _check_anchor(page, attrs, site_netloc, client, path_status):
    if attrs.get("linktype") == "page" and attrs.get("id", "").isdigit():
        target_id = int(attrs["id"])
        if not Page.objects.filter(pk=target_id, live=True).exists():
            return Finding(
                "broken-page-link",
                f"{page} ({page.url}) links to page id={target_id}, which is "
                "deleted or unpublished.",
            )
        return None

    if attrs.get("linktype") == "document" and attrs.get("id", "").isdigit():
        target_id = int(attrs["id"])
        if not Document.objects.filter(pk=target_id).exists():
            return Finding(
                "broken-document-link",
                f"{page} ({page.url}) links to document id={target_id}, which no "
                "longer exists.",
            )
        return None

    href = attrs.get("href")
    path = _internal_path(href, site_netloc) if href else None
    if path is None:
        return None

    if path not in path_status:
        try:
            path_status[path] = client.get(path).status_code
        except Exception:  # noqa: BLE001 - any failure to resolve counts as broken
            path_status[path] = None
    status = path_status[path]
    if status is None or status >= 400:
        return Finding(
            "broken-link",
            f"{page} ({page.url}) links to {path}, which returns "
            f"{status if status is not None else 'an error'}.",
        )
    return None


def _find_broken_related_article_picks():
    findings = []
    for article in ArticlePage.objects.live():
        for child in article.body:
            if child.block_type != "related_articles":
                continue
            for picked in child.value.get("articles") or []:
                if picked is None or not picked.live:
                    findings.append(
                        Finding(
                            "broken-related-pick",
                            f'"{article.title}" ({article.url}): a related-'
                            "articles block picks a page that is deleted or "
                            "unpublished.",
                        )
                    )
    return findings


def _find_broken_featured_guide_picks():
    findings = []
    for category in CategoryPage.objects.live():
        for item in category.featured_guides.select_related("article"):
            if not item.article.live:
                findings.append(
                    Finding(
                        "broken-featured-guide",
                        f'"{category.title}" ({category.url}): a featured guide '
                        "picks an article that is deleted or unpublished.",
                    )
                )
    return findings


def find_broken_internal_links(client=None):
    """
    Broken links in live, public pages. Internal links are resolved in-process
    (the Django test client, no real network call); external URLs are never
    fetched (no SSRF, and it respects merchant terms).
    """
    from django.test import Client

    client = client or Client()
    site_netloc = urlsplit(settings.SITE_URL).netloc
    path_status = {}
    findings = []

    for page in Page.objects.live().public().specific():
        for source in _richtext_sources(page):
            for attrs in _anchor_attrs(source):
                finding = _check_anchor(page, attrs, site_netloc, client, path_status)
                if finding:
                    findings.append(finding)

    findings.extend(_find_broken_related_article_picks())
    findings.extend(_find_broken_featured_guide_picks())
    return findings
