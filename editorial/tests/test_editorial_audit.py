"""
Module 10 (MBP-010): the ``editorial_audit`` checks. The audit only reports; it
never edits content (business rule 1), and legacy data that bypassed block/model
validation is exactly what these checks exist to catch.
"""

from datetime import date, timedelta

from django.test import TestCase, override_settings
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

from catalog.models import ProductStatus
from catalog.tests.helpers import make_brand, make_merchant, make_offer, make_product

from .helpers import (
    TempMediaMixin,
    card_block,
    make_article,
    make_author,
    make_category,
)


def categories(findings):
    return {f.category for f in findings}


class StalePricedArticleTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category()
        self.brand = make_brand()

    def article_with_product(self, title, excerpt, last_verified_at):
        product = make_product(
            "K1", brand=self.brand, last_verified_at=last_verified_at
        )
        make_article(
            self.hub,
            self.author,
            title=title,
            excerpt=excerpt,
            body=[card_block(product, block_id="k1")],
        )
        return product

    def run_audit(self):
        from editorial.audits import run_editorial_audit

        return run_editorial_audit()

    def test_price_claim_with_stale_product_is_flagged(self):
        self.article_with_product(
            "Best Keyboards Under ₹2000", "A budget pick.", date(2020, 1, 1)
        )
        findings = self.run_audit()
        self.assertIn("stale-priced-article", categories(findings))

    def test_price_claim_with_never_verified_product_is_flagged(self):
        self.article_with_product("Keyboards Under ₹2000", "Cheap picks.", None)
        findings = self.run_audit()
        self.assertIn("stale-priced-article", categories(findings))

    def test_price_claim_with_recently_verified_product_is_not_flagged(self):
        self.article_with_product(
            "Keyboards Under ₹2000",
            "Cheap picks.",
            date.today() - timedelta(days=1),
        )
        findings = self.run_audit()
        self.assertNotIn("stale-priced-article", categories(findings))

    def test_non_price_article_with_stale_product_is_not_flagged(self):
        self.article_with_product(
            "Best Keyboards", "A short summary.", date(2020, 1, 1)
        )
        findings = self.run_audit()
        self.assertNotIn("stale-priced-article", categories(findings))

    @override_settings(EDITORIAL_AUDIT_STALE_DAYS=3650)
    def test_threshold_comes_from_settings(self):
        self.article_with_product(
            "Keyboards Under ₹2000", "Cheap picks.", date(2020, 1, 1)
        )
        findings = self.run_audit()
        self.assertNotIn("stale-priced-article", categories(findings))


class UnavailableProductReferenceTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category()
        self.brand = make_brand()

    def run_audit(self):
        from editorial.audits import run_editorial_audit

        return run_editorial_audit()

    def test_live_article_referencing_discontinued_product_is_flagged(self):
        product = make_product(
            "K1", brand=self.brand, status=ProductStatus.DISCONTINUED
        )
        make_article(self.hub, self.author, body=[card_block(product, block_id="k1")])
        findings = self.run_audit()
        self.assertIn("unavailable-product-reference", categories(findings))

    def test_live_article_referencing_active_product_is_not_flagged(self):
        product = make_product("K1", brand=self.brand)
        make_article(self.hub, self.author, body=[card_block(product, block_id="k1")])
        findings = self.run_audit()
        self.assertNotIn("unavailable-product-reference", categories(findings))

    def test_draft_article_referencing_discontinued_product_is_not_flagged(self):
        product = make_product(
            "K1", brand=self.brand, status=ProductStatus.DISCONTINUED
        )
        make_article(
            self.hub,
            self.author,
            body=[card_block(product, block_id="k1")],
            live=False,
        )
        findings = self.run_audit()
        self.assertNotIn("unavailable-product-reference", categories(findings))


class UntestedEvidenceClaimTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category()
        self.brand = make_brand()

    def run_audit(self):
        from editorial.audits import run_editorial_audit

        return run_editorial_audit()

    def test_tested_by_editor_without_evidence_is_flagged(self):
        # Bypasses ProductCardBlock.clean() on purpose: this is legacy-style data
        # the live validation would now reject, which is exactly what the audit
        # exists to catch.
        product = make_product("K1", brand=self.brand)
        make_article(
            self.hub,
            self.author,
            body=[
                card_block(
                    product,
                    block_id="k1",
                    tested_by_editor=True,
                    editorial_evidence="",
                    evidence_media=None,
                )
            ],
        )
        findings = self.run_audit()
        self.assertIn("untested-evidence-claim", categories(findings))

    def test_tested_by_editor_with_notes_is_not_flagged(self):
        product = make_product("K1", brand=self.brand)
        make_article(
            self.hub,
            self.author,
            body=[
                card_block(
                    product,
                    block_id="k1",
                    tested_by_editor=True,
                    editorial_evidence="Used it daily for two weeks.",
                )
            ],
        )
        findings = self.run_audit()
        self.assertNotIn("untested-evidence-claim", categories(findings))

    def test_not_tested_by_editor_is_never_flagged(self):
        product = make_product("K1", brand=self.brand)
        make_article(self.hub, self.author, body=[card_block(product, block_id="k1")])
        findings = self.run_audit()
        self.assertNotIn("untested-evidence-claim", categories(findings))


class MissingImageEvidenceTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.brand = make_brand()

    def run_audit(self):
        from editorial.audits import run_editorial_audit

        return run_editorial_audit()

    def test_product_image_without_provenance_is_flagged(self):
        image = Image.objects.create(title="K1", file=get_test_image_file())
        product = make_product("K1", brand=self.brand)
        # Bypass full_clean(): simulates a row saved before this check existed.
        product.image = image
        product.image_provenance = ""
        product.save()

        findings = self.run_audit()
        self.assertIn("missing-image-evidence", categories(findings))

    def test_product_image_with_provenance_and_credit_is_not_flagged(self):
        image = Image.objects.create(title="K1", file=get_test_image_file())
        product = make_product("K1", brand=self.brand)
        product.image = image
        product.image_provenance = "other_licensed"
        product.image_credit = "Licensed from Acme press kit."
        product.save()

        findings = self.run_audit()
        self.assertNotIn("missing-image-evidence", categories(findings))

    def test_product_without_an_image_is_not_flagged(self):
        make_product("K1", brand=self.brand)
        findings = self.run_audit()
        self.assertNotIn("missing-image-evidence", categories(findings))


class StaleOfferTests(TestCase):
    def setUp(self):
        self.brand = make_brand()
        self.merchant = make_merchant()

    def run_audit(self):
        from editorial.audits import run_editorial_audit

        return run_editorial_audit()

    def test_stale_active_offer_is_flagged(self):
        product = make_product("K1", brand=self.brand)
        make_offer(product, self.merchant, last_checked_at=date(2020, 1, 1))
        findings = self.run_audit()
        self.assertIn("stale-offer", categories(findings))

    def test_recently_checked_offer_is_not_flagged(self):
        product = make_product("K1", brand=self.brand)
        make_offer(
            product, self.merchant, last_checked_at=date.today() - timedelta(days=1)
        )
        findings = self.run_audit()
        self.assertNotIn("stale-offer", categories(findings))

    def test_stale_inactive_offer_is_not_flagged(self):
        product = make_product("K1", brand=self.brand)
        make_offer(
            product,
            self.merchant,
            active=False,
            last_checked_at=date(2020, 1, 1),
        )
        findings = self.run_audit()
        self.assertNotIn("stale-offer", categories(findings))


class AuditIsReadOnlyTests(TestCase):
    def test_audit_does_not_change_product_or_offer_rows(self):
        from editorial.audits import run_editorial_audit

        brand = make_brand()
        merchant = make_merchant()
        product = make_product(
            "K1",
            brand=brand,
            status=ProductStatus.DISCONTINUED,
            last_verified_at=date(2020, 1, 1),
        )
        make_offer(product, merchant, last_checked_at=date(2020, 1, 1))
        before = (product.name, product.status, product.last_verified_at)

        run_editorial_audit()

        product.refresh_from_db()
        after = (product.name, product.status, product.last_verified_at)
        self.assertEqual(before, after)
