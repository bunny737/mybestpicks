from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
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


def has_ad_consent(request):
    """
    Consent gate for advertising cookies & third-party AdSense scripts.
    Privacy by default (CLAUDE.md Invariant 9).
    Requires explicit consent cookie ('ads_consent=granted') or request flag.
    """
    if getattr(request, "ad_consent_granted", False):
        return True
    return request.COOKIES.get("ads_consent") == "granted"


def is_page_ad_eligible(request):
    """
    Determine whether the current request path is eligible for AdSense.
    Google AdSense site-optimization policy strictly forbids ads on:
    - Non-content pages (search, error pages, login, policy/terms pages)
    - Previews, drafts, thin or unpopulated hubs
    """
    if getattr(request, "in_preview_panel", False):
        return False

    path = request.path_info or request.path
    disallowed_prefixes = (
        "/admin/",
        "/django-admin/",
        "/search/",
        "/documents/",
        "/feed/",
    )
    if any(path.startswith(prefix) for prefix in disallowed_prefixes):
        return False

    return True


def _get_adsense_config(request):
    """
    Collects AdSense settings with correct precedence:
    SiteSettings (Wagtail admin) takes precedence over environment fallback.
    Catches only expected lookup errors; programming errors remain visible.
    """
    from home.models import SiteSettings

    pub_id = getattr(settings, "ADSENSE_PUBLISHER_ID", "").strip()
    enabled = getattr(settings, "ADSENSE_ENABLED", False)
    auto_ads = getattr(settings, "ADSENSE_AUTO_ADS", False)
    in_article_slot_id = getattr(settings, "ADSENSE_IN_ARTICLE_SLOT_ID", "").strip()
    feed_slot_id = getattr(settings, "ADSENSE_FEED_SLOT_ID", "").strip()

    site = Site.find_for_request(request)
    if site:
        try:
            site_setting = SiteSettings.for_site(site)
            # Per-site enabled switch and publisher ID
            if site_setting.adsense_publisher_id:
                pub_id = site_setting.adsense_publisher_id.strip()
            # The Wagtail admin switches always govern if the record exists
            enabled = site_setting.adsense_enabled
            auto_ads = site_setting.adsense_auto_ads
            if site_setting.adsense_in_article_slot_id:
                in_article_slot_id = site_setting.adsense_in_article_slot_id.strip()
            if site_setting.adsense_feed_slot_id:
                feed_slot_id = site_setting.adsense_feed_slot_id.strip()
        except ObjectDoesNotExist, AttributeError:
            pass

    client_id = pub_id
    if pub_id and not client_id.startswith("ca-"):
        client_id = f"ca-{client_id}"

    consent = has_ad_consent(request)
    eligible = enabled and bool(client_id) and consent and is_page_ad_eligible(request)

    return {
        "publisher_id": pub_id,
        "client_id": client_id,
        "enabled": enabled,
        "auto_ads": auto_ads,
        "in_article_slot_id": in_article_slot_id,
        "feed_slot_id": feed_slot_id,
        "consent_granted": consent,
        "is_ad_eligible": eligible,
    }


def site_navigation(request):
    adsense_config = SimpleLazyObject(lambda: _get_adsense_config(request))
    return {
        "nav_categories": SimpleLazyObject(lambda: _nav_categories(request)),
        "footer_pages": SimpleLazyObject(lambda: _footer_pages(request)),
        "adsense_publisher_id": SimpleLazyObject(
            lambda: adsense_config["publisher_id"]
        ),
        "adsense_client_id": SimpleLazyObject(lambda: adsense_config["client_id"]),
        "adsense_enabled": SimpleLazyObject(lambda: adsense_config["enabled"]),
        "adsense_auto_ads": SimpleLazyObject(lambda: adsense_config["auto_ads"]),
        "adsense_in_article_slot_id": SimpleLazyObject(
            lambda: adsense_config["in_article_slot_id"]
        ),
        "adsense_feed_slot_id": SimpleLazyObject(
            lambda: adsense_config["feed_slot_id"]
        ),
        "adsense_consent_granted": SimpleLazyObject(
            lambda: adsense_config["consent_granted"]
        ),
        "adsense_is_eligible": SimpleLazyObject(
            lambda: adsense_config["is_ad_eligible"]
        ),
    }
