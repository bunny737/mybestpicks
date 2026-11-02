"""
Site-wide navigation context (module 02).

Both values are lazy: nothing is queried unless a template actually uses them, so
the Wagtail admin and non-HTML responses pay no cost. Categories come only from
``CategoryPage.objects.discoverable()`` (CLAUDE.md invariant 5); ``show_in_menus`` is
used for the footer pages only, and never for category hubs.
"""

from django.utils.functional import SimpleLazyObject
from wagtail.models import Site

from editorial.models import CategoryPage, StandardPage


def _site_root(request):
    site = Site.find_for_request(request)
    return site.root_page if site else None


def _nav_categories(request):
    root = _site_root(request)
    if root is None:
        return []
    # Page tree order, so editors control the menu order by dragging pages.
    categories = list(CategoryPage.objects.child_of(root).discoverable())
    for category in categories:
        url = category.get_url(request)
        category.nav_current = bool(url) and request.path.startswith(url)
    return categories


def _footer_pages(request):
    root = _site_root(request)
    if root is None:
        return []
    return list(
        StandardPage.objects.child_of(root).live().public().in_menu(),
    )


def site_navigation(request):
    return {
        "nav_categories": SimpleLazyObject(lambda: _nav_categories(request)),
        "footer_pages": SimpleLazyObject(lambda: _footer_pages(request)),
    }
