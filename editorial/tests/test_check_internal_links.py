"""
Module 10 (MBP-010): ``check_internal_links`` finds broken internal links on
live, public pages without ever fetching an external URL.
"""

from django.test import TestCase
from wagtail.documents.models import Document
from wagtail.documents.tests.utils import get_test_document_file

from editorial.audits import find_broken_internal_links
from editorial.models import CategoryFeaturedGuide, DiscoveryMode

from .helpers import make_article, make_author, make_category


def categories(findings):
    return {f.category for f in findings}


def paragraph(html):
    return {"type": "paragraph", "value": html}


class PageLinkTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)

    def test_link_to_an_unpublished_page_is_flagged(self):
        draft = make_article(self.hub, self.author, slug="draft-target", live=False)
        make_article(
            self.hub,
            self.author,
            slug="source",
            body=[
                paragraph(
                    f'<p>See our <a linktype="page" id="{draft.pk}">'
                    "other guide</a>.</p>"
                )
            ],
        )
        findings = find_broken_internal_links()
        self.assertIn("broken-page-link", categories(findings))

    def test_link_to_a_live_page_is_not_flagged(self):
        target = make_article(self.hub, self.author, slug="live-target")
        make_article(
            self.hub,
            self.author,
            slug="source",
            body=[
                paragraph(
                    f'<p>See our <a linktype="page" id="{target.pk}">'
                    "other guide</a>.</p>"
                )
            ],
        )
        findings = find_broken_internal_links()
        self.assertNotIn("broken-page-link", categories(findings))

    def test_link_to_a_deleted_page_id_is_flagged(self):
        make_article(
            self.hub,
            self.author,
            slug="source",
            body=[paragraph('<p>See <a linktype="page" id="999999">this</a>.</p>')],
        )
        findings = find_broken_internal_links()
        self.assertIn("broken-page-link", categories(findings))


class DocumentLinkTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)

    def test_link_to_an_existing_document_is_not_flagged(self):
        doc = Document.objects.create(title="Spec sheet", file=get_test_document_file())
        make_article(
            self.hub,
            self.author,
            slug="source",
            body=[
                paragraph(
                    f'<p>Read the <a linktype="document" id="{doc.pk}">spec</a>.</p>'
                )
            ],
        )
        findings = find_broken_internal_links()
        self.assertNotIn("broken-document-link", categories(findings))

    def test_link_to_a_missing_document_is_flagged(self):
        make_article(
            self.hub,
            self.author,
            slug="source",
            body=[
                paragraph(
                    '<p>Read the <a linktype="document" id="999999">spec</a>.</p>'
                )
            ],
        )
        findings = find_broken_internal_links()
        self.assertIn("broken-document-link", categories(findings))


class HrefLinkTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)

    def test_href_to_a_missing_path_is_flagged(self):
        make_article(
            self.hub,
            self.author,
            slug="source",
            body=[paragraph('<p>See <a href="/no-such-page-anywhere/">this</a>.</p>')],
        )
        findings = find_broken_internal_links()
        self.assertIn("broken-link", categories(findings))

    def test_href_to_the_homepage_is_not_flagged(self):
        make_article(
            self.hub,
            self.author,
            slug="source",
            body=[paragraph('<p>Back to the <a href="/">homepage</a>.</p>')],
        )
        findings = find_broken_internal_links()
        self.assertNotIn("broken-link", categories(findings))

    def test_external_link_is_never_flagged(self):
        make_article(
            self.hub,
            self.author,
            slug="source",
            body=[
                paragraph('<p>See <a href="https://example.test/review">this</a>.</p>')
            ],
        )
        findings = find_broken_internal_links()
        self.assertEqual(findings, [])

    def test_mailto_and_fragment_links_are_never_flagged(self):
        make_article(
            self.hub,
            self.author,
            slug="source",
            body=[
                paragraph(
                    '<p><a href="mailto:hello@example.test">Email us</a> or jump to '
                    '<a href="#section-2">section 2</a>.</p>'
                )
            ],
        )
        findings = find_broken_internal_links()
        self.assertEqual(findings, [])


class RelatedArticlesPickTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)

    def test_related_pick_of_an_unpublished_article_is_flagged(self):
        draft = make_article(self.hub, self.author, slug="draft-target", live=False)
        make_article(
            self.hub,
            self.author,
            slug="source",
            body=[
                {
                    "type": "related_articles",
                    "value": {"heading": "Related", "articles": [draft.pk]},
                }
            ],
        )
        findings = find_broken_internal_links()
        self.assertIn("broken-related-pick", categories(findings))

    def test_related_pick_of_a_live_article_is_not_flagged(self):
        target = make_article(self.hub, self.author, slug="live-target")
        make_article(
            self.hub,
            self.author,
            slug="source",
            body=[
                {
                    "type": "related_articles",
                    "value": {"heading": "Related", "articles": [target.pk]},
                }
            ],
        )
        findings = find_broken_internal_links()
        self.assertNotIn("broken-related-pick", categories(findings))


class FeaturedGuidePickTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)

    def test_featured_guide_pointing_at_an_unpublished_article_is_flagged(self):
        article = make_article(self.hub, self.author, slug="now-unpublished")
        CategoryFeaturedGuide.objects.create(category=self.hub, article=article)
        article.live = False
        article.save()

        findings = find_broken_internal_links()
        self.assertIn("broken-featured-guide", categories(findings))

    def test_featured_guide_pointing_at_a_live_article_is_not_flagged(self):
        article = make_article(self.hub, self.author, slug="still-live")
        CategoryFeaturedGuide.objects.create(category=self.hub, article=article)

        findings = find_broken_internal_links()
        self.assertNotIn("broken-featured-guide", categories(findings))
