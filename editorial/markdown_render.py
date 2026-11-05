"""
Server-side markdown (and HTML) for the article ``markdown`` block.

Pasted text is untrusted, so the output is cleaned against an allowlist after
markdown is converted: only simple text, list, link and table tags survive, every
attribute except a few on links and table cells is removed, scripts, styles and
embeds are dropped with their contents, images are dropped (every image needs
recorded provenance, CLAUDE.md invariant 8), links may only be http(s), mailto,
relative or in-page, and H1 becomes H2 because the page title is always the H1.
"""

from urllib.parse import urlsplit

import markdown
from bs4 import BeautifulSoup
from bs4.element import PreformattedString
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from catalog.validators import validate_affiliate_url

SAFE_LINK_SCHEMES = ("http://", "https://", "mailto:", "/", "#")

ALLOWED_TAGS = {
    "p", "br", "hr",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "b", "em", "i", "u", "del", "s", "sub", "sup", "small", "code", "pre",
    "blockquote", "ul", "ol", "li",
    "a",
    "table", "caption", "thead", "tbody", "tfoot", "tr", "th", "td",
}  # fmt: skip

# Removed together with everything inside them; other unknown tags keep their text.
DROP_WITH_CONTENT = {
    "script", "style", "iframe", "object", "embed", "applet", "noscript", "template",
    "svg", "math", "form", "textarea", "select", "option", "button", "head", "title",
    "img", "picture", "video", "audio", "source", "track", "canvas", "link", "meta",
}  # fmt: skip

ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "th": {"colspan", "rowspan", "scope"},
    "td": {"colspan", "rowspan", "scope"},
}


def _new_converter():
    md = markdown.Markdown(extensions=["tables", "sane_lists"])
    for name in ("image_link", "image_reference", "short_image_ref"):
        md.inlinePatterns.deregister(name)
    return md


def _clean_attributes(tag):
    allowed = ALLOWED_ATTRIBUTES.get(tag.name, set())
    for name in list(tag.attrs):
        if name not in allowed:
            del tag[name]
    for name in ("colspan", "rowspan"):
        if name in tag.attrs and not str(tag[name]).strip().isdigit():
            del tag[name]


def _sanitise(soup):
    for node in soup.find_all(string=lambda s: isinstance(s, PreformattedString)):
        node.extract()  # comments, CDATA, doctype, processing instructions

    for tag in soup.find_all(True):
        if tag.decomposed:
            continue
        if tag.name in DROP_WITH_CONTENT:
            tag.decompose()

    for tag in soup.find_all(True):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()
        else:
            _clean_attributes(tag)


def _link_host(href):
    try:
        return (urlsplit(href).hostname or "").lower()
    except ValueError:
        return ""


def _is_alone_in_paragraph(link):
    """True when ``link`` is the only content of its own ``<p>`` (a line by itself)."""
    paragraph = link.parent
    if paragraph is None or paragraph.name != "p":
        return False
    others = [
        child
        for child in paragraph.children
        if child is not link and (getattr(child, "name", None) or str(child).strip())
    ]
    return not others


def _style_as_button(link):
    """Our own button classes; pasted classes and styles are never kept."""
    link["class"] = ["btn", "btn-primary"]
    link.parent["class"] = ["my-3"]


def render_markdown_with_links(text, affiliate_hosts=None):
    """
    Render ``text`` and report whether it holds an affiliate link.

    ``affiliate_hosts`` is the set of tracking hostnames merchants may use
    (``Merchant.allowed_link_domains``, invariant 6). A link to one of them must be
    a clean https URL and then gets ``rel="sponsored nofollow noopener"``; if it is
    not (for example plain http) it is unwrapped to text, never published unmarked.
    The host is only compared as text: nothing is fetched or resolved.

    Affiliate links open in a new tab (``target="_blank"``, set here, never taken
    from the pasted text; ``noopener`` is already in their ``rel``).

    An affiliate link that sits alone in its paragraph (a line by itself) renders as
    a button, styled with our own classes. A link inside a sentence stays a text
    link, and only affiliate links are ever styled as buttons.

    Returns ``(html, has_affiliate_links)``.
    """
    affiliate_hosts = {h.lower() for h in (affiliate_hosts or ())}
    has_affiliate_links = False

    html = _new_converter().convert(text or "")
    soup = BeautifulSoup(html, "html.parser")
    _sanitise(soup)

    for link in soup.find_all("a"):
        href = (link.get("href") or "").strip()
        if not href.lower().startswith(SAFE_LINK_SCHEMES):
            link.unwrap()
            continue
        if href.lower().startswith(("http://", "https://")):
            if _link_host(href) in affiliate_hosts:
                try:
                    validate_affiliate_url(href, affiliate_hosts)
                except ValidationError:
                    link.unwrap()
                    continue
                link["rel"] = "sponsored nofollow noopener"
                link["target"] = "_blank"  # ours, never copied from pasted HTML
                has_affiliate_links = True
                if _is_alone_in_paragraph(link):
                    _style_as_button(link)
            else:
                link["rel"] = "noopener"

    for heading in soup.find_all("h1"):
        heading.name = "h2"

    for header_cell in soup.select("thead th"):
        header_cell["scope"] = "col"

    for table in soup.find_all("table"):
        table["class"] = ["table", "table-bordered", "align-middle", "mb-0"]
        wrapper = soup.new_tag("div", attrs={"class": "table-scroll my-4"})
        table.wrap(wrapper)

    return mark_safe(str(soup)), has_affiliate_links  # noqa: S308 - sanitised above


def render_markdown(text, affiliate_hosts=None):
    return render_markdown_with_links(text, affiliate_hosts)[0]
