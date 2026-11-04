from django.test import SimpleTestCase, TestCase

from editorial.markdown_render import render_markdown
from editorial.models import DiscoveryMode

from .helpers import make_article, make_author, make_category


class RenderMarkdownTests(SimpleTestCase):
    def test_headings_lists_bold_and_links_render(self):
        html = render_markdown(
            "## Sizing\n\nPick **oil** heaters.\n\n- one\n- two\n\n[Guide](https://a.in/x)"
        )
        self.assertIn("<h2>Sizing</h2>", html)
        self.assertIn("<strong>oil</strong>", html)
        self.assertIn("<li>two</li>", html)
        self.assertIn('<a href="https://a.in/x" rel="noopener">Guide</a>', html)

    def test_h1_becomes_h2_because_the_page_title_is_the_h1(self):
        html = render_markdown("# Heading")
        self.assertIn("<h2>Heading</h2>", html)
        self.assertNotIn("<h1", html)

    def test_tables_render_with_bootstrap_classes_and_scope(self):
        html = render_markdown("| A | B |\n|---|---|\n| 1 | 2 |")
        self.assertIn('<table class="table table-bordered', html)
        self.assertIn('<th scope="col">A</th>', html)
        self.assertIn("<td>2</td>", html)
        self.assertIn('class="table-scroll', html)

    def test_raw_html_is_escaped_not_rendered(self):
        html = render_markdown(
            '<script>alert(1)</script>\n\n<div onclick="x()">hi</div>\n\n'
            '<iframe src="https://evil.example"></iframe>'
        )
        self.assertNotIn("<script", html)
        self.assertNotIn("<div onclick", html)
        self.assertNotIn("<iframe", html)
        self.assertIn("&lt;script&gt;", html)

    def test_images_are_dropped(self):
        html = render_markdown("![x](https://a.in/p.png)\n\n![y][ref]\n\n[ref]: /p.png")
        self.assertNotIn("<img", html)

    def test_unsafe_link_schemes_are_unwrapped(self):
        html = render_markdown(
            "[a](javascript:alert(1)) [b](data:text/html;base64,AAAA) "
            "[c](JaVaScRiPt:alert(1)) <javascript:alert(2)>"
        )
        self.assertNotIn("href=", html)
        self.assertNotIn("<a", html)

    def test_relative_mailto_and_anchor_links_are_kept(self):
        html = render_markdown("[a](/guides/x/) [b](mailto:hi@a.in) [c](#top)")
        self.assertIn('href="/guides/x/"', html)
        self.assertIn('href="mailto:hi@a.in"', html)
        self.assertIn('href="#top"', html)

    def test_external_links_do_not_get_sponsored_or_follow_claims(self):
        html = render_markdown("[x](https://www.flipkart.com/p)")
        self.assertNotIn("sponsored", html)

    def test_empty_input_renders_nothing(self):
        self.assertEqual(render_markdown(""), "")
        self.assertEqual(render_markdown(None), "")


class MarkdownBlockPageTests(TestCase):
    def test_markdown_block_is_in_the_server_html(self):
        article = make_article(
            make_category(mode=DiscoveryMode.FORCE_SHOW),
            make_author(),
            body=[
                {
                    "type": "markdown",
                    "value": (
                        "## Best for small rooms\n\n| A | B |\n|---|---|\n| 1 | 2 |"
                        "\n\n<script>x()</script>"
                    ),
                }
            ],
        )
        response = self.client.get(article.url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("<h2>Best for small rooms</h2>", html)
        self.assertIn("<td>2</td>", html)
        self.assertNotIn("<script>x()</script>", html)
