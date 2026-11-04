"""The other body blocks, and the Wagtail reference index (module 04 rule 8)."""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import ReferenceIndex

from catalog.provenance import ImageProvenance
from catalog.tests.helpers import make_brand, make_product
from editorial.blocks import ImageBlock, SourceNoteBlock
from editorial.models import ArticlePage, DiscoveryMode

from .helpers import (
    TempMediaMixin,
    card_block,
    make_article,
    make_author,
    make_category,
    plain_table_block,
)


class BodyBlockRenderingTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.image = Image.objects.create(title="Desk", file=get_test_image_file())

    def render(self, *blocks):
        article = make_article(self.hub, self.author, body=list(blocks))
        response = self.client.get(article.url)
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_image_block_has_alt_dimensions_lazy_caption_and_credit(self):
        html = self.render(
            {
                "type": "image",
                "value": {
                    "image": self.image.pk,
                    "alt_text": "A tidy desk",
                    "caption": "My desk",
                    "provenance": ImageProvenance.OTHER_LICENSED,
                    "credit": "CC BY 4.0, A. Person",
                },
            }
        )
        figure = html[html.index("<figure") : html.index("</figure>")]
        self.assertIn('alt="A tidy desk"', figure)
        self.assertIn('loading="lazy"', figure)
        self.assertRegex(figure, r'width="\d+"')
        self.assertRegex(figure, r'height="\d+"')
        self.assertIn("My desk", figure)
        self.assertIn("Image: CC BY 4.0, A. Person", figure)

    def test_image_caption_is_escaped(self):
        html = self.render(
            {
                "type": "image",
                "value": {
                    "image": self.image.pk,
                    "alt_text": "x",
                    "caption": "<script>alert(1)</script>",
                    "provenance": ImageProvenance.OWNED_ORIGINAL,
                    "credit": "",
                },
            }
        )
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_plain_table_with_header_row(self):
        html = self.render(
            plain_table_block([["Type", "Best for"], ["Oil", "Bedrooms"]])
        )
        table = html[html.index('<table class="table table-bordered') :]
        table = table[: table.index("</table>")]
        self.assertIn("<thead", table)
        self.assertIn('<th scope="col"', table)
        self.assertIn("<td", table)
        self.assertIn("Bedrooms", table)

    def test_plain_table_without_header_has_no_thead(self):
        html = self.render(plain_table_block([["Oil", "Bedrooms"]], header="neither"))
        self.assertIn('<table class="table table-bordered', html)
        self.assertNotIn("<thead", html)
        self.assertNotIn('<th scope="col"', html)
        self.assertIn("Bedrooms", html)

    def test_plain_table_caption_and_cells_are_escaped(self):
        html = self.render(
            plain_table_block(
                [["H1", "H2"], ["<script>cell()</script>", "x"]],
                caption="<script>caption()</script>",
            )
        )
        self.assertNotIn("<script>caption()</script>", html)
        self.assertNotIn("<script>cell()</script>", html)
        self.assertIn("&lt;script&gt;caption()", html)

    def test_empty_plain_table_renders_nothing(self):
        html = self.render(plain_table_block([], header="neither"))
        self.assertNotIn('<table class="table table-bordered', html)

    def test_key_takeaways(self):
        html = self.render(
            {
                "type": "key_takeaways",
                "value": {"heading": "Short version", "points": ["Buy A", "Skip B"]},
            }
        )
        self.assertIn("Short version", html)
        self.assertIn("<li>Buy A</li>", html)

    def test_buying_criteria(self):
        html = self.render(
            {
                "type": "buying_criteria",
                "value": {
                    "heading": "What matters",
                    "criteria": [{"name": "Layout", "why": "Desk space."}],
                },
            }
        )
        self.assertIn("<dt>Layout</dt>", html)
        self.assertIn("<dd>Desk space.</dd>", html)

    def test_faq_text_is_in_the_server_html(self):
        html = self.render(
            {
                "type": "faq",
                "value": {
                    "heading": "FAQ",
                    "questions": [
                        {"question": "Is it loud?", "answer": "<p>A little.</p>"}
                    ],
                },
            }
        )
        self.assertIn("Is it loud?", html)
        self.assertIn("A little.", html)

    def test_source_note_links_are_nofollow_and_noopener(self):
        html = self.render(
            {
                "type": "source_note",
                "value": {
                    "text": "Weight from the spec sheet.",
                    "source_name": "Maker spec",
                    "url": "https://maker.test/spec",
                },
            }
        )
        self.assertIn('href="https://maker.test/spec" rel="noopener nofollow"', html)

    def test_related_articles_show_only_live_chosen_pages(self):
        live = make_article(self.hub, self.author, slug="live", title="Live One")
        draft = make_article(
            self.hub, self.author, slug="draft", title="Draft One", live=False
        )
        html = self.render(
            {
                "type": "related_articles",
                "value": {"heading": "More reading", "articles": [live.pk, draft.pk]},
            }
        )
        self.assertIn("More reading", html)
        self.assertIn("Live One", html)
        self.assertNotIn("Draft One", html)

    def test_related_articles_with_nothing_live_render_nothing(self):
        draft = make_article(self.hub, self.author, slug="d2", live=False)
        html = self.render(
            {
                "type": "related_articles",
                "value": {"heading": "More reading", "articles": [draft.pk]},
            }
        )
        self.assertNotIn("More reading", html)


class BodyBlockValidationTests(TestCase):
    def setUp(self):
        self.image = Image.objects.create(title="Desk", file=get_test_image_file())
        self.block = ImageBlock()

    def clean(self, **fields):
        value = {
            "image": self.image.pk,
            "alt_text": "A desk",
            "caption": "",
            "provenance": ImageProvenance.OWNED_ORIGINAL,
            "credit": "",
        }
        value.update(fields)
        return self.block.clean(self.block.to_python(value))

    def test_an_owned_image_needs_no_credit(self):
        self.clean()

    def test_a_licensed_image_needs_a_credit(self):
        with self.assertRaises(ValidationError) as ctx:
            self.clean(provenance=ImageProvenance.MANUFACTURER_LICENSED)
        self.assertIn("credit", ctx.exception.block_errors)
        self.clean(provenance=ImageProvenance.MANUFACTURER_LICENSED, credit="Press kit")

    def test_alt_text_is_required(self):
        with self.assertRaises(ValidationError):
            self.clean(alt_text="")

    def test_source_note_urls_must_be_http_or_https(self):
        block = SourceNoteBlock()
        ok = {"text": "x", "source_name": "", "url": "https://maker.test/a"}
        block.clean(block.to_python(ok))
        for bad in ("javascript:alert(1)", "ftp://maker.test/a"):
            with self.subTest(url=bad), self.assertRaises(ValidationError):
                block.clean(block.to_python({**ok, "url": bad}))


class ReferenceIndexTests(TestCase):
    """Module 04 rule 8: Wagtail can tell which articles use a product."""

    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        brand = make_brand()
        self.a = make_product("A", brand=brand)
        self.b = make_product("B", brand=brand)
        self.page_type = ContentType.objects.get_for_model(ArticlePage)

    def pages_using(self, product):
        """Primary keys of the articles Wagtail says reference ``product``."""
        return {
            int(ref.object_id)
            for ref in ReferenceIndex.get_references_to(product)
            if ref.content_type_id == self.page_type.pk
        }

    def test_an_article_using_a_product_is_found_through_the_reference_index(self):
        article = make_article(self.hub, self.author, body=[card_block(self.a)])
        article.save_revision().publish()
        self.assertIn(article.pk, self.pages_using(self.a))
        self.assertNotIn(article.pk, self.pages_using(self.b))

    def test_swapping_the_product_moves_the_reference(self):
        article = make_article(self.hub, self.author, body=[card_block(self.a)])
        article.save_revision().publish()
        article = ArticlePage.objects.get(pk=article.pk)
        article.body = [card_block(self.b)]
        article.save_revision().publish()

        self.assertIn(article.pk, self.pages_using(self.b))
        self.assertNotIn(article.pk, self.pages_using(self.a))

    def test_the_same_product_in_two_cards_is_one_article(self):
        article = make_article(
            self.hub, self.author, body=[card_block(self.a), card_block(self.a)]
        )
        article.save_revision().publish()
        self.assertEqual(sorted(self.pages_using(self.a)), [article.pk])
