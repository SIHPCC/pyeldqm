"""
Tests for core.health_thresholds
"""
import pytest
from core.health_thresholds import (
    get_aegl_thresholds,
    get_erpg_thresholds,
    get_idlh_threshold,
    get_pac_thresholds,
    get_all_thresholds,
)


CHLORINE = "chlorine"
AMMONIA = "ammonia"


class TestGetAeglThresholds:
    def test_returns_dict_with_expected_keys(self):
        result = get_aegl_thresholds(CHLORINE)
        # The API returns keys like 'AEGL-1', 'AEGL-2', 'AEGL-3'
        assert len(result) > 0, "Expected at least one AEGL threshold"
        for v in result.values():
            assert v is None or isinstance(v, float)

    def test_values_are_float_or_none(self):
        result = get_aegl_thresholds(AMMONIA)
        for k, v in result.items():
            assert v is None or isinstance(v, float), f"Key {k} has unexpected type {type(v)}"

    def test_severity_ordering(self):
        """AEGL-3 (lethal) > AEGL-2 (disabling) > AEGL-1 (notable) when all defined."""
        result = get_aegl_thresholds(CHLORINE, duration_min=10)
        a1 = result.get("AEGL-1")
        a2 = result.get("AEGL-2")
        a3 = result.get("AEGL-3")
        if a1 is not None and a2 is not None:
            assert a2 >= a1, "AEGL-2 should be >= AEGL-1"
        if a2 is not None and a3 is not None:
            assert a3 >= a2, "AEGL-3 should be >= AEGL-2"


class TestGetErpgThresholds:
    def test_known_chemical_returns_values(self):
        result = get_erpg_thresholds(CHLORINE)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_unknown_chemical_returns_nones_or_empty(self):
        result = get_erpg_thresholds("unobtanium_xyz_999")
        # Should not raise; all values should be None or dict empty
        for v in result.values():
            assert v is None


class TestGetIdlhThreshold:
    def test_chlorine_positive(self):
        val = get_idlh_threshold(CHLORINE)
        assert val is not None and val > 0

    def test_unknown_returns_none(self):
        val = get_idlh_threshold("notachemical_12345")
        assert val is None


class TestGetAllThresholds:
    def test_returns_dict(self):
        result = get_all_thresholds(AMMONIA)
        assert isinstance(result, dict)

    def test_contains_required_sections(self):
        result = get_all_thresholds(CHLORINE)
        for section in ("chemical", "AEGL", "ERPG", "PAC", "IDLH"):
            assert section in result, f"Missing section: {section}"

    def test_chemical_field_matches_input(self):
        result = get_all_thresholds(CHLORINE)
        assert CHLORINE.lower() in result["chemical"].lower()
