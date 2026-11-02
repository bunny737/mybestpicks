import sys

from django.core.management.base import BaseCommand

from editorial.audits import find_broken_internal_links


class Command(BaseCommand):
    help = (
        "Finds broken internal links in live, public pages: page and document "
        "links, same-site hrefs, related-article picks and featured guides that "
        "point at a deleted or unpublished page. Internal links are resolved "
        "in-process; external URLs are never fetched."
    )

    def handle(self, *args, **options):
        findings = find_broken_internal_links()
        if not findings:
            self.stdout.write(self.style.SUCCESS("No broken internal links found."))
            return

        for finding in findings:
            self.stdout.write(str(finding))
        self.stdout.write(self.style.ERROR(f"\n{len(findings)} finding(s)."))
        sys.exit(1)
