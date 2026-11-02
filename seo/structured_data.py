import json
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

SITE_DESCRIPTION = (
    "Independent buying guides and honest comparisons for shoppers in India."
)


def public_url(path):
    base = urlsplit(settings.SITE_URL)
    return urlunsplit((base.scheme, base.netloc, path, "", ""))


def page_description(page):
    if not hasattr(page, "search_description"):
        return SITE_DESCRIPTION
    if page.search_description:
        return page.search_description
    for field in ("excerpt", "hero_text", "introduction", "expertise", "intro", "body"):
        value = getattr(page, field, "")
        if value:
            return Truncator(strip_tags(str(value))).chars(160)
    return SITE_DESCRIPTION


def _breadcrumb_data(page):
    from editorial.models import ArticlePage, CategoryPage

    if not isinstance(page, (ArticlePage, CategoryPage)):
        return None
    crumbs = [("Home", public_url("/"))]
    if isinstance(page, ArticlePage):
        category = page.category
        crumbs.append((category.title, public_url(category.url)))
    crumbs.append((page.title, public_url(page.url)))
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "name": name,
                "item": url,
            }
            for position, (name, url) in enumerate(crumbs, start=1)
        ],
    }


def structured_data(page):
    from editorial.models import ArticlePage

    graph = []
    breadcrumb = _breadcrumb_data(page)
    if breadcrumb:
        graph.append(breadcrumb)
    if isinstance(page, ArticlePage):
        article = {
            "@type": "BlogPosting",
            "headline": page.title,
            "description": page_description(page),
            "mainEntityOfPage": public_url(page.url),
            "author": {
                "@type": "Person",
                "name": page.author.title,
                "url": public_url(page.author.url),
            },
            "publisher": {
                "@type": "Organization",
                "name": "MyBestPicks",
                "url": public_url("/"),
            },
        }
        if page.first_published_at:
            article["datePublished"] = page.first_published_at.isoformat()
        if page.last_published_at:
            article["dateModified"] = page.last_published_at.isoformat()
        if page.featured_image:
            article["image"] = public_url(page.featured_image.file.url)
        graph.insert(0, article)
    if not graph:
        return None
    return {"@context": "https://schema.org", "@graph": graph}


def structured_data_script(page):
    data = structured_data(page)
    if data is None:
        return ""
    # Escape characters that could terminate a script element while retaining JSON.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e")
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')
