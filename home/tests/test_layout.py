"""Module 02: base layout, navigation, breadcrumbs, accessibility hooks."""

import re
import shutil
import tempfile

from django.db import connection
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

from catalog.provenance import ImageProvenance
from editorial.models import ArticleKind, DiscoveryMode
from editorial.tests.helpers import (
    get_home,
    make_article,
    make_articles,
    make_author,
    make_category,
    make_standard_page,
)


def h1_count(response):
    return len(re.findall(r"<h1[\s>]", response.content.decode()))


def header_nav(response):
    """The primary navigation markup only (not the footer copy)."""
    html = response.content.decode()
    start = html.index('aria-label="Primary"')
    return html[start : html.index("</header>", start)]


class NavigationTests(TestCase):
    def setUp(self):
        self.author = make_author()

    def test_nav_lists_only_discoverable_categories(self):
        make_category("Shown Hub", "shown", DiscoveryMode.FORCE_SHOW)
        make_category("Secret Hub", "secret", DiscoveryMode.FORCE_HIDE)
        make_category("Draft Hub", "draft", DiscoveryMode.FORCE_SHOW, live=False)
        auto = make_category("Auto Hub", "auto", DiscoveryMode.AUTO)
        make_articles(auto, self.author, 3)
        thin = make_category("Thin Hub", "thin", DiscoveryMode.AUTO)
        make_articles(thin, self.author, 2, prefix="thin")

        nav = header_nav(self.client.get("/"))

        self.assertIn("Shown Hub", nav)
        self.assertIn("Auto Hub", nav)
        for hidden in ("Secret Hub", "Draft Hub", "Thin Hub"):
            self.assertNotIn(hidden, nav)

    def test_show_in_menus_never_reveals_a_hidden_category(self):
        hub = make_category("Secret Hub", "secret", DiscoveryMode.FORCE_HIDE)
        hub.show_in_menus = True
        hub.save()

        response = self.client.get("/")

        self.assertNotContains(response, "Secret Hub")

    def test_nav_query_count_does_not_grow_with_the_number_of_categories(self):
        make_category("Hub 0", "hub-0", DiscoveryMode.FORCE_SHOW)
        self.client.get("/")  # warm caches (site root paths, content types)

        with CaptureQueriesContext(connection) as few:
            self.client.get("/")
        for i in range(1, 8):
            make_category(f"Hub {i}", f"hub-{i}", DiscoveryMode.FORCE_SHOW)
        with CaptureQueriesContext(connection) as many:
            response = self.client.get("/")

        self.assertContains(response, "Hub 7")
        self.assertEqual(len(few), len(many))

    def test_nav_is_not_queried_outside_public_templates(self):
        make_category("Shown Hub", "shown", DiscoveryMode.FORCE_SHOW)
        with CaptureQueriesContext(connection) as queries:
            self.client.get("/admin/login/")
        self.assertFalse(any("discovery_mode" in q["sql"] for q in queries))

    def test_current_category_is_marked_in_the_nav(self):
        hub = make_category("Shown Hub", "shown", DiscoveryMode.FORCE_SHOW)
        make_category("Other Hub", "other", DiscoveryMode.FORCE_SHOW)
        article = make_article(hub, self.author, slug="inside")

        for url in (hub.url, article.url):
            nav = header_nav(self.client.get(url))
            self.assertEqual(nav.count('aria-current="page"'), 1, url)
            self.assertRegex(nav, r'class="nav-link active"[^>]*aria-current="page"')

    def test_categories_are_repeated_in_the_footer_for_no_javascript(self):
        make_category("Shown Hub", "shown", DiscoveryMode.FORCE_SHOW)
        html = self.client.get("/").content.decode()
        footer = html[html.index("<footer") :]
        self.assertIn("Shown Hub", footer)

    def test_footer_lists_only_standard_pages_marked_for_menus(self):
        listed = make_standard_page("Privacy Policy", "privacy-policy")
        listed.show_in_menus = True
        listed.save()
        make_standard_page("Unlisted Page", "unlisted")

        html = self.client.get("/").content.decode()
        footer = html[html.index("<footer") :]

        self.assertIn("Privacy Policy", footer)
        self.assertNotIn("Unlisted Page", footer)


class SkeletonAndAccessibilityTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.article = make_article(self.hub, self.author)
        self.about = make_standard_page()

    def urls(self):
        return {
            "home": "/",
            "category": self.hub.url,
            "article": self.article.url,
            "author": self.author.url,
            "authors": "/authors/",
            "standard": self.about.url,
            "search": "/search/?query=guide",
        }

    def test_every_page_type_has_exactly_one_h1(self):
        for name, url in self.urls().items():
            with self.subTest(page=name):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(h1_count(response), 1)

    def test_every_page_has_the_accessibility_skeleton(self):
        for name, url in self.urls().items():
            with self.subTest(page=name):
                html = self.client.get(url).content.decode()
                self.assertIn('<html lang="en-IN">', html)
                self.assertIn('name="viewport"', html)
                self.assertIn('href="#main-content"', html)  # skip link
                self.assertIn('<main id="main-content"', html)
                self.assertIn('role="search"', html)
                self.assertIn('aria-label="Primary"', html)

    def test_bootstrap_is_served_from_our_own_static_files(self):
        html = self.client.get("/").content.decode()
        self.assertIn("vendor/bootstrap/bootstrap.min.css", html)
        self.assertIn("vendor/bootstrap/bootstrap.bundle.min.js", html)
        self.assertNotIn("cdn.jsdelivr.net", html)

    def test_the_site_works_without_javascript_for_reading(self):
        # Article text is in the server HTML, not injected by scripts.
        article = make_article(
            self.hub,
            self.author,
            slug="static-text",
            body=[{"type": "paragraph", "value": "<p>Server rendered words.</p>"}],
        )
        self.assertContains(self.client.get(article.url), "Server rendered words.")


class BreadcrumbTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.article = make_article(self.hub, self.author, title="Best Keyboards")

    def test_article_breadcrumb_trail(self):
        html = self.client.get(self.article.url).content.decode()
        trail = html[html.index('aria-label="Breadcrumb"') :]
        trail = trail[: trail.index("</nav>")]
        self.assertLess(trail.index("Home"), trail.index("Developer Setup"))
        self.assertLess(trail.index("Developer Setup"), trail.index("Best Keyboards"))
        self.assertIn('aria-current="page">Best Keyboards', trail)
        self.assertIn('href="/developer-setup/"', trail)

    def test_category_breadcrumb_trail_ends_at_the_category(self):
        html = self.client.get(self.hub.url).content.decode()
        self.assertIn('aria-current="page">Developer Setup', html)

    def test_home_page_has_no_breadcrumb(self):
        self.assertNotContains(self.client.get("/"), 'aria-label="Breadcrumb"')


class ArticleLayoutTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        override = override_settings(MEDIA_ROOT=self.media)
        override.enable()
        self.addCleanup(override.disable)

        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.image = Image.objects.create(title="Desk", file=get_test_image_file())

    def test_related_guides_are_live_siblings_only(self):
        article = make_article(self.hub, self.author, slug="main", title="Main Guide")
        make_article(self.hub, self.author, slug="sib", title="Sibling Guide")
        make_article(self.hub, self.author, slug="dr", title="Draft Guide", live=False)
        other = make_category("Other", "other", DiscoveryMode.FORCE_SHOW)
        make_article(other, self.author, slug="far", title="Faraway Guide")

        html = self.client.get(article.url).content.decode()
        related = html[html.index("Related guides") :]

        self.assertIn("Sibling Guide", related)
        self.assertNotIn("Main Guide", related)
        self.assertNotIn("Draft Guide", html)
        self.assertNotIn("Faraway Guide", html)

    def test_hero_image_is_high_priority_and_not_lazy_with_dimensions(self):
        article = make_article(
            self.hub,
            self.author,
            slug="with-image",
            featured_image=self.image,
            featured_image_provenance=ImageProvenance.OTHER_LICENSED,
            featured_image_credit="Photo by A. Person, CC BY 4.0",
        )
        html = self.client.get(article.url).content.decode()
        hero = re.search(r"<img[^>]*fetchpriority=\"high\"[^>]*>", html)

        self.assertIsNotNone(hero)
        self.assertRegex(hero.group(0), r'width="\d+"')
        self.assertRegex(hero.group(0), r'height="\d+"')
        self.assertNotIn('loading="lazy"', hero.group(0))
        self.assertIn("Image: Photo by A. Person, CC BY 4.0", html)

    def test_card_images_are_lazy_with_dimensions(self):
        make_article(
            self.hub,
            self.author,
            slug="card-image",
            featured_image=self.image,
            featured_image_provenance=ImageProvenance.OWNED_ORIGINAL,
        )
        html = self.client.get(self.hub.url).content.decode()
        card = re.search(r"<img[^>]*card-img-top[^>]*>", html)

        self.assertIsNotNone(card)
        self.assertIn('loading="lazy"', card.group(0))
        self.assertRegex(card.group(0), r'width="\d+"')
        self.assertRegex(card.group(0), r'height="\d+"')

    def test_methodology_is_in_the_html_and_collapsible(self):
        article = make_article(
            self.hub,
            self.author,
            slug="method",
            methodology="<p>We compared forty spec sheets.</p>",
        )
        html = self.client.get(article.url).content.decode()
        self.assertIn("<details", html)
        self.assertIn("We compared forty spec sheets.", html)


class HomeSectionsTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)

    def test_latest_comparisons_lists_only_comparison_articles(self):
        make_article(
            self.hub,
            self.author,
            slug="cmp",
            title="Mechanical vs Membrane",
            article_kind=ArticleKind.COMPARISON,
        )
        make_article(self.hub, self.author, slug="guide", title="Plain Buying Guide")
        home = self.client.get("/")

        html = home.content.decode()
        comparisons = html[html.index("Latest comparisons") :]
        comparisons = comparisons[: comparisons.index("</section>")]

        self.assertIn("Mechanical vs Membrane", comparisons)
        self.assertNotIn("Plain Buying Guide", comparisons)


class EmptySiteTests(TestCase):
    def test_empty_site_has_no_empty_sections(self):
        html = self.client.get("/").content.decode()
        for heading in (
            "Browse by category",
            "Featured guides",
            "Latest comparisons",
            "Recently updated",
        ):
            self.assertNotIn(heading, html)
        hero = get_home().hero_title
        self.assertEqual(hero, "Find the Best Picks for Everyday Life.")
        self.assertIn(hero, html)


class ErrorPageTests(TestCase):
    def test_404_uses_the_site_layout(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)
        self.assertContains(response, 'aria-label="Primary"', status_code=404)

    def test_500_page_is_standalone_and_needs_no_database(self):
        html = render_to_string("500.html")
        self.assertIn("Something went wrong", html)
        self.assertNotIn("Primary", html)
        self.assertEqual(len(re.findall(r"<h1[\s>]", html)), 1)
