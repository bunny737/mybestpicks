from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from catalog import specs
from catalog.specs import (
    PRODUCT_SPEC_SCHEMAS,
    PRODUCT_TYPE_CHOICES,
    VALUE_TYPES,
    spec_rows,
    validate_key_specs,
)

KEYBOARD_OK = {"layout": "tkl", "switch_type": "mechanical", "connectivity": "wired"}


def problems(product_type, key_specs):
    try:
        validate_key_specs(product_type, key_specs)
    except ValidationError as exc:
        return exc.message_dict
    return None


class SchemaShapeTests(SimpleTestCase):
    """Every schema must be well formed, so a bad edit to specs.py fails loudly."""

    def test_there_is_at_least_one_product_type(self):
        self.assertTrue(PRODUCT_SPEC_SCHEMAS)
        self.assertEqual(
            [k for k, _ in PRODUCT_TYPE_CHOICES], list(PRODUCT_SPEC_SCHEMAS)
        )

    def test_schema_keys_match_their_product_type(self):
        for key, schema in PRODUCT_SPEC_SCHEMAS.items():
            self.assertEqual(schema.product_type, key)

    def test_spec_keys_are_unique_snake_case_within_a_type(self):
        for schema in PRODUCT_SPEC_SCHEMAS.values():
            keys = [s.key for s in schema.specs]
            with self.subTest(schema=schema.product_type):
                self.assertEqual(len(keys), len(set(keys)))
                for key in keys:
                    self.assertRegex(key, r"^[a-z][a-z0-9_]*$")

    def test_value_types_are_known_and_choices_are_consistent(self):
        for schema in PRODUCT_SPEC_SCHEMAS.values():
            for spec in schema.specs:
                with self.subTest(spec=f"{schema.product_type}.{spec.key}"):
                    self.assertIn(spec.value_type, VALUE_TYPES)
                    if spec.value_type == specs.CHOICE:
                        values = [v for v, _ in spec.choices]
                        self.assertTrue(values)
                        self.assertEqual(len(values), len(set(values)))
                    else:
                        self.assertEqual(spec.choices, ())

    def test_display_order_is_strictly_increasing(self):
        for schema in PRODUCT_SPEC_SCHEMAS.values():
            orders = [s.display_order for s in schema.specs]
            with self.subTest(schema=schema.product_type):
                self.assertEqual(orders, sorted(set(orders)))

    def test_every_type_has_a_required_spec(self):
        for schema in PRODUCT_SPEC_SCHEMAS.values():
            self.assertTrue(any(s.required for s in schema.specs), schema.product_type)

    def test_no_price_specs_exist(self):
        # CLAUDE.md invariant 2: no price data anywhere in the MVP.
        banned = ("price", "mrp", "cost", "discount", "rupee", "inr")
        for schema in PRODUCT_SPEC_SCHEMAS.values():
            for spec in schema.specs:
                text = f"{spec.key} {spec.label}".lower()
                self.assertFalse(any(b in text for b in banned), spec.key)

    def test_units_show_in_the_display_label(self):
        usb_c = PRODUCT_SPEC_SCHEMAS["usb_c_hub"].get("power_watts")
        self.assertEqual(usb_c.display_label, "Power Delivery pass-through (W)")
        keyboard = PRODUCT_SPEC_SCHEMAS["keyboard"].get("layout")
        self.assertEqual(keyboard.display_label, "Layout")


class ValidateKeySpecsTests(SimpleTestCase):
    def test_valid_specs_pass_and_are_returned(self):
        self.assertEqual(validate_key_specs("keyboard", KEYBOARD_OK), KEYBOARD_OK)

    def test_optional_specs_may_be_left_out(self):
        validate_key_specs("keyboard", KEYBOARD_OK)  # no weight, no backlight

    def test_missing_required_specs_are_all_reported(self):
        errors = problems("keyboard", {"layout": "tkl"})["key_specs"]
        joined = " ".join(errors)
        self.assertIn("switch_type", joined)
        self.assertIn("connectivity", joined)
        self.assertNotIn("layout", joined)

    def test_empty_and_none_count_as_missing(self):
        errors = problems("keyboard", {**KEYBOARD_OK, "layout": ""})["key_specs"]
        self.assertTrue(any("layout" in e and "required" in e for e in errors))
        errors = problems("keyboard", {**KEYBOARD_OK, "switch_type": None})
        self.assertIn("key_specs", errors)

    def test_blank_optional_values_are_dropped(self):
        cleaned = validate_key_specs("keyboard", {**KEYBOARD_OK, "weight_g": None})
        self.assertNotIn("weight_g", cleaned)

    def test_unknown_keys_are_rejected(self):
        errors = problems("keyboard", {**KEYBOARD_OK, "colour": "black"})["key_specs"]
        self.assertTrue(any("colour" in e for e in errors))

    def test_a_key_from_another_type_is_unknown(self):
        errors = problems("keyboard", {**KEYBOARD_OK, "ports_usb_a": 3})["key_specs"]
        self.assertTrue(any("ports_usb_a" in e for e in errors))

    def test_wrong_types_are_rejected(self):
        cases = [
            ("weight_g", "heavy"),  # int given text
            ("weight_g", 12.5),  # int given a fraction
            ("weight_g", True),  # bool is not a number
            ("hot_swappable", "yes"),  # bool given text
            ("hot_swappable", 1),  # bool given an int
            ("layout", "gigantic"),  # not one of the choices
            ("layout", 5),  # choice given a number
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                self.assertIn(
                    "key_specs", problems("keyboard", {**KEYBOARD_OK, key: value})
                )

    def test_numbers_cannot_be_negative(self):
        self.assertIn(
            "key_specs", problems("keyboard", {**KEYBOARD_OK, "weight_g": -1})
        )

    def test_decimal_specs_accept_ints_and_floats_but_not_nan(self):
        base = {"material": "Aluminium", "adjustable_height": True}
        validate_key_specs("laptop_stand", {**base, "max_load_kg": 5})
        validate_key_specs("laptop_stand", {**base, "max_load_kg": 4.5})
        for bad in (float("nan"), float("inf"), "5"):
            with self.subTest(bad=bad):
                self.assertIn(
                    "key_specs",
                    problems("laptop_stand", {**base, "max_load_kg": bad}),
                )

    def test_text_specs_are_trimmed_and_must_not_be_blank_or_huge(self):
        base = {"adjustable_height": False}
        cleaned = validate_key_specs("laptop_stand", {**base, "material": "  Steel "})
        self.assertEqual(cleaned["material"], "Steel")
        self.assertIn(
            "key_specs", problems("laptop_stand", {**base, "material": "x" * 101})
        )

    def test_specs_must_be_a_json_object(self):
        for bad in ([], "text", 5):
            with self.subTest(bad=bad):
                self.assertIn("key_specs", problems("keyboard", bad))

    def test_none_is_treated_as_no_specs(self):
        self.assertIn("key_specs", problems("keyboard", None))  # required ones missing

    def test_unknown_product_type_is_rejected(self):
        self.assertIn("product_type", problems("toaster", {}))


class SpecRowsTests(SimpleTestCase):
    def test_rows_follow_schema_order_and_include_unrecorded_specs(self):
        rows = spec_rows("keyboard", KEYBOARD_OK)
        self.assertEqual(
            [r.key for r in rows][:3], ["layout", "switch_type", "connectivity"]
        )
        weight = next(r for r in rows if r.key == "weight_g")
        self.assertIsNone(weight.value)
        self.assertEqual(weight.display_value, "")
        self.assertEqual(weight.label, "Weight (g)")

    def test_display_values_are_human_readable(self):
        rows = {
            r.key: r
            for r in spec_rows(
                "keyboard", {**KEYBOARD_OK, "hot_swappable": True, "weight_g": 750}
            )
        }
        self.assertEqual(rows["layout"].display_value, "Tenkeyless (TKL)")
        self.assertEqual(rows["hot_swappable"].display_value, "Yes")
        self.assertEqual(rows["weight_g"].display_value, "750")

    def test_false_is_shown_as_no_not_missing(self):
        rows = {r.key: r for r in spec_rows("keyboard", {"hot_swappable": False})}
        self.assertEqual(rows["hot_swappable"].display_value, "No")

    def test_unknown_type_gives_no_rows(self):
        self.assertEqual(spec_rows("toaster", {"a": 1}), [])
