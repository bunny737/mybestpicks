# Module: Editorial blocks

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Done (2026-11-02)
**Priority:** P0
**Ticket:** MBP-004
**Plan reference:** docs/mybestpicks_plan_v4.md §4 (StreamField blocks, rendering contract, safeguards), §6 (link rendering)
**Depends on:** 03, 05
**Blocks:** 06, 10

## Purpose
The StreamField blocks used to write articles. Product cards are the **only**
source of per-article verdicts. Comparison tables are built from those cards and
never re-select products.

## Blocks (as-built)
Code: `editorial/blocks.py` (`ArticleBody` is the body's `StreamBlock`),
`editorial/rendering.py`, templates in `editorial/templates/editorial/blocks/` and
`mybestpicks/templates/components/`. Migration `editorial.0003`.

```
paragraph          rich text (h2-h4, bold, italic, lists, links)
markdown           pasted markdown or simple HTML (headings, lists, links, tables), cleaned
                   and rendered on the server by editorial/markdown_render.py;
                   scripts, styles, embeds and images are removed
heading            text + level (H2/H3); H1 is always the page title
image              image, alt_text (required), caption, provenance (required), credit
table              plain TableBlock (Wagtail contrib): caption, header row/column toggle
                   plain reference tables only; NOT for product comparisons
key_takeaways      heading + 1-8 points
buying_criteria    heading + criteria (name, why)
product_card       product (ProductChooserBlock → catalog.Product)
                   recommendation_label, best_for, verdict (rich text), pros[], cons[]
                   tested_by_editor, editorial_evidence (notes), evidence_media (own photo)
comparison_table   heading, card_positions[] (optional), spec_keys[] (optional)
                   NO product chooser
faq                heading + questions (question, answer)
source_note        text, source_name, url (http/https only)
related_articles   heading + 1-6 article pages (only live ones render)
```
`ProductChooserBlock` is a `SnippetChooserBlock` that loads the brand with the product
in the same bulk query that loads every product in the article.

## Rendering contract (CLAUDE.md invariant 4) — as-built
`ArticlePage.get_context()` calls `resolve_article_products(self.body)` **once, before
any block renders**:
1. Walks `body` and collects every `product_card` in order (block id, 1-based
   position as an editor counts them).
2. The products come from one bulk query (`ProductChooserBlock.bulk_to_python`, with
   brands joined).
3. One query loads the **renderable** offers with their merchants; each offer is
   handed its product so `is_renderable` costs no query.
4. One query loads every product and evidence image, with their renditions
   prefetched (`width-400` for products, `width-640` for evidence; the `{% image %}`
   tags use the same specs).
5. Specs are normalised once with `catalog.specs.spec_rows()`.
6. Each card value gets `card.resolved = ProductEntry(...)`, which the card template
   reads. The context also gets `article_products` (entries in order),
   `has_active_offers`, `first_cta_block_id` and `quick_picks`.

Cards, quick picks and comparison tables read only from these values, so a table may
appear above the cards it reads. The number of queries does not depend on the number
of cards (measured: identical for 2 and for 9 cards, each with an image, an offer and
an evidence photo). An article with no cards runs no catalog query at all.

## Article page order (as-built)
breadcrumb → title, author, dates, short answer → hero image → methodology
(collapsible) → **affiliate disclosure (only if `has_active_offers`)** → quick picks →
body → public sources, tags, last reviewed → related guides. The disclosure sits
before the body because every CTA is inside a body product card, so it is always
before the first CTA whatever order the editor builds.

## Business rules
Each rule maps to a test in `editorial/tests/` (file in brackets).
1. `ProductCardBlock.clean()` raises a `ValidationError` when `tested_by_editor` is
   ticked and there are neither evidence notes (whitespace does not count) nor an
   evidence photo. (`test_product_cards`)
2. An untested card never uses hands-on wording: its HTML does not contain "tested" at
   all, and says "Based on desk research; we have not used this product." A tested
   card shows "Hands-on tested by our editor" plus the evidence. (`test_product_cards`)
3. `comparison_table` shows every card by default, or the chosen `card_positions` in
   the given order. Saving is blocked if the article has fewer than two cards, a
   position does not exist or a position is repeated. At render time a position with
   no card (removed since) is skipped, never an error. (`test_comparison_table`)
4. Columns are comparable specs only. A column no included product records is left
   out (even if the editor listed it); a spec one product lacks shows an em dash and is
   never guessed. With fewer than two products or no columns, nothing renders.
   (`test_comparison_table`)
5. A CTA renders only for a renderable offer, as
   `<a rel="sponsored nofollow noopener">` in the same tab, labelled with the
   merchant's button text ("View at Flipkart", "Check price at Amazon"). It never
   shows a price. Inactive offers, disabled merchants, discontinued products and
   hosts no longer in the allowlist produce no button. (`test_product_cards`)
6. The disclosure renders once, before the first CTA, and only when an offer will
   render; offers that will not render never trigger it. It makes no programme claims
   (no "Amazon", "Associate", merchant names). (`test_disclosure`)
7. Rendering N cards uses a constant number of queries (`test_rendering_contract`).
8. Wagtail's reference index finds the articles that use a product, and swapping a
   product moves the reference. (`test_body_blocks.ReferenceIndexTests`)
9. An `image` block needs alt text and provenance, and a credit unless the image is an
   owned original (invariant 8). (`test_body_blocks`)
10. Block text is escaped (verdicts, pros, captions). `source_note` links are
    `rel="noopener nofollow"` and only http/https. (`test_product_cards`, `test_body_blocks`)

## Edge cases handled
- **A product deleted after a card used it.** StreamField references are not
  database foreign keys, so deletion cannot be blocked. Decision: the card is left out
  for readers and for tables (no broken page); Wagtail's usage count warns editors
  before they delete. (`test_product_cards`, `test_comparison_table`,
  `test_rendering_contract`)
- **The same product in two cards** gets two entries. (`test_rendering_contract`)
- **A discontinued or unavailable product** keeps its card with a plain note; a
  discontinued product's offers do not render. (`test_product_cards`)
- **An article with no cards:** no tables, no disclosure, no quick picks, no catalog
  queries. (`test_product_cards`, `test_rendering_contract`)

## Open questions / Decisions
- [DECISION 2026-11-02] **Quick picks is a template section, not a block.** It lists
  the cards that have a `recommendation_label` (with their `best_for`), links to each
  card, and is omitted when no card has a label. One less block for editors to place,
  and it can never disagree with the cards.
- [DECISION 2026-11-02] The comparison table chooses cards by **position** (1, 2, 3 in
  the order they appear), not by block id: editors never see block ids. The article's
  `clean()` rejects positions that do not exist. Trade-off: reordering cards changes
  what a position means; the help text says so.
- [DECISION 2026-11-02] `comparison_table` column choices come from a *callable*
  (`catalog.specs.comparable_spec_choices`), so editing `specs.py` never needs a
  migration. The generated migration references the function, not a list of specs.
- [DECISION 2026-11-02] Dropped unrecorded columns (rule 4) rather than showing a
  column of dashes.
- [DECISION 2026-11-02] The disclosure has no link to the Affiliate Disclosure page
  yet: that page's URL is not guaranteed to exist. Module 06 can add the link.
- [DECISION 2026-11-02] The disclosure text is generic ("Some links on this page are
  affiliate links...") and names no network, because it must stay true for Flipkart via
  Cuelinks and must never imply Amazon Associate status.
- [DECISION 2026-11-02] FAQ answers render as visible headings and text (not
  collapsed), so they are in the server HTML. FAQ structured data is module 06.
- [DECISION 2026-11-03] Added a `table` block (`PlainTableBlock`, a thin subclass of
  `wagtail.contrib.table_block.blocks.TableBlock`) so editors can paste a simple table
  from Excel, Google Sheets or Word instead of building it by hand. No new dependency:
  the contrib app ships inside the pinned `wagtail` package and is now in
  `INSTALLED_APPS`. It is a sibling of `comparison_table`, not a replacement:
  `comparison_table` stays the only block that compares this article's products
  (invariant 3), and `table` knows nothing about product cards. Cell text is escaped
  (the `text` renderer; the template never uses `|safe`). Its help text warns against
  product comparisons and prices; nothing enforces that, because cell text cannot be
  checked reliably. Needed migration `editorial.0005`, since this Wagtail version keeps
  the StreamField block definition in migration state.
- [DECISION 2026-11-04] Added a `markdown` block (`MarkdownBlock`, a `TextBlock`
  rendered by `editorial/markdown_render.py`) so an editor can paste a whole article
  as markdown. The owner approved the one new dependency, `Markdown==3.11.2`, pinned
  in `requirements/base.txt` and `constraints.txt`. Output is server-rendered HTML
  (invariant 1). Pasted text is untrusted, so the renderer is deliberately narrow:
  images are dropped (invariant 8: every image needs recorded provenance, so use an
  Image block), links must be http(s), mailto, relative or `#` (anything else, such as
  `javascript:`, is unwrapped to plain text), and `#` becomes H2 because the page
  title is the H1. (Raw HTML handling was first "escape it"; see the next decision.)
  External links get `rel="noopener"` only: an affiliate link
  pasted here would carry no `sponsored` rel and would bypass the disclosure rule
  (invariants 6 and 7), so the help text says to use product cards instead. Nothing
  enforces that, as with prices. Tables get the same Bootstrap classes and scroll
  wrapper as the `table` block. Needed migration `editorial.0006`.
- [DECISION 2026-11-04] The `markdown` block also accepts simple HTML (labelled
  "Markdown / HTML"; the block name `markdown` is unchanged so stored data keeps
  working). The first version escaped raw HTML; the owner asked for HTML support, so
  the renderer now keeps raw HTML and cleans it against an allowlist in
  `editorial/markdown_render.py` instead (no new dependency; BeautifulSoup is already
  installed with Wagtail). Allowed: `p br hr h1-h6 strong b em i u del s sub sup small
  code pre blockquote ul ol li a table caption thead tbody tfoot tr th td`. Only
  `href`/`title` on links and `colspan`/`rowspan`/`scope` on cells survive; every other
  attribute (`style`, `class`, `id`, `on*`, `target`) is removed. `script`, `style`,
  `iframe`, `object`, `form`, `svg`, `img` and similar are removed together with their
  contents; other unknown tags such as `div`, `span` and `font` are unwrapped and keep
  their text; comments are removed. The link-scheme, image, H1 and table rules above
  apply to HTML as well as markdown. Markdown inside an HTML block is not converted
  (no `md_in_html`). No migration: the help text and label are not part of the saved
  block definition.
- [DECISION 2026-11-03] The `paragraph` block already accepts markdown-style typing
  shortcuts and rich text pasted from Google Docs or Word; only plain-text markdown
  needed the new block above.
- [OPEN] Body `image` blocks create their renditions one query per image (only product
  and evidence images are prefetched). Fine for a few images per article; revisit with
  real performance data.
- [OPEN] Product cards have no per-card "update date": the card shows the product's
  `last_verified_at` ("Facts checked ...").

## Changelog
- 2026-11-02  Created stub from plan v4.
- 2026-11-02  Built: `ArticleBody` with ten blocks, `ProductChooserBlock`, the
  resolver in `editorial/rendering.py`, product card, comparison table, disclosure and
  block templates, quick picks, migration `editorial.0003`, 78 new tests (241 in
  total). Mutation-checked the evidence, disclosure, renderable-offer and query-count
  rules. Visually checked an article with cards and a table at 320px.
- 2026-11-03  Added the plain `table` block (`PlainTableBlock`), its template,
  migration `editorial.0005` and 5 tests (338 in total).
- 2026-11-04  Added the `markdown` block, `editorial/markdown_render.py`, the pinned
  `Markdown==3.11.2` dependency, migration `editorial.0006` and 10 tests (348 in
  total). Checked the renderer against raw HTML, `javascript:`/`data:` links, images
  and reference-style images.
- 2026-11-04  The `markdown` block now also accepts simple HTML through an allowlist
  (label "Markdown / HTML"); 8 new tests for it (356 in total), no migration.
