"""Invariant 8: every published image records provenance."""

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

from catalog.provenance import ImageProvenance, validate_image_provenance
from editorial.models import ArticlePage, CategoryPage

from .helpers import make_author


def check(image, provenance="", credit=""):
    validate_image_provenance(
        image=image,
        provenance=provenance,
        credit=credit,
        image_field="image",
        provenance_field="image_provenance",
        credit_field="image_credit",
    )


class ValidateImageProvenanceTests(SimpleTestCase):
    def test_no_image_needs_nothing(self):
        check(image=None)

    def test_image_without_provenance_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            check(image=object())
        self.assertIn("image_provenance", ctx.exception.message_dict)

    def test_owned_original_needs_no_credit(self):
        check(image=object(), provenance=ImageProvenance.OWNED_ORIGINAL)

    def test_licensed_image_without_credit_is_rejected(self):
        for provenance in (
            ImageProvenance.MANUFACTURER_LICENSED,
            ImageProvenance.OTHER_LICENSED,
            ImageProvenance.PERMITTED_PROGRAM_CONTENT,
        ):
            with self.subTest(provenance=provenance):
                with self.assertRaises(ValidationError) as ctx:
                    check(image=object(), provenance=provenance, credit="  ")
                self.assertIn("image_credit", ctx.exception.message_dict)

    def test_licensed_image_with_credit_is_accepted(self):
        check(
            image=object(),
            provenance=ImageProvenance.MANUFACTURER_LICENSED,
            credit="Press kit, permission email 2026-10-30",
        )


class PageImageProvenanceTests(TestCase):
    def setUp(self):
        self.image = Image.objects.create(title="Desk", file=get_test_image_file())
        self.author = make_author()

    def test_article_with_image_but_no_provenance_fails_clean(self):
        article = ArticlePage(
            title="A",
            slug="a",
            excerpt="x",
            author=self.author,
            featured_image=self.image,
        )
        with self.assertRaises(ValidationError) as ctx:
            article.clean()
        self.assertIn("featured_image_provenance", ctx.exception.message_dict)

    def test_article_with_owned_image_passes_clean(self):
        article = ArticlePage(
            title="A",
            slug="a",
            excerpt="x",
            author=self.author,
            featured_image=self.image,
            featured_image_provenance=ImageProvenance.OWNED_ORIGINAL,
        )
        article.clean()

    def test_category_banner_requires_provenance_and_credit(self):
        hub = CategoryPage(title="Hub", slug="hub", banner=self.image)
        with self.assertRaises(ValidationError) as ctx:
            hub.clean()
        self.assertIn("banner_provenance", ctx.exception.message_dict)

        hub.banner_provenance = ImageProvenance.OTHER_LICENSED
        with self.assertRaises(ValidationError) as ctx:
            hub.clean()
        self.assertIn("banner_credit", ctx.exception.message_dict)

        hub.banner_credit = "CC BY 4.0, photo by A. Person"
        hub.clean()
