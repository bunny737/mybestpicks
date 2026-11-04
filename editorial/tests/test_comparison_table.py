"""Module 04 rules 3 and 4: tables are built from the article's own cards."""

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from catalog.tests.helpers import make_brand, make_product
from editorial.blocks import ArticleBody, ComparisonTableBlock
from editorial.models import DiscoveryMode
from editorial.rendering import MISSING, build_comparison_table

from .helpers import (
    card_block,
    make_article,
    make_author,
    make_category,
    plain_table_block,
    table_block,
)


class ComparisonTableRenderingTests(TestCase):
    def setUp(self):
        self.author = make_author()
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        brand = make_brand()
        self.k1 = make_product(
            "K1",
            brand=brand,
            key_specs={
                "layout": "tkl",
                "switch_type": "mechanical",
                "connectivity": "wired",
                "weight_g": 900,
            },
        )
        self.k2 = make_product(
            "K2",
            brand=brand,
            key_specs={
                "layout": "75",
                "switch_type": "membrane",
                "connectivity": "bluetooth",
            },
        )
        self.k3 = make_product(
            "K3",
            brand=brand,
            key_specs={
                "layout": "full",
                "switch_type": "optical",
                "connectivity": "wired",
                "weight_g": 700,
            },
        )

    def page(self, *blocks):
        article = make_article(self.hub, self.author, body=list(blocks))
        response = self.client.get(article.url)
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def cards(self):
        return [
            card_block(self.k1, block_id="c1"),
            card_block(self.k2, block_id="c2"),
            card_block(self.k3, block_id="c3"),
        ]

    def table(self, html):
        start = html.index("<table")
        return html[start : html.index("</table>", start)]

    def test_the_default_table_compares_every_card_in_order(self):
        table = self.table(self.page(*self.cards(), table_block()))
        self.assertLess(table.index("Acme K1"), table.index("Acme K2"))
        self.assertLess(table.index("Acme K2"), table.index("Acme K3"))
        for header in ("Layout", "Switch type", "Connectivity", "Weight (g)"):
            self.assertIn(header, table)
        self.assertIn("Tenkeyless (TKL)", table)
        self.assertIn("Optical", table)

    def test_a_spec_a_product_does_not_record_shows_a_dash_not_a_guess(self):
        table = self.table(self.page(*self.cards(), table_block()))
        k2_row = table[table.index("Acme K2") :]
        k2_row = k2_row[: k2_row.index("</tr>")]
        self.assertIn(MISSING, k2_row)  # K2 has no weight
        self.assertNotIn("0", k2_row.replace("75", ""))  # no invented number

    def test_columns_no_product_records_are_left_out(self):
        table = self.table(self.page(*self.cards(), table_block()))
        self.assertNotIn("Battery life", table)
        self.assertNotIn("Backlight", table)

    def test_the_table_can_come_before_the_cards_it_reads(self):
        # The context is resolved up front, so order in the body does not matter.
        html = self.page(table_block(), *self.cards())
        self.assertLess(html.index("<table"), html.index('id="product-c1"'))
        self.assertIn("Acme K3", self.table(html))

    def test_rows_link_to_their_cards(self):
        table = self.table(self.page(*self.cards(), table_block()))
        self.assertIn('href="#product-c1"', table)
        self.assertIn('href="#product-c3"', table)

    def test_positions_choose_a_subset_in_the_given_order(self):
        table = self.table(self.page(*self.cards(), table_block(positions=[3, 1])))
        self.assertLess(table.index("Acme K3"), table.index("Acme K1"))
        self.assertNotIn("Acme K2", table)

    def test_an_out_of_range_position_is_skipped_without_breaking_the_page(self):
        table = self.table(self.page(*self.cards(), table_block(positions=[1, 9, 2])))
        self.assertIn("Acme K1", table)
        self.assertIn("Acme K2", table)

    def test_chosen_columns_limit_the_table(self):
        table = self.table(
            self.page(*self.cards(), table_block(spec_keys=["connectivity", "layout"]))
        )
        self.assertIn("Layout", table)
        self.assertIn("Connectivity", table)
        self.assertNotIn("Switch type", table)
        self.assertNotIn("Weight", table)

    def test_a_chosen_column_nobody_records_is_dropped(self):
        table = self.table(
            self.page(*self.cards(), table_block(spec_keys=["layout", "backlight"]))
        )
        self.assertNotIn("Backlight", table)

    def test_fewer_than_two_products_renders_no_table(self):
        html = self.page(card_block(self.k1), table_block())
        self.assertNotIn("<table", html)

    def test_a_card_for_a_deleted_product_is_left_out_of_the_table(self):
        gone = make_product("Gone", brand=self.k1.brand)
        article = make_article(
            self.hub,
            self.author,
            body=[
                card_block(gone, block_id="dead"),
                card_block(self.k1, block_id="c1"),
                card_block(self.k2, block_id="c2"),
                table_block(),
            ],
        )
        gone.delete()
        html = self.client.get(article.url).content.decode()
        table = self.table(html)
        self.assertNotIn("Gone", table)
        self.assertIn("Acme K1", table)

    def test_tables_scroll_inside_their_own_box(self):
        html = self.page(*self.cards(), table_block())
        self.assertIn('class="table-scroll"', html)
        self.assertIn('scope="col"', html)
        self.assertIn('scope="row"', html)

    def test_a_heading_is_used_as_the_table_label(self):
        html = self.page(*self.cards(), table_block(heading="Switch showdown"))
        self.assertIn("Switch showdown", html)


class BuildComparisonTableUnitTests(SimpleTestCase):
    def test_no_entries_means_no_table(self):
        self.assertIsNone(build_comparison_table([], [], []))


class ComparisonBlockDefinitionTests(SimpleTestCase):
    def test_the_block_has_no_product_chooser(self):
        # Invariant 3: tables never re-select products.
        names = set(ComparisonTableBlock().child_blocks)
        self.assertEqual(names, {"heading", "card_positions", "spec_keys"})
        self.assertNotIn("product", names)

    def test_column_choices_come_from_the_spec_schemas(self):
        from catalog.specs import comparable_spec_choices

        keys = {key for key, _ in comparable_spec_choices()}
        self.assertIn("layout", keys)
        self.assertIn("power_watts", keys)
        self.assertEqual(len(keys), len(comparable_spec_choices()))


class ComparisonTableValidationTests(TestCase):
    """The editor must not be able to save a table that points at nothing."""

    def setUp(self):
        brand = make_brand()
        self.a = make_product("A", brand=brand)
        self.b = make_product("B", brand=brand)
        self.body = ArticleBody()

    def clean(self, *blocks):
        return self.body.clean(self.body.to_python(list(blocks)))

    def test_a_table_with_two_cards_is_valid(self):
        self.clean(card_block(self.a), card_block(self.b), table_block())

    def test_a_table_needs_at_least_two_cards(self):
        with self.assertRaises(ValidationError):
            self.clean(card_block(self.a), table_block())
        with self.assertRaises(ValidationError):
            self.clean(table_block())

    def test_positions_must_exist(self):
        with self.assertRaises(ValidationError) as ctx:
            self.clean(
                card_block(self.a), card_block(self.b), table_block(positions=[1, 5])
            )
        self.assertIn(2, ctx.exception.block_errors)  # the table is the third block
        self.assertIn("5", str(ctx.exception.block_errors[2].non_block_errors))

    def test_positions_must_be_unique(self):
        with self.assertRaises(ValidationError):
            self.clean(
                card_block(self.a), card_block(self.b), table_block(positions=[1, 1])
            )

    def test_valid_positions_pass(self):
        self.clean(
            card_block(self.a), card_block(self.b), table_block(positions=[2, 1])
        )

    def test_a_table_does_not_need_to_follow_its_cards(self):
        self.clean(table_block(), card_block(self.a), card_block(self.b))

    def test_a_plain_table_neither_satisfies_nor_breaks_the_comparison_rules(self):
        plain = plain_table_block([["a", "b"], ["1", "2"]])
        self.clean(card_block(self.a), card_block(self.b), plain, table_block())
        with self.assertRaises(ValidationError):
            self.clean(card_block(self.a), plain, table_block())
