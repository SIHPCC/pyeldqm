"""Folium visualization workflow.

Demonstrates operational map generation for dispersion outputs, including hazard
zone overlays, wind context, and HTML export for sharing and review.

Dependencies:
`folium`, `scikit-image`, `branca`.
"""

import numpy as np
from datetime import datetime
import sys
import os
from pathlib import Path
import webbrowser
import tempfile
import math

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import pyELDQM modules
from pyeldqm.core.dispersion_models.gaussian_model import single_source_concentration
from pyeldqm.core.dispersion_models.dispersion_utils import get_sigmas
from pyeldqm.core.meteorology.stability import get_stability_class
from pyeldqm.core.meteorology.wind_profile import wind_speed as calc_wind_profile
from pyeldqm.core.geography import get_complete_geographic_info

# Import Folium visualization
try:
    from pyeldqm.core.visualization.folium_maps import (
        create_dispersion_map,
        save_map,
        add_facility_markers,
        add_compass
    )
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("WARNING: Folium not installed. Install with: pip install folium scikit-image")


# %%
# # 1. Setup: Run Gaussian Dispersion Model
# First, we'll run a dispersion calculation to get concentration data

print("=" * 80)
print("FOLIUM VISUALIZATION TUTORIAL - Interactive Dispersion Mapping")
print("=" * 80)

print("\n" + "=" * 80)
print("1. SETUP: RUNNING GAUSSIAN DISPERSION MODEL")
print("=" * 80)

# --- Scenario Parameters ---
print("\nScenario: Ammonia Release from Industrial Facility")
print("-" * 80)

# Chemical properties
chemical_name = "Ammonia (NH3)"
MW = 17.03  # g/mol
release_rate = 1000  # g/s
release_duration = 600  # seconds (10 minutes)

# Location: Karachi Industrial Area
latitude = 24.85
longitude = 67.05
location_name = "Karachi Industrial Zone"

# Get complete geographic info
geo_info = get_complete_geographic_info(
    latitude=latitude,
    longitude=longitude,
    fetch_online=False
)

print(f"Location: {location_name}")
print(f"Coordinates: {latitude}°N, {longitude}°E")
print(f"Terrain: {geo_info.get('terrain', 'flat')}")
print(f"Land Use: {geo_info.get('land_use', 'urban')}")
print(f"Surface Roughness: {geo_info.get('roughness', 'URBAN')}")

# Meteorological conditions
U = 5  # Wind speed (m/s)
wind_direction = 45  # degrees from north (NE wind)
z_ref = 3  # Reference height (m)
h_s = 3  # Source height (m)
temperature = 35 + 273.15  # K

# Date/time for stability calculation
datetime_obj = datetime(2025, 6, 25, 15, 0)
cloudiness_index = 0

print(f"\nMeteorological Conditions:")
print(f"  Wind Speed: {U} m/s at {z_ref}m height")
print(f"  Wind Direction: {wind_direction}° (from North)")
print(f"  Temperature: {temperature - 273.15:.1f}°C")
print(f"  Date/Time: {datetime_obj.strftime('%Y-%m-%d %H:%M')}")

# Calculate stability class
stability_class = get_stability_class(
    wind_speed=U,
    datetime_obj=datetime_obj,
    latitude=latitude,
    longitude=longitude,
    cloudiness_index=cloudiness_index,
    timezone_offset_hrs=5
)

print(f"  Stability Class: {stability_class}")

# Release parameters
print(f"\nRelease Parameters:")
print(f"  Chemical: {chemical_name}")
print(f"  Release Rate: {release_rate} g/s")
print(f"  Duration: {release_duration/60:.1f} minutes")
print(f"  Source Height: {h_s} m")


# %%
# # 2. Calculate Concentration Field
# Run Gaussian model to compute concentration grid

print("\n" + "=" * 80)
print("2. CALCULATING CONCENTRATION FIELD")
print("=" * 80)

# Adjust wind speed for source height
U_local = calc_wind_profile(
    z_user=h_s,
    z0=z_ref,
    U_user=U,
    stability_class=stability_class
)

print(f"\nEffective wind speed at source height ({h_s}m): {U_local:.2f} m/s")

# Create computational grid
x_max = 2000  # meters downwind
y_max = 800   # meters crosswind
nx, ny = 500, 500

x_vals = np.linspace(10, x_max, nx)
y_vals = np.linspace(-y_max, y_max, ny)
X, Y = np.meshgrid(x_vals, y_vals)

print(f"\nGrid Setup:")
print(f"  Downwind extent: {x_max} m")
print(f"  Crosswind extent: ±{y_max} m")
print(f"  Grid resolution: {nx} × {ny} points")

# Calculate concentrations
print("\nCalculating concentration field...")
C_grid = np.zeros_like(X)

# Molar volume for unit conversion
R = 0.08206  # L·atm/(mol·K)
Vm = R * temperature / 1.0  # L/mol at 1 atm

t = release_duration
t_r = release_duration
z0 = 1.5  # Receptor height

for i in range(ny):
    for j in range(nx):
        x = X[i, j]
        y = Y[i, j]
        sig_x, sig_y, sig_z = get_sigmas(x, stability_class, 'URBAN')
        C_grid[i, j] = single_source_concentration(
            x=x,
            y=y,
            z=z0,
            t=t,
            t_r=t_r,
            Q=release_rate,
            U=U_local,
            sigma_x=sig_x,
            sigma_y=sig_y,
            sigma_z=sig_z,
            h_s=h_s,
            mode='continuous'
        )

# Convert to ppm
C_ppm = C_grid * (Vm / MW) * 1000

print(f"Calculation complete!")
print(f"  Maximum concentration: {np.max(C_ppm):.1f} ppm")
print(f"  At location: x={x_vals[np.argmax(C_ppm) % nx]:.0f}m, y={y_vals[np.argmax(C_ppm) // nx]:.0f}m")


# %%
# # 3. Define Hazard Thresholds
# Set AEGL (Acute Exposure Guideline Levels) for Ammonia

print("\n" + "=" * 80)
print("3. DEFINING HAZARD THRESHOLDS")
print("=" * 80)

# AEGL values for Ammonia (10-minute exposure)
AEGL_THRESHOLDS = {
    "AEGL-1": 30,    # Mild discomfort (ppm)
    "AEGL-2": 160,   # Irreversible or serious effects (ppm)
    "AEGL-3": 1100   # Life-threatening effects (ppm)
}

print("\nAcute Exposure Guideline Levels (AEGL) for Ammonia:")
print("-" * 80)
print(f"  AEGL-1: {AEGL_THRESHOLDS['AEGL-1']:>4} ppm - Mild discomfort")
print(f"  AEGL-2: {AEGL_THRESHOLDS['AEGL-2']:>4} ppm - Irreversible effects")
print(f"  AEGL-3: {AEGL_THRESHOLDS['AEGL-3']:>4} ppm - Life-threatening")

# Find centerline distances
centerline_ppm = C_ppm[ny // 2, :]
aegl_distances = {}

print("\nCenterline Distances to AEGL Thresholds:")
print("-" * 80)

for label, threshold in AEGL_THRESHOLDS.items():
    indices = np.where(centerline_ppm >= threshold)[0]
    if len(indices) > 0:
        distance = x_vals[indices[-1]]
        aegl_distances[label] = distance
        print(f"  {label}: {distance:>7.1f} meters")
    else:
        aegl_distances[label] = 0
        print(f"  {label}: Not exceeded")


# %%
# # 4. Create Basic Interactive Map
# Generate Folium map with dispersion contours

if not FOLIUM_AVAILABLE:
    print("\n" + "!" * 80)
    print("ERROR: Folium not available. Please install:")
    print("  pip install folium scikit-image branca")
    print("!" * 80)
else:
    print("\n" + "=" * 80)
    print("4. CREATING INTERACTIVE FOLIUM MAP")
    print("=" * 80)
    
    print("\nGenerating interactive map...")
    
    # Create the map
    dispersion_map = create_dispersion_map(
        source_lat=latitude,
        source_lon=longitude,
        x_grid=X,
        y_grid=Y,
        concentration=C_ppm,
        thresholds=AEGL_THRESHOLDS,
        wind_direction=wind_direction,
        zoom_start=15,
        chemical_name="Ammonia",
        source_height=h_s,
        wind_speed=U,
        stability_class=stability_class,
        include_heatmap=True,
        include_compass=True
    )
    
    print("\n[SUCCESS] Interactive map created!")
    
    # Open in browser instead of just saving
    print("\nOpening map in browser...")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w')
    dispersion_map.save(temp_file.name)
    temp_file.close()
    
    try:
        webbrowser.open('file://' + temp_file.name)
        print("[SUCCESS] Map opened in browser!")
    except Exception as e:
        print(f"[ERROR] Could not open browser: {e}")


# %%
# # 5. Animated Wind Direction Scenario
# Show how wind direction affects dispersion in ONE interactive map

if FOLIUM_AVAILABLE:
    print("\n" + "=" * 80)
    print("6. ANIMATED WIND DIRECTION SCENARIOS")
    print("=" * 80)
    
    print("\nCreating single animated map with multiple wind scenarios...")
    print("This map will have layers for different wind directions that you can toggle!")
    
    import folium
    
    # Create base map
    animated_map = folium.Map(
        location=[latitude, longitude],
        zoom_start=12,
        tiles='OpenStreetMap',
        control_scale=True
    )

    # Add compass overlay on the animated map as well
    add_compass(animated_map, position='bottomright')
    
    # Add source marker
    folium.Marker(
        [latitude, longitude],
        popup=f'<b>{chemical_name} Release Source</b>',
        tooltip='Release Source',
        icon=folium.Icon(color='red', icon='warning-sign', prefix='glyphicon')
    ).add_to(animated_map)
    
    wind_scenarios = [0, 45, 90, 135, 180, 225, 270, 315]  # 8 directions
    wind_labels = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    
    print(f"\nAdding {len(wind_scenarios)} wind direction scenarios as toggleable layers...")
    
    for wind_dir, wind_label in zip(wind_scenarios, wind_labels):
        print(f"  • Wind from {wind_label} ({wind_dir}°)")
        
        # Create feature group for this wind direction
        wind_group = folium.FeatureGroup(
            name=f'Wind from {wind_label} ({wind_dir}°)',
            show=(wind_dir == wind_direction)  # Show current wind direction by default
        )
        
        # Convert grid to lat/lon for this wind direction
        from pyeldqm.core.visualization.folium_maps import meters_to_latlon, add_concentration_contour
        lat_grid_rot, lon_grid_rot = meters_to_latlon(X, Y, latitude, longitude, wind_dir)
        
        # Add contours for this wind direction
        for label, threshold in sorted(AEGL_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            try:
                add_concentration_contour(
                    wind_group,
                    lat_grid_rot,
                    lon_grid_rot,
                    C_ppm,
                    threshold,
                    label,
                    "Ammonia"
                )
            except:
                pass
        
        wind_group.add_to(animated_map)
    
    # Add layer control
    folium.LayerControl(collapsed=False).add_to(animated_map)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 60px; width: 450px; height: 80px; 
                background-color: white; border: 2px solid grey; z-index: 9999; 
                font-size: 14px; padding: 10px; border-radius: 5px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <h4 style="margin: 0; color: #d32f2f;">Ammonia Dispersion - Wind Direction Analysis</h4>
        <p style="margin: 5px 0 0 0; font-size: 11px;">
            Toggle different wind directions using the layer control (top right) →<br>
            <i>Each layer shows how the plume rotates with changing wind direction</i>
        </p>
    </div>
    '''
    animated_map.get_root().html.add_child(folium.Element(title_html))
    
    print("\n[SUCCESS] Animated wind scenario map created!")
    print("Opening in browser...")
    print("\nTip: Use the layer control (top-right) to toggle between wind directions!")
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w')
    animated_map.save(temp_file.name)
    temp_file.close()
    webbrowser.open('file://' + temp_file.name)


# %%
# # 6. Save Map to File (Optional)
# Example: How to save a map to a permanent file

if FOLIUM_AVAILABLE:
    print("\n" + "=" * 80)
    print("6. SAVING MAP TO FILE (OPTIONAL)")
    print("=" * 80)
    
    print("\nAll previous maps opened directly in browser.")
    print("Here's how to save a map to a permanent file:")
    
    # Create output directory
    output_dir = Path(parent_dir) / 'outputs' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a final summary map
    print("\nCreating final summary map for saving...")
    final_map = create_dispersion_map(
        source_lat=latitude,
        source_lon=longitude,
        x_grid=X,
        y_grid=Y,
        concentration=C_ppm,
        thresholds=AEGL_THRESHOLDS,
        wind_direction=wind_direction,
        zoom_start=12,
        chemical_name="Ammonia",
        source_height=h_s,
        wind_speed=U,
        stability_class=stability_class,
        include_heatmap=True
    )
    
    # Save to permanent file
    map_file = output_dir / 'ammonia_dispersion_report.html'
    save_map(final_map, str(map_file))
    
    print(f"\n[SUCCESS] Map saved to permanent file!")
    print(f"File: {map_file}")
    print(f"Size: {map_file.stat().st_size / 1024:.1f} KB")