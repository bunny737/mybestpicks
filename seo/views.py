from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def robots_txt(request):
    sitemap_url = f"{settings.SITE_URL.rstrip('/')}/sitemap.xml"
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /django-admin/",
        "Disallow: /search/",
        "Disallow: /subscribe/",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


@require_GET
def ads_txt(request):
    """
    Standard ads.txt endpoint required for Google AdSense verification.
    Google requires: google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
    """
    from wagtail.models import Site

    from home.models import SiteSettings

    pub_id = getattr(settings, "ADSENSE_PUBLISHER_ID", "").strip()
    custom_lines = ""

    site = Site.find_for_request(request)
    if site:
        try:
            site_setting = SiteSettings.for_site(site)
            if site_setting.adsense_publisher_id:
                pub_id = site_setting.adsense_publisher_id.strip()
            if site_setting.ads_txt_custom:
                custom_lines = site_setting.ads_txt_custom.strip()
        except ObjectDoesNotExist, AttributeError:
            pass

    lines = []
    if pub_id:
        clean_pub = pub_id[3:] if pub_id.startswith("ca-") else pub_id
        if not clean_pub.startswith("pub-"):
            clean_pub = f"pub-{clean_pub}"
        lines.append(f"google.com, {clean_pub}, DIRECT, f08c47fec0942fa0")

    if custom_lines:
        lines.append(custom_lines)

    if not lines:
        lines.append(
            "# Google AdSense ads.txt. Configure ADSENSE_PUBLISHER_ID to activate."
        )

    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
