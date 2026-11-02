from django.contrib import admin

from .models import EmailSubscriber


@admin.register(EmailSubscriber)
class EmailSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "consented_at", "confirmed_at", "consent_text_version")
    search_fields = ("email",)
    readonly_fields = (
        "email",
        "consented_at",
        "confirmed_at",
        "consent_text_version",
        "unsubscribe_token",
    )

    def has_add_permission(self, request):
        return False
