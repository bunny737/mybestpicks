from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

from catalog.models import (
    Brand,
    Merchant,
    MerchantOffer,
    Product,
    ProductStatus,
)
from catalog.provenance import ImageProvenance

from .helpers import (
    GOOD_LINK,
    KEYBOARD_SPECS,
    make_brand,
    make_merchant,
    make_offer,
    make_product,
)


class BrandTests(TestCase):
    def test_slug_is_generated_and_unique(self):
        first = Brand.objects.create(name="Acme Co")
        second = Brand.objects.create(name="acme-co")
        self.assertEqual(first.slug, "acme-co")
        self.assertEqual(second.slug, "acme-co-2")

    def test_an_explicit_slug_is_kept(self):
        self.assertEqual(Brand.objects.create(name="Zed", slug="custom").slug, "custom")

    def test_website_must_be_https(self):
        brand = Brand(name="Acme", website="http://acme.test/")
        with self.assertRaises(ValidationError) as ctx:
            brand.full_clean()
        self.assertIn("website", ctx.exception.message_dict)
        Brand(name="Acme", website="https://acme.test/").full_clean(exclude=["slug"])

    def test_names_are_unique(self):
        make_brand("Acme")
        with self.assertRaises(ValidationError):
            Brand(name="Acme").full_clean()


class ProductTests(TestCase):
    def test_str_combines_brand_and_name(self):
        self.assertEqual(str(make_product("K1")), "Acme K1")

    def test_clean_rejects_bad_specs_and_keeps_good_ones(self):
        brand = make_brand()
        bad = Product(
            brand=brand,
            name="K2",
            product_type="keyboard",
            key_specs={"layout": "tkl"},
        )
        with self.assertRaises(ValidationError) as ctx:
            bad.full_clean()
        self.assertIn("key_specs", ctx.exception.message_dict)

        good = make_product("K3", brand=brand)
        self.assertEqual(good.key_specs, KEYBOARD_SPECS)

    def test_specs_are_validated_against_the_chosen_product_type(self):
        keyboard_specs_on_a_hub = Product(
            brand=make_brand(),
            name="Hub",
            product_type="usb_c_hub",
            key_specs=dict(KEYBOARD_SPECS),
        )
        with self.assertRaises(ValidationError) as ctx:
            keyboard_specs_on_a_hub.full_clean()
        self.assertIn("key_specs", ctx.exception.message_dict)

    def test_unknown_product_type_is_rejected(self):
        product = Product(
            brand=make_brand(), name="X", product_type="toaster", key_specs={}
        )
        with self.assertRaises(ValidationError) as ctx:
            product.full_clean()
        self.assertIn("product_type", ctx.exception.message_dict)

    def test_clean_normalises_the_specs_it_stores(self):
        product = make_product(
            "K4",
            product_type="laptop_stand",
            key_specs={
                "material": "  Steel ",
                "adjustable_height": True,
                "weight_g": None,
            },
        )
        self.assertEqual(
            product.key_specs, {"material": "Steel", "adjustable_height": True}
        )

    def test_the_same_product_cannot_be_added_twice(self):
        brand = make_brand()
        make_product("K1", brand=brand, model_number="M-1")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.create(
                brand=brand,
                name="K1",
                model_number="M-1",
                product_type="keyboard",
                key_specs=dict(KEYBOARD_SPECS),
            )

    def test_a_brand_with_products_cannot_be_deleted(self):
        product = make_product()
        with self.assertRaises(ProtectedError):
            product.brand.delete()

    def test_status_defaults_to_active(self):
        self.assertEqual(make_product().status, ProductStatus.ACTIVE)

    def test_spec_rows_property_uses_the_schema(self):
        rows = make_product().spec_rows
        self.assertEqual(rows[0].key, "layout")
        self.assertEqual(rows[0].display_value, "Tenkeyless (TKL)")

    def test_last_verified_at_is_a_date(self):
        product = make_product(last_verified_at=date(2026, 11, 1))
        product.refresh_from_db()
        self.assertEqual(product.last_verified_at, date(2026, 11, 1))


class ProductImageProvenanceTests(TestCase):
    def setUp(self):
        self.image = Image.objects.create(title="K", file=get_test_image_file())

    def test_an_image_needs_provenance(self):
        product = Product(
            brand=make_brand(),
            name="K9",
            product_type="keyboard",
            key_specs=dict(KEYBOARD_SPECS),
            image=self.image,
        )
        with self.assertRaises(ValidationError) as ctx:
            product.full_clean()
        self.assertIn("image_provenance", ctx.exception.message_dict)

    def test_a_licensed_image_needs_a_credit(self):
        product = Product(
            brand=make_brand(),
            name="K9",
            product_type="keyboard",
            key_specs=dict(KEYBOARD_SPECS),
            image=self.image,
            image_provenance=ImageProvenance.MANUFACTURER_LICENSED,
        )
        with self.assertRaises(ValidationError) as ctx:
            product.full_clean()
        self.assertIn("image_credit", ctx.exception.message_dict)
        product.image_credit = "Press kit, permission email 2026-10-30"
        product.full_clean()

    def test_an_owned_original_needs_no_credit(self):
        make_product(
            "K10", image=self.image, image_provenance=ImageProvenance.OWNED_ORIGINAL
        )


class NoPriceFieldsTests(TestCase):
    def test_no_catalog_model_has_a_price_field(self):
        # CLAUDE.md invariant 2.
        for model in (Brand, Product, Merchant, MerchantOffer):
            names = [f.name.lower() for f in model._meta.get_fields()]
            for name in names:
                with self.subTest(model=model.__name__, field=name):
                    self.assertFalse(
                        any(w in name for w in ("price", "mrp", "cost", "amount")),
                    )

    def test_there_is_no_click_tracking_or_article_product_model(self):
        # CLAUDE.md invariants 3 and 9.
        from django.apps import apps

        model_names = {m.__name__.lower() for m in apps.get_models()}
        self.assertNotIn("affiliateclickevent", model_names)
        self.assertNotIn("articleproduct", model_names)


class MerchantTests(TestCase):
    def test_allowed_domains_are_normalised_on_clean(self):
        merchant = make_merchant(allowed=" Track.Example.Test \n\nOther.Example.Test\n")
        self.assertEqual(
            merchant.allowed_link_domains, "track.example.test\nother.example.test"
        )
        self.assertEqual(
            merchant.allowed_hosts, {"track.example.test", "other.example.test"}
        )

    def test_bad_allowlist_entries_are_rejected(self):
        for bad in (
            "https://track.example.test",
            "*.example.test",
            "track.example.test/x",
        ):
            with self.subTest(bad=bad):
                merchant = Merchant(
                    name="M",
                    destination_domain="shopmart.test",
                    allowed_link_domains=bad,
                )
                with self.assertRaises(ValidationError) as ctx:
                    merchant.full_clean()
                self.assertIn("allowed_link_domains", ctx.exception.message_dict)

    def test_destination_domain_must_be_a_bare_hostname(self):
        merchant = Merchant(name="M", destination_domain="https://shopmart.test")
        with self.assertRaises(ValidationError) as ctx:
            merchant.full_clean()
        self.assertIn("destination_domain", ctx.exception.message_dict)

    def test_network_and_destination_are_stored_separately(self):
        # A Cuelinks-tracked Flipkart link: tracker host in the allowlist,
        # retailer in destination_domain, display label "View at Flipkart".
        merchant = make_merchant(
            name="Flipkart", destination_domain="flipkart.com", network="cuelinks"
        )
        self.assertEqual(merchant.network, "cuelinks")
        self.assertEqual(merchant.destination_domain, "flipkart.com")
        self.assertNotIn("flipkart.com", merchant.allowed_hosts)
        self.assertEqual(merchant.cta_label, "View at Flipkart")

    def test_button_text_can_be_overridden(self):
        merchant = make_merchant(name="Amazon", cta_text="Check price at Amazon")
        self.assertEqual(merchant.cta_label, "Check price at Amazon")

    def test_a_merchant_with_offers_cannot_be_deleted(self):
        merchant = make_merchant()
        make_offer(make_product(), merchant)
        with self.assertRaises(ProtectedError):
            merchant.delete()


class MerchantOfferTests(TestCase):
    def setUp(self):
        self.product = make_product()
        self.merchant = make_merchant()

    def build(self, **fields):
        data = {
            "product": self.product,
            "merchant": self.merchant,
            "affiliate_url": GOOD_LINK,
            "last_checked_at": date(2026, 11, 1),
        }
        data.update(fields)
        return MerchantOffer(**data)

    def test_a_valid_offer_is_saved_inactive_by_default(self):
        offer = self.build()
        offer.full_clean()
        offer.save()
        self.assertFalse(offer.active)

    def test_offer_url_rules_are_enforced_through_clean(self):
        for url in (
            "http://track.example.test/x",
            "https://shopmart.test/p/1",  # retailer host, not the tracker
            "https://user:pw@track.example.test/x",
            "https://track.example.test/x?token=abc",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValidationError) as ctx:
                    self.build(affiliate_url=url).full_clean()
                self.assertIn("affiliate_url", ctx.exception.message_dict)

    def test_destination_url_must_be_on_the_merchant_domain(self):
        self.build(destination_product_url="https://www.shopmart.test/p/9").full_clean()
        with self.assertRaises(ValidationError) as ctx:
            self.build(destination_product_url="https://other.test/p/9").full_clean()
        self.assertIn("destination_product_url", ctx.exception.message_dict)

    def test_destination_url_is_optional(self):
        self.build(destination_product_url="").full_clean()

    def test_an_offer_cannot_be_activated_without_a_manual_check_date(self):
        offer = self.build(active=True, last_checked_at=None)
        with self.assertRaises(ValidationError) as ctx:
            offer.full_clean()
        self.assertIn("last_checked_at", ctx.exception.message_dict)
        self.build(active=False, last_checked_at=None).full_clean()

    def test_offers_belong_to_the_product_and_delete_with_it(self):
        make_offer(self.product, self.merchant)
        self.assertEqual(self.product.offers.count(), 1)
        self.product.delete()
        self.assertEqual(MerchantOffer.objects.count(), 0)

    def test_offers_stay_in_editor_order(self):
        a = make_offer(self.product, self.merchant, url=GOOD_LINK + "&n=1")
        b = make_offer(self.product, self.merchant, url=GOOD_LINK + "&n=2")
        a.sort_order, b.sort_order = 2, 1
        a.save()
        b.save()
        self.assertEqual(list(self.product.offers.all()), [b, a])


class RenderableOfferTests(TestCase):
    """Module 05 rule 5: when an offer may be shown to readers."""

    def setUp(self):
        self.product = make_product()
        self.merchant = make_merchant()
        self.offer = make_offer(self.product, self.merchant)

    def renderable(self):
        qs = MerchantOffer.objects.renderable()
        return [o for o in qs.select_related("merchant", "product") if o.is_renderable]

    def test_an_active_offer_on_an_enabled_merchant_is_renderable(self):
        self.assertEqual(self.renderable(), [self.offer])

    def test_inactive_offers_are_not_renderable(self):
        MerchantOffer.objects.update(active=False)
        self.assertEqual(self.renderable(), [])

    def test_a_disabled_merchant_hides_its_offers(self):
        Merchant.objects.update(enabled=False)
        self.assertEqual(self.renderable(), [])

    def test_a_discontinued_product_hides_its_offers(self):
        Product.objects.update(status=ProductStatus.DISCONTINUED)
        self.assertEqual(self.renderable(), [])

    def test_a_temporarily_unavailable_product_still_shows_its_offer(self):
        Product.objects.update(status=ProductStatus.UNAVAILABLE)
        self.assertEqual(self.renderable(), [self.offer])

    def test_removing_the_host_from_the_allowlist_stops_rendering(self):
        # The queryset cannot see this; is_renderable re-checks the link host.
        Merchant.objects.update(allowed_link_domains="other.example.test")
        self.assertEqual(len(MerchantOffer.objects.renderable()), 1)
        self.assertEqual(self.renderable(), [])

    def test_offers_rendered_for_an_article_use_a_bounded_number_of_queries(self):
        for i in range(5):
            make_offer(make_product(f"P{i}"), self.merchant, url=GOOD_LINK + f"&n={i}")
        with self.assertNumQueries(1):
            offers = list(
                MerchantOffer.objects.renderable().select_related("merchant", "product")
            )
        self.assertEqual(len(offers), 6)
        with self.assertNumQueries(0):
            self.assertTrue(all(o.is_renderable for o in offers))
