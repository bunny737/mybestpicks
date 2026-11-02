from django.core.exceptions import ValidationError
from django.test import TestCase

from editorial.models import CategoryFeaturedGuide, DiscoveryMode
from editorial.tests.helpers import (
    get_home,
    make_article,
    make_articles,
    make_author,
    make_category,
)
from home.models import HomeFeaturedGuide, HomePage


class HomePageTests(TestCase):
    def setUp(self):
        self.author = make_author()

    def test_starter_home_page_exists_with_the_default_hero(self):
        home = get_home()
        self.assertIsInstance(home, HomePage)
        self.assertEqual(home.hero_title, "Find the Best Picks for Everyday Life.")

    def test_home_renders_the_hero(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Find the Best Picks for Everyday Life.")

    def test_home_lists_only_discoverable_categories(self):
        make_category("Shown Hub", "shown-hub", DiscoveryMode.FORCE_SHOW)
        make_category("Secret Hub", "secret-hub", DiscoveryMode.FORCE_HIDE)
        auto = make_category("Auto Hub", "auto-hub", DiscoveryMode.AUTO)
        make_articles(auto, self.author, 3)
        thin = make_category("Thin Hub", "thin-hub", DiscoveryMode.AUTO)
        make_articles(thin, self.author, 1, prefix="thin")

        response = self.client.get("/")

        self.assertContains(response, "Shown Hub")
        self.assertContains(response, "Auto Hub")
        self.assertNotContains(response, "Secret Hub")
        self.assertNotContains(response, "Thin Hub")

    def test_home_without_discoverable_categories_has_no_empty_grid(self):
        make_category("Secret Hub", "secret-hub", DiscoveryMode.FORCE_HIDE)
        response = self.client.get("/")
        self.assertNotContains(response, "Browse by category")

    def test_featured_guides_show_only_live_articles(self):
        hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        live = make_article(hub, self.author, slug="live", title="Live Guide")
        draft = make_article(hub, self.author, slug="draft", title="Draft Guide")
        HomeFeaturedGuide.objects.create(home=get_home(), article=live)
        HomeFeaturedGuide.objects.create(home=get_home(), article=draft)
        draft.unpublish()

        response = self.client.get("/")

        self.assertContains(response, "Live Guide")
        self.assertNotContains(response, "Draft Guide")


class CategoryFeaturedGuideTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.other = make_category("Other", "other", DiscoveryMode.FORCE_SHOW)

    def test_featuring_an_article_from_another_category_is_rejected(self):
        foreign = make_article(self.other, self.author, slug="foreign")
        item = CategoryFeaturedGuide(category=self.hub, article=foreign)
        with self.assertRaises(ValidationError):
            item.clean()

    def test_featured_guide_appears_on_its_own_category_page(self):
        article = make_article(
            self.hub, self.author, slug="mine", title="Featured Mine"
        )
        CategoryFeaturedGuide.objects.create(category=self.hub, article=article)
        item = CategoryFeaturedGuide.objects.get()
        item.clean()

        response = self.client.get(self.hub.url)

        self.assertContains(response, "Featured guides")
        self.assertContains(response, "Featured Mine")
