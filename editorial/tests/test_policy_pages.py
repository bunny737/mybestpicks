"""
Module 06: the six standing policy pages are seeded by
editorial/migrations/0004_seed_policy_pages.py as unpublished drafts, so they
exist for the owner to review and publish, and so the slug lookups elsewhere
(``affiliate_disclosure_page``, ``privacy_policy_page``, the Contact page) have
something to find once they are.
"""

from django.test import TestCase
from wagtail.models import Site

from editorial.models import StandardPage
from home.models import SiteSettings

EXPECTED_SLUGS = {
    "about",
    "contact",
    "editorial-policy",
    "affiliate-disclosure",
    "privacy-policy",
    "terms",
}


class SeededPolicyPageTests(TestCase):
    def test_all_six_policy_pages_exist_as_unpublished_drafts(self):
        slugs = set(
            StandardPage.objects.filter(slug__in=EXPECTED_SLUGS).values_list(
                "slug", flat=True
            )
        )
        self.assertEqual(slugs, EXPECTED_SLUGS)
        for page in StandardPage.objects.filter(slug__in=EXPECTED_SLUGS):
            self.assertFalse(page.live, f"{page.slug} should start unpublished")
            self.assertTrue(page.show_in_menus)

    def test_no_seed_placeholder_is_left_in_any_page_body(self):
        for page in StandardPage.objects.filter(slug__in=EXPECTED_SLUGS):
            self.assertNotIn("__", page.body)

    def test_cross_links_resolve_to_real_published_pages_once_live(self):
        for page in StandardPage.objects.filter(slug__in=EXPECTED_SLUGS):
            page.live = True
            page.save()

        about = StandardPage.objects.get(slug="about")
        response = self.client.get(about.url)
        self.assertEqual(response.status_code, 200)
        editorial_policy = StandardPage.objects.get(slug="editorial-policy")
        self.assertContains(response, f'href="{editorial_policy.url}"')


class ContactPageTests(TestCase):
    def setUp(self):
        self.contact = StandardPage.objects.get(slug="contact")
        self.contact.live = True
        self.contact.save()

    def test_no_contact_email_configured_shows_no_mailto_link(self):
        response = self.client.get(self.contact.url)
        self.assertNotContains(response, "mailto:")

    def test_configured_contact_email_renders_as_a_mailto_link(self):
        site = Site.objects.get(is_default_site=True)
        settings_obj = SiteSettings.for_site(site)
        settings_obj.contact_email = "hello@mybestpicks.in"
        settings_obj.save()

        response = self.client.get(self.contact.url)
        self.assertContains(response, 'href="mailto:hello@mybestpicks.in"')

    def test_contact_email_never_appears_on_other_standard_pages(self):
        site = Site.objects.get(is_default_site=True)
        settings_obj = SiteSettings.for_site(site)
        settings_obj.contact_email = "hello@mybestpicks.in"
        settings_obj.save()

        about = StandardPage.objects.get(slug="about")
        about.live = True
        about.save()
        response = self.client.get(about.url)
        self.assertNotContains(response, "mailto:")


class PrivacyPolicyFooterLinkTests(TestCase):
    def test_footer_links_to_privacy_policy_once_published(self):
        response = self.client.get("/")
        self.assertNotContains(response, "Read our")

        privacy = StandardPage.objects.get(slug="privacy-policy")
        privacy.live = True
        privacy.save()

        response = self.client.get("/")
        self.assertContains(response, f'href="{privacy.url}"')
