from django.test import TestCase, override_settings

from editorial.models import DiscoveryMode
from editorial.tests.helpers import make_article, make_author, make_category

GTAG_URL = "googletagmanager.com"


class GA4ConsentGateTests(TestCase):
    """Invariant 9: GA4 never loads before consent, and is off when unconfigured."""

    def setUp(self):
        hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.article = make_article(hub, make_author())

    @override_settings(GA4_MEASUREMENT_ID="")
    def test_nothing_renders_when_unset(self):
        response = self.client.get(self.article.url)
        self.assertNotContains(response, "analytics-consent")
        self.assertNotContains(response, GTAG_URL)

    @override_settings(GA4_MEASUREMENT_ID="G-NXFRFV6QD3")
    def test_banner_renders_but_gtag_is_never_in_server_html(self):
        response = self.client.get(self.article.url)
        self.assertContains(response, 'id="analytics-consent"')
        self.assertContains(response, 'data-ga4-id="G-NXFRFV6QD3"')
        self.assertNotContains(response, GTAG_URL)
        self.assertNotContains(response, "gtag(")

    @override_settings(GA4_MEASUREMENT_ID="G-NXFRFV6QD3")
    def test_gtag_not_in_html_even_with_consent_cookie(self):
        # The script is injected client-side only, so it is never server-rendered.
        self.client.cookies["analytics_consent"] = "granted"
        response = self.client.get(self.article.url)
        self.assertNotContains(response, GTAG_URL)

    @override_settings(GA4_MEASUREMENT_ID="not-an-id")
    def test_malformed_id_is_ignored(self):
        for bad in ("not-an-id", 'G-ABC123"><script>', "g-nxfrfv6qd3"):
            with self.subTest(bad=bad), override_settings(GA4_MEASUREMENT_ID=bad):
                response = self.client.get(self.article.url)
                self.assertNotContains(response, "analytics-consent")
