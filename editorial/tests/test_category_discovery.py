from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from wagtail.models import PageViewRestriction

from editorial.models import (
    DISCOVERY_AUTO_MIN_ARTICLES,
    CategoryPage,
    DiscoveryMode,
    StandardPage,
)

from .helpers import (
    get_home,
    make_article,
    make_articles,
    make_author,
    make_category,
)


class DiscoveryModeRuleTests(TestCase):
    """Module 03 rules 1-3: discovery_mode is the single visibility rule."""

    def setUp(self):
        self.author = make_author()

    def test_new_category_defaults_to_force_hide(self):
        hub = CategoryPage(title="New", slug="new")
        self.assertEqual(hub.discovery_mode, DiscoveryMode.FORCE_HIDE)
        self.assertFalse(hub.is_discoverable)

    def test_force_show_is_discoverable_with_no_articles(self):
        hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.assertEqual(hub.live_child_count, 0)
        self.assertTrue(hub.is_discoverable)

    def test_force_hide_is_hidden_even_with_many_live_articles(self):
        hub = make_category(mode=DiscoveryMode.FORCE_HIDE)
        make_articles(hub, self.author, DISCOVERY_AUTO_MIN_ARTICLES + 2)
        self.assertFalse(hub.is_discoverable)

    def test_auto_needs_the_minimum_number_of_live_articles(self):
        hub = make_category(mode=DiscoveryMode.AUTO)
        make_articles(hub, self.author, DISCOVERY_AUTO_MIN_ARTICLES - 1)
        self.assertFalse(CategoryPage.objects.get(pk=hub.pk).is_discoverable)

        make_article(hub, self.author, slug="the-third")
        hub = CategoryPage.objects.get(pk=hub.pk)
        self.assertEqual(hub.live_child_count, DISCOVERY_AUTO_MIN_ARTICLES)
        self.assertTrue(hub.is_discoverable)

    def test_auto_ignores_draft_articles(self):
        hub = make_category(mode=DiscoveryMode.AUTO)
        make_articles(hub, self.author, DISCOVERY_AUTO_MIN_ARTICLES - 1)
        make_article(hub, self.author, slug="a-draft", live=False)
        hub = CategoryPage.objects.get(pk=hub.pk)
        self.assertEqual(hub.live_child_count, DISCOVERY_AUTO_MIN_ARTICLES - 1)
        self.assertFalse(hub.is_discoverable)

    def test_auto_counts_only_article_children(self):
        hub = make_category(mode=DiscoveryMode.AUTO)
        make_articles(hub, self.author, DISCOVERY_AUTO_MIN_ARTICLES - 1)
        # A live non-article child must not push the hub over the threshold.
        CategoryPage.objects.get(pk=hub.pk).add_child(
            instance=StandardPage(title="Not an article", slug="nope", body="<p>x</p>")
        )
        hub = CategoryPage.objects.get(pk=hub.pk)
        self.assertEqual(hub.live_child_count, DISCOVERY_AUTO_MIN_ARTICLES - 1)
        self.assertFalse(hub.is_discoverable)


class DiscoverableQuerySetTests(TestCase):
    """The queryset used by navigation must agree with ``is_discoverable``."""

    def setUp(self):
        self.author = make_author()

    def test_queryset_matches_the_property_for_every_mode(self):
        shown = make_category("Shown", "shown", DiscoveryMode.FORCE_SHOW)
        hidden = make_category("Hidden", "hidden", DiscoveryMode.FORCE_HIDE)
        auto_ok = make_category("Auto OK", "auto-ok", DiscoveryMode.AUTO)
        auto_low = make_category("Auto Low", "auto-low", DiscoveryMode.AUTO)
        make_articles(hidden, self.author, 5, prefix="h")
        make_articles(auto_ok, self.author, 3, prefix="ok")
        make_articles(auto_low, self.author, 2, prefix="low")

        result = set(CategoryPage.objects.discoverable().values_list("pk", flat=True))

        self.assertEqual(result, {shown.pk, auto_ok.pk})
        for hub in CategoryPage.objects.all():
            self.assertEqual(hub.pk in result, hub.is_discoverable, hub.slug)

    def test_unpublished_hub_is_excluded(self):
        make_category("Draft", "draft", DiscoveryMode.FORCE_SHOW, live=False)
        self.assertEqual(CategoryPage.objects.discoverable().count(), 0)

    def test_private_hub_is_excluded(self):
        hub = make_category("Private", "private", DiscoveryMode.FORCE_SHOW)
        PageViewRestriction.objects.create(
            page=hub, restriction_type=PageViewRestriction.LOGIN
        )
        self.assertEqual(CategoryPage.objects.discoverable().count(), 0)

    def test_discoverable_query_count_does_not_grow_with_hubs(self):
        home = get_home()

        def run():
            with CaptureQueriesContext(connection) as queries:
                hubs = list(CategoryPage.objects.child_of(home).discoverable())
            return hubs, len(queries)

        for i in range(2):
            hub = make_category(f"Hub {i}", f"hub-{i}", DiscoveryMode.AUTO)
            make_articles(hub, self.author, i + 2, prefix=f"a{i}")
        _, few = run()

        for i in range(2, 8):
            hub = make_category(f"Hub {i}", f"hub-{i}", DiscoveryMode.AUTO)
            make_articles(hub, self.author, i + 2, prefix=f"a{i}")
        hubs, many = run()

        self.assertEqual(few, many)
        # one query for the hubs, plus Wagtail's lookup of private-page restrictions
        self.assertLessEqual(many, 2)
        self.assertEqual(
            len(hubs), 7
        )  # only hub 0 (2 live articles) is below the minimum
        self.assertEqual(
            sorted(h.live_article_count for h in hubs), [3, 4, 5, 6, 7, 8, 9]
        )
