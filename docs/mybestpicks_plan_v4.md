# MyBestPicks.in — Audience-First Django + Wagtail + PostgreSQL Launch Plan (v4 — final baseline)

**Status:** Implementation baseline v4 — architecture frozen; Telegram audience-distribution addendum integrated; remaining refinements belong in code review  
**Prepared:** 1 November 2026  
**Primary domain:** https://mybestpicks.in/  
**Target audience:** India (English-language content, INR buying context)  
**Business model:** Content and audience first; optional later Amazon Associates, **Flipkart through Cuelinks**, and Google AdSense  
**Project goal:** Establish an audience for original, fast, trustworthy product advice, initially for developer setups, with flexible expansion into other categories. No first-90-day revenue target; prioritize search, useful referral distribution and an owned subscriber channel.

> **Decision:** Use **Django + Wagtail CMS + PostgreSQL**, server-rendered Django templates, Bootstrap 5, and limited JavaScript. Do not introduce React or a separate API in the MVP. Domain control, current DNS, affiliate credentials, product rights, and live hosting configuration must be verified before deployment.

---

## 1. Product vision and launch scope

### Positioning

**MyBestPicks** helps shoppers in India make informed product decisions using clearly explained comparisons, practical buying criteria, and transparent affiliate disclosures. It is **not** an e-commerce checkout site and does not represent that it personally tested items unless it did.

### Initial editorial category hubs — extensible

1. Home & Kitchen — organizers, lights, space-saving home tools.
2. Developer Setup — keyboards, laptop stands, hubs, accessories for coding.
3. Car Accessories — dashcams, phone mounts, cleaning tools.
4. Gadgets & Tech — chargers, power banks, USB-C accessories.
5. Home Office — chairs, monitor arms, desk lighting.

**Launch focus:** Developer Setup is the first visible hub. Create **Developer Setup** first. Create other hubs only when their first article is ready; publish each parent `CategoryPage` before its first child article so breadcrumbs and URLs resolve. Visibility is independent of publication and follows the three-way `discovery_mode` policy in Section 5A. The threshold applies to discoverability, **not** article publishing. New categories may be added via Wagtail Admin at any time; see Section 5A.

### MVP includes

- Editorial homepage, live category URLs with separate editorial discovery controls, and Wagtail-created categories without code changes.
- Buying guides, comparisons, explainers, and evergreen tutorials.
- Wagtail authoring workflow: drafts, previews, scheduling, publishing, revisions.
- Reusable product cards, comparison tables, pros/cons and editorial verdicts; conditional disclosures only when active affiliate offers are shown.
- Structured product catalog (editorial metadata) and separate **optional** merchant offers; articles can launch without any merchant links.
- Wagtail image/document handling, responsive templates and search.
- Canonical tags, sitemap, robots.txt, breadcrumbs, metadata, redirects, RSS feed, a visible existing Telegram channel link, privacy-conscious audience analytics and basic schema.
- Secure operations: backups, HTTPS, admin restrictions, and error monitoring.

### Out of scope until meaningful traffic

- Retail checkout, user accounts, comments, mobile app, scraping, live price history, dynamic pricing, automated deal feed, complex personalization, multi-language support and a frontend SPA.

### Metrics (targets, not forecasts)

| By | Editorial | Technical | Business |
|---|---|---|---|
| End of week 2 | Two drafts, one evidence-backed hands-on guide | **Minimal production deploy available**, CMS/editor models functional | Search Console setup and content workflow confirmed |
| End of week 4 | Four to six published articles, additional drafts | Public site, sitemap, Search Console, privacy controls | Baseline indexing and impressions recorded; **no sales goal** |
| End of week 8 | Eight to twelve published articles | Comparison components, broken-link audit, performance baseline | Review top impressions and queries; improve internal links |
| End of week 12 | **12–18** quality articles; **30 stretch only** | SEO/QA audit and backup restore test | Track search impressions, clicks, indexing, referral discovery and reader subscriptions; zero revenue is fine |

### Audience acquisition from launch (not only SEO)

- **Search:** publish focused original developer-setup guides; watch Search Console indexing, queries and impressions. A new domain may attract little search traffic initially.
- **Community:** share genuinely helpful insights (not link dumps) on LinkedIn and relevant developer groups; respect self-promotion rules, and record referral sources.
- **Owned channels:** expose `/feed/` RSS in the header/footer; link the existing Telegram channel on the homepage/article footer; add a minimal optional email signup with clear privacy notice, unsubscribe process and verified consent where feasible. Store only necessary data and avoid building a complex newsletter platform.
- **Telegram:** share concise original takeaways, article links and periodic polls; do not treat the channel as a deal-spam feed. Begin with manual publishing and UTM-tagged links; automation is a post-launch convenience, not a blocker.
- **Measurement:** Search Console is authoritative for Google search performance; use privacy-reviewed self-hosted Umami or similar for visitor/referral trends. A cookieless deployment **does not automatically establish legal consent exemption**—review analytics configuration, local laws and hosting/cross-border data flows. GA4 is optional, not the default MVP dependency.

---

## 2. Stack, versions and reference repositories

| Layer | Decision | Rationale |
|---|---|---|
| Python | Supported Python 3.x, pin a compatible stable release | Avoid compatibility surprises |
| Framework | Django version compatible with pinned Wagtail release | Productive ORM, auth, security |
| CMS | Stable Wagtail release, pinned in dependencies | Page tree, editing, preview, scheduling |
| DB | PostgreSQL, current supported major release | Reliable relational structure and indexing |
| Presentation | Django templates + Bootstrap 5 + minimal JS | Search-readable HTML, fast initial build |
| Web serving | Gunicorn + Nginx or managed app platform | Straightforward production setup |
| Static files | WhiteNoise or CDN/object storage as deployment requires | Efficient static delivery |
| Media | Persistent local Docker volume initially, backed up off-box nightly | Keep original images and Wagtail renditions persistent; object storage later |
| Local setup | Python venv + Docker Compose for PostgreSQL (optional) | Easy Windows development |
| CI | GitHub Actions | Tests, security checks and deployment gating |
| Analytics | Google Search Console + optional self-hosted Umami; GA4 only if separately justified and consent-configured | Search performance plus privacy-conscious audience measurement |

**Version policy:** Verify current Wagtail/Django/Python/PostgreSQL compatibility at installation, choose maintained stable versions, pin them in the lock/requirements workflow, and record versions in README. Never use unpinned `latest` in production.

References:
- Wagtail: https://github.com/wagtail/wagtail
- Wagtail installation: https://docs.wagtail.org/en/stable/getting_started/tutorial.html
- Integration: https://docs.wagtail.org/en/stable/getting_started/integrating_into_django.html
- StreamField: https://docs.wagtail.org/en/stable/topics/streamfield.html
- Snippets: https://docs.wagtail.org/en/stable/topics/snippets.html
- Wagtail Bakery Demo (reference only, not a production affiliate starter): https://github.com/wagtail/bakerydemo

---

## 3. Repository layout and Wagtail bootstrap

**Choose the final package layout before the first migration.** The Wagtail starter creates a project package named `mybestpicks` (including `mybestpicks/settings/`), not `config/settings/`.

Use the starter's native layout for the MVP; add top-level apps directly to avoid unnecessary app-label churn:

```text
mybestpicks/
├── mybestpicks/
│   ├── settings/{base,dev,production}.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── home/                  # homepage, navigation, site settings
├── editorial/             # category, article, author pages, blocks
├── catalog/               # products, brands, merchants, offers, schemas
├── seo/                   # thin JSON-LD and template-tag helpers ONLY
├── templates/
│   ├── base.html
│   └── components/{product_card,comparison_table,affiliate_disclosure}.html
├── static/{css,js,icons}/
├── tests/
├── requirements/          # pinned dependencies
├── compose.yaml
├── Dockerfile
├── .env.example
├── .github/workflows/ci.yml
├── manage.py
└── README.md
```

If you later move apps under `apps/`, update dotted `AppConfig.name`, imports, and installed app paths consistently **before migrations**. Prefer Wagtail built-ins: `wagtail.contrib.sitemaps`, `wagtail.contrib.redirects`, `wagtail.contrib.settings`; use `RoutablePageMixin` only if a page genuinely needs custom routes. Search uses Wagtail's database search backend with PostgreSQL. No Elasticsearch or separate SPA.

---

## 4. Content types and data model

### Wagtail page types

| Page/model | Important fields / behavior |
|---|---|
| `HomePage(Page)` | hero, featured guides, curated category links, trust panel |
| `CategoryPage(Page)` | title, introduction, banner, featured guides, child article listing; `discovery_mode` (`force_hide`/`auto`/`force_show`), computed `live_child_count`, derived `is_discoverable` |
| `ArticlePage(Page)` | article kind, excerpt, author, featured image, body StreamField, published/reviewed dates, methodology, affiliate flags |
| `StandardPage(Page)` | About, Contact, Editorial Policy, Privacy, Affiliate Disclosure, Terms |
| `AuthorPage(Page)` | name, bio, expertise, editorial contributions |

Use Wagtail's built-in `Page` fields for SEO title, search description, slug, live status, and publication state; avoid duplicate custom SEO columns without a clear need.

### Product and merchant models

- `Brand` snippet: `name`, `slug`, optional `website`.
- `Product` snippet: `brand`, `name`, `model_number`, **`product_type`** (e.g. `keyboard`, `usb_c_hub`, `laptop_stand`), `key_specs` (validated against a **product-type-specific schema**), image with documented licensing/ownership, `status`, `last_verified_at`. Product type is independent of editorial category/hub.
- **Choose one approach for MVP:** versioned Python `PRODUCT_SPEC_SCHEMAS` mapping in `catalog/specs.py` keyed by `product_type`. Each spec has canonical key, label, unit, value type, comparable/required flags, display order. Validate with `Product.clean()`; no spec admin model or migrations. Example: `power_watts` displayed as `Power (W)`. Move schemas to database only if non-developer editing becomes necessary.
- `Merchant`: `name`, `destination_domain` (e.g. `flipkart.com`), `network` (direct / Cuelinks), `allowed_link_domains` (explicit allowlist), enabled, disclosure notes.
- `MerchantOffer`: FK product, FK merchant, `affiliate_url`, `destination_product_url` (optional URL used for human review), `last_checked_at`, `active`, `campaign_notes`. **No price columns in the MVP.**
- `EditorialSource`: article, source name, URL, access date, type; support research audit.
- **No `ArticleProduct` model**: per-article verdict, pros/cons, ranking and evidence live exclusively in the article's product StreamField blocks.
- **No `AffiliateClickEvent` table in the MVP**: if affiliate reporting is later needed, enable consent-aware GA4 custom outbound-click events; merchant dashboards remain the source of truth for conversions.

`Product` facts are globally reusable. Article-specific editorial judgment exists **only in StreamField**. Wagtail's reference index supports finding pages that refer to snippets; verify its behavior for the chosen chooser/block implementation and test reference changes.

### StreamField blocks for `ArticlePage`

- `RichTextBlock`, `HeadingBlock`, `ImageBlock` with captions/license attribution.
- `KeyTakeawaysBlock`, `BuyingCriteriaBlock`.
- `ProductCardBlock`: `SnippetChooserBlock` referencing `Product`, plus **article-specific** verdict, pros, cons, recommendation label, editorial evidence, and `tested_by_editor` flag backed by notes or images. No duplicated `ArticleProduct`.
- `ComparisonTableBlock`: derive ordered products from the article's existing `ProductCardBlock` instances at render time; optionally configure which canonical specs to show. **Never re-select products** in the table editor.
- `FAQBlock`, `SourceNoteBlock`, `RelatedArticlesBlock`; template-level disclosure only if `article_products` includes at least one active rendered offer.

**Rendering contract:** `ArticlePage.get_context()` collects all ordered `ProductCardBlock` values **before any body block is rendered**, resolves each referenced product and active offers, validates and normalizes its product-type specs once, then passes `article_products` into quick picks, comparison tables, and product-card templates. The comparison table may appear above cards because it uses the precomputed context. Avoid per-card database queries (`select_related`/batch retrieval as appropriate). Multiple tables may select a subset of the collected card IDs; never re-choose a product.

### Data validation and editorial safeguards

- Require approved `https://` URLs; parse the **tracking-link hostname** and compare it against `Merchant.allowed_link_domains`, not the destination retailer domain alone. Maintain Cuelinks hostname allowlists based on verified links issued to this account; do **not** accept arbitrary third-party redirectors.
- Store `network=Cuelinks` and `destination_domain=flipkart.com` separately. Keep merchant display labels clear (“View on Flipkart”); track source network internally.
- Reject affiliate URLs with suspicious credentials/parameters and unsupported schemes; inspect actual destination manually before activation. Do not blindly resolve arbitrary redirects server-side (SSRF risk).
- No price fields or static price widgets. **Price-dependent titles** such as “under ₹1,000” need a `last_verified_at` check and a re-verification task (suggest every 30 days; sooner for volatile categories); unverified titles must be rewritten.
- Enforce hands-on evidence in **`ProductCardBlock.clean(value)`**: if `tested_by_editor=True` and evidence notes/media reference is absent, raise `ValidationError`; add unit tests for both valid and invalid inputs. Do not imply hands-on experience otherwise. Require license status, research sources, and review dates.
- Keep author identity as an `AuthorPage`, linked from articles, with a biography and description of research/testing experience.

---

## 5. Site URLs, navigation and homepage

### URL patterns

```text
/
/home-kitchen/
/home-kitchen/best-kitchen-organizers-small-kitchens/
/developer-setup/
/developer-setup/best-keyboards-for-coding/
/car-accessories/
/gadgets/
/home-office/
/about/
/contact/
/editorial-policy/
/affiliate-disclosure/
/privacy-policy/
/terms/
/search/
/sitemap.xml
/robots.txt
/admin/                        # Wagtail admin, security controls
```

Use Wagtail's page tree to support category/child article paths. Establish URL conventions before publishing; add 301 redirects whenever slugs change. Decide apex as canonical (`https://mybestpicks.in/`) and redirect `www` to it.

### 5A. Adding and managing categories in the future (no migration required)

**Editorial hubs and product types are different concepts:** a Wagtail `CategoryPage` is a browsing/SEO destination, while `Product.product_type` is a technical spec-validation key. A USB-C hub may appear in articles in both Developer Setup and Gadgets without changing its product type.

**How to create a category:** In Wagtail Admin → Pages → Home → Add child → Category Page; enter title, unique slug, introduction and optional hero image. Publish it as a **live page** before publishing child articles, so breadcrumbs and parent URLs stay valid. Add `ArticlePage` children via the editor, or relocate an article using Wagtail's page move feature with redirects for any URL changes. Wagtail's page tree makes this possible without coding or schema migrations.

**Discoverability policy (single source of truth):**

```python
DISCOVERY_MODES = [
    ("auto", "Auto (≥3 live articles)"),
    ("force_show", "Always show"),
    ("force_hide", "Always hide"),
]

discovery_mode = models.CharField(
    max_length=16,
    choices=DISCOVERY_MODES,
    default="force_hide",
)


@property
def is_discoverable(self):
    if self.discovery_mode == "force_show":
        return True
    if self.discovery_mode == "force_hide":
        return False
    return self.get_children().type(ArticlePage).live().count() >= 3
```

- `live_child_count` is a **count of live direct `ArticlePage` children**, not a subjective quality score. The snippet illustrates the behavior; implement an efficient, tested queryset in the app.
- `force_hide` is the safe default. Editors can explicitly feature a strong hub with fewer than three articles using `force_show`, or withhold a weak hub regardless of count using `force_hide`. Set `auto` only after editorial review.
- Only **live and discoverable** hubs appear in navigation, homepage tiles and category directories. `show_in_menus` is a secondary editor option, not the discovery rule.
- Undiscoverable hubs remain live (to support child article URLs and breadcrumbs) but the **hub itself** gets `noindex,follow` and is excluded from sitemap via `CategoryPage.get_sitemap_urls()`. Published article children remain independently indexable and in the sitemap. A noindex tag is not an immediate removal guarantee.
- Do not create empty Car Accessories, Gadgets or Home Office hubs just to complete a menu. Create the parent as the first article is ready; **publish parent before child**. If a hub is live but empty, render a useful introductory/coming-soon state, never a broken grid.
- Navigation queries eligible categories dynamically, with suitable cache invalidation on publication or mode changes.

**Example expansion:** Add a new `Fitness Accessories` hub in Wagtail Admin when the first guide is ready → publish the hub (`force_hide`) → publish articles → after quality review choose `auto` or `force_show`. No code change or migration is required for a new editorial category.

**When code changes are required:** New **editorial category**: no code. New **product type** (e.g. `fitness_tracker`): add a key and field definitions to `catalog/specs.py`, update product-type choices/configuration and tests, then deploy. Existing product types can be reused across multiple hubs.

**Article categorization convention:** Each `ArticlePage` has one primary `CategoryPage` parent to keep URLs and breadcrumbs stable. Cross-topic discovery uses tags, search, related articles, and manually curated links; avoid duplicating the same article under two hubs.

### Homepage hierarchy

1. Logo, primary category navigation and visible search.
2. Hero: **“Find the Best Picks for Everyday Life.”** Supporting line explains independent buying guides.
3. Cards for **live categories whose `is_discoverable` is true**; never gate the homepage using a separate hard-coded article-count rule.
4. Featured guides (hand-picked by editors; not keyword stuffing).
5. Latest comparisons and recently updated articles.
6. Budget-buying collections only where price bounds are re-verified and `last_verified_at` is recent; otherwise use price-neutral selection labels.
7. “How We Choose” editorial methodology and affiliate transparency.
8. Footer: legal pages, contact, and social channels.

### Article template hierarchy

1. Breadcrumb, H1, accurate author/reviewed dates.
2. Short answer and methodology; only show an in-article affiliate disclosure before placements **if a visible card has at least one active offer**.
3. Quick picks with who each is for.
4. Mobile-friendly comparison table.
5. Detailed product discussions, negatives, compatibility, availability caveats.
6. Buying advice, FAQ where useful, sources and alternatives.
7. Related guides and final editorial update date.

---

## 6. Affiliate implementation and compliance

### Link rendering rules

**Deferred implementation:** Do not require an affiliate URL for any article or product card. When enabled, use dashboard-generated Cuelinks deeplinks stored server-side; never inject the Cuelinks auto-convert JavaScript.

- Each `MerchantOffer` stores a program-approved URL, **network attribution** and a separately validated tracking link domain; review destination and tags manually.
- Render `rel="sponsored nofollow noopener"` on affiliate outbound anchors; open in same tab unless justified otherwise.
- Prefer direct, approved affiliate URLs to opaque cloaked redirects. If click tracking is used, record a privacy-safe event on the page before normal navigation; do not impair merchant attribution.
- Label buttons **“Check price at Amazon”**, **“View at Flipkart”** rather than suggesting an internal checkout.
- Use price-neutral CTA when live authorized prices cannot be reliably maintained.
- Do not copy retailer photos, reviews, descriptions, ratings, or prices without rights and program permission.
- Do not mix Amazon-sourced restricted API content with competitor promotion in a way disallowed by Amazon license. Have a compliance review before integrating automatic product APIs.
- Confirm `mybestpicks.in` and the publishing channel are authorized by Cuelinks and Amazon (when applied); check Cuelinks Flipkart campaign availability before using its links.
- Show an in-article affiliate disclosure **only when `article_products` includes an active merchant offer that will render**, positioned before the first affiliate CTA. Never claim Amazon Associate status until the site/account is actually accepted into the program; only then display Amazon’s required identification in the appropriate site location. The standalone Affiliate Disclosure policy page may state that affiliate links **may be used in future** when none are active.
- Review applicable ASCI advertising disclosure requirements and Indian privacy/tax rules; use professional advice as needed.

### Confirmed affiliate route and program timing

**Flipkart is via Cuelinks, not direct Flipkart Associates.** Verify the live campaign's participation rules, payout by category, deeplink behavior and attribution in the signed-in Cuelinks dashboard before publishing. Cuelinks's public Flipkart campaign lists a **30-minute cookie duration**, tracking and validation rules, and campaign-dependent rates; do not promise specific payout percentages. Flipkart is secondary income until dashboard data shows otherwise. Reference: https://www.cuelinks.com/campaigns/flipkart-affiliate-program

**Amazon India application timing:** Official Amazon India documentation requires **at least three qualifying sales in the first 180 days**, excluding personal orders, for review; Amazon describes **at least 10 publicly accessible original posts** as a useful benchmark. Do **not** apply automatically at week 1, week 2, or week 4 with only 4–6 articles. Apply when there are at least 10 substantive public articles and a plausible path to qualified sales. If an Amazon account already exists, **check its actual application/approval/clock status** rather than assuming a fresh 180 days. References: https://affiliate-program.amazon.in/help/node/topic/G8TW5AE9XL2VX9VM and https://affiliate-program.amazon.in/help/node/topic/G7MJTPEP9NC3YKMG

### Amazon / Cuelinks–Flipkart implementation stages

| Stage | Scope |
|---|---|
| MVP | Manual product research and authorized imagery; **zero merchant links required**. `MerchantOffer` infrastructure may exist but need not be populated. No automatic prices. |
| Later | API integrations only with verified credentials, terms, licensing, eligibility and cache lifetimes |
| Later | Broken-link checks, merchant eligibility alerts and compliance audit trail |

Keep attribution and conversion data in official affiliate dashboards as the source of truth; website clicks are not equivalent to orders.

---

## 7. SEO, discoverability and quality assurance

### Technical checklist

- Render full article text server side; no essential SEO content hidden behind client-side scripts.
- Descriptive page-specific title, meta description, one main H1, canonical URL, valid HTTP status.
- Add XML sitemap through Wagtail's sitemap support; include live canonical indexable pages.
- Add robots.txt and block nonpublic staging via authentication or indexing prevention; do not block production articles.
- Use `Article` / `BlogPosting` JSON-LD where appropriate and `BreadcrumbList` on article/category pages. Use product review markup only when genuinely eligible and truthful; do not invent aggregate ratings.
- Compress images, serve WebP/AVIF renditions when practical, provide width/height and alt text; lazy load below-fold media.
- Optimize Core Web Vitals, especially LCP and CLS; cache public pages appropriately and avoid excessive scripts.
- Breadcrumbs, contextual internal links, distinct page intent, author/methodology pages.
- Search Console: verify the domain/apex property, submit sitemap, monitor indexing and performance.
- Analyze query intent and current India search results before writing. Do not mass-produce near-duplicate “best” articles.

### Product image sourcing (critical editorial dependency)

Do not download Amazon or Flipkart listing photos just because they are public. Build an image provenance field (`owned_original`, `manufacturer_licensed`, `other_licensed`, `permitted_program_content`) and store license evidence/credit. Prefer original photos of equipment actually owned/tested, then written permission or licensed manufacturer media. Plan for image sourcing in every article's research hours. When no legal image is available, use a text/specification-based card rather than questionable photography.

### Editorial standards

Every recommendation should explain: **selection criteria, evidence, fit, limitations, alternatives, and research date**. Don't call research-only lists hands-on reviews. Track source citations privately and publish useful references as needed. Review content when products become unavailable or materially change.

### Performance and accessibility acceptance criteria

- Mobile nav, cards and horizontally scrolling tables function down to 320px viewport.
- Keyboard navigation, visible focus states, meaningful link labels and contrast checks.
- Images do not cause major layout shifts.
- All published pages load over HTTPS without mixed content.
- No critical broken internal links; no invalid structured-data syntax.

---

## 8. Local environment and onboarding

### Initial bootstrap (commands are illustrative; check stable compatible versions first)

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install wagtail psycopg[binary] django-environ gunicorn
wagtail start mybestpicks
cd mybestpicks
# Wagtail generates mybestpicks/settings/; modify it before first migration
# Set DATABASE_URL to a local PostgreSQL instance via .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

For a clean repo, it may be simpler to run `wagtail start mybestpicks` in a new empty folder, then add apps and PostgreSQL settings. Always inspect generated settings and requirements before combining scaffolding commands. On Windows, Gunicorn is for Linux production, not local development.

### Environment variables

```dotenv
DJANGO_SETTINGS_MODULE=mybestpicks.settings.dev
SECRET_KEY=replace-with-generated-secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://mybestpicks:password@localhost:5432/mybestpicks
WAGTAILADMIN_BASE_URL=http://localhost:8000
SITE_URL=http://localhost:8000
# Production values managed by hosting secret store; never commit credentials.
```

For deployment, set `DEBUG=False`, a production secret, secure cookie and CSRF settings, proper trusted origins, allowed hosts, live site URL, persistent media backend, and database TLS if provider requires it. `manage.py check --deploy` should pass without security-critical warnings.

### CI and code quality

- Ruff or equivalent formatter/linter; unit tests and Django/Wagtail system checks.
- Migration check: `makemigrations --check --dry-run` and test database migrations.
- Render tests for home/category/article pages and schema output.
- Validate product blocks, merchant domains, disclosure rendering, redirect behavior and sitemap exclusions.
- Dependabot/Renovate alerts and periodic dependency updates.

---

## 9. Production hosting and deployment

**MVP production architecture:** Cloudflare (optional proxy/DNS) → Nginx → Gunicorn/Django/Wagtail + PostgreSQL on **one small VPS via Docker Compose**. Persist DB and Wagtail media in named volumes. Back up **both** nightly to a separate off-box destination, keep retention, and rehearse restoration. Delay object storage until needed.

### Deployment sequence

1. Back up and inspect current `mybestpicks.in` DNS and any existing site; ensure no important content will be overwritten.
2. Create production host and PostgreSQL; choose automatic backups and monitor database storage.
3. Set env secrets; deploy pinned app dependencies; run migrations and `collectstatic`.
4. Configure persistent image storage; test uploads and image renditions.
5. Configure Wagtail Site hostname/port and default root page; set `WAGTAILADMIN_BASE_URL`.
6. Set HTTPS, apex canonical redirect and DNS records.
7. Test `/admin/`, robots, sitemap, homepage, article preview, affiliate links and search.
8. Connect Search Console, submit sitemap and check crawl accessibility.
9. Set daily DB backups, restore test, uptime alerts and rollback procedure.

**Hosting estimate:** Budget roughly ₹3,000–₹8,000 for the first 90 days including domain/hosting/miscellaneous if coding is done in-house, but actual pricing depends on provider, media, traffic and purchases for product testing. Do not choose a hosting vendor solely on a teaser price.

---

## 10. Twelve-week execution plan — realistic solo-developer schedule

**Scheduling rule:** Weeks 1–2 are mainly infrastructure and **drafting**. A minimal public deployment is available in week 2 so publishing never precedes launch. Only count articles as *published* after they're accessible publicly and pass QA. Baseline: **12–18 substantive pieces in 12 weeks**, 1–2 per week after the initial build; 30 remains a **stretch goal**, not a promised outcome. Dates below run from November 1, 2026; allow flexible shifts for product verification.

| Week | Engineering & operations | Editorial deliverable | Baseline cumulative live |
|---|---|---|---:|
| 1 (Nov 1–7) | Wagtail starter, Postgres, environment, models planned, staging | Draft: ergonomic coding desk and laptop-stand guide; gather own photos | 0 |
| 2 (Nov 8–14) | Minimal production deploy, HTTPS, basic editorial templates, author + policy pages; add existing Telegram channel link | Publish first evidence-backed developer guide if ready (otherwise keep as draft; **deploy takes priority**) | 1 |
| 3 (Nov 15–21) | Product snippets, article cards, affiliate offer model (links optional) | Publish laptop-stand guide and a USB-C hub compatibility explainer | 3 |
| 4 (Nov 22–28) | Search Console, sitemap, privacy-conscious analytics, RSS and category visibility rules; establish manual Telegram post template and UTM convention | Publish mechanical-vs-membrane comparison and coding keyboard buying guide | 5 |
| 5 (Nov 29–Dec 5) | Derive comparison tables from product cards; editorial QA | Publish USB-C hubs for developers (verified specs) | 6 |
| 6 (Dec 6–12) | Validate product-type Python spec schema, performance fixes | Publish monitor arms or keyboard ergonomics guide | 7 |
| 7 (Dec 13–19) | Image provenance QA, internal links and site search | Publish desk cable management and a home-office lighting guide | 9 |
| 8 (Dec 20–26) | Link audit, analytics review (including Telegram referrals), first restore rehearsal | Publish small-space desk setup guide | 10 |
| 9 (Dec 27–Jan 2) | Search query review; prioritize titles and snippets with existing impressions | Publish first researched home-kitchen guide | 11 |
| 10 (Jan 3–9) | Approve Home & Kitchen discovery when hub content is ready; improve older content | Publish 1–2 home-kitchen organizers/guides | 12–13 |
| 11 (Jan 10–16) | Improve article usefulness, navigation and internal discovery; review source licenses | Publish 1–2 additional guides (car or gadgets only if researched) | 13–15 |
| 12 (Jan 17–23) | Full SEO, consent, backups and compliance audit | Publish 1–2 verified guides; update earlier articles | 14–17 |

**January 24–31 buffer:** finish outstanding work, stabilize live site, and optionally reach **18** articles. Do not manufacture filler to hit 30. Delay adding Car Accessories, Gadgets & Tech and Home Office hubs to the public navigation until each has three useful articles; a developer-focused site at first is acceptable.

### Weekly editorial workflow

1. Validate search intent in India; identify a specific useful reader decision.
2. Check what the editor owns or can test; distinguish firsthand testing from desk research.
3. Obtain licensed/owned images and keep provenance evidence.
4. Normalize specs against the product-type schema; verify product availability. Add merchant links only where genuinely helpful and approved.
5. Draft with transparent evidence, limitations, practical use cases and disclosure.
6. Review on mobile and publish when technically live; update internal links and indexing.
7. Audit existing claims, particularly any price-dependent headline, against verification dates.
8. Share one genuinely useful, non-spammy Telegram summary and a tracked article link when relevant; collect reader questions to improve the next guide.

---

## 11. Monetization rollout and measurements

### Phase 1: Audience first; merchant links optional (weeks 1–12)

Prioritize useful articles, discoverable category hubs, fast pages, Search Console indexing, internal links, reader trust and organic audience. **No affiliate links are required for first publication.** MerchantOffer stays optional. When affiliate links are added, use manually created Cuelinks deeplinks stored as `MerchantOffer.affiliate_url`; **never load Cuelinks auto-conversion JavaScript**. Apply merchant tracking-domain allowlists and `rel="sponsored nofollow noopener"`. Avoid making Amazon application timing part of the release schedule; revisit after meaningful content and traffic, mindful of its qualifying-sales timeframe. Zero revenue in the first 90 days is acceptable.

### Phase 2: Monetization readiness only when audience/content justify it

Assess policies, content originality, navigation, mobile usability, privacy disclosures and appropriate ad placements. No universal minimum posts or views guarantee approval. Avoid excessive ads around product recommendation buttons or layouts likely to confuse users.

### Reader-distribution and subscription workflow

Publish RSS at `/feed/` and include it in the footer and page metadata. Add a minimal newsletter signup only if operational consent/unsubscribe requirements can be met; otherwise RSS is the required launch baseline and email signup is the first post-launch enhancement. Promote one helpful observation from each article on LinkedIn and in relevant developer communities, without spam or unsupported testing claims. Measure subscriber opt-ins and referral channels separately from organic clicks.

### Telegram channel — audience distribution and feedback

**Purpose:** Use the user's existing Telegram channel to bring interested readers back to trustworthy guides, learn what questions readers have, and build an audience independent of Google rankings. **Do not presume the channel's current topic, size, handle or audience overlap**; review it before introducing the MyBestPicks brand. Existing subscribers should not be flooded with unrelated posts.

**MVP (manual; no Bot API dependency):**

1. Store the verified public channel URL/handle in Wagtail site settings (`telegram_channel_url`, optionally `telegram_channel_label`); show a contextual **Join on Telegram** link on the homepage, footer and relevant article pages. Do not invent a URL; display nothing until configured.
2. Maintain a reusable Markdown/plain-text post template: practical takeaway, one or two bullets, optional question, then a canonical article link with `utm_source=telegram&utm_medium=social&utm_campaign=article_share` (optionally a short content-specific `utm_content`). Preserve existing query parameters when adding UTMs.
3. Post manually after reviewing each article; alternate article announcements with standalone tips and occasional polls. Suggested starting cadence: **2–3 useful posts per week**, adjusted to channel interests; no quota or forced schedule.
4. Include a clear community invitation in articles but do not obscure main content with popups. Telegram subscribers and referral visits are different metrics; neither is a guaranteed measure of unique repeat readers.
5. Track visits/engaged article reads from Telegram in privacy-reviewed Umami or equivalent. Use comments, poll responses and questions to identify future article topics. Respect Telegram channel/group privacy and avoid importing subscriber details into the website.

**Optional after stable publishing (P2 / MBP-014):** Add a Wagtail **Preview → Confirm → Publish to Telegram** admin action. Use the Telegram Bot API only after making a bot an authorized channel administrator with posting permission. Store the bot token in environment/secrets management, never in Wagtail settings or source code; store only the channel identifier and nonsecret preferences in settings. Record publication status, send timestamp, article ID and returned Telegram message ID for deduplication and retries; prevent duplicate sends. Prefer text-plus-link for the initial implementation; use images only when usage rights are clear. Publishing remains **explicitly human-approved** (no automatic on-publish hook). Treat API errors and rate limits gracefully. Automation must not delay the website launch.

**Telegram success indicators:** channel click-through to helpful guides, Telegram-referred article engagement, new questions and repeat useful participation; review weekly alongside Search Console. Avoid measuring success only by raw subscriber count.

**Analytics:** prefer self-hosted Umami on a properly secured deployment (separate service/container if needed); avoid assuming cookieless analytics are automatically exempt from notice or consent rules. Use a privacy review to decide whether a banner is necessary. GA4 remains optional, enabled only with appropriate consent configuration; any later custom `affiliate_click` event must not fire before applicable consent.

### Reporting dashboard (internal)

- Live article count by category and article type.
- Google Search Console: indexed pages, impressions, clicks, queries, CTR.
- Umami (or equivalent cookieless analytics, subject to privacy review): visits, top pages, referrals (including Telegram UTM campaigns) and approximate returning visitor trends. These figures are not a guaranteed census of all visitors.
- Optional later: consented GA4 `affiliate_click` event with `data-merchant`, `data-product`, and article identifier on merchant CTA anchors; no custom click table. Enhanced measurement alone may lack product/article detail.
- Merchant-reported orders, valid commissions, returns/cancellations **only after monetization is active**.
- Hosting cost and editorial time spent.

**Audience-first decision:** No affiliate sales, click-through or AdSense approval quotas in the first 90 days. Track relevant search impressions, indexing, clicks, article usefulness and repeat visitors. Estimate commissions only when monetization becomes a priority.

---

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Thin AI-generated listicles fail to rank | Original buying criteria, verification, focused audience and useful comparisons |
| Amazon/Cuelinks link or image policy violations | Network-specific allowlists, approved deep links, clear disclosures, licensed imagery and regular terms review |
| Price/stock changes | No unverified static prices; use check-price CTAs and scheduled audits |
| Five categories dilute topical authority | Start with Developer Setup, then Home & Kitchen; create later hubs when first article is ready and keep undiscoverable until editorial review |
| No early search traffic | Publish genuinely helpful guides to LinkedIn and appropriate developer communities (respecting community rules); add RSS and a minimal opt-in email channel |
| Hosting/storage failure | Automated DB backups, media backups, tested restore and health monitoring |
| Security issues in admin | MFA where available, strong passwords, restricted access, patching, HTTPS |
| Structural URL changes | Stable slugs and permanent redirects |
| Scope creep | Defer scraping, price tracking and custom frontend framework |

---

## 13. Definition of done for MVP

- [ ] `mybestpicks.in` resolves to the new deployment with valid TLS and canonical apex redirect.
- [ ] Editors can create, preview, revise, schedule and publish guides in Wagtail.
- [ ] Categories and article pages have correct URLs, responsive layouts, breadcrumb links, SEO metadata.
- [ ] Reusable product snippets; **one canonical StreamField product-card source** for per-article verdicts and comparison-table membership; optional merchant links render with `rel="sponsored"` and clear disclosures **if present**.
- [ ] If affiliate links are present, disclosures and sponsored attributes render correctly, and merchant links/images pass relevant program compliance review; **not a launch blocker when absent**.
- [ ] About, Contact, Editorial Policy, Affiliate Disclosure and Privacy Policy are published.
- [ ] Sitemap, robots, schema and Search Console setup are verified.
- [ ] Existing Telegram channel link is configurable in Wagtail settings and only appears when a verified URL is set; manual article sharing uses consistent UTMs.
- [ ] Basic search, RSS feed, minimal opt-in email signup (with double opt-in if available), privacy-conscious analytics and appropriate consent controls, off-box DB + media backups, logging and monitoring work.
- [ ] Deployment and rollback are documented; backups successfully restored in a test.
- [ ] Minimal site is live by week 2 with one reviewed article; at least 4–6 substantive articles are live by end of week 4; 12–18 are the 90-day goal.

---

## 14. Immediate next actions — revised implementation tickets

| Priority | Ticket | Deliverable |
|---|---|---|
| P0 | MBP-001: Project scaffold | Native Wagtail starter layout, Postgres, pinned requirements, `.env.example`, Docker Compose/README |
| P0 | MBP-002: Base layout | Bootstrap navigation from dynamic discoverable categories, mobile design, early minimal deploy |
| P0 | MBP-003: Page models | `HomePage`, `CategoryPage` with computed discovery and sitemap policy, `ArticlePage` with precomputed `get_context()`, **`AuthorPage`**, `StandardPage` |
| P0 | MBP-004: Editorial blocks | ProductCard `SnippetChooserBlock`, validated `tested_by_editor` evidence, derived comparison table using precomputed context, pros/cons |
| P0 | MBP-005: Product catalog | Brand/Product/Merchant/Offer snippets, `Product.product_type`, Python `catalog/specs.py` schema, optional Cuelinks deeplinks, **no price fields** |
| P0 | MBP-006: Trust, privacy & SEO | Pages, site settings, sitemap, redirects, JSON-LD, **consent controls where applicable**, RSS and email signup privacy text, image provenance |
| P0 | MBP-007: Release pipeline | Single-VPS Compose app/Postgres/Nginx, Cloudflare, nightly off-box DB + media backups, restore test |
| P1 | MBP-008: Internal search | Wagtail database search on PostgreSQL; no Elasticsearch |
| P1 | MBP-009: Metrics | Search Console + privacy-reviewed Umami first, Telegram UTM referrals and RSS/email acquisition measurement; optional consented GA4 affiliate events later; **no AffiliateClickEvent model** |
| P1 | MBP-010: Editorial QA | Product research/license evidence, price-dependent headline re-verification, test fixtures |
| P2 | MBP-011: Merchant API | Evaluate only after program terms, approved access and product/media rights verified |
| P2 | MBP-012: AdSense | Consider after sufficient useful public content and policy review; no fixed submission week |
| P2 | MBP-013: Amazon eligibility check | Assess **existing account status**, 180-day clock, 3 qualifying sales requirement and readiness |
| P2 | MBP-014: Telegram posting integration | Optional Wagtail preview/confirm admin action via Telegram Bot API; secure token, explicit channel permissions, logging/deduplication; manual posting remains MVP |

### Confirmed decisions and unresolved checks

**Fixed:** Existing Telegram channel used for audience distribution (manual first, automation optional); audience-first launch; Django + Wagtail + PostgreSQL; server-rendered Bootstrap; one-VPS deployment; `mybestpicks.in`; admin-created extensible categories; product-type spec schemas; optional **Cuelinks for Flipkart**; editorially verified products; no manual prices or server click log.

**Must verify before later monetization:** Cuelinks Flipkart eligibility, current tracking hostnames/commission/attribution, Amazon account status and site eligibility, product image permissions, DNS/hosting rights, and the applicable privacy/consent obligations. India’s DPDP framework has phased commencement dates; do not assume every provision was already in force on 1 November 2026. Implement privacy-friendly defaults and obtain jurisdiction-specific guidance where necessary.

### Explicit launch acceptance gates and optional future work

**Before public launch:** Wagtail login and editorial workflow, PostgreSQL, category parent URLs, one useful published article, SEO metadata, sitemap, RSS, Search Console property, HTTPS, legal pages, mobile usability and backups. **Not blockers:** Telegram bot automation, Amazon approval, Cuelinks acceptance, affiliate CTAs, AdSense, custom click tracking, or 30 posts.

**Before revealing a new hub:** Verify it has meaningful introduction and editorial depth, working links/breadcrumbs, unique metadata, and an intentional `auto`/`force_show` decision. Test nav, sitemap, robots meta and structured data end-to-end.

**Later enhancements:** multi-category editorial tags, richer filters, more product-type schemas, evergreen comparison refresh workflows, optional approved merchant API data, richer email newsletter workflows once reader interest exists.

### Primary documentation and source links

- Amazon India application review: https://affiliate-program.amazon.in/help/node/topic/G8TW5AE9XL2VX9VM
- Amazon India 180-day dormancy/application policy: https://affiliate-program.amazon.in/help/node/topic/G7MJTPEP9NC3YKMG
- Cuelinks Flipkart campaign: https://www.cuelinks.com/campaigns/flipkart-affiliate-program
- Wagtail docs: https://docs.wagtail.org/en/stable/
- India DPDP implementation chronology (secondary explanatory source): https://www.agicentral.com/resources/dpdp-timeline

**Final:** Build a small, trustworthy developer-accessory editorial site with search, referral and subscriber acquisition first; expand it into the broader MyBestPicks category brand as each hub earns enough useful coverage.
