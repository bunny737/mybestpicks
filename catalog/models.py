"""
Product catalog (module 05): reusable editorial facts about products, plus optional
merchant offers.

Product facts are global and reusable. Per-article judgement (verdicts, pros and
cons, ranking) lives only in the article's StreamField product-card blocks
(CLAUDE.md invariant 3), so there is no ArticleProduct model. There are no price
fields anywhere (invariant 2) and no click-tracking model (invariant 9).
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.html import format_html, format_html_join
from django.utils.text import slugify
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, HelpPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable
from wagtail.search import index

from .provenance import ImageProvenance, validate_image_provenance
from .specs import (
    PRODUCT_SPEC_SCHEMAS,
    PRODUCT_TYPE_CHOICES,
    spec_rows,
    validate_key_specs,
)
from .validators import (
    parse_allowed_hosts,
    validate_affiliate_url,
    validate_destination_url,
    validate_hostname,
    validate_https_url,
)


def _unique_slug(model, base, instance_pk=None):
    base = slugify(base) or "item"
    slug, n = base, 2
    others = model.objects.exclude(pk=instance_pk) if instance_pk else model.objects
    while others.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


class Brand(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(
        max_length=140,
        unique=True,
        blank=True,
        help_text="Leave blank to generate it from the name.",
    )
    website = models.URLField(
        blank=True, validators=[validate_https_url], help_text="Optional, https only."
    )

    panels = [FieldPanel("name"), FieldPanel("slug"), FieldPanel("website")]

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Brand, self.name, self.pk)
        super().save(*args, **kwargs)


class ProductStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    DISCONTINUED = "discontinued", "Discontinued"
    UNAVAILABLE = "unavailable", "Temporarily unavailable"


def _spec_guide_html():
    """Editor help: the keys each product type accepts (from catalog/specs.py)."""
    items = []
    for schema in PRODUCT_SPEC_SCHEMAS.values():
        keys = ", ".join(
            f"{s.key}{'*' if s.required else ''} ({s.value_type})" for s in schema.specs
        )
        items.append((schema.label, keys))
    return format_html(
        "<p>Enter specs as a JSON object whose keys match the product type "
        "(<code>*</code> = required). Example: "
        '<code>{{"layout": "tkl", "switch_type": "mechanical", '
        '"connectivity": "wired"}}</code></p><ul>{}</ul>',
        format_html_join("", "<li><strong>{}</strong>: {}</li>", items),
    )


class Product(index.Indexed, ClusterableModel):
    """
    A product's reusable facts. ``product_type`` selects the spec schema in
    ``catalog/specs.py`` and is independent of any editorial category.
    """

    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    model_number = models.CharField(max_length=100, blank=True)
    product_type = models.CharField(max_length=40, choices=PRODUCT_TYPE_CHOICES)
    key_specs = models.JSONField(default=dict, blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    image_provenance = models.CharField(
        max_length=30, choices=ImageProvenance.choices, blank=True
    )
    image_credit = models.CharField(
        "Image credit or licence evidence", max_length=255, blank=True
    )
    status = models.CharField(
        max_length=20, choices=ProductStatus.choices, default=ProductStatus.ACTIVE
    )
    last_verified_at = models.DateField(
        null=True,
        blank=True,
        help_text="When these facts were last checked against a reliable source.",
    )

    panels = [
        FieldPanel("brand"),
        FieldPanel("name"),
        FieldPanel("model_number"),
        FieldPanel("product_type"),
        HelpPanel(content=_spec_guide_html()),
        FieldPanel("key_specs"),
        MultiFieldPanel(
            [
                FieldPanel("image"),
                FieldPanel("image_provenance"),
                FieldPanel("image_credit"),
            ],
            heading="Image",
        ),
        FieldPanel("status"),
        FieldPanel("last_verified_at"),
        InlinePanel("offers", label="Merchant offer", heading="Merchant offers"),
    ]

    search_fields = [
        index.SearchField("name"),
        index.SearchField("model_number"),
        index.FilterField("product_type"),
        index.FilterField("status"),
        index.RelatedFields("brand", [index.SearchField("name")]),
    ]

    class Meta:
        ordering = ["brand__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["brand", "name", "model_number"], name="unique_product"
            )
        ]

    def __str__(self):
        return f"{self.brand.name} {self.name}"

    def clean(self):
        super().clean()
        # Normalise (trim text, drop blanks) while validating.
        self.key_specs = validate_key_specs(self.product_type, self.key_specs)
        validate_image_provenance(
            image=self.image,
            provenance=self.image_provenance,
            credit=self.image_credit,
            image_field="image",
            provenance_field="image_provenance",
            credit_field="image_credit",
        )

    @property
    def spec_rows(self):
        return spec_rows(self.product_type, self.key_specs)


class Network(models.TextChoices):
    DIRECT = "direct", "Direct"
    CUELINKS = "cuelinks", "Cuelinks"


class Merchant(models.Model):
    """
    A retailer we may link to. ``destination_domain`` is where the shopper ends up
    (flipkart.com); ``network`` is how the link is tracked; ``allowed_link_domains``
    lists the tracking hostnames an offer's link may use. Keep them separate.
    """

    name = models.CharField(
        max_length=80, unique=True, help_text="Shown to readers, e.g. Flipkart."
    )
    destination_domain = models.CharField(
        max_length=253,
        validators=[validate_hostname],
        help_text="Where the shopper lands, e.g. flipkart.com (lowercase, host only).",
    )
    network = models.CharField(
        max_length=20, choices=Network.choices, default=Network.DIRECT
    )
    allowed_link_domains = models.TextField(
        blank=True,
        help_text=(
            "Exact hostnames an offer link may use, one per line, copied from "
            "verified links in your affiliate dashboard. Subdomains are not implied."
        ),
    )
    enabled = models.BooleanField(default=True)
    cta_text = models.CharField(
        "Button text",
        max_length=60,
        blank=True,
        help_text='Leave blank for "View at <name>". Amazon: "Check price at Amazon".',
    )
    disclosure_notes = models.TextField(blank=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("destination_domain"),
        FieldPanel("network"),
        FieldPanel("allowed_link_domains"),
        FieldPanel("enabled"),
        FieldPanel("cta_text"),
        FieldPanel("disclosure_notes"),
    ]

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        try:
            hosts = parse_allowed_hosts(self.allowed_link_domains)
        except ValidationError as exc:
            raise ValidationError({"allowed_link_domains": exc.messages}) from exc
        self.allowed_link_domains = "\n".join(hosts)

    @property
    def allowed_hosts(self):
        return set(parse_allowed_hosts(self.allowed_link_domains))

    @property
    def cta_label(self):
        return self.cta_text or f"View at {self.name}"


class MerchantOfferQuerySet(models.QuerySet):
    def renderable(self):
        """
        Offers that may be shown: active, merchant enabled, product not discontinued.

        Callers must also check ``offer.is_renderable``, which re-validates the link
        host against the merchant's *current* allowlist (a database filter cannot).
        """
        return self.filter(active=True, merchant__enabled=True).exclude(
            product__status=ProductStatus.DISCONTINUED
        )


class MerchantOffer(Orderable):
    """
    A manually created affiliate link for a product. Optional: articles launch
    without any. No price fields.
    """

    product = ParentalKey(Product, on_delete=models.CASCADE, related_name="offers")
    merchant = models.ForeignKey(
        Merchant, on_delete=models.PROTECT, related_name="offers"
    )
    affiliate_url = models.URLField(
        max_length=2000,
        help_text="The tracking link from your dashboard. https, on an allowed host.",
    )
    destination_product_url = models.URLField(
        max_length=2000,
        blank=True,
        help_text="The retailer page, for your own manual check. Never fetched.",
    )
    last_checked_at = models.DateField(
        null=True,
        blank=True,
        help_text="When you last opened the link and confirmed where it goes.",
    )
    active = models.BooleanField(
        default=False,
        help_text="Turn on only after you have checked the link's destination by hand.",
    )
    campaign_notes = models.TextField(blank=True)

    panels = [
        FieldPanel("merchant"),
        FieldPanel("affiliate_url"),
        FieldPanel("destination_product_url"),
        FieldPanel("last_checked_at"),
        FieldPanel("active"),
        FieldPanel("campaign_notes"),
    ]

    objects = MerchantOfferQuerySet.as_manager()

    def __str__(self):
        return f"{self.merchant.name} offer" if self.merchant_id else "Offer"

    def clean(self):
        super().clean()
        errors = {}
        if self.merchant_id:
            merchant = self.merchant
            if self.affiliate_url:
                try:
                    validate_affiliate_url(self.affiliate_url, merchant.allowed_hosts)
                except ValidationError as exc:
                    errors["affiliate_url"] = exc.messages
            if self.destination_product_url:
                try:
                    validate_destination_url(
                        self.destination_product_url, merchant.destination_domain
                    )
                except ValidationError as exc:
                    errors["destination_product_url"] = exc.messages
        if self.active and not self.last_checked_at:
            errors["last_checked_at"] = (
                "Record the date you checked the link by hand before activating it."
            )
        if errors:
            raise ValidationError(errors)

    @property
    def is_renderable(self):
        """
        True when this offer may be shown to readers right now.

        Re-checks the link against the merchant's current allowlist, so removing a
        host from the allowlist immediately stops existing links from rendering.
        """
        if not (self.active and self.merchant.enabled):
            return False
        if self.product.status == ProductStatus.DISCONTINUED:
            return False
        try:
            validate_affiliate_url(self.affiliate_url, self.merchant.allowed_hosts)
        except ValidationError:
            return False
        return True
