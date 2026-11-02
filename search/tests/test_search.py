"""
Module 08: /search/ uses Wagtail's database search backend. Business rules:
drafts and private pages never appear, an empty/whitespace query runs no query,
and results are paginated and marked noindex,follow.
"""

from django.test import TestCase
from django.urls import reverse
from wagtail.models import PageViewRestriction

from editorial.tests.helpers import make_article, make_author, make_category


class SearchTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category()

    def search(self, query=None):
        params = {"query": query} if query is not None else {}
        return self.client.get(reverse("search"), params)

    def test_live_article_matching_title_appears(self):
        make_article(
            self.hub,
            self.author,
            slug="mechanical-keyboards",
            title="Best Mechanical Keyboards",
        )
        response = self.search("mechanical")
        self.assertContains(response, "Best Mechanical Keyboards")

    def test_match_on_excerpt_body_and_tags_is_found(self):
        article = make_article(
            self.hub,
            self.author,
            slug="ergonomic-chairs",
            title="Office Chairs",
            excerpt="A guide to standing desks for home offices.",
        )
        article.tags.add("standing-desk")
        article.save()
        response = self.search("standing")
        self.assertContains(response, "Office Chairs")

    def test_draft_article_never_appears(self):
        make_article(
            self.hub,
            self.author,
            slug="draft-guide",
            title="Draft Guide Keyboards",
            live=False,
        )
        response = self.search("keyboards")
        self.assertNotContains(response, "Draft Guide Keyboards")

    def test_privately_restricted_page_never_appears(self):
        article = make_article(
            self.hub,
            self.author,
            slug="restricted-guide",
            title="Restricted Guide Keyboards",
        )
        PageViewRestriction.objects.create(
            page=article, restriction_type="password", password="secret"
        )
        response = self.search("keyboards")
        self.assertNotContains(response, "Restricted Guide Keyboards")

    def test_empty_query_runs_no_query_and_shows_empty_state(self):
        make_article(self.hub, self.author, slug="some-guide", title="Some Guide")
        response = self.search("")
        self.assertNotContains(response, "Some Guide")
        self.assertContains(response, "Type a few words to search")

    def test_whitespace_only_query_runs_no_query(self):
        make_article(self.hub, self.author, slug="some-guide", title="Some Guide")
        response = self.search("   ")
        self.assertNotContains(response, "Some Guide")
        self.assertContains(response, "Type a few words to search")

    def test_no_results_shows_helpful_message(self):
        response = self.search("doesnotexistanywhere")
        self.assertContains(response, "No results found")

    def test_results_are_paginated(self):
        for i in range(15):
            make_article(
                self.hub,
                self.author,
                slug=f"keyboard-guide-{i}",
                title=f"Keyboard Guide {i}",
            )
        page_one = self.search("keyboard")
        self.assertEqual(len(page_one.context["search_results"]), 10)
        page_two = self.client.get(reverse("search"), {"query": "keyboard", "page": 2})
        self.assertEqual(len(page_two.context["search_results"]), 5)

    def test_search_results_are_noindex_follow(self):
        response = self.search("keyboard")
        self.assertContains(response, 'content="noindex,follow"')

    def test_category_introduction_is_indexed(self):
        hub = make_category(
            title="Desk Setup",
            slug="desk-setup",
            mode="force_show",
        )
        hub.introduction = "<p>Guides for a productive home office setup.</p>"
        hub.save()
        response = self.search("productive")
        self.assertContains(response, "Desk Setup")
