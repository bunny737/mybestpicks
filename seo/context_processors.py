from urllib.parse import urlsplit, urlunsplit

from django.conf import settings


def _public_url(path):
    base = urlsplit(settings.SITE_URL)
    return urlunsplit((base.scheme, base.netloc, path, "", ""))


def seo_defaults(request):
    """Stable public URLs: never allow query strings into canonical/feed links."""
    return {
        "canonical_url": _public_url(request.path),
        "rss_feed_url": _public_url("/feed/"),
    }
