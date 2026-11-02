from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from wagtail.models import Site

from editorial.models import DiscoveryMode
from editorial.tests.helpers import (
    make_article,
    make_author,
    make_category,
    make_standard_page,
)
from home.models import SiteSettings, validate_ads_txt_lines


class AdSenseValidationAndConfigurationTests(TestCase):
    def setUp(self):
        self.site = Site.objects.get(is_default_site=True)
        self.settings = SiteSettings.for_site(self.site)
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.article = make_article(self.hub, self.author)
        self.policy = make_standard_page("Privacy Policy", "privacy-policy")

    def test_publisher_id_validation(self):
        valid_ids = ["pub-1234567890123456", "ca-pub-1234567890123456"]
        for valid in valid_ids:
            self.settings.adsense_publisher_id = valid
            self.settings.full_clean()  # should not raise

        invalid_ids = [
            "not-a-pub",
            "pub-12345",
            "1234567890123456",
            "pub-abcdefghijklmnop",
        ]
        for invalid in invalid_ids:
            self.settings.adsense_publisher_id = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                self.settings.full_clean()

    def test_slot_id_validation(self):
        self.settings.adsense_publisher_id = "pub-1234567890123456"
        self.settings.adsense_in_article_slot_id = "1234567890"
        self.settings.full_clean()

        for invalid in ["123", "abcdefghij", "123456789012"]:
            self.settings.adsense_in_article_slot_id = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                self.settings.full_clean()

    def test_ads_txt_line_validator(self):
        valid_block = (
            "# Comment line\n"
            "google.com, pub-1234567890123456, DIRECT, f08c47fec0942fa0\n"
            "example.com, pub-9999999999999999, RESELLER\n"
        )
        validate_ads_txt_lines(valid_block)  # Should not raise

        with self.assertRaises(ValidationError):
            validate_ads_txt_lines("malformed line without commas")

    def test_ads_txt_endpoint(self):
        self.settings.adsense_publisher_id = "pub-1234567890123456"
        self.settings.ads_txt_custom = "example.com, pub-9999999999999999, RESELLER"
        self.settings.save()

        response = self.client.get("/ads.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(
            response, "google.com, pub-1234567890123456, DIRECT, f08c47fec0942fa0"
        )
        self.assertContains(response, "example.com, pub-9999999999999999, RESELLER")

    def test_adsense_head_script_requires_consent_and_enabled_state(self):
        self.settings.adsense_publisher_id = "pub-1234567890123456"
        self.settings.adsense_enabled = True
        self.settings.save()

        # Without consent cookie: script must NOT be loaded (Invariant 9)
        response = self.client.get(self.article.url)
        self.assertNotContains(response, "pagead2.googlesyndication.com")

        # With explicit consent cookie: script loads on eligible article page
        self.client.cookies["ads_consent"] = "granted"
        response = self.client.get(self.article.url)
        self.assertContains(response, "pagead2.googlesyndication.com")
        self.assertContains(response, "ca-pub-1234567890123456")

    def test_adsense_head_script_never_loads_on_non_content_pages(self):
        self.settings.adsense_publisher_id = "pub-1234567890123456"
        self.settings.adsense_enabled = True
        self.settings.save()
        self.client.cookies["ads_consent"] = "granted"

        # Search is a non-content page: excluded from AdSense scripts
        search_res = self.client.get("/search/?query=guide")
        self.assertNotContains(search_res, "pagead2.googlesyndication.com")

        # StandardPage policy pages (Privacy, Terms, About) are excluded
        policy_res = self.client.get(self.policy.url)
        self.assertNotContains(policy_res, "pagead2.googlesyndication.com")

    def test_auto_ads_flag_controls_enable_page_level_ads(self):
        self.settings.adsense_publisher_id = "pub-1234567890123456"
        self.settings.adsense_enabled = True
        self.client.cookies["ads_consent"] = "granted"

        # When auto ads is False
        self.settings.adsense_auto_ads = False
        self.settings.save()
        response = self.client.get(self.article.url)
        self.assertContains(response, "enable_page_level_ads: false")

        # When auto ads is True
        self.settings.adsense_auto_ads = True
        self.settings.save()
        response = self.client.get(self.article.url)
        self.assertContains(response, "enable_page_level_ads: true")

    def test_manual_ad_unit_requires_slot_id(self):
        self.settings.adsense_publisher_id = "pub-1234567890123456"
        self.settings.adsense_enabled = True
        self.client.cookies["ads_consent"] = "granted"

        # Without slot ID configured: manual ad unit must NOT be rendered
        self.settings.adsense_in_article_slot_id = ""
        self.settings.save()
        response = self.client.get(self.article.url)
        self.assertNotContains(response, 'class="adsbygoogle"')

        # With slot ID configured: unit renders with valid data-ad-slot
        self.settings.adsense_in_article_slot_id = "9876543210"
        self.settings.save()
        response = self.client.get(self.article.url)
        self.assertContains(response, 'class="adsbygoogle"')
        self.assertContains(response, 'data-ad-slot="9876543210"')
        self.assertContains(response, "Advertisement")

    @override_settings(
        ADSENSE_ENABLED=True, ADSENSE_PUBLISHER_ID="pub-1234567890123456"
    )
    def test_site_setting_enabled_false_overrides_environment(self):
        self.settings.adsense_enabled = False
        self.settings.save()
        self.client.cookies["ads_consent"] = "granted"

        response = self.client.get(self.article.url)
        self.assertNotContains(response, "pagead2.googlesyndication.com")
