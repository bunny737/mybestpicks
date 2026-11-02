"""
Invariant 7 / module 04 rule 6: the affiliate disclosure renders ONCE, before the
first CTA, and ONLY when an offer will actually render.
"""

from django.test import TestCase

from catalog.models import Merchant, MerchantOffer, Product, ProductStatus
from catalog.tests.helpers import (
    GOOD_LINK,
    make_brand,
    make_merchant,
    make_offer,
    make_product,
)
from editorial.models import DiscoveryMode

from .helpers import card_block, make_article, make_author, make_category, table_block

MARKER = "affiliate-disclosure"


class DisclosureTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.brand = make_brand()
        self.merchant = make_merchant()
        self.product = make_product("K1", brand=self.brand)
        self.article = make_article(
            self.hub,
            self.author,
            body=[
                {"type": "paragraph", "value": "<p>Intro.</p>"},
                card_block(self.product, block_id="k1"),
            ],
        )

    def html(self):
        return self.client.get(self.article.url).content.decode()

    def test_no_offers_means_no_disclosure(self):
        self.assertNotIn(MARKER, self.html())

    def test_an_active_offer_shows_the_disclosure_once_before_the_first_cta(self):
        make_offer(self.product, self.merchant)
        html = self.html()
        self.assertEqual(html.count(MARKER), 1)
        self.assertLess(html.index(MARKER), html.index('rel="sponsored'))

    def test_it_stays_once_with_many_cards_offers_and_a_table(self):
        other = make_product("K2", brand=self.brand)
        make_offer(self.product, self.merchant)
        make_offer(other, self.merchant, url=GOOD_LINK + "&n=2")
        make_offer(other, self.merchant, url=GOOD_LINK + "&n=3")
        article = make_article(
            self.hub,
            self.author,
            slug="many",
            body=[
                card_block(self.product),
                card_block(other),
                card_block(self.product),
                table_block(),
            ],
        )
        html = self.client.get(article.url).content.decode()
        self.assertEqual(html.count(MARKER), 1)
        self.assertGreaterEqual(html.count('rel="sponsored'), 3)
        self.assertLess(html.index(MARKER), html.index('rel="sponsored'))

    def test_the_disclosure_comes_before_the_whole_article_body(self):
        make_offer(self.product, self.merchant)
        html = self.html()
        self.assertLess(html.index(MARKER), html.index("Intro."))

    def test_an_offer_that_will_not_render_never_triggers_the_disclosure(self):
        make_offer(self.product, self.merchant)
        cases = {
            "inactive": lambda: MerchantOffer.objects.update(active=False),
            "merchant disabled": lambda: Merchant.objects.update(enabled=False),
            "product discontinued": lambda: Product.objects.update(
                status=ProductStatus.DISCONTINUED
            ),
            "host no longer allowed": lambda: Merchant.objects.update(
                allowed_link_domains="other.example.test"
            ),
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                change()
                html = self.html()
                self.assertNotIn(MARKER, html)
                self.assertNotIn("sponsored", html)
                # restore for the next case
                MerchantOffer.objects.update(active=True)
                Merchant.objects.update(
                    enabled=True, allowed_link_domains="track.example.test"
                )
                Product.objects.update(status=ProductStatus.ACTIVE)

    def test_the_disclosure_makes_no_program_claims(self):
        # Never claim Amazon Associate (or any programme) status.
        make_offer(self.product, self.merchant)
        html = self.html()
        text = html[html.index(MARKER) :]
        text = text[: text.index("</aside>")]
        for word in ("Amazon", "Associate", "Flipkart", "Cuelinks", "price"):
            self.assertNotIn(word, text)
        self.assertIn("affiliate links", text)
