"""
StreamField blocks for article bodies (module 04).

Per-article judgement (verdict, pros and cons, ranking, evidence) lives ONLY in
``ProductCardBlock`` values (CLAUDE.md invariant 3); there is no ArticleProduct
model. ``ComparisonTableBlock`` never chooses products: it reads the article's
existing cards, which ``ArticlePage.get_context()`` resolves once up front
(invariant 4, see ``editorial/rendering.py``).
"""

import copy

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.forms.utils import ErrorList
from wagtail import blocks
from wagtail.blocks.stream_block import StreamBlockValidationError
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock

from catalog.provenance import ImageProvenance, validate_image_provenance
from catalog.specs import comparable_spec_choices
from editorial.markdown_render import render_markdown

BODY_RICH_TEXT_FEATURES = [
    "h2",
    "h3",
    "h4",
    "bold",
    "italic",
    "ol",
    "ul",
    "link",
    "document-link",
]

# Short rich text (verdicts, answers): no headings, no embeds.
INLINE_RICH_TEXT_FEATURES = ["bold", "italic", "ol", "ul", "link"]


def _struct_error(field_errors):
    """Turn ``{field: [messages]}`` into a StructBlockValidationError."""
    return StructBlockValidationError(
        block_errors={
            name: ErrorList([ValidationError(message) for message in messages])
            for name, messages in field_errors.items()
        }
    )


class HeadingBlock(blocks.StructBlock):
    # H1 is always the page title, so body headings start at H2.
    text = blocks.CharBlock(max_length=150)
    level = blocks.ChoiceBlock(
        choices=[("h2", "Section (H2)"), ("h3", "Subsection (H3)")],
        default="h2",
    )

    class Meta:
        icon = "title"
        label = "Heading"
        template = "editorial/blocks/heading_block.html"


class ImageBlock(blocks.StructBlock):
    """A body image. Every image records where it came from (invariant 8)."""

    image = ImageChooserBlock()
    alt_text = blocks.CharBlock(
        max_length=150, help_text="Describe the image for people who cannot see it."
    )
    caption = blocks.CharBlock(max_length=250, required=False)
    provenance = blocks.ChoiceBlock(choices=ImageProvenance.choices)
    credit = blocks.CharBlock(
        max_length=255,
        required=False,
        label="Credit or licence evidence",
        help_text="Required unless this is an owned original.",
    )

    class Meta:
        icon = "image"
        label = "Image"
        template = "editorial/blocks/image_block.html"

    def clean(self, value):
        result = super().clean(value)
        try:
            validate_image_provenance(
                image=result.get("image"),
                provenance=result.get("provenance"),
                credit=result.get("credit"),
                image_field="image",
                provenance_field="provenance",
                credit_field="credit",
            )
        except ValidationError as exc:
            raise _struct_error(exc.message_dict) from exc
        return result


class KeyTakeawaysBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=80, default="Key takeaways")
    points = blocks.ListBlock(blocks.CharBlock(max_length=250), min_num=1, max_num=8)

    class Meta:
        icon = "list-ul"
        label = "Key takeaways"
        template = "editorial/blocks/key_takeaways_block.html"


class CriterionBlock(blocks.StructBlock):
    name = blocks.CharBlock(max_length=80)
    why = blocks.TextBlock(max_length=400, help_text="Why this matters when choosing.")


class BuyingCriteriaBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=80, default="What to look for when buying")
    criteria = blocks.ListBlock(CriterionBlock(), min_num=1)

    class Meta:
        icon = "tick"
        label = "Buying criteria"
        template = "editorial/blocks/buying_criteria_block.html"


class ProductChooserBlock(SnippetChooserBlock):
    """
    Choose a catalog ``Product``. Loads the brand with the product, in the same
    single query that loads every product chosen in the article, so product cards
    never trigger per-card queries.
    """

    def __init__(self, **kwargs):
        super().__init__("catalog.Product", **kwargs)

    def bulk_to_python(self, values):
        objects = self.model_class.objects.select_related("brand").in_bulk(values)
        seen, result = set(), []
        for pk in values:
            obj = objects.get(pk)
            if obj is not None and pk in seen:
                # The same product in two cards needs a distinct instance each.
                obj = copy.copy(obj)
            result.append(obj)
            seen.add(pk)
        return result


class ProductCardBlock(blocks.StructBlock):
    """
    The only place per-article judgement about a product lives.

    The template reads ``value.resolved`` (a ``ProductEntry`` attached by
    ``ArticlePage.get_context()``); it never queries.
    """

    product = ProductChooserBlock()
    recommendation_label = blocks.CharBlock(
        max_length=60,
        required=False,
        help_text='Short label for the quick-picks list, e.g. "Best overall".',
    )
    best_for = blocks.CharBlock(
        max_length=150, required=False, help_text="Who this product suits."
    )
    verdict = blocks.RichTextBlock(features=INLINE_RICH_TEXT_FEATURES)
    pros = blocks.ListBlock(blocks.CharBlock(max_length=200), required=False)
    cons = blocks.ListBlock(blocks.CharBlock(max_length=200), required=False)
    tested_by_editor = blocks.BooleanBlock(
        required=False,
        label="Tested hands-on by our editor",
        help_text=(
            "Tick only if we really used it. Requires evidence notes or a photo of "
            "our own."
        ),
    )
    editorial_evidence = blocks.TextBlock(
        required=False,
        label="Evidence notes",
        help_text="What you did and saw: dates, how long, what you measured.",
    )
    evidence_media = ImageChooserBlock(
        required=False,
        label="Evidence photo (our own)",
    )

    class Meta:
        icon = "cog"
        label = "Product card"
        template = "components/product_card.html"

    def clean(self, value):
        result = super().clean(value)
        if result.get("tested_by_editor"):
            has_notes = bool((result.get("editorial_evidence") or "").strip())
            if not (has_notes or result.get("evidence_media")):
                raise _struct_error(
                    {
                        "editorial_evidence": [
                            "Add evidence notes or a photo of your own: a hands-on "
                            "claim needs evidence."
                        ]
                    }
                )
        return result


class ComparisonTableBlock(blocks.StructBlock):
    """
    A table built from this article's product cards. There is no product chooser:
    products are never re-selected here.
    """

    heading = blocks.CharBlock(max_length=100, required=False)
    card_positions = blocks.ListBlock(
        blocks.IntegerBlock(min_value=1),
        required=False,
        label="Cards to include",
        help_text=(
            "Optional. Positions of product cards in this article, counting from 1 "
            "in the order they appear. Leave empty to compare every card."
        ),
    )
    spec_keys = blocks.MultipleChoiceBlock(
        choices=comparable_spec_choices,
        required=False,
        label="Columns",
        help_text=(
            "Optional. Leave empty to show every spec the products have in common."
        ),
    )

    class Meta:
        icon = "table"
        label = "Comparison table"
        template = "components/comparison_table.html"

    def get_context(self, value, parent_context=None):
        from .rendering import build_comparison_table

        context = super().get_context(value, parent_context)
        entries = (parent_context or {}).get("article_products", [])
        context["table"] = build_comparison_table(
            entries,
            positions=list(value.get("card_positions") or []),
            spec_keys=list(value.get("spec_keys") or []),
        )
        return context


class FAQItemBlock(blocks.StructBlock):
    question = blocks.CharBlock(max_length=200)
    answer = blocks.RichTextBlock(features=INLINE_RICH_TEXT_FEATURES)


class FAQBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=80, default="Frequently asked questions")
    questions = blocks.ListBlock(FAQItemBlock(), min_num=1)

    class Meta:
        icon = "help"
        label = "FAQ"
        template = "editorial/blocks/faq_block.html"


class SourceNoteBlock(blocks.StructBlock):
    """An inline note that cites where a claim came from."""

    text = blocks.CharBlock(max_length=300)
    source_name = blocks.CharBlock(max_length=150, required=False)
    url = blocks.URLBlock(
        required=False, validators=[URLValidator(schemes=["http", "https"])]
    )

    class Meta:
        icon = "doc-full"
        label = "Source note"
        template = "editorial/blocks/source_note_block.html"


class RelatedArticlesBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=80, default="Related guides")
    articles = blocks.ListBlock(
        blocks.PageChooserBlock(page_type="editorial.ArticlePage"),
        min_num=1,
        max_num=6,
    )

    class Meta:
        icon = "link"
        label = "Related articles"
        template = "editorial/blocks/related_articles_block.html"

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        # Chosen pages may have been unpublished or deleted since.
        context["related"] = [
            page for page in value["articles"] if page is not None and page.live
        ]
        return context


class PlainTableBlock(TableBlock):
    """Plain reference table; never a product comparison (invariant 3) or prices."""

    def __init__(self, **kwargs):
        kwargs.setdefault(
            "help_text",
            "A plain reference table only. Not for comparing this article's products "
            "(use 'Comparison table') and never a price column.",
        )
        super().__init__(**kwargs)

    class Meta:
        icon = "table"
        label = "Table"
        template = "editorial/blocks/table_block.html"


class MarkdownBlock(blocks.TextBlock):
    """Pasted markdown, rendered on the server. Raw HTML and images are not allowed."""

    def __init__(self, **kwargs):
        kwargs.setdefault("rows", 20)
        kwargs.setdefault(
            "help_text",
            "Paste markdown: headings, bold, lists, links and tables. Raw HTML and "
            "images are not supported (use an Image block). No affiliate links or "
            "prices here; use product cards.",
        )
        super().__init__(**kwargs)

    def render_basic(self, value, context=None):
        return render_markdown(value)

    class Meta:
        icon = "code"
        label = "Markdown"


class ArticleBody(blocks.StreamBlock):
    paragraph = blocks.RichTextBlock(features=BODY_RICH_TEXT_FEATURES)
    markdown = MarkdownBlock()
    heading = HeadingBlock()
    image = ImageBlock()
    table = PlainTableBlock()
    key_takeaways = KeyTakeawaysBlock()
    buying_criteria = BuyingCriteriaBlock()
    product_card = ProductCardBlock()
    comparison_table = ComparisonTableBlock()
    faq = FAQBlock()
    source_note = SourceNoteBlock()
    related_articles = RelatedArticlesBlock()

    def clean(self, value):
        cleaned = super().clean(value)
        # A comparison table reads the article's own cards, so it can only be valid
        # when enough cards exist and any chosen positions point at real ones.
        card_count = sum(1 for child in cleaned if child.block_type == "product_card")
        errors = {}
        for index, child in enumerate(cleaned):
            if child.block_type != "comparison_table":
                continue
            problems = []
            if card_count < 2:
                problems.append(
                    "A comparison table needs at least two product cards in this "
                    "article."
                )
            positions = [int(p) for p in child.value.get("card_positions") or []]
            bad = sorted({p for p in positions if p > card_count})
            if bad and card_count >= 2:
                problems.append(
                    f"Card position(s) {', '.join(map(str, bad))} do not exist: this "
                    f"article has {card_count} product cards."
                )
            if len(positions) != len(set(positions)):
                problems.append("Each card position can only be listed once.")
            if problems:
                errors[index] = StructBlockValidationError(
                    non_block_errors=ErrorList([ValidationError(p) for p in problems])
                )
        if errors:
            raise StreamBlockValidationError(block_errors=errors)
        return cleaned
