"""
core/utils/geo_constants.py
===========================
Shared geographic constants and unit-conversion helpers.

Using a single source of truth avoids the ``111320.0`` literal being scattered
across dispersion, visualization, evacuation, and sensor modules.
"""
from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Earth geometry constants
# ---------------------------------------------------------------------------

#: Approximate metres per degree of latitude (equirectangular, valid < 100 km)
METERS_PER_DEGREE_LAT: float = 111_320.0


# ---------------------------------------------------------------------------
# Inline conversion helpers
# ---------------------------------------------------------------------------

def m_to_deg_lat(meters: float) -> float:
    """Convert a north-south distance in metres to degrees of latitude."""
    return meters / METERS_PER_DEGREE_LAT


def m_to_deg_lon(meters: float, latitude_deg: float) -> float:
    """Convert an east-west distance in metres to degrees of longitude at *latitude_deg*."""
    return meters / (METERS_PER_DEGREE_LAT * math.cos(math.radians(latitude_deg)))


def deg_lat_to_m(degrees: float) -> float:
    """Convert degrees of latitude to metres."""
    return degrees * METERS_PER_DEGREE_LAT
