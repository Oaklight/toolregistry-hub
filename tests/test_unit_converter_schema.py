"""Tests that ``UnitConverter.convert`` exposes its ``conversion`` parameter
as a closed ``Literal`` so MCP / JSON schema callers see an ``enum``.

Covers issue #117.
"""

from __future__ import annotations

from typing import Literal, get_args, get_origin, get_type_hints

import pytest

from toolregistry_hub.unit_converter import BaseUnitConverter, UnitConverter
from toolregistry_hub.utils import get_all_static_methods


class TestConvertEnumSchema:
    def test_conversion_param_is_literal(self):
        hints = get_type_hints(UnitConverter.convert)
        annotation = hints["conversion"]
        assert get_origin(annotation) is Literal

    def test_literal_lists_every_conversion(self):
        hints = get_type_hints(UnitConverter.convert)
        choices = set(get_args(hints["conversion"]))
        expected = set(get_all_static_methods(BaseUnitConverter))
        assert choices == expected
        # Spot-check a few well-known entries to guard against regressions
        # in get_all_static_methods.
        for name in (
            "celsius_to_fahrenheit",
            "kilograms_to_pounds",
            "meters_to_feet",
        ):
            assert name in choices

    def test_runtime_call_still_works(self):
        # Literal narrowing is a schema-only concern; runtime behavior is
        # unaffected.
        result = UnitConverter.convert(100, "celsius_to_fahrenheit")
        assert result == 212.0

    def test_invalid_name_still_raises(self):
        with pytest.raises(ValueError, match="not recognized"):
            UnitConverter.convert(1.0, "kg_to_lb")
