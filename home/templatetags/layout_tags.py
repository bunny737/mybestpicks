from django import template
from wagtail.models import Site

register = template.Library()


@register.inclusion_tag("components/breadcrumbs.html", takes_context=True)
def breadcrumbs(context):
    """Home > ancestors > current page. Renders nothing on the home page itself."""
    request = context.get("request")
    page = context.get("page")
    site = Site.find_for_request(request) if request else None
    if page is None or site is None or page.depth <= site.root_page.depth:
        return {"show": False}
    ancestors = page.get_ancestors().filter(depth__gt=site.root_page.depth).live()
    return {
        "show": True,
        "request": request,
        "home": site.root_page,
        "ancestors": ancestors,
        "page": page,
    }
