"""
Multi-Source Gaussian Dispersion + Folium Visualization
=======================================================

This example simulates multiple continuous release sources under a shared wind
field, sums their Gaussian contributions on a common grid, and visualizes
AEGL hazard zones on an interactive Folium map.

Dependencies:
    pip install folium scikit-image branca
"""

import numpy as np
from datetime import datetime
import sys
import os
import tempfile
import webbrowser

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# pyELDQM imports
from core.dispersion_models.gaussian_model import multi_source_concentration
from core.meteorology.stability import get_stability_class
from core.meteorology.wind_profile import wind_speed as calc_wind_profile
from core.geography import get_complete_geographic_info
from core.visualization.folium_maps import (
    create_dispersion_map,
    add_facility_markers,
    meters_to_latlon
)

print("=" * 80)
print("MULTI-SOURCE DISPERSION - Interactive Threat Zone Mapping")
print("=" * 80)

# Scenario setup
chemical_name = "Ammonia (NH3)"
MW = 17.03  # g/mol

# Location (Karachi area)
latitude = 24.85
longitude = 67.05
location_name = "Industrial Cluster"

geo_info = get_complete_geographic_info(
    latitude=latitude,
    longitude=longitude,
    fetch_online=False
)
print(f"Location: {location_name} | {latitude:.4f}°N, {longitude:.4f}°E")
print(f"Terrain: {geo_info.get('terrain', 'flat')}, Land Use: {geo_info.get('land_use', 'urban')}")

# Meteorology
U = 5.0                 # wind speed (m/s) at reference height
wind_direction = 45   # degrees from north (meteorological convention)
z_ref = 3.0             # reference height (m)
h_s_default = 3.0       # default source height (m)
T = 35 + 273.15         # K (for ppm conversion)

# Stability
datetime_obj = datetime(2025, 6, 25, 15, 0)
stability_class = get_stability_class(
    wind_speed=U,
    datetime_obj=datetime_obj,
    latitude=latitude,
    longitude=longitude,
    cloudiness_index=0,
    timezone_offset_hrs=5
)
print(f"Stability Class: {stability_class}")

# Adjust wind speed for source height
U_local = calc_wind_profile(
    z_user=h_s_default,
    z0=z_ref,
    U_user=U,
    stability_class=stability_class
)
print(f"Effective wind speed at {h_s_default} m: {U_local:.2f} m/s")

# Computational grid (meters, aligned with local x/y)
x_max = 2000
y_max = 800
nx, ny = 400, 400
x_vals = np.linspace(10, x_max, nx)
y_vals = np.linspace(-y_max, y_max, ny)
X, Y = np.meshgrid(x_vals, y_vals)

# Define multiple sources (offsets in meters relative to the origin)
# Each source: Q (g/s), x0 (m), y0 (m), h_s (m)
sources = [
    {"name": "Source A", "Q": 800, "x0": 0,   "y0": 0,    "h_s": 3.0, "wind_dir": 45.0},
    {"name": "Source B", "Q": 600, "x0": 250, "y0": -120, "h_s": 2.5, "wind_dir": 45.0},
    {"name": "Source C", "Q": 500, "x0": 600, "y0": 180,  "h_s": 3.5, "wind_dir": 45.0},
]

# Release schedule
release_duration = 600  # seconds
z_receptor = 1.5        # receptor height (m)

# Compute combined concentration (g/m^3 scaled by Gaussian model)
C_total = multi_source_concentration(
    sources=sources,
    x_grid=X,
    y_grid=Y,
    z=z_receptor,
    t=release_duration,
    t_r=release_duration,
    U=U_local,
    stability_class=stability_class,
    roughness='URBAN',
    mode='continuous',
    grid_wind_direction=wind_direction
)

# Convert to ppm
R = 0.08206  # L·atm/(mol·K)
Vm = R * T / 1.0  # L/mol at 1 atm
C_ppm = C_total * (Vm / MW) * 1000

print(f"Max combined concentration: {np.max(C_ppm):.1f} ppm")

# AEGL thresholds for Ammonia (10-minute exposure)
AEGL_THRESHOLDS = {
    "AEGL-3": 1100,
    "AEGL-2": 160,
    "AEGL-1": 30,
}

# Create interactive map with combined threat zones
m = create_dispersion_map(
    source_lat=latitude,
    source_lon=longitude,
    x_grid=X,
    y_grid=Y,
    concentration=C_ppm,
    thresholds=AEGL_THRESHOLDS,
    wind_direction=wind_direction,
    zoom_start=14,
    chemical_name="Ammonia",
    source_height=h_s_default,
    wind_speed=U,
    stability_class=stability_class,
    include_heatmap=True,
    include_compass=True,
)

# Add markers for each source (convert local offsets to lat/lon)
source_markers = []
for src in sources:
    lat_s, lon_s = meters_to_latlon(
        np.array([[src['x0']]]),
        np.array([[src['y0']]]),
        latitude,
        longitude,
        rotation_deg=wind_direction
    )
    source_markers.append({
        'name': f"{src['name']} (Q={src['Q']} g/s, WD={src['wind_dir']}°)",
        'lat': float(lat_s[0, 0]),
        'lon': float(lon_s[0, 0]),
        'type': 'industrial'
    })

add_facility_markers(m, source_markers, group_name="Release Sources")

# Open in browser
print("Opening interactive map in browser...")
tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
m.save(tmp.name)
tmp.close()
webbrowser.open('file://' + tmp.name)
