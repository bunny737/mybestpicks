"""ArticleSource: research sources kept per article, private unless marked public."""

from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from editorial.models import ArticleSource, DiscoveryMode

from .helpers import make_article, make_author, make_category


class ArticleSourceTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.article = make_article(self.hub, self.author, slug="sourced")

    def add(self, name, url="https://maker.test/spec", public=False, order=None):
        return ArticleSource.objects.create(
            article=self.article,
            source_name=name,
            url=url,
            accessed_on=date(2026, 11, 1),
            is_public=public,
            sort_order=order,
        )

    def test_private_sources_are_not_shown_to_readers(self):
        self.add("Private datasheet")
        response = self.client.get(self.article.url)
        self.assertNotContains(response, "Private datasheet")
        self.assertNotContains(response, "Sources")

    def test_public_sources_are_listed_with_safe_link_attributes(self):
        self.add("Maker spec sheet", public=True)
        self.add("Hidden note", url="https://notes.test/x")
        response = self.client.get(self.article.url)
        self.assertContains(response, "Maker spec sheet")
        self.assertContains(response, "accessed 1 November 2026")
        self.assertContains(response, 'rel="noopener nofollow"')
        self.assertNotContains(response, "Hidden note")

    def test_sources_keep_editor_order(self):
        self.add("Second", public=True, order=2)
        self.add("First", public=True, order=1)
        html = self.client.get(self.article.url).content.decode()
        self.assertLess(html.index("First"), html.index("Second"))

    def test_only_http_and_https_urls_are_accepted(self):
        for url in ("javascript:alert(1)", "ftp://maker.test/x", "data:text/html,hi"):
            with self.subTest(url=url):
                source = ArticleSource(
                    article=self.article,
                    source_name="Bad",
                    url=url,
                    accessed_on=date(2026, 11, 1),
                )
                with self.assertRaises(ValidationError) as ctx:
                    source.full_clean()
                self.assertIn("url", ctx.exception.message_dict)

    def test_sources_are_deleted_with_their_article(self):
        self.add("Gone soon")
        self.article.delete()
        self.assertEqual(ArticleSource.objects.count(), 0)
