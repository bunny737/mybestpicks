import json
import re

from django.test import TestCase, override_settings

from editorial.models import DiscoveryMode
from editorial.tests.helpers import make_article, make_author, make_category


def json_ld(response):
    match = re.search(
        r'<script type="application/ld\+json">(.*?)</script>',
        response.content.decode(),
    )
    if match is None:
        return None
    return json.loads(match.group(1))


@override_settings(SITE_URL="https://mybestpicks.in")
class StructuredDataTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)

    def test_article_has_valid_blog_posting_and_breadcrumb_json(self):
        article = make_article(
            self.hub,
            self.author,
            title="A trustworthy guide",
            excerpt="Evidence-based advice.",
        )

        data = json_ld(self.client.get(article.url))

        self.assertEqual(data["@context"], "https://schema.org")
        posting, breadcrumbs = data["@graph"]
        self.assertEqual(posting["@type"], "BlogPosting")
        self.assertEqual(posting["headline"], article.title)
        self.assertEqual(posting["description"], article.excerpt)
        self.assertEqual(posting["author"]["name"], self.author.title)
        self.assertEqual(
            posting["mainEntityOfPage"],
            "https://mybestpicks.in/developer-setup/best-keyboards/",
        )
        self.assertNotIn("review", posting)
        self.assertNotIn("aggregateRating", posting)
        self.assertEqual(breadcrumbs["@type"], "BreadcrumbList")
        self.assertEqual(
            [item["name"] for item in breadcrumbs["itemListElement"]],
            ["Home", "Developer Setup", "A trustworthy guide"],
        )

    def test_category_has_breadcrumbs_but_no_article_markup(self):
        data = json_ld(self.client.get(self.hub.url))

        self.assertEqual(len(data["@graph"]), 1)
        self.assertEqual(data["@graph"][0]["@type"], "BreadcrumbList")

    def test_home_does_not_claim_an_unsupported_schema_type(self):
        self.assertIsNone(json_ld(self.client.get("/")))

    def test_json_ld_escapes_script_terminators(self):
        article = make_article(
            self.hub,
            self.author,
            slug="safe-json",
            title="Safe </script><script>alert(1)</script>",
        )
        html = self.client.get(article.url).content.decode()

        self.assertEqual(html.count('type="application/ld+json"'), 1)
        self.assertNotIn("</script><script>alert(1)</script>", html)
        self.assertEqual(
            json_ld(self.client.get(article.url))["@graph"][0]["headline"],
            article.title,
        )


class IndexingProtectionTests(TestCase):
    @override_settings(BLOCK_SEARCH_INDEXING=True)
    def test_nonpublic_environment_marks_every_response_noindex(self):
        for path in ("/", "/robots.txt", "/no-such-page/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    @override_settings(BLOCK_SEARCH_INDEXING=False)
    def test_production_does_not_block_indexing_globally(self):
        self.assertNotIn("X-Robots-Tag", self.client.get("/"))

    def test_search_page_is_noindex_even_when_global_block_is_off(self):
        response = self.client.get("/search/?query=desk")
        self.assertContains(response, '<meta name="robots" content="noindex,follow"')


class MetaDescriptionTests(TestCase):
    def test_article_uses_excerpt_when_search_description_is_blank(self):
        author = make_author()
        hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        article = make_article(hub, author, excerpt="A unique article summary.")

        self.assertContains(
            self.client.get(article.url),
            '<meta name="description" content="A unique article summary."',
        )

    def test_every_rendered_page_has_a_description_fallback(self):
        for path in ("/", "/search/", "/no-such-page/"):
            with self.subTest(path=path):
                self.assertContains(
                    self.client.get(path),
                    '<meta name="description"',
                    status_code=404 if path == "/no-such-page/" else 200,
                )
