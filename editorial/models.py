"""
Page models for the editorial site: category hubs, articles, authors, policy pages.

Visibility of a category hub is decided by ``discovery_mode`` only (CLAUDE.md
invariant 5). Everything that lists or indexes hubs (navigation, homepage tiles,
the sitemap, robots meta) goes through ``CategoryPage.objects.discoverable()`` or
``CategoryPage.is_discoverable``.
"""

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.db.models import Count, F, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page, PageManager
from wagtail.query import PageQuerySet
from wagtail.search import index

from catalog.provenance import ImageProvenance, validate_image_provenance

from .blocks import ArticleBody
from .rendering import render_markdown_blocks, resolve_article_products

# A hub in "auto" mode is discoverable once it has this many live articles.
DISCOVERY_AUTO_MIN_ARTICLES = 3


class DiscoveryMode(models.TextChoices):
    AUTO = "auto", f"Auto ({DISCOVERY_AUTO_MIN_ARTICLES}+ live articles)"
    FORCE_SHOW = "force_show", "Always show"
    FORCE_HIDE = "force_hide", "Always hide"


class ArticleKind(models.TextChoices):
    BUYING_GUIDE = "buying_guide", "Buying guide"
    COMPARISON = "comparison", "Comparison"
    EXPLAINER = "explainer", "Explainer"
    TUTORIAL = "tutorial", "Tutorial"


# --- Authors -----------------------------------------------------------------


class AuthorIndexPage(Page):
    """Lives at /authors/ and holds the AuthorPages."""

    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = ["editorial.AuthorPage"]

    intro = RichTextField(blank=True)

    content_panels = [*Page.content_panels, FieldPanel("intro")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["authors"] = AuthorPage.objects.child_of(self).live().order_by("title")
        return context


class AuthorPage(Page):
    """An editor or writer. The page title is the author's name."""

    parent_page_types = ["editorial.AuthorIndexPage"]
    subpage_types = []

    bio = RichTextField()
    expertise = models.CharField(max_length=255, blank=True)
    experience = RichTextField(
        blank=True,
        help_text="Research and hands-on testing experience, stated honestly.",
    )
    photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Use your own photo.",
    )

    content_panels = [
        *Page.content_panels,
        FieldPanel("photo"),
        FieldPanel("bio"),
        FieldPanel("expertise"),
        FieldPanel("experience"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["articles"] = (
            ArticlePage.objects.filter(author=self)
            .live()
            .order_by(F("first_published_at").desc(nulls_last=True))
        )
        return context


# --- Articles ----------------------------------------------------------------


class ArticlePageTag(TaggedItemBase):
    content_object = ParentalKey(
        "editorial.ArticlePage", related_name="tagged_items", on_delete=models.CASCADE
    )


class SourceType(models.TextChoices):
    MANUFACTURER = "manufacturer", "Manufacturer spec or page"
    DATASHEET = "datasheet", "Standard or datasheet"
    REVIEW = "review", "Independent review"
    RETAILER = "retailer", "Retailer listing (for fact-checking only)"
    OTHER = "other", "Other"


class ArticleSource(Orderable):
    """
    A source consulted for an article, kept for the research audit. Private unless
    ``is_public`` is ticked, in which case it is listed under the article's sources.
    """

    article = ParentalKey(
        "editorial.ArticlePage", related_name="sources", on_delete=models.CASCADE
    )
    source_name = models.CharField(max_length=200)
    url = models.URLField(
        max_length=2000, validators=[URLValidator(schemes=["http", "https"])]
    )
    accessed_on = models.DateField()
    source_type = models.CharField(
        max_length=20, choices=SourceType.choices, default=SourceType.MANUFACTURER
    )
    is_public = models.BooleanField(
        default=False, help_text="List this source at the end of the article."
    )

    panels = [
        FieldPanel("source_name"),
        FieldPanel("url"),
        FieldPanel("accessed_on"),
        FieldPanel("source_type"),
        FieldPanel("is_public"),
    ]

    def __str__(self):
        return self.source_name


class ArticlePage(Page):
    """
    A buying guide, comparison, explainer or tutorial.

    The published date is Wagtail's ``first_published_at``; only the review date is
    stored here. Whether the article shows an affiliate disclosure is derived from
    its rendered offers (``has_active_offers``), never from a hand-set flag.
    """

    parent_page_types = ["editorial.CategoryPage"]
    subpage_types = []

    article_kind = models.CharField(
        max_length=20, choices=ArticleKind.choices, default=ArticleKind.BUYING_GUIDE
    )
    excerpt = models.TextField(
        max_length=300, help_text="One or two sentences shown in listings and feeds."
    )
    author = models.ForeignKey(
        "editorial.AuthorPage", on_delete=models.PROTECT, related_name="articles"
    )
    featured_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    featured_image_provenance = models.CharField(
        max_length=30, choices=ImageProvenance.choices, blank=True
    )
    featured_image_credit = models.CharField(
        "Featured image credit or licence evidence", max_length=255, blank=True
    )
    body = StreamField(ArticleBody(), blank=True)
    methodology = RichTextField(
        blank=True,
        help_text="Selection criteria, evidence and research date.",
    )
    reviewed_date = models.DateField(
        null=True,
        blank=True,
        help_text="When the facts in this article were last checked.",
    )
    tags = ClusterTaggableManager(through=ArticlePageTag, blank=True)

    search_fields = Page.search_fields + [
        index.SearchField("excerpt"),
        index.SearchField("body"),
        index.SearchField("methodology"),
        index.SearchField("tags_text"),
        index.RelatedFields("author", [index.SearchField("title")]),
        index.FilterField("article_kind"),
    ]

    content_panels = [
        *Page.content_panels,
        FieldPanel("article_kind"),
        FieldPanel("excerpt"),
        FieldPanel("author"),
        MultiFieldPanel(
            [
                FieldPanel("featured_image"),
                FieldPanel("featured_image_provenance"),
                FieldPanel("featured_image_credit"),
            ],
            heading="Featured image",
        ),
        FieldPanel("body"),
        FieldPanel("methodology"),
        FieldPanel("reviewed_date"),
        FieldPanel("tags"),
        InlinePanel("sources", label="Source", heading="Research sources"),
    ]

    def clean(self):
        super().clean()
        validate_image_provenance(
            image=self.featured_image,
            provenance=self.featured_image_provenance,
            credit=self.featured_image_credit,
            image_field="featured_image",
            provenance_field="featured_image_provenance",
            credit_field="featured_image_credit",
        )

    @property
    def category(self):
        """The one primary hub this article belongs to (its parent page)."""
        return self.get_parent().specific

    @property
    def tags_text(self):
        return " ".join(tag.name for tag in self.tags.all())

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["public_sources"] = [s for s in self.sources.all() if s.is_public]
        # The rendering contract (invariant 4): resolve every product card, its
        # offers, images and specs ONCE, before any body block renders. Cards,
        # quick picks and comparison tables read only from these values.
        products = resolve_article_products(self.body)
        context["article_products"] = products.entries
        context["has_active_offers"] = products.has_active_offers
        # Pasted markdown/HTML blocks are rendered here too, so the disclosure above
        # the body also covers affiliate links written straight into the text.
        markdown = render_markdown_blocks(self.body)
        context["markdown_html"] = markdown.html
        context["has_affiliate_links"] = (
            products.has_active_offers or markdown.has_affiliate_links
        )
        context["affiliate_disclosure_page"] = (
            StandardPage.objects.live()
            .public()
            .filter(slug="affiliate-disclosure")
            .first()
            if context["has_affiliate_links"]
            else None
        )
        context["first_cta_block_id"] = products.first_cta_block_id
        context["quick_picks"] = [
            entry for entry in products.entries if entry.card["recommendation_label"]
        ]
        # Other live guides in the same hub.
        context["related_articles"] = (
            ArticlePage.objects.sibling_of(self, inclusive=False)
            .live()
            .select_related("author", "featured_image")
            .order_by(F("first_published_at").desc(nulls_last=True))[:3]
        )
        return context


# --- Category hubs -----------------------------------------------------------


class CategoryPageQuerySet(PageQuerySet):
    def with_live_article_count(self):
        """Annotate ``live_article_count``: live direct ArticlePage children."""
        live_articles = (
            ArticlePage.objects.live()
            .filter(path__startswith=OuterRef("path"), depth=OuterRef("depth") + 1)
            .order_by()
            .annotate(grouping=Value(1))
            .values("grouping")
            .annotate(total=Count("pk"))
            .values("total")
        )
        return self.annotate(
            live_article_count=Coalesce(
                Subquery(live_articles, output_field=IntegerField()), 0
            )
        )

    def discoverable(self):
        """
        Live, public hubs that may appear in navigation, homepage tiles, directories.

        One query, however many hubs exist. Mirrors ``CategoryPage.is_discoverable``.
        """
        return (
            self.live()
            .public()
            .with_live_article_count()
            .filter(
                Q(discovery_mode=DiscoveryMode.FORCE_SHOW)
                | Q(
                    discovery_mode=DiscoveryMode.AUTO,
                    live_article_count__gte=DISCOVERY_AUTO_MIN_ARTICLES,
                )
            )
        )


class CategoryPage(Page):
    """
    An editorial hub such as Developer Setup. Created in the Wagtail admin; a new
    hub needs no code change or migration.
    """

    parent_page_types = ["home.HomePage"]
    subpage_types = ["editorial.ArticlePage"]

    introduction = RichTextField(blank=True)
    banner = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    banner_provenance = models.CharField(
        max_length=30, choices=ImageProvenance.choices, blank=True
    )
    banner_credit = models.CharField(
        "Banner credit or licence evidence", max_length=255, blank=True
    )
    discovery_mode = models.CharField(
        max_length=16,
        choices=DiscoveryMode.choices,
        default=DiscoveryMode.FORCE_HIDE,
        help_text=(
            "Hidden hubs stay live (their articles keep working) but are left out of "
            "navigation and the sitemap and are marked noindex. Choose Auto or Always "
            "show only after an editorial review."
        ),
    )

    objects = PageManager.from_queryset(CategoryPageQuerySet)()

    search_fields = Page.search_fields + [
        index.SearchField("introduction"),
    ]

    content_panels = [
        *Page.content_panels,
        FieldPanel("introduction"),
        MultiFieldPanel(
            [
                FieldPanel("banner"),
                FieldPanel("banner_provenance"),
                FieldPanel("banner_credit"),
            ],
            heading="Banner image",
        ),
        InlinePanel(
            "featured_guides", label="Featured guide", heading="Featured guides"
        ),
    ]
    settings_panels = [*Page.settings_panels, FieldPanel("discovery_mode")]

    def clean(self):
        super().clean()
        validate_image_provenance(
            image=self.banner,
            provenance=self.banner_provenance,
            credit=self.banner_credit,
            image_field="banner",
            provenance_field="banner_provenance",
            credit_field="banner_credit",
        )

    @property
    def live_child_count(self):
        """Live direct ArticlePage children (not a quality score)."""
        annotated = getattr(self, "live_article_count", None)
        if annotated is not None:
            return annotated
        return ArticlePage.objects.child_of(self).live().count()

    @property
    def is_discoverable(self):
        if self.discovery_mode == DiscoveryMode.FORCE_SHOW:
            return True
        if self.discovery_mode == DiscoveryMode.FORCE_HIDE:
            return False
        return self.live_child_count >= DISCOVERY_AUTO_MIN_ARTICLES

    @property
    def robots_meta(self):
        """Value for <meta name="robots">; empty means indexable (no tag)."""
        return "" if self.is_discoverable else "noindex,follow"

    def get_sitemap_urls(self, request=None):
        # Undiscoverable hubs stay live for URLs and breadcrumbs, but are not
        # offered to search engines. Their articles keep their own sitemap entries.
        if not self.is_discoverable:
            return []
        return super().get_sitemap_urls(request)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["robots_meta"] = self.robots_meta
        context["articles"] = (
            ArticlePage.objects.child_of(self)
            .live()
            .select_related("author")
            .order_by(F("first_published_at").desc(nulls_last=True))
        )
        context["featured_articles"] = [
            item.article
            for item in self.featured_guides.select_related("article")
            if item.article.live
        ]
        return context


class CategoryFeaturedGuide(Orderable):
    category = ParentalKey(
        "editorial.CategoryPage",
        related_name="featured_guides",
        on_delete=models.CASCADE,
    )
    article = models.ForeignKey(
        "editorial.ArticlePage", on_delete=models.CASCADE, related_name="+"
    )

    panels = [FieldPanel("article")]

    def clean(self):
        super().clean()
        # Only articles that belong to this hub can be featured on it.
        if self.article_id and self.category_id:
            if self.article.get_parent().pk != self.category_id:
                raise ValidationError(
                    {"article": "Choose an article that belongs to this category."}
                )


# --- Standard pages ----------------------------------------------------------


class StandardPage(Page):
    """About, Contact, Editorial Policy, Affiliate Disclosure, Privacy, Terms."""

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    body = RichTextField()

    content_panels = [*Page.content_panels, FieldPanel("body")]
