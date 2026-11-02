from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page

from editorial.models import CategoryPage


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
