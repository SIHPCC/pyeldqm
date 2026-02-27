"""
Tests for core.utils.geo_constants
"""
import math
import pytest
from pyeldqm.core.utils.geo_constants import (
    METERS_PER_DEGREE_LAT,
    m_to_deg_lat,
    m_to_deg_lon,
    deg_lat_to_m,
)


def test_meters_per_degree_lat_value():
    """Canonical value is 111 320 m/degree."""
    assert METERS_PER_DEGREE_LAT == pytest.approx(111_320.0, rel=1e-6)


def test_m_to_deg_lat_round_trip():
    """Converting 1 deg to metres and back must recover 1 degree."""
    metres = METERS_PER_DEGREE_LAT
    degrees = m_to_deg_lat(metres)
    assert degrees == pytest.approx(1.0, rel=1e-9)


def test_deg_lat_to_m_round_trip():
    deg = 0.5
    assert deg_lat_to_m(deg) == pytest.approx(deg * METERS_PER_DEGREE_LAT, rel=1e-9)


def test_m_to_deg_lon_equator():
    """At the equator lon and lat degrees should be equal."""
    lon_deg = m_to_deg_lon(METERS_PER_DEGREE_LAT, latitude_deg=0.0)
    assert lon_deg == pytest.approx(1.0, rel=1e-6)


def test_m_to_deg_lon_poles_approach():
    """At 89° latitude, 1 lon degree covers far fewer metres → deg_per_m is large."""
    lon_deg_89 = m_to_deg_lon(1000.0, latitude_deg=89.0)
    lon_deg_0  = m_to_deg_lon(1000.0, latitude_deg=0.0)
    assert lon_deg_89 > lon_deg_0 * 10, "Longitude degrees should expand near poles"


def test_m_to_deg_lat_positive():
    for metres in [1.0, 100.0, 10_000.0]:
        assert m_to_deg_lat(metres) > 0
