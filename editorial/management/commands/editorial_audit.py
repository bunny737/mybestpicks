import sys

from django.core.management.base import BaseCommand

from editorial.audits import run_editorial_audit


class Command(BaseCommand):
    help = (
        "Reports editorial claims that may no longer be true: price claims against "
        "unverified products, product images missing provenance or licence "
        "evidence, live articles referencing discontinued or unavailable products, "
        "stale offer link checks, and hands-on claims without evidence. Only "
        "reports: it never edits content."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Override EDITORIAL_AUDIT_STALE_DAYS for this run.",
        )

    def handle(self, *args, **options):
        findings = run_editorial_audit(days=options["days"])
        if not findings:
            self.stdout.write(self.style.SUCCESS("Editorial audit: no findings."))
            return

        for finding in findings:
            self.stdout.write(str(finding))
        self.stdout.write(self.style.ERROR(f"\n{len(findings)} finding(s)."))
        sys.exit(1)
