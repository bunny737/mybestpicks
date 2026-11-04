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

    def test_simple_html_is_accepted(self):
        html = render_markdown(
            "<h2>Sizing</h2>\n\n<p>Pick <strong>oil</strong> and <em>quartz</em> "
            'heaters. <a href="https://a.in/x" title="T">Guide</a></p>\n\n'
            "<ul><li>one</li><li>two</li></ul>"
        )
        self.assertIn("<h2>Sizing</h2>", html)
        self.assertIn("<strong>oil</strong>", html)
        self.assertIn("<em>quartz</em>", html)
        self.assertIn(
            '<a href="https://a.in/x" rel="noopener" title="T">Guide</a>', html
        )
        self.assertIn("<li>two</li>", html)

    def test_html_and_markdown_can_be_mixed(self):
        html = render_markdown("## Heading\n\n<p>Para <b>bold</b></p>\n\n- item")
        self.assertIn("<h2>Heading</h2>", html)
        self.assertIn("<b>bold</b>", html)
        self.assertIn("<li>item</li>", html)

    def test_html_tables_get_the_same_classes_and_wrapper(self):
        html = render_markdown(
            "<table><thead><tr><th>A</th></tr></thead>"
            '<tbody><tr><td colspan="2" onclick="x()">1</td></tr></tbody></table>'
        )
        self.assertIn('<table class="table table-bordered', html)
        self.assertIn('class="table-scroll', html)
        self.assertIn('<th scope="col">A</th>', html)
        self.assertIn('<td colspan="2">1</td>', html)
        self.assertNotIn("onclick", html)

    def test_html_h1_becomes_h2(self):
        html = render_markdown("<h1>Title</h1>")
        self.assertIn("<h2>Title</h2>", html)
        self.assertNotIn("<h1", html)

    def test_scripts_styles_and_embeds_are_removed_with_their_contents(self):
        html = render_markdown(
            "<p>Keep</p><script>alert(1)</script><style>p{x:y}</style>"
            '<iframe src="https://evil.example">inner</iframe>'
            '<object data="x">o</object><form action="/x"><button>Go</button></form>'
        )
        self.assertIn("<p>Keep</p>", html)
        for bad in ("script", "alert", "style", "iframe", "inner", "object", "form"):
            self.assertNotIn(bad, html)
        self.assertNotIn("Go", html)

    def test_event_handlers_styles_classes_and_ids_are_removed(self):
        html = render_markdown(
            '<p onclick="x()" style="color:red" class="big" id="a">Text</p>'
            '<a href="https://a.in" onmouseover="x()" target="_blank">L</a>'
        )
        self.assertIn("<p>Text</p>", html)
        for bad in ("onclick", "onmouseover", "style", 'class="big"', "id=", "target"):
            self.assertNotIn(bad, html)

    def test_unknown_wrapper_tags_are_unwrapped_but_keep_their_text(self):
        html = render_markdown("<div><span>Hello</span> <font>there</font></div>")
        self.assertIn("Hello", html)
        self.assertIn("there", html)
        for bad in ("<div", "<span", "<font"):
            self.assertNotIn(bad, html)

    def test_html_images_and_comments_are_removed(self):
        html = render_markdown(
            '<p>A<img src="https://a.in/p.png" onerror="x()"><!-- secret --></p>'
        )
        self.assertNotIn("<img", html)
        self.assertNotIn("onerror", html)
        self.assertNotIn("secret", html)
        self.assertIn("<p>A</p>", html)

    def test_unsafe_html_link_schemes_are_unwrapped(self):
        html = render_markdown(
            '<a href="javascript:alert(1)">a</a> <a href="  JaVaScRiPt:x">b</a> '
            '<a href="java&#9;script:x">c</a> <a href="data:text/html,x">d</a> '
            '<a href="vbscript:x">e</a>'
        )
        self.assertNotIn("href=", html)
        self.assertNotIn("<a", html)
        for text in "abcde":
            self.assertIn(text, html)

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
