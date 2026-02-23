"""Shelter-in-place versus evacuation analysis workflow.

Compares protective action strategies using indoor exposure modeling,
building leakage assumptions, and time-dependent concentration projections.

Run:
`python 10_shelter_in_place_analysis.py`
"""
import os
import sys
import time
import tempfile
import webbrowser
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

import numpy as np
import folium
from shapely.geometry import Polygon, Point
from skimage import measure

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# pyELDQM imports
from core.utils import LiveLoopManager
from core.utils.features import setup_computational_grid
from core.utils.zone_extraction import extract_zones
from core.dispersion_models.gaussian_model import calculate_gaussian_dispersion
from core.meteorology.realtime_weather import get_weather
from core.protective_actions import (
    shelter_protection_factor,
    compare_protective_actions,
    recommend_protective_action,
    analyze_shelter_zones
)
from core.visualization import add_shelter_in_place_panel, ensure_layer_control, fit_map_to_polygons


class Config:
    # Location
    LAT = 31.691100
    LON = 74.082167
    CHEM = "Ammonia (NH3)"
    MW = 17.03
    RELEASE_RATE = 800.0
    HEIGHT = 3.0
    Z_REF = 3.0
    
    # Grid
    X_MAX = 4000
    Y_MAX = 4000
    NX = 600
    NY = 600
    
    # AEGL thresholds
    AEGL = {"AEGL-1": 30, "AEGL-2": 160, "AEGL-3": 1100}
    
    # Weather
    USE_MANUAL_WEATHER = False
    MANUAL_WIND_SPEED_MS = 1.5
    MANUAL_WIND_DIR_DEG = 270
    MANUAL_TEMPERATURE_K = 298.15
    MANUAL_HUMIDITY = 0.55
    MANUAL_CLOUD_COVER = 0.2
    
    # Shelter analysis
    BUILDING_TYPE = "industrial"  # residential_tight, residential_leaky, commercial, industrial
    SHELTERING_TIME_MIN = 60
    EVACUATION_TIME_MIN = 15
    SAMPLE_GRID_POINTS = 15  # Grid density for zone analysis
    
    # Live update
    UPDATE_INTERVAL_SECONDS = 20


# extract_zones() is now imported from core.utils.zone_extraction


def render_protective_action_zones(
    m: folium.Map,
    threat_zones: Dict[str, Optional[Polygon]],
    shelter_analysis: Dict,
    source_lat: float,
    source_lon: float
):
    """Render shelter vs evacuate zones on map."""
    
    # Create feature groups
    shelter_fg = folium.FeatureGroup(name="SHELTER-IN-PLACE Zones", show=True)
    evacuate_fg = folium.FeatureGroup(name="EVACUATE Zones", show=True)
    
    for zone_name, zone_data in shelter_analysis.items():
        zone_poly = threat_zones.get(zone_name)
        if zone_poly is None or zone_poly.is_empty:
            continue
        
        primary_rec = zone_data["primary_recommendation"]
        
        # Color by recommendation
        if primary_rec == "SHELTER":
            color = "#4CAF50"  # Green for shelter
            fg = shelter_fg
            label = f"{zone_name}: SHELTER-IN-PLACE ({zone_data['shelter_percentage']:.0f}%)"
        else:
            color = "#FF5722"  # Orange-red for evacuate
            fg = evacuate_fg
            label = f"{zone_name}: EVACUATE ({zone_data['shelter_percentage']:.0f}% shelter)"
        
        popup_html = f"""
        <div style="font-family: Arial; font-size: 11px;">
            <b>{zone_name}</b><br>
            <b>Primary Recommendation:</b> {primary_rec}<br>
            Shelter: {zone_data['shelter_count']} samples ({zone_data['shelter_percentage']:.1f}%)<br>
            Evacuate: {zone_data['evacuate_count']} samples
        </div>
        """
        
        folium.GeoJson(
            zone_poly,
            name=label,
            style_function=lambda x, c=color: {
                "fillColor": c,
                "color": c,
                "weight": 2,
                "fillOpacity": 0.3
            },
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(fg)
    
    shelter_fg.add_to(m)
    evacuate_fg.add_to(m)


def main():
    """Live shelter-in-place analysis with weather updates."""
    print("\n" + "=" * 90)
    print("SHELTER-IN-PLACE vs EVACUATION ANALYSIS")
    print("=" * 90)
    print(f"Location: {Config.LAT}°N, {Config.LON}°E")
    print(f"Chemical: {Config.CHEM}")
    print(f"Building Type: {Config.BUILDING_TYPE}")
    print(f"Sheltering Duration: {Config.SHELTERING_TIME_MIN} min")
    print("=" * 90 + "\n")

    # Setup grid
    X, Y, _, _ = setup_computational_grid(Config.X_MAX, Config.Y_MAX, Config.NX, Config.NY)

    temp_output_file = Path(tempfile.gettempdir()) / "shelter_in_place_analysis.html"
    manager = LiveLoopManager(
        update_interval=Config.UPDATE_INTERVAL_SECONDS,
        output_file=str(temp_output_file),
        app_name="Shelter-in-Place Analysis"
    )

    try:
        for cycle in manager.run():
            print(f"\n{'='*90}")
            print(f"CYCLE #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*90}")
            try:
                # Weather
                if Config.USE_MANUAL_WEATHER:
                    wind_dir = (Config.MANUAL_WIND_DIR_DEG + (cycle - 1) * 20) % 360
                    weather = {
                        "source": "manual",
                        "wind_speed": Config.MANUAL_WIND_SPEED_MS,
                        "wind_dir": wind_dir,
                        "temperature_K": Config.MANUAL_TEMPERATURE_K,
                        "humidity": Config.MANUAL_HUMIDITY,
                        "cloud_cover": Config.MANUAL_CLOUD_COVER,
                    }
                else:
                    weather = get_weather(source="open_meteo", latitude=Config.LAT, longitude=Config.LON)
                C, U, stab, _ = calculate_gaussian_dispersion(
                    weather=weather, X=X, Y=Y,
                    source_lat=Config.LAT, source_lon=Config.LON,
                    molecular_weight=Config.MW,
                    default_release_rate=Config.RELEASE_RATE,
                    default_height=Config.HEIGHT,
                    z_ref=Config.Z_REF,
                    sources=[{"lat": Config.LAT, "lon": Config.LON, "name": "Tank", "height": Config.HEIGHT, "rate": Config.RELEASE_RATE}],
                    latitude=Config.LAT, longitude=Config.LON, timezone_offset_hrs=12
                )
                print(f"  Stability: {stab}, Max Conc: {np.nanmax(C):.1f} ppm")

                # Extract zones
                zones = extract_zones(X, Y, C, Config.AEGL, Config.LAT, Config.LON, weather["wind_dir"])

                # Analyze shelter recommendations
                print("  Analyzing protective actions...")
                shelter_analysis = analyze_shelter_zones(
                    zones, Config.LAT, Config.LON,
                    grid_points=Config.SAMPLE_GRID_POINTS,
                    building_type=Config.BUILDING_TYPE
                )

                # Print recommendations
                for zone_name, data in shelter_analysis.items():
                    print(f"  {zone_name}: {data['primary_recommendation']} ({data['shelter_percentage']:.0f}% shelter)")

                # Build map
                m = folium.Map(location=[Config.LAT, Config.LON], zoom_start=13, tiles='OpenStreetMap')
                folium.TileLayer(
                    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                    attr='Esri', name='Satellite', overlay=False, control=True
                ).add_to(m)

                # Source marker
                folium.Marker(
                    [Config.LAT, Config.LON],
                    tooltip="Hazard Source",
                    icon=folium.Icon(color="red", icon="warning-sign")
                ).add_to(m)

                # Render protective action zones
                render_protective_action_zones(m, zones, shelter_analysis, Config.LAT, Config.LON)

                # Auto-zoom to fit all zones
                fit_map_to_polygons(m, zones.values())

                # Info panel (centralized)
                add_shelter_in_place_panel(
                    m,
                    shelter_analysis,
                    building_type=Config.BUILDING_TYPE,
                    shelter_time_min=Config.SHELTERING_TIME_MIN,
                    weather=weather,
                    position="bottomleft",
                )

                # Layer control (centralized ensure)
                ensure_layer_control(m)

                # Save
                m.save(str(temp_output_file))
                print(f"  ✓ Map saved: {temp_output_file}")

                # Open browser on first cycle
                manager.open_browser_once()

                print(f"\n  Recommendation: Shelter-in-Place zones determined")
                
                # Wait for next cycle
                manager.wait_for_next_cycle()
        
            except Exception as e:
                manager.handle_error(e)
                continue

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
