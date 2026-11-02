from django.conf import settings


class SearchIndexingProtectionMiddleware:
    """Prevent every response from an explicitly nonpublic environment being indexed."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if settings.BLOCK_SEARCH_INDEXING:
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response
