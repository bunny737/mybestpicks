"""URL safety for affiliate links (CLAUDE.md invariant 6). Strings only, no network."""

import socket
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from catalog.validators import (
    parse_allowed_hosts,
    validate_affiliate_url,
    validate_destination_url,
    validate_hostname,
    validate_https_url,
)

ALLOWED = {"track.example.test"}


def rejects(func, *args):
    with mock.patch.object(socket, "getaddrinfo", side_effect=AssertionError("DNS!")):
        with mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network!")
        ):
            try:
                func(*args)
            except ValidationError:
                return True
    return False


class AffiliateUrlTests(SimpleTestCase):
    def test_a_good_link_on_an_allowed_host_passes(self):
        url = "https://track.example.test/c/abc?cid=42&sub=desk"
        self.assertEqual(validate_affiliate_url(url, ALLOWED), url)

    def test_https_is_required(self):
        for url in (
            "http://track.example.test/x",
            "ftp://track.example.test/x",
            "javascript:alert(1)",
            "//track.example.test/x",
            "track.example.test/x",
        ):
            with self.subTest(url=url):
                self.assertTrue(rejects(validate_affiliate_url, url, ALLOWED))

    def test_the_tracking_host_must_be_allowlisted_not_the_retailer(self):
        # A Cuelinks-style link has the *tracker's* host, not the retailer's.
        self.assertTrue(
            rejects(validate_affiliate_url, "https://shopmart.test/p/1", ALLOWED)
        )
        self.assertTrue(
            rejects(validate_affiliate_url, "https://evil.example.test/x", ALLOWED)
        )

    def test_matching_is_exact_so_subdomains_and_suffixes_are_rejected(self):
        for host in (
            "sub.track.example.test",
            "track.example.test.evil.test",
            "xtrack.example.test",
            "example.test",
        ):
            with self.subTest(host=host):
                self.assertTrue(
                    rejects(validate_affiliate_url, f"https://{host}/x", ALLOWED)
                )

    def test_the_host_comparison_ignores_case(self):
        validate_affiliate_url("https://TRACK.Example.TEST/x", {"Track.Example.Test"})

    def test_credentials_in_the_url_are_rejected(self):
        for url in (
            "https://user:pw@track.example.test/x",
            "https://user@track.example.test/x",
            "https://track.example.test@evil.test/x",
            "https://evil.test#@track.example.test/x",
        ):
            with self.subTest(url=url):
                self.assertTrue(rejects(validate_affiliate_url, url, ALLOWED))

    def test_non_default_ports_are_rejected_but_443_is_fine(self):
        self.assertTrue(
            rejects(
                validate_affiliate_url, "https://track.example.test:8443/x", ALLOWED
            )
        )
        validate_affiliate_url("https://track.example.test:443/x", ALLOWED)

    def test_hidden_characters_and_backslashes_are_rejected(self):
        for url in (
            "https://track.example.test\\@evil.test/x",
            "https://track.example.test/x y",
            "https://track.example.test/x\n",
            " https://track.example.test/x",
            "https://track.example.test/\x00x",
        ):
            with self.subTest(url=repr(url)):
                self.assertTrue(rejects(validate_affiliate_url, url, ALLOWED))

    def test_credential_like_query_parameters_are_rejected(self):
        for name in ("password", "token", "Access_Token", "api_key", "sessionid"):
            with self.subTest(name=name):
                self.assertTrue(
                    rejects(
                        validate_affiliate_url,
                        f"https://track.example.test/x?{name}=abc",
                        ALLOWED,
                    )
                )

    def test_ordinary_tracking_parameters_are_allowed(self):
        validate_affiliate_url(
            "https://track.example.test/x?cid=1&utm_source=mbp&tag=site-21", ALLOWED
        )

    def test_empty_and_overlong_urls_are_rejected(self):
        self.assertTrue(rejects(validate_affiliate_url, "", ALLOWED))
        self.assertTrue(
            rejects(
                validate_affiliate_url,
                "https://track.example.test/" + "a" * 2000,
                ALLOWED,
            )
        )

    def test_an_empty_allowlist_rejects_everything(self):
        self.assertTrue(
            rejects(validate_affiliate_url, "https://track.example.test/x", set())
        )

    def test_ip_addresses_are_rejected_even_if_allowlisted(self):
        self.assertTrue(
            rejects(validate_affiliate_url, "https://127.0.0.1/x", {"127.0.0.1"})
        )
        self.assertTrue(
            rejects(
                validate_affiliate_url,
                "https://169.254.169.254/latest",
                {"169.254.169.254"},
            )
        )


class DestinationUrlTests(SimpleTestCase):
    def test_host_must_be_the_domain_or_a_subdomain(self):
        for ok in ("https://shopmart.test/p/1", "https://www.shopmart.test/p/1"):
            validate_destination_url(ok, "shopmart.test")
        for bad in (
            "https://evilshopmart.test/p/1",
            "https://shopmart.test.evil.test/p/1",
            "http://shopmart.test/p/1",
            "https://user@shopmart.test/p/1",
        ):
            with self.subTest(url=bad):
                self.assertTrue(rejects(validate_destination_url, bad, "shopmart.test"))


class HostnameTests(SimpleTestCase):
    def test_valid_hostnames(self):
        for host in ("flipkart.com", "track.example.test", "xn--bcher-kva.example"):
            validate_hostname(host)

    def test_invalid_hostnames(self):
        for host in (
            "",
            "localhost",  # single label
            "Flipkart.com",  # not lowercase
            "https://flipkart.com",
            "flipkart.com/path",
            "flipkart.com:443",
            "*.flipkart.com",
            "flip kart.com",
            "-bad.example.test",
            "under_score.example.test",
            "1.2.3.4",
            "a" * 64 + ".test",
        ):
            with self.subTest(host=host):
                self.assertTrue(rejects(validate_hostname, host))

    def test_parse_allowed_hosts_normalises_and_dedupes(self):
        text = "  Track.Example.Test \n\n other.example.test\ntrack.example.test\n"
        self.assertEqual(
            parse_allowed_hosts(text), ["track.example.test", "other.example.test"]
        )
        self.assertEqual(parse_allowed_hosts(""), [])
        self.assertEqual(parse_allowed_hosts(None), [])

    def test_parse_allowed_hosts_rejects_bad_lines(self):
        self.assertTrue(
            rejects(parse_allowed_hosts, "track.example.test\nhttps://bad.example.test")
        )


class HttpsUrlTests(SimpleTestCase):
    def test_brand_websites_must_be_https(self):
        validate_https_url("https://acme.test/")
        self.assertTrue(rejects(validate_https_url, "http://acme.test/"))
        self.assertTrue(rejects(validate_https_url, "https://"))
