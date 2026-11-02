from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import Brand, Merchant, Product


class BrandViewSet(SnippetViewSet):
    model = Brand
    icon = "tag"
    list_display = ["name", "website"]
    search_fields = ("name",)


class ProductViewSet(SnippetViewSet):
    model = Product
    icon = "cog"
    list_display = ["name", "brand", "product_type", "status", "last_verified_at"]
    list_filter = ["product_type", "status", "brand"]


class MerchantViewSet(SnippetViewSet):
    model = Merchant
    icon = "link"
    list_display = ["name", "network", "destination_domain", "enabled"]
    list_filter = ["network", "enabled"]
    search_fields = ("name", "destination_domain")


class CatalogViewSetGroup(SnippetViewSetGroup):
    items = (ProductViewSet, BrandViewSet, MerchantViewSet)
    menu_icon = "folder-open-inverse"
    menu_label = "Catalog"
    menu_name = "catalog"
    menu_order = 200


register_snippet(CatalogViewSetGroup)
