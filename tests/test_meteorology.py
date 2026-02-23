"""
Tests for core.meteorology — wind profile and stability utilities.
"""
import math
import datetime
import pytest
from core.meteorology.wind_profile import (
    obukhov_length,
    psi_zeta,
    stability_exponent,
    friction_velocity,
    wind_speed,
)
from core.meteorology.stability import get_stability_class


# ---------------------------------------------------------------------------
# obukhov_length
# ---------------------------------------------------------------------------

class TestObukhovLength:
    def test_neutral_class_D_is_infinite(self):
        L = obukhov_length(0.1, "D")
        assert math.isinf(L)

    def test_unstable_classes_negative(self):
        for stab in "ABC":
            L = obukhov_length(0.1, stab)
            assert L < 0, f"Obukhov length for class {stab} should be negative (unstable)"

    def test_stable_classes_positive(self):
        for stab in "EF":
            L = obukhov_length(0.1, stab)
            assert L > 0, f"Obukhov length for class {stab} should be positive (stable)"

    def test_invalid_class_raises(self):
        with pytest.raises(ValueError):
            obukhov_length(0.1, "Z")


# ---------------------------------------------------------------------------
# psi_zeta
# ---------------------------------------------------------------------------

class TestPsiZeta:
    def test_neutral(self):
        assert psi_zeta(0.0) == 0.0

    def test_stable_negative(self):
        assert psi_zeta(1.0) < 0

    def test_unstable_positive(self):
        assert psi_zeta(-1.0) > 0


# ---------------------------------------------------------------------------
# stability_exponent
# ---------------------------------------------------------------------------

class TestStabilityExponent:
    @pytest.mark.parametrize("cls,expected", [
        ("A", 0.108), ("B", 0.112), ("C", 0.120),
        ("D", 0.142), ("E", 0.203), ("F", 0.253),
    ])
    def test_known_values(self, cls, expected):
        assert stability_exponent(cls) == pytest.approx(expected, abs=1e-6)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            stability_exponent("G")


# ---------------------------------------------------------------------------
# wind_speed
# ---------------------------------------------------------------------------

class TestWindSpeed:
    def test_power_law_returns_positive(self):
        u = wind_speed(10.0, 0.1, 5.0, "D", method="power_law")
        assert u > 0

    def test_power_law_increases_with_height(self):
        u10 = wind_speed(10.0, 0.1, 5.0, "D", method="power_law")
        u50 = wind_speed(50.0, 0.1, 5.0, "D", method="power_law")
        assert u50 > u10

    def test_monin_obukhov_neutral(self):
        u = wind_speed(10.0, 0.1, 5.0, "D", method="monin_obukhov")
        assert u > 0


# ---------------------------------------------------------------------------
# get_stability_class (basic smoke)
# ---------------------------------------------------------------------------

class TestGetStabilityClass:
    def test_returns_letter_in_A_to_F(self):
        # Midday in summer at a mid-latitude location
        dt = datetime.datetime(2024, 6, 15, 12, 0, 0)
        result = get_stability_class(
            wind_speed=3.0,
            datetime_obj=dt,
            latitude=14.6,   # Manila-ish
            longitude=121.0,
            cloudiness_index=3,
        )
        assert result in set("ABCDEF"), f"Unexpected stability class: {result}"
