import re

from django.core.exceptions import ValidationError
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

adsense_publisher_id_validator = RegexValidator(
    regex=r"^(?:ca-)?pub-\d{16}$",
    message=(
        "Enter a valid Google AdSense Publisher ID such as "
        "pub-1234567890123456 or ca-pub-1234567890123456."
    ),
)

adsense_slot_id_validator = RegexValidator(
    regex=r"^\d{10}$",
    message="Enter a 10-digit AdSense ad unit ID (e.g. 1234567890).",
)


def validate_ads_txt_lines(value):
    """Ensure custom ads.txt lines follow IAB specification or comment syntax."""
    if not value:
        return
    pattern = re.compile(
        r"^[A-Za-z0-9.-]+,\s*[A-Za-z0-9-]+,\s*(?:DIRECT|RESELLER)(?:,\s*[A-Fa-f0-9]+)?$",
        re.IGNORECASE,
    )
    for lineno, raw_line in enumerate(value.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not pattern.match(line):
            raise ValidationError(
                f"Line {lineno} is invalid ('{line}'). Expected format: "
                "<domain>, <publisher_id>, <DIRECT|RESELLER>[, <cert_id>]"
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
    adsense_publisher_id = models.CharField(
        max_length=64,
        blank=True,
        validators=[adsense_publisher_id_validator],
        help_text=(
            "e.g. pub-1234567890123456 or ca-pub-1234567890123456. "
            "Leave blank to disable."
        ),
    )
    adsense_enabled = models.BooleanField(
        default=False,
        help_text="Master switch to activate Google AdSense on eligible content pages.",
    )
    adsense_auto_ads = models.BooleanField(
        default=False,
        help_text="Enable Google AdSense Auto Ads (automatic ad placement).",
    )
    adsense_in_article_slot_id = models.CharField(
        max_length=32,
        blank=True,
        validators=[adsense_slot_id_validator],
        help_text="10-digit AdSense ad unit ID for in-article manual placements.",
    )
    adsense_feed_slot_id = models.CharField(
        max_length=32,
        blank=True,
        validators=[adsense_slot_id_validator],
        help_text="10-digit AdSense ad unit ID for category feed manual placements.",
    )
    ads_txt_custom = models.TextField(
        blank=True,
        validators=[validate_ads_txt_lines],
        help_text="Custom lines to append to /ads.txt.",
    )

    panels = [
        FieldPanel("telegram_channel_url"),
        FieldPanel("telegram_channel_label"),
        FieldPanel("adsense_publisher_id"),
        FieldPanel("adsense_enabled"),
        FieldPanel("adsense_auto_ads"),
        FieldPanel("adsense_in_article_slot_id"),
        FieldPanel("adsense_feed_slot_id"),
        FieldPanel("ads_txt_custom"),
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
        "editorial.ArticlePage",
        on_delete=models.CASCADE,
        related_name="+",
    )

    panels = [
        FieldPanel("article"),
    ]
