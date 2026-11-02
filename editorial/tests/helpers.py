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
    return get_home().add_child(
        instance=StandardPage(title=title, slug=slug, body="<p>Hello.</p>")
    )
