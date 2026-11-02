from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page

from editorial.models import ArticleKind, ArticlePage, CategoryPage

telegram_url_validator = RegexValidator(
    regex=r"^https://t\.me/[A-Za-z0-9_]+/?$",
    message="Enter a Telegram channel URL such as https://t.me/mybestpicks.",
)


@register_setting
class SiteSettings(BaseSiteSetting):
    """Public, per-site settings. Secrets must never be stored here."""

    telegram_channel_url = models.URLField(
        blank=True,
        validators=[telegram_url_validator],
        help_text="Public channel URL. Leave blank to hide every Telegram link.",
    )
    telegram_channel_label = models.CharField(
        max_length=80, blank=True, default="Join on Telegram"
    )

    panels = [
        FieldPanel("telegram_channel_url"),
        FieldPanel("telegram_channel_label"),
    ]


class HomePage(Page):
    """
    The site root. Category tiles are not configured here: they always come from
    ``CategoryPage.objects.discoverable()`` (CLAUDE.md invariant 5).
    """

    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "editorial.CategoryPage",
        "editorial.StandardPage",
        "editorial.AuthorIndexPage",
    ]

    hero_title = models.CharField(
        max_length=120, default="Find the Best Picks for Everyday Life."
    )
    hero_text = models.TextField(
        blank=True,
        default=(
            "Independent buying guides and honest comparisons for shoppers in India."
        ),
    )
    trust_panel = RichTextField(
        blank=True,
        help_text='Short "How We Choose" text. Link to the editorial policy page.',
    )

    content_panels = [
        *Page.content_panels,
        FieldPanel("hero_title"),
        FieldPanel("hero_text"),
        InlinePanel(
            "featured_guides", label="Featured guide", heading="Featured guides"
        ),
        FieldPanel("trust_panel"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["categories"] = CategoryPage.objects.child_of(self).discoverable()
        live_articles = (
            ArticlePage.objects.descendant_of(self)
            .live()
            .select_related("author", "featured_image")
        )
        newest = F("first_published_at").desc(nulls_last=True)
        context["latest_comparisons"] = live_articles.filter(
            article_kind=ArticleKind.COMPARISON
        ).order_by(newest)[:3]
        context["recently_updated"] = live_articles.order_by(
            F("last_published_at").desc(nulls_last=True)
        )[:6]
        context["featured_articles"] = [
            item.article
            for item in self.featured_guides.select_related("article")
            if item.article.live
        ]
        return context


class HomeFeaturedGuide(Orderable):
    home = ParentalKey(
        "home.HomePage", related_name="featured_guides", on_delete=models.CASCADE
    )
    article = models.ForeignKey(
        "editorial.ArticlePage", on_delete=models.CASCADE, related_name="+"
    )

    panels = [FieldPanel("article")]
