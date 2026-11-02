from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from wagtail.contrib.sitemaps.sitemap_generator import Sitemap


class PublicSitemap(Sitemap):
    """Wagtail sitemap whose locations use the configured canonical origin."""

    def _urls(self, page, protocol, domain):
        urls = super()._urls(page, protocol, domain)
        origin = urlsplit(settings.SITE_URL)
        for item in urls:
            current = urlsplit(item["location"])
            item["location"] = urlunsplit(
                (origin.scheme, origin.netloc, current.path, "", "")
            )
        return urls
