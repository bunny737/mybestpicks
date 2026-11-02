"""
Product-type spec schemas (module 05).

``PRODUCT_SPEC_SCHEMAS`` maps a ``Product.product_type`` to the specs a product of
that type must (or may) record in ``Product.key_specs``. It is plain, versioned Python:
no admin model and no migration when it changes. Product type is independent of the
editorial hub, so a USB-C hub can appear in Developer Setup and in Gadgets.

PROVISIONAL: the four types below and their keys were proposed on 2026-11-02 as a
starting set; the owner names real ones when a post needs them
(docs/modules/05-product-catalog.md). Adding or changing
a type means editing this file and ``catalog/tests/test_specs.py``, then deploying.

There are no price specs, by design (CLAUDE.md invariant 2).
"""

import math
from dataclasses import dataclass, replace

from django.core.exceptions import ValidationError

SCHEMA_VERSION = 1

INT = "int"
DECIMAL = "decimal"
BOOL = "bool"
STR = "str"
CHOICE = "choice"
VALUE_TYPES = (INT, DECIMAL, BOOL, STR, CHOICE)

MAX_STR_LENGTH = 100


@dataclass(frozen=True)
class SpecDef:
    key: str  # canonical, snake_case, never renamed once data exists
    label: str
    value_type: str
    unit: str = ""
    required: bool = False
    comparable: bool = True  # may be shown as a comparison-table column
    choices: tuple[tuple[str, str], ...] = ()  # (value, label) for CHOICE
    minimum: float | None = 0  # numeric specs only; None means no lower bound
    display_order: int = 0  # set by _ordered(); the position in the schema

    @property
    def display_label(self):
        """Label with its unit, e.g. ``Power (W)``."""
        return f"{self.label} ({self.unit})" if self.unit else self.label


@dataclass(frozen=True)
class ProductTypeSchema:
    product_type: str
    label: str
    specs: tuple[SpecDef, ...]

    def get(self, key):
        return next((s for s in self.specs if s.key == key), None)


@dataclass(frozen=True)
class SpecRow:
    """One spec of one product, ready to display or compare."""

    key: str
    label: str  # includes the unit
    value: object  # the stored value, or None when not recorded
    display_value: str  # "" when not recorded; templates show a dash
    comparable: bool


def _ordered(*specs):
    return tuple(
        replace(spec, display_order=(i + 1) * 10) for i, spec in enumerate(specs)
    )


PRODUCT_SPEC_SCHEMAS = {
    "keyboard": ProductTypeSchema(
        "keyboard",
        "Keyboard",
        _ordered(
            SpecDef(
                "layout",
                "Layout",
                CHOICE,
                required=True,
                choices=(
                    ("full", "Full size"),
                    ("tkl", "Tenkeyless (TKL)"),
                    ("75", "75%"),
                    ("65", "65%"),
                    ("60", "60%"),
                    ("other", "Other"),
                ),
            ),
            SpecDef(
                "switch_type",
                "Switch type",
                CHOICE,
                required=True,
                choices=(
                    ("mechanical", "Mechanical"),
                    ("membrane", "Membrane"),
                    ("scissor", "Scissor"),
                    ("optical", "Optical"),
                    ("other", "Other"),
                ),
            ),
            SpecDef(
                "connectivity",
                "Connectivity",
                CHOICE,
                required=True,
                choices=(
                    ("wired", "Wired"),
                    ("bluetooth", "Bluetooth"),
                    ("wireless_2_4ghz", "2.4 GHz wireless"),
                    ("multi_mode", "Multi-mode"),
                ),
            ),
            SpecDef("hot_swappable", "Hot-swappable switches", BOOL),
            SpecDef(
                "backlight",
                "Backlight",
                CHOICE,
                choices=(("none", "None"), ("white", "White"), ("rgb", "RGB")),
            ),
            SpecDef("battery_life_hours", "Battery life", INT, unit="hours"),
            SpecDef("weight_g", "Weight", INT, unit="g"),
        ),
    ),
    "laptop_stand": ProductTypeSchema(
        "laptop_stand",
        "Laptop stand",
        _ordered(
            SpecDef("material", "Material", STR, required=True),
            SpecDef("adjustable_height", "Adjustable height", BOOL, required=True),
            SpecDef("min_height_cm", "Minimum height", DECIMAL, unit="cm"),
            SpecDef("max_height_cm", "Maximum height", DECIMAL, unit="cm"),
            SpecDef("max_laptop_size_in", "Largest laptop", DECIMAL, unit="in"),
            SpecDef("max_load_kg", "Maximum load", DECIMAL, unit="kg"),
            SpecDef("foldable", "Foldable", BOOL),
            SpecDef("weight_g", "Weight", INT, unit="g"),
        ),
    ),
    "usb_c_hub": ProductTypeSchema(
        "usb_c_hub",
        "USB-C hub",
        _ordered(
            SpecDef("ports_usb_a", "USB-A ports", INT, required=True),
            SpecDef("ports_usb_c", "USB-C ports", INT, required=True),
            SpecDef(
                "hdmi",
                "HDMI",
                CHOICE,
                required=True,
                choices=(
                    ("none", "None"),
                    ("1.4", "HDMI 1.4"),
                    ("2.0", "HDMI 2.0"),
                    ("2.1", "HDMI 2.1"),
                ),
            ),
            SpecDef(
                "ethernet",
                "Ethernet",
                CHOICE,
                choices=(
                    ("none", "None"),
                    ("100mbps", "100 Mbps"),
                    ("gigabit", "Gigabit"),
                ),
            ),
            SpecDef("sd_card_reader", "SD card reader", BOOL),
            SpecDef("power_watts", "Power Delivery pass-through", INT, unit="W"),
            SpecDef("data_speed_gbps", "Data speed", DECIMAL, unit="Gbps"),
            SpecDef("weight_g", "Weight", INT, unit="g"),
        ),
    ),
    "monitor_arm": ProductTypeSchema(
        "monitor_arm",
        "Monitor arm",
        _ordered(
            SpecDef(
                "arm_count",
                "Monitors supported",
                CHOICE,
                required=True,
                choices=(("single", "Single"), ("dual", "Dual"), ("triple", "Triple")),
            ),
            SpecDef(
                "vesa_mount",
                "VESA mount",
                CHOICE,
                required=True,
                choices=(
                    ("75x75", "75 x 75"),
                    ("100x100", "100 x 100"),
                    ("both", "75 x 75 and 100 x 100"),
                ),
            ),
            SpecDef("min_screen_in", "Smallest screen", INT, unit="in"),
            SpecDef("max_screen_in", "Largest screen", INT, unit="in"),
            SpecDef("max_load_kg", "Maximum load per arm", DECIMAL, unit="kg"),
            SpecDef(
                "desk_mount",
                "Desk mount",
                CHOICE,
                choices=(
                    ("clamp", "Clamp"),
                    ("grommet", "Grommet"),
                    ("both", "Clamp or grommet"),
                ),
            ),
            SpecDef("gas_spring", "Gas spring", BOOL),
        ),
    ),
}

PRODUCT_TYPE_CHOICES = [
    (key, schema.label) for key, schema in PRODUCT_SPEC_SCHEMAS.items()
]


def comparable_spec_choices():
    """
    ``(key, label)`` for every comparable spec across all product types, one entry
    per key. Used as a *callable* choices source for the comparison-table block, so a
    change to the schemas never changes a migration.
    """
    seen = {}
    for schema in PRODUCT_SPEC_SCHEMAS.values():
        for spec in sorted(schema.specs, key=lambda s: s.display_order):
            if spec.comparable and spec.key not in seen:
                seen[spec.key] = spec.display_label
    return list(seen.items())


def get_schema(product_type):
    return PRODUCT_SPEC_SCHEMAS.get(product_type)


def _is_number(value):
    return isinstance(value, int | float) and not isinstance(value, bool)


def _normalise_value(spec, value):
    """Return the cleaned value, or raise ValueError with a short reason."""
    if spec.value_type == BOOL:
        if not isinstance(value, bool):
            raise ValueError("must be true or false")
        return value

    if spec.value_type in (INT, DECIMAL):
        if spec.value_type == INT:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError("must be a whole number")
        elif not _is_number(value) or not math.isfinite(value):
            raise ValueError("must be a number")
        if spec.minimum is not None and value < spec.minimum:
            raise ValueError(f"must be at least {spec.minimum}")
        return value

    if spec.value_type == CHOICE:
        allowed = {v for v, _ in spec.choices}
        if value not in allowed:
            raise ValueError("must be one of: " + ", ".join(sorted(allowed)))
        return value

    if not isinstance(value, str):
        raise ValueError("must be text")
    value = value.strip()
    if not value:
        raise ValueError("must not be empty")
    if len(value) > MAX_STR_LENGTH:
        raise ValueError(f"must be at most {MAX_STR_LENGTH} characters")
    return value


def validate_key_specs(product_type, key_specs):
    """
    Validate ``key_specs`` against the schema for ``product_type``.

    Returns the normalised dict (blank values dropped, text trimmed). Raises
    ``ValidationError`` listing every problem: unknown keys, missing required specs,
    and values of the wrong type.
    """
    schema = get_schema(product_type)
    if schema is None:
        raise ValidationError(
            {"product_type": f"Unknown product type {product_type!r}."}
        )
    if key_specs is None:
        key_specs = {}
    if not isinstance(key_specs, dict):
        raise ValidationError({"key_specs": "Specs must be a JSON object."})

    problems = []
    known = {spec.key: spec for spec in schema.specs}

    for key in key_specs:
        if key not in known:
            problems.append(
                f"Unknown spec {key!r} for a {schema.label.lower()}. "
                f"Allowed: {', '.join(known)}."
            )

    cleaned = {}
    for spec in schema.specs:
        value = key_specs.get(spec.key)
        if value is None or (isinstance(value, str) and not value.strip()):
            if spec.required:
                problems.append(f"{spec.display_label} ({spec.key}) is required.")
            continue
        try:
            cleaned[spec.key] = _normalise_value(spec, value)
        except ValueError as exc:
            problems.append(f"{spec.display_label} ({spec.key}) {exc}.")

    if problems:
        raise ValidationError({"key_specs": problems})
    return cleaned


def _display_value(spec, value):
    if value is None:
        return ""
    if spec.value_type == BOOL:
        return "Yes" if value else "No"
    if spec.value_type == CHOICE:
        return dict(spec.choices).get(value, str(value))
    return str(value)


def spec_rows(product_type, key_specs):
    """
    Every spec in the schema, in display order, for one product.

    Specs the product does not record are included with ``value=None`` so a
    comparison table can show a dash instead of guessing. Assumes ``key_specs`` was
    already validated (``validate_key_specs``); unknown keys are ignored.
    """
    schema = get_schema(product_type)
    if schema is None:
        return []
    key_specs = key_specs or {}
    rows = []
    for spec in sorted(schema.specs, key=lambda s: s.display_order):
        value = key_specs.get(spec.key)
        rows.append(
            SpecRow(
                key=spec.key,
                label=spec.display_label,
                value=value,
                display_value=_display_value(spec, value),
                comparable=spec.comparable,
            )
        )
    return rows
