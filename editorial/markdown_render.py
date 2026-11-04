"""
Server-side markdown for the article ``markdown`` block.

Pasted markdown is untrusted text, so this is deliberately narrow: raw HTML is
escaped (not parsed), images are dropped (every image needs recorded provenance,
CLAUDE.md invariant 8), links may only be http(s), mailto, relative or in-page, and
H1 becomes H2 because the page title is always the H1.
"""

import markdown
from bs4 import BeautifulSoup
from django.utils.safestring import mark_safe

SAFE_LINK_SCHEMES = ("http://", "https://", "mailto:", "/", "#")


def _new_converter():
    md = markdown.Markdown(extensions=["tables", "sane_lists"])
    md.preprocessors.deregister("html_block")
    for name in ("html", "image_link", "image_reference", "short_image_ref"):
        md.inlinePatterns.deregister(name)
    return md


def render_markdown(text):
    html = _new_converter().convert(text or "")
    soup = BeautifulSoup(html, "html.parser")

    for img in soup.find_all("img"):
        img.decompose()

    for link in soup.find_all("a"):
        href = (link.get("href") or "").strip()
        if not href.lower().startswith(SAFE_LINK_SCHEMES):
            link.unwrap()
            continue
        if href.lower().startswith(("http://", "https://")):
            link["rel"] = "noopener"

    for heading in soup.find_all("h1"):
        heading.name = "h2"

    for header_cell in soup.select("thead th"):
        header_cell["scope"] = "col"

    for table in soup.find_all("table"):
        table["class"] = ["table", "table-bordered", "align-middle", "mb-0"]
        wrapper = soup.new_tag("div", attrs={"class": "table-scroll my-4"})
        table.wrap(wrapper)

    return mark_safe(str(soup))  # noqa: S308 - sanitised above
