"""Health impact threshold zone workflow.

Performs multi-threshold hazard assessment using AEGL, ERPG, PAC, and IDLH
criteria with live or manual meteorological inputs.

Run:
`python 11_health_impact_threshold_zones.py`
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
from shapely.geometry import Polygon
from skimage import measure

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# pyELDQM imports
from core.utils import LiveLoopManager
from core.utils.features import setup_computational_grid
from core.utils.zone_extraction import extract_zones, parse_threshold
from core.dispersion_models.gaussian_model import calculate_gaussian_dispersion
from core.meteorology.realtime_weather import get_weather
from core.health_thresholds import (
    get_aegl_thresholds,
    get_erpg_thresholds,
    get_pac_thresholds,
    get_idlh_threshold,
    display_thresholds
)
from core.visualization import add_health_thresholds_panel, ensure_layer_control, add_zone_polygons, fit_map_to_polygons


class Config:
    # Location
    LAT = 31.691100
    LON = 74.082167
    CHEMICAL = "AMMONIA"  # Try: CHLORINE, HYDROGEN SULFIDE, etc.
    MW = 17.03
    RELEASE_RATE = 800.0  # Increased for better zone visibility
    HEIGHT = 3.0
    Z_REF = 3.0
    
    # Grid
    X_MAX = 5000
    Y_MAX = 5000
    NX = 800
    NY = 800
    
    # Weather mode
    USE_MANUAL_WEATHER = False  # Set to False for real-time weather
    MANUAL_WIND_SPEED_MS = 1
    MANUAL_WIND_DIR_DEG = 270
    MANUAL_TEMPERATURE_K = 298.15
    MANUAL_HUMIDITY = 0.55
    MANUAL_CLOUD_COVER = 0.2
    
    # Display options
    SHOW_AEGL = True
    SHOW_ERPG = True
    SHOW_PAC = True
    SHOW_IDLH = True
    
    # Live update
    UPDATE_INTERVAL_SECONDS = 60  # Time between updates


# Note: extract_zones() is now imported from core.utils.zone_extraction
# This is the universal implementation used across all examples


def main():
    """Live ERPG/IDLH/AEGL zone visualization with weather updates."""
    print("\n" + "=" * 90)
    print(f"HEALTH IMPACT ASSESSMENT: {Config.CHEMICAL.upper()}")
    print("ERPG, IDLH, and AEGL Threat Zones")
    print("=" * 90)
    print(f"Location: {Config.LAT}°N, {Config.LON}°E")
    print(f"Release Rate: {Config.RELEASE_RATE} g/s")
    print(f"Weather Mode: {'MANUAL' if Config.USE_MANUAL_WEATHER else 'REAL-TIME'}")
    print("=" * 90 + "\n")

    # Display all available thresholds
    display_thresholds(Config.CHEMICAL)

    # Get thresholds from database
    aegl_thresh = get_aegl_thresholds(Config.CHEMICAL) if Config.SHOW_AEGL else {}
    erpg_thresh = get_erpg_thresholds(Config.CHEMICAL) if Config.SHOW_ERPG else {}
    pac_thresh = get_pac_thresholds(Config.CHEMICAL) if Config.SHOW_PAC else {}
    idlh_value = get_idlh_threshold(Config.CHEMICAL) if Config.SHOW_IDLH else None

    # Setup grid
    X, Y, _, _ = setup_computational_grid(Config.X_MAX, Config.Y_MAX, Config.NX, Config.NY)

    temp_output_file = Path(tempfile.gettempdir()) / "erpg_idlh_zones.html"
    manager = LiveLoopManager(
        update_interval=Config.UPDATE_INTERVAL_SECONDS,
        output_file=str(temp_output_file),
        app_name="ERPG/IDLH Zones"
    )

    try:
        for cycle in manager.run():
            print(f"\n{'='*90}")
            print(f"CYCLE #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*90}")
            try:
                # Weather data
                if Config.USE_MANUAL_WEATHER:
                    # Rotate wind direction for demonstration
                    wind_dir = (Config.MANUAL_WIND_DIR_DEG + (cycle - 1) * 15) % 360
                    weather = {
                        "source": "manual",
                        "wind_speed": Config.MANUAL_WIND_SPEED_MS,
                        "wind_dir": wind_dir,
                        "temperature_K": Config.MANUAL_TEMPERATURE_K,
                        "humidity": Config.MANUAL_HUMIDITY,
                        "cloud_cover": Config.MANUAL_CLOUD_COVER,
                    }
                    print(f"  Weather: Manual (wind rotating)")
                else:
                    weather = get_weather(source="open_meteo", latitude=Config.LAT, longitude=Config.LON)

                # Run dispersion model
                print("  Running dispersion model...")
                C, U, stab, _ = calculate_gaussian_dispersion(
                    weather=weather, X=X, Y=Y,
                    source_lat=Config.LAT, source_lon=Config.LON,
                    molecular_weight=Config.MW,
                    default_release_rate=Config.RELEASE_RATE,
                    default_height=Config.HEIGHT,
                    z_ref=Config.Z_REF,
                    sources=[{
                        "lat": Config.LAT, "lon": Config.LON,
                        "name": "Tank", "height": Config.HEIGHT,
                        "rate": Config.RELEASE_RATE
                    }],
                    latitude=Config.LAT, longitude=Config.LON, timezone_offset_hrs=5
                )
                max_concentration = np.nanmax(C)
                print(f"  Stability: {stab}, Max Conc: {max_concentration:.1f} ppm")
                
                # Show threshold comparison
                print(f"\n  Threshold Comparison:")
                if Config.SHOW_AEGL:
                    for name, val in aegl_thresh.items():
                        num_val = parse_threshold(val)
                        status = "✓" if num_val and num_val < max_concentration else "✗"
                        print(f"    {status} {name}: {num_val:.1f} ppm")
                if Config.SHOW_ERPG:
                    for name, val in erpg_thresh.items():
                        num_val = parse_threshold(val)
                        status = "✓" if num_val and num_val < max_concentration else "✗"
                        print(f"    {status} {name}: {num_val:.1f} ppm")
                if Config.SHOW_PAC:
                    for name, val in pac_thresh.items():
                        num_val = parse_threshold(val)
                        status = "✓" if num_val and num_val < max_concentration else "✗"
                        print(f"    {status} {name}: {num_val:.1f} ppm")
                if Config.SHOW_IDLH and idlh_value:
                    num_val = parse_threshold(idlh_value)
                    status = "✓" if num_val and num_val < max_concentration else "✗"
                    print(f"    {status} IDLH: {num_val:.1f} ppm")

                # Extract zones for each threshold type
                print(f"\n  Extracting threat zones:")
                
                all_zones = {}
                
                if Config.SHOW_AEGL:
                    print("  AEGL zones:")
                    aegl_zones = extract_zones(X, Y, C, aegl_thresh, Config.LAT, Config.LON, weather["wind_dir"])
                    for name, poly in aegl_zones.items():
                        if poly and not poly.is_empty:
                            all_zones[name] = poly
                
                if Config.SHOW_ERPG:
                    print("  ERPG zones:")
                    erpg_zones = extract_zones(X, Y, C, erpg_thresh, Config.LAT, Config.LON, weather["wind_dir"])
                    for name, poly in erpg_zones.items():
                        if poly and not poly.is_empty:
                            all_zones[name] = poly
                
                if Config.SHOW_PAC:
                    print("  PAC zones:")
                    pac_zones = extract_zones(X, Y, C, pac_thresh, Config.LAT, Config.LON, weather["wind_dir"])
                    for name, poly in pac_zones.items():
                        if poly and not poly.is_empty:
                            all_zones[name] = poly
                
                if Config.SHOW_IDLH and idlh_value:
                    print("  IDLH zone:")
                    idlh_zones = extract_zones(
                        X, Y, C,
                        {"IDLH": idlh_value},
                        Config.LAT, Config.LON, weather["wind_dir"]
                    )
                    if idlh_zones.get("IDLH") and not idlh_zones["IDLH"].is_empty:
                        all_zones["IDLH"] = idlh_zones["IDLH"]

                if not all_zones:
                    print("  ⚠ No zones extracted - concentrations may be too low or thresholds too high")
                    print(f"    Try increasing RELEASE_RATE or decreasing thresholds\n")

                # Create map
                print("  Creating visualization...")
                m = folium.Map(location=[Config.LAT, Config.LON], zoom_start=13, tiles='OpenStreetMap')
                
                folium.TileLayer(
                    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                    attr='Esri', name='Satellite', overlay=False, control=True
                ).add_to(m)

                # Source marker
                folium.Marker(
                    [Config.LAT, Config.LON],
                    tooltip=f"{Config.CHEMICAL} Release Source",
                    icon=folium.Icon(color="red", icon="warning-sign")
                ).add_to(m)

                # Add zones to map (centralized rendering)
                add_zone_polygons(
                    m,
                    all_zones,
                    thresholds_context={
                        "AEGL": aegl_thresh if Config.SHOW_AEGL else {},
                        "ERPG": erpg_thresh if Config.SHOW_ERPG else {},
                        "PAC": pac_thresh if Config.SHOW_PAC else {},
                        "IDLH": {"IDLH": idlh_value} if Config.SHOW_IDLH else {},
                    },
                    name_prefix=None,
                )
                # Auto-zoom to fit all zones
                fit_map_to_polygons(m, all_zones.values())

                # Info panel
                threshold_rows = ""
                
                if Config.SHOW_AEGL:
                    threshold_rows += "<tr><td colspan='2' style='background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; font-weight:bold; padding:6px; font-size:10px;'>📊 AEGL (60 min)</td></tr>"
                    for level in ["AEGL-1", "AEGL-2", "AEGL-3"]:
                        val = aegl_thresh.get(level)
                        num_val = parse_threshold(val)
                        status = "<span style='color:#00C851;'>✓</span>" if level in all_zones else "<span style='color:#ccc;'>—</span>"
                        color_map = {"AEGL-1": "#FFFF00", "AEGL-2": "#FFA500", "AEGL-3": "#FF0000"}
                        num_val_str = f"{num_val:.1f}" if num_val is not None else 'N/A'
                        threshold_rows += f"<tr><td style='padding:5px;'>{status} <span style='color:{color_map[level]};'>●</span> {level}</td><td style='padding:5px; text-align:right; font-weight:bold;'>{num_val_str} ppm</td></tr>"
                
                if Config.SHOW_ERPG:
                    threshold_rows += "<tr><td colspan='2' style='background:linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color:white; font-weight:bold; padding:6px; font-size:10px; border-top:2px solid #ddd;'>🛡️ ERPG (1 hour)</td></tr>"
                    for level in ["ERPG-1", "ERPG-2", "ERPG-3"]:
                        val = erpg_thresh.get(level)
                        num_val = parse_threshold(val)
                        status = "<span style='color:#00C851;'>✓</span>" if level in all_zones else "<span style='color:#ccc;'>—</span>"
                        color_map = {"ERPG-1": "#00FF00", "ERPG-2": "#FF00FF", "ERPG-3": "#8B0000"}
                        num_val_str = f"{num_val:.1f}" if num_val is not None else 'N/A'
                        threshold_rows += f"<tr><td style='padding:5px;'>{status} <span style='color:{color_map[level]};'>- -</span> {level}</td><td style='padding:5px; text-align:right; font-weight:bold;'>{num_val_str} ppm</td></tr>"
                
                if Config.SHOW_PAC:
                    threshold_rows += "<tr><td colspan='2' style='background:linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color:white; font-weight:bold; padding:6px; font-size:10px; border-top:2px solid #ddd;'>💊 PAC (Protective Action Criteria)</td></tr>"
                    for level in ["PAC-1", "PAC-2", "PAC-3"]:
                        val = pac_thresh.get(level)
                        num_val = parse_threshold(val)
                        status = "<span style='color:#00C851;'>✓</span>" if level in all_zones else "<span style='color:#ccc;'>—</span>"
                        color_map = {"PAC-1": "#1E90FF", "PAC-2": "#DC143C", "PAC-3": "#800080"}
                        num_val_str = f"{num_val:.1f}" if num_val is not None else 'N/A'
                        threshold_rows += f"<tr><td style='padding:5px;'>{status} <span style='color:{color_map[level]};'>•-</span> {level}</td><td style='padding:5px; text-align:right; font-weight:bold;'>{num_val_str} ppm</td></tr>"
                
                if Config.SHOW_IDLH:
                    threshold_rows += "<tr><td colspan='2' style='background:linear-gradient(135deg, #FFB84D 0%, #FF6B6B 100%); color:white; font-weight:bold; padding:6px; font-size:10px; border-top:2px solid #ddd;'>⚠️ IDLH (30 min escape)</td></tr>"
                    status = "<span style='color:#00C851;'>✓</span>" if "IDLH" in all_zones else "<span style='color:#ccc;'>—</span>"
                    num_val = parse_threshold(idlh_value)
                    num_val_str = f"{num_val:.1f}" if num_val is not None else 'N/A'
                    threshold_rows += f"<tr><td style='padding:5px;'>{status} <span style='color:#0000FF;'>· ·</span> IDLH</td><td style='padding:5px; text-align:right; font-weight:bold;'>{num_val_str} ppm</td></tr>"

                # Info panel (centralized)
                add_health_thresholds_panel(
                    m,
                    chemical=Config.CHEMICAL,
                    weather=weather,
                    release_rate_gps=Config.RELEASE_RATE,
                    max_concentration_ppm=max_concentration,
                    cycle=cycle,
                    aegl=aegl_thresh if Config.SHOW_AEGL else None,
                    erpg=erpg_thresh if Config.SHOW_ERPG else None,
                    pac=pac_thresh if Config.SHOW_PAC else None,
                    idlh_value=idlh_value if Config.SHOW_IDLH else None,
                    zones_present=list(all_zones.keys()),
                    position="bottomleft",
                )

                # Layer control (centralized ensure)
                ensure_layer_control(m)

                # Save map
                m.save(str(temp_output_file))
                print(f"  ✓ Map saved: {temp_output_file}")

                # Open browser on first cycle
                manager.open_browser_once()

                print(f"\n  Zones displayed: {', '.join(all_zones.keys()) if all_zones else 'None'}")
                
                # Wait for next cycle
                manager.wait_for_next_cycle()
        
            except Exception as e:
                manager.handle_error(e)
                continue

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
