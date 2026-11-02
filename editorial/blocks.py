"""
StreamField blocks for article bodies.

Module 03 ships only the minimum needed to write an article. Module 04 adds the
product card, comparison table and the other editorial blocks.
"""

from wagtail import blocks

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


def article_body_blocks():
    return [
        ("paragraph", blocks.RichTextBlock(features=BODY_RICH_TEXT_FEATURES)),
        ("heading", HeadingBlock()),
    ]
