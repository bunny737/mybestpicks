"""Builders for catalog tests. Hostnames use the reserved .test TLD, never real ones."""

from catalog.models import Brand, Merchant, MerchantOffer, Product

TRACK_HOST = "track.example.test"
GOOD_LINK = f"https://{TRACK_HOST}/c/abc123?cid=42"

KEYBOARD_SPECS = {
    "layout": "tkl",
    "switch_type": "mechanical",
    "connectivity": "wired",
}


def make_brand(name="Acme"):
    return Brand.objects.create(name=name)


def make_product(
    name="K1",
    brand=None,
    product_type="keyboard",
    key_specs=None,
    **fields,
):
    brand = brand or Brand.objects.get_or_create(name="Acme")[0]
    if key_specs is None:
        key_specs = dict(KEYBOARD_SPECS)
    product = Product(
        brand=brand,
        name=name,
        product_type=product_type,
        key_specs=key_specs,
        **fields,
    )
    product.full_clean()
    product.save()
    return product


def make_merchant(
    name="Shopmart",
    destination_domain="shopmart.test",
    network="cuelinks",
    allowed=TRACK_HOST,
    **fields,
):
    merchant = Merchant(
        name=name,
        destination_domain=destination_domain,
        network=network,
        allowed_link_domains=allowed,
        **fields,
    )
    merchant.full_clean()
    merchant.save()
    return merchant


def make_offer(product, merchant, url=GOOD_LINK, active=True, **fields):
    fields.setdefault("last_checked_at", "2026-11-01")
    offer = MerchantOffer(
        product=product, merchant=merchant, affiliate_url=url, active=active, **fields
    )
    offer.full_clean()
    offer.save()
    return offer
