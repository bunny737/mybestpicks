"""Module 04: product cards, hands-on evidence, CTAs, quick picks."""

import re

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

from catalog.models import Product, ProductStatus
from catalog.provenance import ImageProvenance
from catalog.tests.helpers import (
    GOOD_LINK,
    make_brand,
    make_merchant,
    make_offer,
    make_product,
)
from editorial.blocks import ProductCardBlock
from editorial.models import DiscoveryMode

from .helpers import (
    TempMediaMixin,
    card_block,
    make_article,
    make_author,
    make_category,
)


class HandsOnEvidenceRuleTests(TestCase):
    """Invariant 8: a hands-on claim needs evidence (unit tests of the block)."""

    def setUp(self):
        self.product = make_product()
        self.block = ProductCardBlock()

    def value(self, **fields):
        raw = card_block(self.product, **fields)["value"]
        return self.block.to_python(raw)

    def test_tested_without_evidence_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            self.block.clean(self.value(tested_by_editor=True))
        self.assertIn("editorial_evidence", ctx.exception.block_errors)

    def test_whitespace_only_notes_are_not_evidence(self):
        with self.assertRaises(ValidationError):
            self.block.clean(
                self.value(tested_by_editor=True, editorial_evidence="   \n ")
            )

    def test_tested_with_evidence_notes_is_valid(self):
        self.block.clean(
            self.value(
                tested_by_editor=True,
                editorial_evidence="Typed on it for two weeks, 6 hours a day.",
            )
        )

    def test_tested_with_an_evidence_photo_is_valid(self):
        image = Image.objects.create(title="Mine", file=get_test_image_file())
        self.block.clean(self.value(tested_by_editor=True, evidence_media=image.pk))

    def test_not_tested_needs_no_evidence(self):
        self.block.clean(self.value(tested_by_editor=False))

    def test_the_error_is_a_validation_error_subclass(self):
        # Wagtail's StructBlockValidationError is a ValidationError.
        try:
            self.block.clean(self.value(tested_by_editor=True))
        except ValidationError as exc:
            self.assertIsInstance(exc, ValidationError)
        else:
            self.fail("expected a ValidationError")


class ProductCardRenderingTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.brand = make_brand("Acme")
        self.product = make_product("K1", brand=self.brand)
        self.merchant = make_merchant()

    def article(self, *blocks, slug="guide"):
        return make_article(self.hub, self.author, slug=slug, body=list(blocks))

    def get(self, article):
        response = self.client.get(article.url)
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def card_html(self, html):
        start = html.index('class="product-card')
        return html[start : html.index("</section>", start)]

    def test_card_shows_the_product_the_verdict_and_pros_and_cons(self):
        article = self.article(
            card_block(
                self.product,
                verdict="<p>Great <b>switches</b>.</p>",
                pros=["Quiet", "Solid build"],
                cons=["Heavy"],
                best_for="Long typing sessions",
            )
        )
        card = self.card_html(self.get(article))
        self.assertIn("Acme K1", card)
        self.assertIn("Great <b>switches</b>.", card)
        self.assertIn("<li>Quiet</li>", card)
        self.assertIn("<li>Heavy</li>", card)
        self.assertIn("Best for: Long typing sessions", card)

    def test_card_lists_the_product_specs_with_readable_values(self):
        card = self.card_html(self.get(self.article(card_block(self.product))))
        self.assertIn("Layout", card)
        self.assertIn("Tenkeyless (TKL)", card)
        self.assertIn("Switch type", card)

    def test_an_untested_card_never_uses_hands_on_wording(self):
        # Module 04 rule 2.
        card = self.card_html(self.get(self.article(card_block(self.product))))
        self.assertNotIn("tested", card.lower())
        self.assertNotIn("in our testing", card.lower())
        self.assertIn("desk research", card)

    def test_a_tested_card_shows_the_evidence(self):
        article = self.article(
            card_block(
                self.product,
                tested_by_editor=True,
                editorial_evidence="Used daily for a fortnight.",
            )
        )
        card = self.card_html(self.get(article))
        self.assertIn("Hands-on tested by our editor", card)
        self.assertIn("Used daily for a fortnight.", card)
        self.assertNotIn("desk research", card)

    def test_a_card_gets_an_anchor_from_its_block_id(self):
        article = self.article(card_block(self.product, block_id="abc-123"))
        self.assertIn('id="product-abc-123"', self.get(article))

    def test_product_image_has_dimensions_and_is_lazy_with_a_credit(self):
        image = Image.objects.create(title="K1", file=get_test_image_file())
        product = make_product(
            "K2",
            brand=self.brand,
            image=image,
            image_provenance=ImageProvenance.MANUFACTURER_LICENSED,
            image_credit="Press kit, permission 2026-10-30",
        )
        card = self.card_html(self.get(self.article(card_block(product))))
        img = re.search(r"<img[^>]*>", card).group(0)
        self.assertRegex(img, r'width="\d+"')
        self.assertRegex(img, r'height="\d+"')
        self.assertIn('loading="lazy"', card)
        self.assertIn("Image: Press kit, permission 2026-10-30", card)

    def test_verdict_text_cannot_inject_script(self):
        article = self.article(
            card_block(self.product, pros=["<script>alert(1)</script>"])
        )
        self.assertNotIn("<script>alert(1)</script>", self.get(article))

    def test_product_status_notes(self):
        article = self.article(card_block(self.product))
        Product.objects.update(status=ProductStatus.DISCONTINUED)
        self.assertIn("has been discontinued", self.get(article))
        Product.objects.update(status=ProductStatus.UNAVAILABLE)
        self.assertIn("temporarily out of stock", self.get(article))

    def test_a_card_for_a_deleted_product_renders_nothing_and_does_not_break(self):
        # Decision: StreamField references are not database foreign keys, so a
        # deleted product cannot be blocked. The card is simply left out.
        gone = make_product("Gone", brand=self.brand)
        article = self.article(
            card_block(gone, block_id="dead"), card_block(self.product, block_id="ok")
        )
        gone.delete()
        html = self.get(article)
        self.assertNotIn("product-dead", html)
        self.assertIn("product-ok", html)

    def test_an_article_without_cards_renders_no_product_markup(self):
        article = self.article({"type": "paragraph", "value": "<p>Just words.</p>"})
        html = self.get(article)
        self.assertNotIn("product-card", html)
        self.assertNotIn("Quick picks", html)
        self.assertNotIn("affiliate-disclosure", html)


class CtaRenderingTests(TestCase):
    """Module 04 rule 5: a CTA is a sponsored link for a renderable offer only."""

    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.product = make_product()
        self.merchant = make_merchant(name="Shopmart")
        self.offer = make_offer(self.product, self.merchant)
        self.article = make_article(
            self.hub, self.author, body=[card_block(self.product)]
        )

    def html(self):
        return self.client.get(self.article.url).content.decode()

    def test_the_cta_is_a_sponsored_same_tab_link_with_the_merchant_label(self):
        html = self.html()
        self.assertIn(
            f'<a class="btn btn-primary" href="{GOOD_LINK}" '
            'rel="sponsored nofollow noopener">View at Shopmart</a>',
            html,
        )
        self.assertNotIn("target=", html[html.index("product-card") :])

    def test_a_custom_button_text_is_used(self):
        self.merchant.cta_text = "Check price at Shopmart"
        self.merchant.save()
        self.assertIn("Check price at Shopmart", self.html())

    def test_no_price_appears_anywhere_in_the_card(self):
        html = self.html()
        card = html[html.index("product-card") :]
        for symbol in ("₹", "Rs.", "INR", "MRP", "price:"):
            self.assertNotIn(symbol, card)

    def test_several_offers_each_get_a_button_in_editor_order(self):
        other = make_merchant(
            name="Gadgetworld",
            destination_domain="gadgetworld.test",
            allowed="track.example.test",
        )
        make_offer(self.product, other, url=GOOD_LINK + "&n=2")
        html = self.html()
        self.assertLess(
            html.index("View at Shopmart"), html.index("View at Gadgetworld")
        )

    def test_non_renderable_offers_produce_no_button(self):
        for change in (
            lambda: type(self.offer).objects.update(active=False),
            lambda: type(self.merchant).objects.update(enabled=False),
            lambda: Product.objects.update(status=ProductStatus.DISCONTINUED),
        ):
            with self.subTest(change=change):
                change()
                self.assertNotIn("sponsored", self.html())
                type(self.offer).objects.update(active=True)
                type(self.merchant).objects.update(enabled=True)
                Product.objects.update(status=ProductStatus.ACTIVE)


class QuickPicksTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        brand = make_brand()
        self.a = make_product("A1", brand=brand)
        self.b = make_product("B2", brand=brand)

    def test_quick_picks_list_only_labelled_cards_and_link_to_them(self):
        article = make_article(
            self.hub,
            self.author,
            body=[
                card_block(
                    self.a,
                    block_id="one",
                    recommendation_label="Best overall",
                    best_for="Most people",
                ),
                card_block(self.b, block_id="two"),
            ],
        )
        html = self.client.get(article.url).content.decode()
        picks = html[html.index("Quick picks") : html.index("article-body")]
        self.assertIn("Best overall", picks)
        self.assertIn('href="#product-one"', picks)
        self.assertIn("Most people", picks)
        self.assertNotIn("B2", picks)

    def test_no_quick_picks_section_when_no_card_has_a_label(self):
        article = make_article(self.hub, self.author, body=[card_block(self.a)])
        self.assertNotContains(self.client.get(article.url), "Quick picks")


class ProductChooserBlockTests(SimpleTestCase):
    def test_it_deconstructs_without_arguments(self):
        # So a migration never embeds the model reference twice.
        from editorial.blocks import ProductChooserBlock

        _, args, kwargs = ProductChooserBlock().deconstruct()
        self.assertEqual((args, kwargs), ((), {}))
