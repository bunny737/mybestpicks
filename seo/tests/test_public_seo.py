import re

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from wagtail.models import Site

from editorial.models import DiscoveryMode
from editorial.tests.helpers import make_article, make_author, make_category
from home.models import SiteSettings


@override_settings(SITE_URL="https://mybestpicks.in")
class PublicSeoTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.article = make_article(
            self.hub, self.author, slug="new-guide", title="New Guide"
        )

    def test_sitemap_contains_articles_and_omits_hidden_hubs(self):
        hidden = make_category("Hidden Hub", "hidden", DiscoveryMode.FORCE_HIDE)
        hidden_article = make_article(
            hidden, self.author, slug="visible-article", title="Visible Article"
        )

        response = self.client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.url)
        self.assertContains(response, hidden_article.url)
        locations = re.findall(r"<loc>(.*?)</loc>", response.content.decode())
        self.assertTrue(
            all(url.startswith("https://mybestpicks.in/") for url in locations)
        )
        self.assertFalse(any(url.endswith(hidden.url) for url in locations))

    def test_robots_allows_content_and_blocks_admin_and_search(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(response, "Allow: /")
        self.assertContains(response, "Disallow: /admin/")
        self.assertContains(response, "Disallow: /search/")
        self.assertContains(response, "Sitemap: https://mybestpicks.in/sitemap.xml")

    def test_pages_have_one_query_free_canonical_and_feed_discovery_link(self):
        response = self.client.get(f"{self.article.url}?utm_source=test")
        html = response.content.decode()

        self.assertEqual(html.count('rel="canonical"'), 1)
        self.assertIn(
            f'<link rel="canonical" href="https://mybestpicks.in{self.article.url}"',
            html,
        )
        self.assertNotIn("utm_source", html)
        self.assertIn('type="application/rss+xml"', html)
        self.assertIn('href="https://mybestpicks.in/feed/"', html)

    def test_feed_is_newest_first_and_uses_canonical_links(self):
        older = self.article
        newer = make_article(
            self.hub, self.author, slug="newer-guide", title="Newer Guide"
        )
        type(older).objects.filter(pk=older.pk).update(
            first_published_at="2026-10-01T00:00:00Z"
        )
        type(newer).objects.filter(pk=newer.pk).update(
            first_published_at="2026-11-01T00:00:00Z"
        )

        response = self.client.get("/feed/")
        xml = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/rss+xml; charset=utf-8")
        self.assertLess(xml.index("Newer Guide"), xml.index("New Guide"))
        self.assertIn("https://mybestpicks.in/developer-setup/newer-guide/", xml)
        self.assertNotIn("utm_", xml)


class TelegramSettingTests(TestCase):
    def site_settings(self):
        return SiteSettings.for_site(Site.objects.get(is_default_site=True))

    def test_invalid_or_insecure_telegram_urls_are_rejected(self):
        for url in ("http://t.me/mybestpicks", "https://example.com/mybestpicks"):
            setting = self.site_settings()
            setting.telegram_channel_url = url
            with self.subTest(url=url), self.assertRaises(ValidationError):
                setting.full_clean()

    def test_telegram_cta_is_absent_when_url_is_blank(self):
        response = self.client.get("/")
        self.assertNotContains(response, "Join on Telegram")
        self.assertNotContains(response, "t.me/")

    def test_configured_telegram_cta_uses_custom_label_across_site(self):
        setting = self.site_settings()
        setting.telegram_channel_url = "https://t.me/mybestpicks"
        setting.telegram_channel_label = "Follow our channel"
        setting.full_clean()
        setting.save()
        author = make_author()
        hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        article = make_article(hub, author)

        for url in ("/", article.url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "https://t.me/mybestpicks", count=2)
                self.assertContains(response, "Follow our channel", count=2)
