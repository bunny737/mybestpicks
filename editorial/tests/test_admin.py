"""The Wagtail admin forms for every page type must build (bad panels fail here)."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from editorial.models import AuthorIndexPage, DiscoveryMode

from .helpers import (
    get_home,
    make_article,
    make_author,
    make_category,
    make_standard_page,
)


class AdminFormSmokeTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_superuser(
            "editor", "editor@example.com", "pw"
        )
        self.client.force_login(user)
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.article = make_article(self.hub, self.author)
        self.about = make_standard_page()

    def assertAdminOk(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
        return response

    def test_edit_forms_render_for_every_page_type(self):
        pages = [
            get_home(),
            self.hub,
            self.article,
            self.author,
            AuthorIndexPage.objects.get(),
            self.about,
        ]
        for page in pages:
            with self.subTest(page=type(page.specific).__name__):
                self.assertAdminOk(reverse("wagtailadmin_pages:edit", args=(page.pk,)))

    def test_add_forms_render_under_the_allowed_parents(self):
        cases = [
            ("editorial", "categorypage", get_home().pk),
            ("editorial", "articlepage", self.hub.pk),
            ("editorial", "authorpage", AuthorIndexPage.objects.get().pk),
            ("editorial", "standardpage", get_home().pk),
        ]
        for app, model, parent_pk in cases:
            with self.subTest(model=model):
                self.assertAdminOk(
                    reverse("wagtailadmin_pages:add", args=(app, model, parent_pk))
                )

    def test_discovery_mode_is_editable_in_the_settings_tab(self):
        response = self.assertAdminOk(
            reverse("wagtailadmin_pages:edit", args=(self.hub.pk,))
        )
        self.assertContains(response, "discovery_mode")
