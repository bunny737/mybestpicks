"""Small builders for page trees used in tests (module 10 grows these into fixtures)."""

from editorial.models import (
    ArticlePage,
    AuthorIndexPage,
    AuthorPage,
    CategoryPage,
    DiscoveryMode,
    StandardPage,
)
from home.models import HomePage


def get_home():
    # Always re-fetch: treebeard needs a fresh numchild/path to add children.
    return HomePage.objects.get(slug="home")


def make_author(name="Asha Rao", slug="asha-rao"):
    home = get_home()
    index = AuthorIndexPage.objects.first()
    if index is None:
        index = home.add_child(
            instance=AuthorIndexPage(title="Authors", slug="authors")
        )
    index = AuthorIndexPage.objects.get(pk=index.pk)
    return index.add_child(
        instance=AuthorPage(title=name, slug=slug, bio="<p>Writes about desks.</p>")
    )


def make_category(
    title="Developer Setup",
    slug="developer-setup",
    mode=DiscoveryMode.FORCE_HIDE,
    live=True,
):
    return get_home().add_child(
        instance=CategoryPage(title=title, slug=slug, discovery_mode=mode, live=live)
    )


def make_article(category, author, slug="best-keyboards", live=True, **fields):
    category = CategoryPage.objects.get(pk=category.pk)
    fields.setdefault("title", slug.replace("-", " ").title())
    fields.setdefault("excerpt", "A short summary.")
    return category.add_child(
        instance=ArticlePage(slug=slug, author=author, live=live, **fields)
    )


def make_articles(category, author, count, live=True, prefix="guide"):
    return [
        make_article(category, author, slug=f"{prefix}-{i}", live=live)
        for i in range(count)
    ]


def make_standard_page(title="About", slug="about"):
    # Six slugs (about, contact, editorial-policy, affiliate-disclosure,
    # privacy-policy, terms) already exist as unpublished drafts, seeded by
    # editorial/migrations/0004_seed_policy_pages.py. Reuse and publish one
    # rather than erroring on a duplicate slug.
    existing = StandardPage.objects.filter(slug=slug).first()
    if existing is not None:
        existing.title = title
        existing.live = True
        existing.save()
        return existing
    return get_home().add_child(
        instance=StandardPage(title=title, slug=slug, body="<p>Hello.</p>")
    )


# --- article body builders (module 04) -----------------------------------------


def card_block(product, block_id=None, **fields):
    """Raw StreamField data for a product card. Fields override the defaults."""
    value = {
        "product": product.pk,
        "verdict": "<p>A solid pick.</p>",
        "recommendation_label": "",
        "best_for": "",
        "pros": [],
        "cons": [],
        "tested_by_editor": False,
        "editorial_evidence": "",
        "evidence_media": None,
    }
    value.update(fields)
    block = {"type": "product_card", "value": value}
    if block_id:
        block["id"] = block_id
    return block


def table_block(positions=(), spec_keys=(), heading=""):
    return {
        "type": "comparison_table",
        "value": {
            "heading": heading,
            "card_positions": list(positions),
            "spec_keys": list(spec_keys),
        },
    }


class TempMediaMixin:
    """Keep image files and renditions made by a test out of the real media folder."""

    def setUp(self):
        import shutil
        import tempfile

        from django.test import override_settings

        super().setUp()
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        override = override_settings(MEDIA_ROOT=media)
        override.enable()
        self.addCleanup(override.disable)
