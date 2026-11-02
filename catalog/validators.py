"""
URL and hostname validation for merchant offers (module 05, CLAUDE.md invariant 6).

Everything here parses strings only. It never opens a connection, never resolves a
name and never follows a redirect, so there is no SSRF surface (a server-side fetch of
an editor-supplied URL could be pointed at internal services).
"""

import ipaddress
import re
from urllib.parse import parse_qsl, urlsplit

from django.core.exceptions import ValidationError

MAX_URL_LENGTH = 2000

# A DNS name with at least two labels, lowercase. No scheme, port, path or wildcard.
_LABEL = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
_HOSTNAME_RE = re.compile(rf"^{_LABEL}(?:\.{_LABEL})+$")

# Whitespace, control characters and backslashes are used to disguise hosts
# (``https://good.example\@evil.example``), so they are rejected outright.
_UNSAFE_CHARS_RE = re.compile(r"[\s\x00-\x1f\x7f\\]")

# Query parameters that look like credentials or session state.
SUSPICIOUS_QUERY_PARAMS = frozenset(
    {
        "password",
        "passwd",
        "pwd",
        "pass",
        "token",
        "access_token",
        "auth",
        "authorization",
        "secret",
        "api_key",
        "apikey",
        "session",
        "sessionid",
        "sid",
    }
)


def validate_hostname(value):
    """A lowercase DNS hostname such as ``flipkart.com``; nothing else."""
    if not isinstance(value, str) or value != value.strip().lower():
        raise ValidationError("Use a lowercase hostname such as example.com.")
    if len(value) > 253 or not _HOSTNAME_RE.match(value):
        raise ValidationError(
            f"{value!r} is not a valid hostname. Use only the host, for example "
            "example.com: no https://, path, port or wildcard."
        )
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return value
    raise ValidationError("An IP address is not allowed; use a hostname.")


def parse_allowed_hosts(text):
    """
    Turn a merchant's one-hostname-per-line text into a list of unique hostnames.

    Lines are lower-cased and trimmed; blank lines are skipped. Raises
    ``ValidationError`` naming the first bad line.
    """
    hosts = []
    for line in (text or "").splitlines():
        host = line.strip().lower()
        if not host:
            continue
        validate_hostname(host)
        if host not in hosts:
            hosts.append(host)
    return hosts


def validate_https_url(value):
    """A plain https URL (used for brand websites)."""
    parts = _split(value)
    if parts.scheme != "https":
        raise ValidationError("Use an https:// URL.")
    if not parts.hostname:
        raise ValidationError("The URL has no host name.")


def _split(url):
    if not isinstance(url, str) or not url:
        raise ValidationError("Enter a URL.")
    if len(url) > MAX_URL_LENGTH:
        raise ValidationError(f"The URL is longer than {MAX_URL_LENGTH} characters.")
    if _UNSAFE_CHARS_RE.search(url):
        raise ValidationError(
            "The URL contains spaces, control characters or a backslash."
        )
    try:
        return urlsplit(url)
    except ValueError as exc:
        raise ValidationError(f"The URL is not valid ({exc}).") from exc


def _checked_https_host(url):
    """Shared checks for any URL we store: https, no userinfo, default port."""
    parts = _split(url)
    if parts.scheme != "https":
        raise ValidationError("Only https:// URLs are allowed.")
    if parts.username is not None or parts.password is not None or "@" in parts.netloc:
        raise ValidationError("The URL must not contain a username or password.")
    try:
        port = parts.port
    except ValueError as exc:
        raise ValidationError("The URL has an invalid port.") from exc
    if port not in (None, 443):
        raise ValidationError("The URL must use the default https port.")
    host = parts.hostname
    if not host:
        raise ValidationError("The URL has no host name.")
    try:
        validate_hostname(host)
    except ValidationError as exc:
        raise ValidationError(f"The URL host is not acceptable: {exc.message}") from exc
    return parts, host


def validate_affiliate_url(url, allowed_hosts):
    """
    Check an affiliate (tracking) link.

    The link's own **hostname** must be in ``allowed_hosts`` (the merchant's
    allowlist). The retailer's destination domain is not enough: a Cuelinks link has
    a Cuelinks host, not a Flipkart one. Matching is exact, so a subdomain of an
    allowed host is not allowed.
    """
    parts, host = _checked_https_host(url)
    allowed = {h.lower() for h in allowed_hosts}
    if host not in allowed:
        listed = ", ".join(sorted(allowed)) or "none set"
        raise ValidationError(
            f"{host} is not an allowed tracking host for this merchant "
            f"(allowed: {listed})."
        )
    for name, _ in parse_qsl(parts.query, keep_blank_values=True):
        if name.lower() in SUSPICIOUS_QUERY_PARAMS:
            raise ValidationError(
                f"The URL has a parameter named {name!r}, which looks like a "
                "credential or session value. Remove it."
            )
    return url


def validate_destination_url(url, destination_domain):
    """
    The retailer page a human should compare the offer against. Never fetched.

    The host must be the merchant's destination domain or one of its subdomains.
    """
    _, host = _checked_https_host(url)
    domain = (destination_domain or "").lower()
    if not domain or not (host == domain or host.endswith("." + domain)):
        raise ValidationError(
            f"The destination URL must be on {domain or 'the merchant domain'}."
        )
    return url
