from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import EmailSignupForm
from .models import EmailSubscriber


def _safe_next(request):
    """A same-site path to return to after signup, never an open redirect."""
    next_url = request.POST.get("next", "")
    if next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return "/"


def _send_confirmation_email(request, subscriber):
    confirm_url = request.build_absolute_uri(
        reverse("subscribe_confirm", args=[subscriber.unsubscribe_token])
    )
    send_mail(
        subject="Confirm your MyBestPicks email updates",
        message=(
            "Please confirm you'd like to receive occasional MyBestPicks updates:\n"
            f"{confirm_url}\n\n"
            "If you did not request this, ignore this email: you will not be "
            "subscribed."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[subscriber.email],
    )


@require_http_methods(["POST"])
def subscribe(request):
    form = EmailSignupForm(request.POST)
    if form.is_valid():
        subscriber, _created = EmailSubscriber.objects.get_or_create(
            email=form.cleaned_data["email"],
            defaults={"consent_text_version": settings.EMAIL_CONSENT_TEXT_VERSION},
        )
        if not subscriber.confirmed_at:
            _send_confirmation_email(request, subscriber)
        messages.success(
            request,
            "Almost done: check your inbox and click the confirmation link to "
            "start receiving updates.",
        )
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, error)
    return redirect(_safe_next(request))


def confirm(request, token):
    subscriber = get_object_or_404(EmailSubscriber, unsubscribe_token=token)
    if not subscriber.confirmed_at:
        subscriber.confirmed_at = timezone.now()
        subscriber.save(update_fields=["confirmed_at"])
    return render(
        request,
        "home/subscribe_confirmed.html",
        {"subscriber": subscriber, "robots_meta": "noindex,follow"},
    )


@require_http_methods(["GET", "POST"])
def unsubscribe(request, token):
    subscriber = get_object_or_404(EmailSubscriber, unsubscribe_token=token)
    if request.method == "POST":
        subscriber.delete()
        return render(
            request,
            "home/subscribe_unsubscribed.html",
            {"robots_meta": "noindex,follow"},
        )
    return render(
        request,
        "home/subscribe_unsubscribe_confirm.html",
        {"subscriber": subscriber, "robots_meta": "noindex,follow"},
    )
