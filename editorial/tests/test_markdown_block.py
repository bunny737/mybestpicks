from django.db import connection
from django.test import SimpleTestCase, TestCase
from django.test.utils import CaptureQueriesContext

from catalog.models import Merchant
from catalog.tests.helpers import GOOD_LINK, make_merchant
from editorial.markdown_render import render_markdown, render_markdown_with_links
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


HOSTS = {"track.example.test"}
AFF = "https://track.example.test/c/abc?cid=1"


class AffiliateLinkRenderingTests(SimpleTestCase):
    def test_allowed_host_link_is_marked_sponsored_nofollow_noopener(self):
        html, found = render_markdown_with_links(f"[View at Shopmart]({AFF})", HOSTS)
        self.assertTrue(found)
        self.assertIn('rel="sponsored nofollow noopener"', html)
        self.assertIn(f'href="{AFF}"', html)

    def test_other_links_stay_plain_noopener_and_report_nothing(self):
        html, found = render_markdown_with_links("[x](https://maker.example/p)", HOSTS)
        self.assertFalse(found)
        self.assertIn('rel="noopener"', html)
        self.assertNotIn("sponsored", html)

    def test_no_known_hosts_means_no_affiliate_links(self):
        html, found = render_markdown_with_links(f"[x]({AFF})", None)
        self.assertFalse(found)
        self.assertNotIn("sponsored", html)

    def test_http_link_to_an_affiliate_host_is_unwrapped_not_published(self):
        html, found = render_markdown_with_links(
            "[x](http://track.example.test/c/abc)", HOSTS
        )
        self.assertFalse(found)
        self.assertNotIn("<a", html)
        self.assertIn("x", html)

    def test_credential_looking_query_is_unwrapped(self):
        html, found = render_markdown_with_links(
            "[x](https://track.example.test/c?token=abc)", HOSTS
        )
        self.assertFalse(found)
        self.assertNotIn("<a", html)

    def test_subdomain_and_lookalike_hosts_are_not_affiliate_hosts(self):
        for url in (
            "https://sub.track.example.test/x",
            "https://track.example.test.evil.example/x",
            "https://evil.example/?u=track.example.test",
        ):
            with self.subTest(url=url):
                html, found = render_markdown_with_links(f"[x]({url})", HOSTS)
                self.assertFalse(found)
                self.assertNotIn("sponsored", html)

    def test_html_anchor_is_marked_too_and_its_own_rel_is_ignored(self):
        html, found = render_markdown_with_links(
            f'<p><a href="{AFF}" rel="nofollow" class="evil" style="x:y" '
            f'target="_blank">Go</a></p>',
            HOSTS,
        )
        self.assertTrue(found)
        self.assertIn('rel="sponsored nofollow noopener"', html)
        self.assertNotIn("evil", html)
        self.assertNotIn("style", html)
        self.assertIn('target="_blank"', html)  # ours, not the pasted value

    def test_affiliate_links_open_in_a_new_tab_other_links_do_not(self):
        html, _ = render_markdown_with_links(f"[x]({AFF})", HOSTS)
        self.assertIn('target="_blank"', html)
        html, _ = render_markdown_with_links("[x](https://maker.example/p)", HOSTS)
        self.assertNotIn("target", html)
        html, _ = render_markdown_with_links(
            '<a href="https://maker.example/p" target="_blank">x</a>', HOSTS
        )
        self.assertNotIn("target", html)

    def test_affiliate_link_alone_on_its_line_becomes_a_button(self):
        for source in (
            f"[Check price at Amazon]({AFF})",
            f'<a href="{AFF}" style="background:#f90">Check price at Amazon</a>',
            f'<p><a href="{AFF}">Check price at Amazon</a></p>',
        ):
            with self.subTest(source=source):
                html, found = render_markdown_with_links(source, HOSTS)
                self.assertTrue(found)
                self.assertIn('class="btn btn-primary"', html)
                self.assertIn('rel="sponsored nofollow noopener"', html)
                self.assertNotIn("background", html)

    def test_affiliate_link_inside_a_sentence_stays_a_text_link(self):
        html, found = render_markdown_with_links(f"Buy it [here]({AFF}) today.", HOSTS)
        self.assertTrue(found)
        self.assertNotIn("btn", html)
        self.assertIn('rel="sponsored nofollow noopener"', html)

    def test_non_affiliate_link_alone_on_its_line_is_never_a_button(self):
        html, found = render_markdown_with_links(
            "[Maker](https://maker.example/p)", HOSTS
        )
        self.assertFalse(found)
        self.assertNotIn("btn", html)

    def test_pasted_classes_never_make_a_button(self):
        html, _ = render_markdown_with_links(
            '<p><a href="https://maker.example/p" class="btn btn-primary">Go</a></p>',
            HOSTS,
        )
        self.assertNotIn("btn", html)

    def test_button_in_a_table_cell_is_not_restyled(self):
        html, found = render_markdown_with_links(
            f"| A |\n|---|\n| [Buy]({AFF}) |", HOSTS
        )
        self.assertTrue(found)
        self.assertNotIn("btn", html)

    def test_a_link_inside_a_table_cell_counts(self):
        html, found = render_markdown_with_links(
            f"| A |\n|---|\n| [Buy]({AFF}) |", HOSTS
        )
        self.assertTrue(found)
        self.assertIn('rel="sponsored nofollow noopener"', html)


class MarkdownAffiliatePageTests(TestCase):
    MARKER = "affiliate-disclosure"

    def setUp(self):
        self.merchant = make_merchant()  # allows track.example.test
        self.hub = make_category(mode=DiscoveryMode.FORCE_SHOW)
        self.author = make_author()

    def page(self, text, slug="heaters"):
        article = make_article(
            self.hub,
            self.author,
            slug=slug,
            body=[
                {"type": "paragraph", "value": "<p>Intro.</p>"},
                {"type": "markdown", "value": text},
            ],
        )
        return self.client.get(article.url).content.decode()

    def test_affiliate_link_in_markdown_shows_disclosure_before_the_body(self):
        html = self.page(f"## Pick\n\n[View at Shopmart]({GOOD_LINK})")
        self.assertEqual(html.count(self.MARKER), 1)
        self.assertIn('rel="sponsored nofollow noopener"', html)
        self.assertLess(html.index(self.MARKER), html.index("Intro."))
        self.assertLess(html.index(self.MARKER), html.index('rel="sponsored'))

    def test_two_affiliate_links_still_show_one_disclosure(self):
        html = self.page(f"[a]({GOOD_LINK})\n\n[b]({GOOD_LINK}&n=2)")
        self.assertEqual(html.count(self.MARKER), 1)
        self.assertEqual(html.count('rel="sponsored'), 2)

    def test_no_affiliate_link_means_no_disclosure(self):
        html = self.page("## Pick\n\n[Maker](https://maker.example/p)")
        self.assertNotIn(self.MARKER, html)
        self.assertNotIn("sponsored", html)

    def test_disabled_merchant_links_are_not_affiliate_links(self):
        Merchant.objects.update(enabled=False)
        html = self.page(f"[x]({GOOD_LINK})")
        self.assertNotIn(self.MARKER, html)
        self.assertNotIn("sponsored", html)

    def test_removing_the_host_from_the_allowlist_removes_marking_and_disclosure(self):
        Merchant.objects.update(allowed_link_domains="other.example.test")
        html = self.page(f"[x]({GOOD_LINK})")
        self.assertNotIn(self.MARKER, html)
        self.assertNotIn("sponsored", html)

    def test_markdown_blocks_add_one_query_not_one_per_block(self):
        body = [
            {"type": "markdown", "value": f"[{i}]({GOOD_LINK}&n={i})"} for i in range(5)
        ]
        one = make_article(self.hub, self.author, slug="one", body=body[:1])
        five = make_article(self.hub, self.author, slug="five", body=body)
        self.client.get(one.url)  # warm per-process caches (site, content types)
        with CaptureQueriesContext(connection) as q1:
            self.client.get(one.url)
        with CaptureQueriesContext(connection) as q5:
            self.client.get(five.url)
        self.assertEqual(len(q1), len(q5))

    def test_article_without_markdown_runs_no_merchant_query(self):
        article = make_article(
            self.hub,
            self.author,
            slug="plain",
            body=[{"type": "paragraph", "value": "<p>Hi</p>"}],
        )
        with CaptureQueriesContext(connection) as queries:
            self.client.get(article.url)
        self.assertFalse([q for q in queries if "catalog_merchant" in q["sql"].lower()])


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
