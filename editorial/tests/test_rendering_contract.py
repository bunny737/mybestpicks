"""
Invariant 4 / module 04 rule 7: products, offers, images and specs are resolved once
before any block renders, in a number of queries that does not depend on the number
of product cards.
"""

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

from catalog.provenance import ImageProvenance
from catalog.tests.helpers import (
    GOOD_LINK,
    make_brand,
    make_merchant,
    make_offer,
    make_product,
)
from editorial.models import ArticlePage, DiscoveryMode
from editorial.rendering import resolve_article_products

from .helpers import (
    TempMediaMixin,
    card_block,
    make_article,
    make_author,
    make_category,
    table_block,
)


class ResolveArticleProductsTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.brand = make_brand()
        self.merchant = make_merchant()

    def article(self, *blocks):
        article = make_article(self.hub, self.author, body=list(blocks))
        return ArticlePage.objects.get(pk=article.pk)

    def test_entries_follow_card_order_with_positions_and_block_ids(self):
        a, b = make_product("A", brand=self.brand), make_product("B", brand=self.brand)
        article = self.article(
            {"type": "paragraph", "value": "<p>x</p>"},
            card_block(b, block_id="second-product"),
            card_block(a, block_id="first-product"),
        )
        result = resolve_article_products(article.body)
        self.assertEqual([e.product.name for e in result.entries], ["B", "A"])
        self.assertEqual([e.position for e in result.entries], [1, 2])
        self.assertEqual(
            [e.block_id for e in result.entries], ["second-product", "first-product"]
        )
        self.assertEqual(result.entries[0].anchor, "product-second-product")

    def test_every_card_value_gets_its_resolved_entry(self):
        a = make_product("A", brand=self.brand)
        article = self.article(card_block(a, block_id="x"))
        result = resolve_article_products(article.body)
        card = next(c for c in article.body if c.block_type == "product_card").value
        self.assertIs(card.resolved, result.entries[0])

    def test_entries_carry_normalised_specs_and_only_renderable_offers(self):
        product = make_product("A", brand=self.brand)
        make_offer(product, self.merchant)
        make_offer(product, self.merchant, url=GOOD_LINK + "&x=2", active=False)
        entry = resolve_article_products(
            self.article(card_block(product)).body
        ).entries[0]
        self.assertEqual(entry.spec_rows[0].key, "layout")
        self.assertEqual(len(entry.offers), 1)
        self.assertTrue(entry.offers[0].is_renderable)

    def test_has_active_offers_and_the_first_cta_card(self):
        plain = make_product("Plain", brand=self.brand)
        sold = make_product("Sold", brand=self.brand)
        make_offer(sold, self.merchant)
        article = self.article(
            card_block(plain, block_id="no-offer"),
            card_block(sold, block_id="has-offer"),
        )
        result = resolve_article_products(article.body)
        self.assertTrue(result.has_active_offers)
        self.assertEqual(result.first_cta_block_id, "has-offer")

    def test_no_offers_means_no_disclosure_flag(self):
        a = make_product("A", brand=self.brand)
        result = resolve_article_products(self.article(card_block(a)).body)
        self.assertFalse(result.has_active_offers)
        self.assertIsNone(result.first_cta_block_id)

    def test_the_same_product_in_two_cards_gives_two_entries(self):
        a = make_product("A", brand=self.brand)
        article = self.article(
            card_block(a, block_id="one"), card_block(a, block_id="two")
        )
        result = resolve_article_products(article.body)
        self.assertEqual([e.block_id for e in result.entries], ["one", "two"])

    def test_a_deleted_product_is_left_out_but_still_counts_for_positions(self):
        gone = make_product("Gone", brand=self.brand)
        keep = make_product("Keep", brand=self.brand)
        article = self.article(card_block(gone), card_block(keep))
        gone.delete()
        result = resolve_article_products(ArticlePage.objects.get(pk=article.pk).body)
        self.assertEqual([e.product.name for e in result.entries], ["Keep"])
        self.assertEqual(result.entries[0].position, 2)  # as the editor counted it

    def test_get_context_exposes_the_contract(self):
        a = make_product("A", brand=self.brand)
        make_offer(a, self.merchant)
        article = self.article(card_block(a, block_id="x", recommendation_label="Best"))
        context = article.get_context(self.client.get("/").wsgi_request)
        self.assertEqual(len(context["article_products"]), 1)
        self.assertTrue(context["has_active_offers"])
        self.assertEqual(context["first_cta_block_id"], "x")
        self.assertEqual(len(context["quick_picks"]), 1)


class QueryBudgetTests(TempMediaMixin, TestCase):
    """The query count must not grow with the number of cards."""

    def setUp(self):
        super().setUp()
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.brand = make_brand()
        self.merchant = make_merchant()
        self.photo = Image.objects.create(title="Mine", file=get_test_image_file())

    def build(self, count, slug):
        blocks = []
        for i in range(count):
            image = Image.objects.create(title=f"p{i}", file=get_test_image_file())
            product = make_product(
                f"P{slug}{i}",
                brand=self.brand,
                image=image,
                image_provenance=ImageProvenance.OWNED_ORIGINAL,
            )
            make_offer(product, self.merchant, url=GOOD_LINK + f"&n={slug}{i}")
            blocks.append(
                card_block(
                    product,
                    recommendation_label=f"Pick {i}",
                    tested_by_editor=True,
                    editorial_evidence="Used it.",
                    evidence_media=self.photo.pk,
                )
            )
        blocks.append(table_block())
        return make_article(self.hub, self.author, slug=slug, body=blocks)

    def queries_for(self, article):
        self.client.get(article.url)  # warm: first view creates the renditions
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(article.url)
        self.assertEqual(response.status_code, 200)
        return response, len(queries)

    def test_query_count_is_the_same_for_2_and_9_cards(self):
        small, few = self.queries_for(self.build(2, "small"))
        large, many = self.queries_for(self.build(9, "large"))
        self.assertContains(large, 'class="product-card', count=9)
        self.assertEqual(few, many)

    def test_the_catalog_is_queried_a_fixed_number_of_times(self):
        article = self.build(6, "fixed")
        self.client.get(article.url)
        with CaptureQueriesContext(connection) as queries:
            self.client.get(article.url)
        sql = [q["sql"] for q in queries]
        self.assertEqual(sum('FROM "catalog_product"' in s for s in sql), 1)
        self.assertEqual(sum('FROM "catalog_merchantoffer"' in s for s in sql), 1)
        self.assertEqual(sum('FROM "catalog_brand"' in s for s in sql), 0)  # joined

    def test_an_article_with_no_cards_runs_no_catalog_queries(self):
        article = make_article(
            self.hub,
            self.author,
            slug="plain",
            body=[{"type": "paragraph", "value": "<p>Words only.</p>"}],
        )
        self.client.get(article.url)
        with CaptureQueriesContext(connection) as queries:
            self.client.get(article.url)
        self.assertFalse(any("catalog_" in q["sql"] for q in queries))
