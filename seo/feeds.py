from django.conf import settings
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed

from editorial.models import ArticlePage


def canonical_page_url(page):
    return f"{settings.SITE_URL.rstrip('/')}{page.url}"


class ArticleFeed(Feed):
    feed_type = Rss201rev2Feed
    title = "MyBestPicks guides"
    description = "Independent buying guides and honest comparisons for India."
    link = "/feed/"

    def items(self):
        return (
            ArticlePage.objects.live()
            .public()
            .select_related("author")
            .order_by("-first_published_at")[:20]
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_link(self, item):
        return canonical_page_url(item)

    def item_author_name(self, item):
        return item.author.title

    def item_pubdate(self, item):
        return item.first_published_at

    def item_updateddate(self, item):
        return item.last_published_at
