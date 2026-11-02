"""
Seeds the six standing policy pages as unpublished drafts, so they exist in the
page tree (and `home.context_processors._privacy_policy_page` / `contact_email`
have something to find) without anything going live before the owner reviews
and publishes them. This is draft text pending owner/legal review (CLAUDE.md:
"stop and ask" when the plan is silent on privacy/disclosure wording) -- not
binding copy.

Uses the real ``StandardPage``/``HomePage`` classes rather than the historical
``apps.get_model`` versions, because Wagtail's page-tree methods (``add_child``)
only exist on the real classes. This is the usual approach for seeding Wagtail
page content in a migration; it is accepted that a later model change could
require updating this migration.
"""

from django.db import migrations

DRAFT_NOTICE = (
    "<p><em>Draft for owner and, where noted, legal review before publishing. "
    "Edit this text in the Wagtail admin, then publish when it is ready.</em></p>"
)

ABOUT_BODY = DRAFT_NOTICE + (
    "<h2>What MyBestPicks is</h2>"
    "<p>MyBestPicks.in publishes buying guides, comparisons and explainers for "
    "shoppers in India. We started with developer and home-office accessories "
    "because that is what our editors actually use and can speak to firsthand; "
    "other categories will grow the same way, one properly researched hub at a "
    "time.</p>"
    "<h2>How we choose what to cover</h2>"
    "<p>We pick topics readers are actually trying to decide on &mdash; "
    "“which of these should I buy”, not “what exists”. Every "
    "recommendation explains our selection criteria, the evidence behind it, who "
    "it suits, its limitations and when we last checked the facts. See our "
    '<a linktype="page" id="__EDITORIAL_POLICY_ID__">Editorial Policy</a> for '
    "the detail.</p>"
    "<h2>How we're funded</h2>"
    "<p>Some links on this site may be affiliate links, as explained in our "
    '<a linktype="page" id="__AFFILIATE_DISCLOSURE_ID__">Affiliate '
    "Disclosure</a>. We do not have a revenue target for the first 90 days, and "
    "a product's ranking is never for sale.</p>"
    "<h2>Get in touch</h2>"
    "<p>Questions, corrections or a product you think we should cover? See our "
    '<a linktype="page" id="__CONTACT_ID__">Contact</a> page.</p>'
)

CONTACT_BODY = DRAFT_NOTICE + (
    "<h2>Questions, corrections and tips</h2>"
    "<p>Spotted something inaccurate, out of date, or have a product you think "
    "we should review? We read every message.</p>"
    "<p>Set a contact email in the Wagtail admin under Settings &rsaquo; Site "
    "Settings so it appears below, and so our Privacy Policy can point readers "
    "to it for data requests. Nothing is shown here until it is set &mdash; we "
    "never invent a contact address.</p>"
)

EDITORIAL_POLICY_BODY = DRAFT_NOTICE + (
    "<h2>Our standard for every recommendation</h2>"
    "<p>Every product we recommend comes with: the selection criteria we used, "
    "the evidence behind the claim, who the product suits, its known "
    "limitations and alternatives, and the date we last checked the facts. A "
    "list based only on desk research is never presented as a hands-on "
    "review.</p>"
    "<h2>What “tested by our editor” means</h2>"
    "<p>We mark a product as hands-on tested only when an editor actually used "
    "it, and only alongside evidence &mdash; notes on what was done and "
    "observed, or a photo we took ourselves. We do not imply hands-on "
    "experience any other way.</p>"
    "<h2>Images</h2>"
    "<p>We do not use retailer listing photos. Every image we publish is our "
    "own, manufacturer-licensed, otherwise licensed with evidence kept on file, "
    "or permitted affiliate-program content used within that program's terms.</p>"
    "<h2>Prices</h2>"
    "<p>We do not publish prices, price widgets or scraped pricing. If a "
    "headline implies a price point (for example, “under &#8377;2,000”), "
    "it is only used while the products behind it have been recently "
    "re-verified; otherwise we rewrite the headline to be price-neutral.</p>"
    "<h2>Independence</h2>"
    "<p>Whether a link is monetised never affects which products we recommend "
    "or how we rank them. See our "
    '<a linktype="page" id="__AFFILIATE_DISCLOSURE_ID__">Affiliate '
    "Disclosure</a>.</p>"
    "<h2>Corrections</h2>"
    "<p>If we get something wrong, we fix it and note the correction. Tell us "
    'via the <a linktype="page" id="__CONTACT_ID__">Contact</a> page.</p>'
)

AFFILIATE_DISCLOSURE_BODY = DRAFT_NOTICE + (
    "<h2>How this works</h2>"
    "<p>Some outbound links on MyBestPicks may be affiliate links &mdash; for "
    "example, through Cuelinks for Flipkart, and potentially Amazon in future. "
    "Where an affiliate link is active, we may earn a small commission if you "
    "buy something after clicking it, at no extra cost to you.</p>"
    "<p><strong>At publication of this page, no affiliate program has been "
    "finalised on this site.</strong> Links may say “may be used in "
    "future” while that remains true; this page is updated as soon as any "
    "affiliate relationship goes live. We do not claim Amazon Associate status "
    "or any other program membership before it is actually in effect.</p>"
    "<h2>What never changes</h2>"
    "<ul>"
    "<li>Our recommendations and rankings are decided before any monetisation "
    "question, and commission never buys a better ranking.</li>"
    '<li>Every affiliate link uses <code>rel="sponsored nofollow noopener"</code> '
    "and plain-language buttons such as “View at Flipkart”, never a "
    "disguised or cloaked redirect.</li>"
    "<li>This notice appears on an article before its first affiliate link, "
    "whenever one is present.</li>"
    "</ul>"
)

PRIVACY_POLICY_BODY = DRAFT_NOTICE + (
    "<p><em>This page needs a legal review for India's Digital Personal Data "
    "Protection (DPDP) Act before publishing, since its phased provisions are "
    "still commencing. Treat the text below as a starting point, not advice.</em></p>"
    "<h2>What we collect</h2>"
    "<p>If you subscribe to email updates, we store your email address, the "
    "date you consented, which version of this notice you agreed to, and &mdash; "
    "once you confirm &mdash; the date you confirmed. That's all: no name, no "
    "other profile data, and we never import contacts from our Telegram "
    "channel.</p>"
    "<h2>What we do not do</h2>"
    "<ul>"
    "<li>We do not log individual clicks on affiliate links on our own servers.</li>"
    "<li>We do not sell personal data.</li>"
    "<li>We do not show you an advertisement or load a third-party advertising "
    "or analytics script before you have given consent, where consent is "
    "required.</li>"
    "</ul>"
    "<h2>Analytics</h2>"
    "<p>We use Google Search Console to understand search performance, and may "
    "use privacy-reviewed, self-hosted analytics (Umami) to understand visits "
    "at an aggregate level. Any cookie-based analytics or advertising only runs "
    "after you consent, where that consent is required under applicable law.</p>"
    "<h2>Your choices</h2>"
    "<p>Every email we send includes an unsubscribe link, which deletes your "
    "email address immediately. You can also ask us to delete your data by "
    "writing to us &mdash; see our "
    '<a linktype="page" id="__CONTACT_ID__">Contact</a> page.</p>'
    "<h2>Changes</h2>"
    "<p>If this notice changes materially, we will update the date below and, "
    "where it affects existing subscribers, note it in our next email.</p>"
)

TERMS_BODY = DRAFT_NOTICE + (
    "<p><em>This page needs owner and, ideally, legal review before "
    "publishing.</em></p>"
    "<h2>What this site is</h2>"
    "<p>MyBestPicks.in is an editorial site. We publish buying guides, "
    "comparisons and explainers. We are not a retailer: we do not sell "
    "products, process payments or handle your orders.</p>"
    "<h2>Using our content</h2>"
    "<p>You may read, share and link to our articles. Please do not republish "
    "our text or images elsewhere without asking first.</p>"
    "<h2>Outbound links</h2>"
    "<p>Links to retailers and other third-party sites take you to pages we do "
    "not control. We are not responsible for their content, pricing, "
    "availability or policies. See our "
    '<a linktype="page" id="__AFFILIATE_DISCLOSURE_ID__">Affiliate '
    "Disclosure</a> for how some of those links are monetised.</p>"
    "<h2>No guarantee</h2>"
    "<p>We research carefully and disclose our evidence, but we cannot "
    "guarantee that any product remains available, priced as described "
    "elsewhere, or suited to every use case. Always check current details with "
    "the retailer before buying.</p>"
    "<h2>Changes</h2>"
    "<p>We may update these terms as the site grows; the current version always "
    "applies.</p>"
)

PAGES = [
    {"key": "about", "title": "About", "slug": "about", "body": ABOUT_BODY},
    {"key": "contact", "title": "Contact", "slug": "contact", "body": CONTACT_BODY},
    {
        "key": "editorial_policy",
        "title": "Editorial Policy",
        "slug": "editorial-policy",
        "body": EDITORIAL_POLICY_BODY,
    },
    {
        "key": "affiliate_disclosure",
        "title": "Affiliate Disclosure",
        "slug": "affiliate-disclosure",
        "body": AFFILIATE_DISCLOSURE_BODY,
    },
    {
        "key": "privacy_policy",
        "title": "Privacy Policy",
        "slug": "privacy-policy",
        "body": PRIVACY_POLICY_BODY,
    },
    {"key": "terms", "title": "Terms", "slug": "terms", "body": TERMS_BODY},
]

SLUGS = [page["slug"] for page in PAGES]


def create_policy_pages(apps, schema_editor):
    from editorial.models import StandardPage
    from home.models import HomePage

    home = HomePage.objects.first()
    if home is None:
        return

    # Per-slug, not all-or-nothing: a database that already has some of these
    # pages (for example from manual admin testing) still gets the missing ones,
    # and an existing page is never touched.
    existing_by_slug = {
        page.slug: page for page in StandardPage.objects.filter(slug__in=SLUGS)
    }

    ids_by_key = {}
    created = []
    for page_data in PAGES:
        existing_page = existing_by_slug.get(page_data["slug"])
        if existing_page is not None:
            ids_by_key[page_data["key"]] = existing_page.pk
            continue
        page = StandardPage(
            title=page_data["title"],
            slug=page_data["slug"],
            body=page_data["body"],
            live=False,
            show_in_menus=True,
        )
        home.add_child(instance=page)
        ids_by_key[page_data["key"]] = page.pk
        created.append(page)

    # Cross-link the pages now that every page (and so its id) exists.
    replacements = {
        "__ABOUT_ID__": ids_by_key["about"],
        "__CONTACT_ID__": ids_by_key["contact"],
        "__EDITORIAL_POLICY_ID__": ids_by_key["editorial_policy"],
        "__AFFILIATE_DISCLOSURE_ID__": ids_by_key["affiliate_disclosure"],
        "__PRIVACY_POLICY_ID__": ids_by_key["privacy_policy"],
        "__TERMS_ID__": ids_by_key["terms"],
    }
    for page in created:
        body = page.body
        for placeholder, page_id in replacements.items():
            body = body.replace(placeholder, str(page_id))
        if body != page.body:
            page.body = body
            page.save()


def remove_policy_pages(apps, schema_editor):
    from editorial.models import StandardPage

    StandardPage.objects.filter(slug__in=SLUGS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("editorial", "0003_alter_articlepage_body"),
        ("home", "0008_sitesettings_contact_email"),
    ]

    operations = [
        migrations.RunPython(create_policy_pages, remove_policy_pages),
    ]
