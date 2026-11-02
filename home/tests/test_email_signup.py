"""
Module 06 (MBP-006): double opt-in email signup. Collects only email + consent
metadata (CLAUDE.md invariant 9), confirms before counting as subscribed, and
lets a subscriber delete themselves with one click.
"""

from django.core import mail
from django.test import TestCase, override_settings

from editorial.models import StandardPage
from home.models import EmailSubscriber


class SubscribeTests(TestCase):
    def post(self, **data):
        data.setdefault("next", "/")
        return self.client.post("/subscribe/", data)

    def test_valid_signup_creates_an_unconfirmed_subscriber(self):
        self.post(email="reader@example.test", consent="on")
        subscriber = EmailSubscriber.objects.get(email="reader@example.test")
        self.assertIsNone(subscriber.confirmed_at)
        self.assertIsNotNone(subscriber.consented_at)
        self.assertTrue(subscriber.unsubscribe_token)

    @override_settings(EMAIL_CONSENT_TEXT_VERSION="2099-01-01")
    def test_consent_text_version_is_recorded_from_settings(self):
        self.post(email="reader@example.test", consent="on")
        subscriber = EmailSubscriber.objects.get(email="reader@example.test")
        self.assertEqual(subscriber.consent_text_version, "2099-01-01")

    def test_valid_signup_sends_a_confirmation_email_with_a_working_link(self):
        self.post(email="reader@example.test", consent="on")
        self.assertEqual(len(mail.outbox), 1)
        subscriber = EmailSubscriber.objects.get(email="reader@example.test")
        self.assertIn(subscriber.unsubscribe_token, mail.outbox[0].body)

    def test_signup_without_consent_creates_no_subscriber(self):
        response = self.post(email="reader@example.test")
        self.assertEqual(EmailSubscriber.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        self.assertRedirects(response, "/")

    def test_signup_with_an_invalid_email_creates_no_subscriber(self):
        self.post(email="not-an-email", consent="on")
        self.assertEqual(EmailSubscriber.objects.count(), 0)

    def test_resubscribing_the_same_email_does_not_duplicate(self):
        self.post(email="reader@example.test", consent="on")
        self.post(email="reader@example.test", consent="on")
        self.assertEqual(EmailSubscriber.objects.count(), 1)

    def test_resubscribing_after_confirmation_does_not_resend_the_email(self):
        self.post(email="reader@example.test", consent="on")
        subscriber = EmailSubscriber.objects.get(email="reader@example.test")
        self.client.get(f"/subscribe/confirm/{subscriber.unsubscribe_token}/")

        self.post(email="reader@example.test", consent="on")

        self.assertEqual(len(mail.outbox), 1)

    def test_redirect_only_goes_to_a_same_site_path(self):
        response = self.post(
            email="reader@example.test", consent="on", next="https://evil.test/"
        )
        self.assertRedirects(response, "/")

    def test_redirect_rejects_a_protocol_relative_next(self):
        response = self.post(
            email="reader@example.test", consent="on", next="//evil.test/"
        )
        self.assertRedirects(response, "/")

    def test_get_is_not_allowed(self):
        response = self.client.get("/subscribe/")
        self.assertEqual(response.status_code, 405)

    def test_footer_signup_form_renders_on_every_page(self):
        response = self.client.get("/")
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="consent"')

    def test_footer_links_to_the_privacy_policy_page_once_it_exists(self):
        response = self.client.get("/")
        self.assertNotContains(response, "Read our")

        privacy_page = StandardPage.objects.get(slug="privacy-policy")
        privacy_page.live = True
        privacy_page.save()
        response = self.client.get("/")
        self.assertContains(response, f'href="{privacy_page.url}"')


class ConfirmTests(TestCase):
    def setUp(self):
        self.client.post(
            "/subscribe/", {"email": "reader@example.test", "consent": "on"}
        )
        self.subscriber = EmailSubscriber.objects.get(email="reader@example.test")

    def test_visiting_the_confirm_link_marks_the_subscriber_confirmed(self):
        response = self.client.get(
            f"/subscribe/confirm/{self.subscriber.unsubscribe_token}/"
        )
        self.assertEqual(response.status_code, 200)
        self.subscriber.refresh_from_db()
        self.assertIsNotNone(self.subscriber.confirmed_at)

    def test_an_unknown_token_404s(self):
        response = self.client.get("/subscribe/confirm/does-not-exist/")
        self.assertEqual(response.status_code, 404)

    def test_confirming_twice_keeps_the_first_confirmation_time(self):
        self.client.get(f"/subscribe/confirm/{self.subscriber.unsubscribe_token}/")
        self.subscriber.refresh_from_db()
        first_confirmed_at = self.subscriber.confirmed_at

        self.client.get(f"/subscribe/confirm/{self.subscriber.unsubscribe_token}/")
        self.subscriber.refresh_from_db()
        self.assertEqual(self.subscriber.confirmed_at, first_confirmed_at)


class UnsubscribeTests(TestCase):
    def setUp(self):
        self.client.post(
            "/subscribe/", {"email": "reader@example.test", "consent": "on"}
        )
        self.subscriber = EmailSubscriber.objects.get(email="reader@example.test")
        self.url = f"/subscribe/unsubscribe/{self.subscriber.unsubscribe_token}/"

    def test_get_shows_a_confirmation_page_without_deleting(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(EmailSubscriber.objects.filter(pk=self.subscriber.pk).exists())

    def test_post_deletes_the_subscriber(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(EmailSubscriber.objects.filter(pk=self.subscriber.pk).exists())

    def test_an_unknown_token_404s(self):
        response = self.client.post("/subscribe/unsubscribe/does-not-exist/")
        self.assertEqual(response.status_code, 404)
