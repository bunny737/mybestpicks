"""The Wagtail admin for the catalog: screens render and the inline offers validate."""

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Product

from .helpers import GOOD_LINK, make_brand, make_merchant, make_offer, make_product


class CatalogAdminTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_superuser("ed", "ed@example.com", "pw")
        self.client.force_login(user)
        self.brand = make_brand()
        self.merchant = make_merchant()
        self.product = make_product()
        make_offer(self.product, self.merchant)

    def url(self, model, action, *args):
        return reverse(f"wagtailsnippets_catalog_{model}:{action}", args=args)

    def test_list_add_and_edit_screens_render_for_every_snippet(self):
        pages = [
            self.url("product", "list"),
            self.url("product", "add"),
            self.url("product", "edit", self.product.pk),
            self.url("brand", "list"),
            self.url("brand", "add"),
            self.url("brand", "edit", self.brand.pk),
            self.url("merchant", "list"),
            self.url("merchant", "add"),
            self.url("merchant", "edit", self.merchant.pk),
        ]
        for url in pages:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_the_product_form_lists_the_spec_keys_for_editors(self):
        response = self.client.get(self.url("product", "add"))
        self.assertContains(response, "switch_type")
        self.assertContains(response, "usb_c_hub".replace("_", "_"))

    def post_data(self, **offer):
        data = {
            "brand": self.brand.pk,
            "name": "K77",
            "model_number": "",
            "product_type": "keyboard",
            "key_specs": json.dumps(
                {"layout": "tkl", "switch_type": "mechanical", "connectivity": "wired"}
            ),
            "image_provenance": "",
            "image_credit": "",
            "status": "active",
            "last_verified_at": "",
            "offers-TOTAL_FORMS": "1",
            "offers-INITIAL_FORMS": "0",
            "offers-MIN_NUM_FORMS": "0",
            "offers-MAX_NUM_FORMS": "1000",
            "offers-0-merchant": self.merchant.pk,
            "offers-0-affiliate_url": GOOD_LINK,
            "offers-0-destination_product_url": "",
            "offers-0-last_checked_at": "2026-11-01",
            "offers-0-campaign_notes": "",
            "offers-0-ORDER": "1",
            "offers-0-DELETE": "",
            "offers-0-id": "",
        }
        for key, value in offer.items():
            data[f"offers-0-{key}"] = value
        return data

    def test_creating_a_product_with_a_valid_offer_works(self):
        response = self.client.post(self.url("product", "add"), self.post_data())
        self.assertEqual(response.status_code, 302, getattr(response, "context", None))
        product = Product.objects.get(name="K77")
        self.assertEqual(product.offers.count(), 1)
        self.assertFalse(product.offers.get().active)

    def test_an_offer_on_a_disallowed_host_is_rejected_by_the_form(self):
        data = self.post_data(affiliate_url="https://evil.example.test/x")
        response = self.client.post(self.url("product", "add"), data)
        self.assertEqual(response.status_code, 200)  # form redisplayed with errors
        self.assertFalse(Product.objects.filter(name="K77").exists())
        self.assertContains(response, "not an allowed tracking host")

    def test_a_product_with_bad_specs_is_rejected_by_the_form(self):
        data = self.post_data()
        data["key_specs"] = json.dumps({"layout": "tkl"})
        data["offers-TOTAL_FORMS"] = "0"
        response = self.client.post(self.url("product", "add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(name="K77").exists())
        self.assertContains(response, "is required")
