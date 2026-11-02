"""Module 03 rules 4-8: robots/sitemap, empty state, page tree, redirects."""

from django.db.models import ProtectedError
from django.test import TestCase
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page

from editorial.models import (
    ArticlePage,
    AuthorIndexPage,
    AuthorPage,
    CategoryPage,
    DiscoveryMode,
    StandardPage,
)
from home.models import HomePage

from .helpers import (
    get_home,
    make_article,
    make_articles,
    make_author,
    make_category,
    make_standard_page,
)

ROBOTS_NOINDEX = '<meta name="robots" content="noindex,follow"'


class RobotsAndSitemapTests(TestCase):
    def setUp(self):
        self.author = make_author()

    def test_hidden_hub_is_noindex_and_not_in_sitemap(self):
        hub = make_category(mode=DiscoveryMode.FORCE_HIDE)
        self.assertEqual(hub.get_sitemap_urls(), [])
        response = self.client.get(hub.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ROBOTS_NOINDEX)

    def test_article_in_hidden_hub_stays_indexable_and_in_sitemap(self):
        hub = make_category(mode=DiscoveryMode.FORCE_HIDE)
        article = make_article(hub, self.author)
        self.assertEqual(len(article.get_sitemap_urls()), 1)
        response = self.client.get(article.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="robots"')

    def test_discoverable_hub_is_indexable_and_in_sitemap(self):
        hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.assertEqual(len(hub.get_sitemap_urls()), 1)
        response = self.client.get(hub.url)
        self.assertNotContains(response, 'name="robots"')

    def test_auto_hub_becomes_indexable_at_the_threshold(self):
        hub = make_category(mode=DiscoveryMode.AUTO)
        make_articles(hub, self.author, 2)
        self.assertEqual(CategoryPage.objects.get(pk=hub.pk).get_sitemap_urls(), [])
        make_article(hub, self.author, slug="third")
        self.assertEqual(len(CategoryPage.objects.get(pk=hub.pk).get_sitemap_urls()), 1)


class CategoryPageRenderingTests(TestCase):
    def setUp(self):
        self.author = make_author()

    def test_live_hub_with_no_articles_shows_a_coming_soon_state(self):
        hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        response = self.client.get(hub.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "coming soon")
        self.assertNotContains(response, "All guides")

    def test_hub_lists_only_live_articles(self):
        hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        make_article(hub, self.author, slug="live-one", title="Live One")
        make_article(hub, self.author, slug="draft-one", title="Draft One", live=False)
        response = self.client.get(hub.url)
        self.assertContains(response, "Live One")
        self.assertNotContains(response, "Draft One")
        self.assertNotContains(response, "coming soon")


class PageTreeRuleTests(TestCase):
    """Rule 6 and the page-type placement rules."""

    def setUp(self):
        self.home = get_home()
        self.author = make_author()
        self.hub = make_category()

    def test_article_can_only_be_created_under_a_category(self):
        self.assertTrue(ArticlePage.can_create_at(self.hub))
        self.assertFalse(ArticlePage.can_create_at(self.home))
        self.assertFalse(ArticlePage.can_create_at(self.author))

    def test_category_can_only_be_created_under_the_home_page(self):
        self.assertTrue(CategoryPage.can_create_at(self.home))
        self.assertFalse(CategoryPage.can_create_at(self.hub))

    def test_author_pages_live_under_the_authors_index(self):
        index = AuthorIndexPage.objects.get()
        self.assertTrue(AuthorPage.can_create_at(index))
        self.assertFalse(AuthorPage.can_create_at(self.home))

    def test_standard_pages_live_under_the_home_page(self):
        self.assertTrue(StandardPage.can_create_at(self.home))
        self.assertFalse(StandardPage.can_create_at(self.hub))

    def test_home_page_is_a_single_root_child(self):
        root = Page.objects.get(depth=1)
        self.assertFalse(HomePage.can_create_at(root))  # one HomePage already exists

    def test_article_urls_nest_under_their_category(self):
        article = make_article(self.hub, self.author, slug="best-keyboards")
        self.assertEqual(article.url, "/developer-setup/best-keyboards/")
        self.assertEqual(article.category.pk, self.hub.pk)

    def test_an_author_with_articles_cannot_be_deleted(self):
        make_article(self.hub, self.author)
        with self.assertRaises(ProtectedError):
            AuthorPage.objects.get(pk=self.author.pk).delete()

    def test_standard_and_author_pages_render(self):
        about = make_standard_page()
        self.assertEqual(self.client.get(about.url).status_code, 200)
        self.assertEqual(self.client.get(self.author.url).status_code, 200)
        self.assertEqual(self.client.get("/authors/").status_code, 200)


class ArticleFieldTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)

    def test_article_renders_body_blocks_and_author(self):
        article = make_article(
            self.hub,
            self.author,
            slug="with-body",
            title="With Body",
            body=[
                {"type": "paragraph", "value": "<p>Intro text.</p>"},
                {"type": "heading", "value": {"text": "Why it matters", "level": "h3"}},
            ],
        )
        response = self.client.get(article.url)
        self.assertContains(response, "Intro text.")
        self.assertContains(response, "<h3>Why it matters</h3>", html=True)
        self.assertContains(response, self.author.title)

    def test_heading_block_text_is_escaped(self):
        article = make_article(
            self.hub,
            self.author,
            slug="escape",
            body=[
                {
                    "type": "heading",
                    "value": {"text": "<script>alert(1)</script>", "level": "h2"},
                }
            ],
        )
        response = self.client.get(article.url)
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_tags_are_saved_and_rendered(self):
        article = make_article(self.hub, self.author, slug="tagged")
        article.tags.add("usb-c")
        article.save()
        response = self.client.get(article.url)
        self.assertContains(response, "usb-c")


class RedirectTests(TestCase):
    """Rule 8: changing a slug or moving a page creates a 301 redirect."""

    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)

    def test_changing_an_article_slug_creates_a_redirect(self):
        article = make_article(self.hub, self.author, slug="old-slug")
        article = ArticlePage.objects.get(pk=article.pk)
        article.slug = "new-slug"
        # Wagtail sends page_slug_changed in transaction.on_commit; TestCase never
        # commits, so run those callbacks explicitly.
        with self.captureOnCommitCallbacks(execute=True):
            article.save_revision().publish()

        redirect = Redirect.objects.get(
            old_path=Redirect.normalise_path("/developer-setup/old-slug/")
        )
        self.assertEqual(redirect.redirect_page_id, article.pk)

        response = self.client.get("/developer-setup/old-slug/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/developer-setup/new-slug/")

    def test_moving_an_article_to_another_category_creates_a_redirect(self):
        other = make_category("Home Office", "home-office", DiscoveryMode.FORCE_SHOW)
        article = make_article(self.hub, self.author, slug="desk-lamps")
        ArticlePage.objects.get(pk=article.pk).move(
            CategoryPage.objects.get(pk=other.pk), pos="last-child"
        )

        response = self.client.get("/developer-setup/desk-lamps/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/home-office/desk-lamps/")
