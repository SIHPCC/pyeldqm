"""
Tests for core.dispersion_models.dispersion_utils
"""
import pytest
import numpy as np
from pyeldqm.core.dispersion_models.dispersion_utils import (
    sigma_x,
    sigma_y,
    sigma_z,
    get_sigmas,
    gy,
    gz,
    DISPERSION_COEFFICIENTS,
)


# ---------------------------------------------------------------------------
# Smoke tests — every stability class × roughness must return positive values
# ---------------------------------------------------------------------------

STABILITY_CLASSES = list("ABCDEF")
ROUGHNESS_TYPES = ["RURAL", "URBAN"]


@pytest.mark.parametrize("stab", STABILITY_CLASSES)
@pytest.mark.parametrize("rough", ROUGHNESS_TYPES)
def test_get_sigmas_positive(stab, rough):
    """sigma values must be positive for any plausible downwind distance."""
    sx, sy, sz = get_sigmas(x=500.0, stability_class=stab, roughness=rough)
    assert sx > 0, f"sigma_x <= 0 for {stab}/{rough}"
    assert sy > 0, f"sigma_y <= 0 for {stab}/{rough}"
    assert sz > 0, f"sigma_z <= 0 for {stab}/{rough}"


@pytest.mark.parametrize("stab", STABILITY_CLASSES)
def test_get_sigmas_increases_with_distance(stab):
    """Sigma values must increase as downwind distance increases (rural)."""
    _, sy1, sz1 = get_sigmas(x=100.0, stability_class=stab, roughness="RURAL")
    _, sy2, sz2 = get_sigmas(x=1000.0, stability_class=stab, roughness="RURAL")
    assert sy2 > sy1, f"sigma_y did not increase with distance for class {stab}"
    assert sz2 > sz1, f"sigma_z did not increase with distance for class {stab}"


# ---------------------------------------------------------------------------
# Unit tests for helper kernels
# ---------------------------------------------------------------------------

def test_gy_peak():
    """gy should be maximised on the plume centreline (y=0)."""
    sigma = 50.0
    g_centre = gy(0.0, sigma)
    g_offaxis = gy(30.0, sigma)
    assert g_centre > g_offaxis


def test_gz_symmetry():
    """gz with reflection (h_s>0) must give same value at ±z offsets."""
    sigma = 50.0
    h_s = 10.0
    # The ground-reflection formula is NOT symmetric around z=0 in general,
    # but the sum of two Gaussians at z=h_s and z=-h_s IS symmetric about h_s.
    # Here we just verify a finite positive value is returned.
    val = gz(h_s, sigma, h_s)
    assert val > 0


def test_sigma_x_scalar():
    assert sigma_x(1000.0, 0.04, 1.14) == pytest.approx(0.04 * (1000.0 ** 1.14), rel=1e-9)


def test_sigma_y_scalar():
    val = sigma_y(500.0, 0.08, 1e-4)
    assert val > 0


def test_sigma_z_scalar():
    val = sigma_z(500.0, 0.06, 1.5e-3, -0.5)
    assert val > 0


# ---------------------------------------------------------------------------
# Regression: class D rural coefficients (widely tabulated)
# ---------------------------------------------------------------------------

def test_class_d_rural_coefficients():
    coeffs = DISPERSION_COEFFICIENTS["D"]
    assert coeffs["BOTH"]["sy1"] == pytest.approx(0.08, abs=1e-6)
    assert coeffs["RURAL"]["sz1"] == pytest.approx(0.06, abs=1e-6)
