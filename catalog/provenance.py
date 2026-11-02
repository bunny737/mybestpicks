"""
Image provenance rules (CLAUDE.md invariant 8), shared by pages and products.

Every image we publish records where it came from. Retailer listing photos are
never an option. This module has no models so any app can import it.
"""

from django.core.exceptions import ValidationError
from django.db import models


class ImageProvenance(models.TextChoices):
    OWNED_ORIGINAL = "owned_original", "Owned original (our own photo)"
    MANUFACTURER_LICENSED = "manufacturer_licensed", "Manufacturer licensed"
    OTHER_LICENSED = "other_licensed", "Other licensed"
    PERMITTED_PROGRAM_CONTENT = (
        "permitted_program_content",
        "Permitted affiliate-program content",
    )


def validate_image_provenance(
    *, image, provenance, credit, image_field, provenance_field, credit_field
):
    """
    Raise ValidationError (keyed by field name) unless an image has provenance.

    - No image: nothing to check.
    - Image: provenance is required.
    - Anything except an owned original also needs a credit or licence evidence.
    """
    if not image:
        return

    errors = {}
    if not provenance:
        errors[provenance_field] = (
            "Say where this image came from (provenance is required for every image)."
        )
    elif provenance != ImageProvenance.OWNED_ORIGINAL and not (credit or "").strip():
        errors[credit_field] = (
            "Add the credit or licence evidence for an image that is not "
            "an owned original."
        )
    if errors:
        raise ValidationError(errors)
