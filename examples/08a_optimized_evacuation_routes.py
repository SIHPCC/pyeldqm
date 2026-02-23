"""
10_optimized_evacuation_routes.py
=================================

LIVE Optimized evacuation routing with weather-driven updates.

Features:
- Real-time threat zone updates as weather changes
- Display all safe roads (green), unsafe roads (red/dim)
- Highlight optimized evacuation route (bright blue)
- Rank multiple shelters by safest route
- Live update loop similar to 08_live_PAR_emergency_routes.py

Run:
    python 10_optimized_evacuation_routes.py

Optional deps:
    pip install osmnx networkx
"""
import os
import sys
import time
import tempfile
import webbrowser
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

import numpy as np
import folium
from shapely.geometry import Polygon, LineString
from skimage import measure

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Imports from pyELDQM
from core.utils import LiveLoopManager
from core.utils.features import setup_computational_grid
from core.utils.zone_extraction import extract_zones
from core.dispersion_models.gaussian_model import calculate_gaussian_dispersion
from core.meteorology.realtime_weather import get_weather
from core.evacuation import (
    build_road_graph,
    classify_edges_with_risk,
    shortest_safe_route,
    rank_shelters
)
from core.visualization import (
    add_evacuation_info_panel,
    ensure_layer_control,
    add_zone_polygons,
    fit_map_to_polygons,
)


class Scenario:
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
    
    # Weather (can be manual or fetched live)
    USE_MANUAL_WEATHER = False
    MANUAL_WIND_SPEED_MS = 1
    MANUAL_WIND_DIR_DEG = 270  # Changes every cycle for demo
    MANUAL_TEMPERATURE_K = 298.15
    MANUAL_HUMIDITY = 0.55
    MANUAL_CLOUD_COVER = 0.2
    
    # Routing
    ROUTE_RADIUS_M = 4000
    PROXIMITY_BUFFER_M = 150
    
    # Shelters (multiple candidate destinations)
    SHELTERS = [
        (LAT + 0.02, LON - 0.02, "North-West"),
        (LAT + 0.03, LON + 0.00, "North"),
        (LAT - 0.02, LON + 0.03, "East-South"),
    ]
    
    # Live update
    UPDATE_INTERVAL_SECONDS = 15
    SHOW_ALL_ROUTES = True  # Show safe + unsafe roads


# extract_zones() is now imported from core.utils.zone_extraction


def render_roads_and_routes(
    m: folium.Map,
    G,
    safe_gdf,
    unsafe_gdf,
    optimized_path: Optional[List[int]],
    show_all: bool = True
):
    """Render all roads and highlight optimized route."""
    # Safe roads (green)
    safe_fg = folium.FeatureGroup(name="Safe Roads", show=True)
    for _, row in safe_gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        if isinstance(geom, LineString):
            coords = [(lat, lon) for lon, lat in geom.coords]
            folium.PolyLine(
                coords,
                color="#00FC0D",
                weight=5,
                opacity=1,
                tooltip="Safe Road"
            ).add_to(safe_fg)
    safe_fg.add_to(m)

    # Unsafe roads (red, dimmed) - optional
    if show_all and len(unsafe_gdf) > 0:
        unsafe_fg = folium.FeatureGroup(name="Unsafe Roads", show=True)
        for _, row in unsafe_gdf.iterrows():
            geom = row.geometry
            if geom is None:
                continue
            if isinstance(geom, LineString):
                coords = [(lat, lon) for lon, lat in geom.coords]
                folium.PolyLine(
                    coords,
                    color="#FF0000",
                    weight=5,
                    opacity=0.25,
                    tooltip="Unsafe Road (Inside Threat Zone)"
                ).add_to(unsafe_fg)
        unsafe_fg.add_to(m)

    # Optimized route (bright blue)
    if optimized_path:
        opt_fg = folium.FeatureGroup(name="Optimized Route", show=True)
        coords = []
        for n in optimized_path:
            data = G.nodes[n]
            coords.append((data["y"], data["x"]))
        folium.PolyLine(
            coords,
            color="#0066FF",
            weight=5,
            opacity=1.0,
            tooltip="Optimized Evacuation Route"
        ).add_to(opt_fg)
        opt_fg.add_to(m)


def main():
    """Live optimization loop with weather-driven updates."""
    print("\n" + "=" * 90)
    print("LIVE OPTIMIZED EVACUATION ROUTE MONITORING")
    print("=" * 90)
    print(f"Location: {Scenario.LAT}°N, {Scenario.LON}°E")
    print(f"Chemical: {Scenario.CHEM}")
    print(f"Release: {Scenario.RELEASE_RATE} g/s")
    print(f"Update Interval: {Scenario.UPDATE_INTERVAL_SECONDS}s")
    print("=" * 90 + "\n")

    # Setup grid once
    X, Y, _, _ = setup_computational_grid(Scenario.X_MAX, Scenario.Y_MAX, Scenario.NX, Scenario.NY)

    temp_output_file = Path(tempfile.gettempdir()) / "optimized_evacuation_routes_live.html"
    G = None  # Graph cached after first build
    manager = LiveLoopManager(
        update_interval=Scenario.UPDATE_INTERVAL_SECONDS,
        output_file=str(temp_output_file),
        app_name="Optimized Evacuation Routes"
    )

    try:
        for cycle in manager.run():
            print(f"\n{'='*90}")
            print(f"UPDATE CYCLE #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*90}")
            try:
                # Weather (rotate for demo)
                if Scenario.USE_MANUAL_WEATHER:
                    wind_dir = (Scenario.MANUAL_WIND_DIR_DEG + (cycle - 1) * 15) % 360
                    weather = {
                        "source": "manual",
                        "wind_speed": Scenario.MANUAL_WIND_SPEED_MS,
                        "wind_dir": wind_dir,
                        "temperature_K": Scenario.MANUAL_TEMPERATURE_K,
                        "humidity": Scenario.MANUAL_HUMIDITY,
                        "cloud_cover": Scenario.MANUAL_CLOUD_COVER,
                    }
                else:
                    weather = get_weather(
                        latitude=Scenario.LAT,
                        longitude=Scenario.LON,
                        source="open_meteo"
                    )

                print(f"  Wind: {weather['wind_speed']:.1f} m/s @ {weather['wind_dir']:.0f}°")

            # Dispersion
                # Dispersion
                C, U, stab, _ = calculate_gaussian_dispersion(
                    weather=weather, X=X, Y=Y,
                    source_lat=Scenario.LAT, source_lon=Scenario.LON,
                    molecular_weight=Scenario.MW,
                    default_release_rate=Scenario.RELEASE_RATE,
                    default_height=Scenario.HEIGHT,
                    z_ref=Scenario.Z_REF,
                    sources=[{"lat": Scenario.LAT, "lon": Scenario.LON, "name": "Tank", "height": Scenario.HEIGHT, "rate": Scenario.RELEASE_RATE, "color": "red"}],
                    latitude=Scenario.LAT, longitude=Scenario.LON, timezone_offset_hrs=12
                )
                print(f"  Stability: {stab}, Max Conc: {np.nanmax(C):.1f} ppm")

                # Extract threat zones
                zones = extract_zones(X, Y, C, Scenario.AEGL, Scenario.LAT, Scenario.LON, weather["wind_dir"])
                for z_name, z_poly in zones.items():
                    if z_poly and not z_poly.is_empty:
                        print(f"  {z_name}: detected")

                # Build map
                m = folium.Map(location=[Scenario.LAT, Scenario.LON], zoom_start=13, tiles='OpenStreetMap')

                folium.TileLayer(
                    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                    attr='Esri',
                    name='Satellite',
                    overlay=False,
                    control=True
                ).add_to(m)

                # Source marker
                folium.Marker(
                    [Scenario.LAT, Scenario.LON],
                    tooltip="Leak Source (Ammonia Tank)",
                    icon=folium.Icon(color="red", icon="warning-sign")
                ).add_to(m)

                # AEGL zones (centralized rendering)
                add_zone_polygons(
                    m,
                    {k: v for k, v in zones.items() if k in ["AEGL-1", "AEGL-2", "AEGL-3"]},
                    thresholds_context={"AEGL": Scenario.AEGL},
                    name_prefix=None,
                )

                # Auto-zoom to fit all threat zones
                fit_map_to_polygons(m, zones.values())

                # Build graph once, reuse
                optimized_path = None
                ranking = []
                try:
                    if G is None:
                        print("  Building road network...")
                        G = build_road_graph(Scenario.LAT, Scenario.LON, Scenario.ROUTE_RADIUS_M)
                        print(f"  ✓ Graph built with {len(G.nodes())} nodes")

                    # Classify edges with current zones
                    safe_gdf, unsafe_gdf = classify_edges_with_risk(G, zones, proximity_buffer_m=Scenario.PROXIMITY_BUFFER_M)
                    print(f"  ✓ Roads classified: {len(safe_gdf)} safe, {len(unsafe_gdf)} unsafe")

                    # Rank shelters
                    shelter_list = [(lat, lon) for lat, lon, _ in Scenario.SHELTERS]
                    ranking = rank_shelters(G, (Scenario.LAT, Scenario.LON), shelter_list)

                    # Get best route
                    best = next((r for r in ranking if "path" in r), None)
                    if best:
                        optimized_path = best["path"]
                        best_shelter_name = Scenario.SHELTERS[shelter_list.index((best["lat"], best["lon"]))][2]
                        print(f"  ✓ Best shelter: {best_shelter_name} (cost: {best['cost']:.0f})")

                    # Display all shelters
                    for idx, (lat, lon, name) in enumerate(Scenario.SHELTERS):
                        is_best = best and best["lat"] == lat and best["lon"] == lon
                        color = "green" if is_best else "blue"
                        icon_str = "home" if is_best else "map-marker"
                        tooltip_text = f"🏆 RECOMMENDED: {name}" if is_best else f"{name}"
                        
                        folium.Marker(
                            [lat, lon],
                            tooltip=tooltip_text,
                            icon=folium.Icon(color=color, icon=icon_str)
                        ).add_to(m)

                    # Render all roads and optimized route
                    render_roads_and_routes(m, G, safe_gdf, unsafe_gdf, optimized_path, show_all=Scenario.SHOW_ALL_ROUTES)

                except Exception as rte:
                    print(f"  ✗ Routing error: {rte}")

                # Info panel (centralized)
                add_evacuation_info_panel(
                    m,
                    weather=weather,
                    stability=stab,
                    shelter_ranking=ranking,
                    shelters_catalog=Scenario.SHELTERS,
                    position="bottomleft",
                )

                # Layer control (centralized ensure)
                ensure_layer_control(m)

                # Save
                m.save(str(temp_output_file))
                print(f"  ✓ Map saved: {temp_output_file}")

                manager.open_browser_once()

                print(f"Routes displayed: Safe routes visualized")
                
                # Wait for next cycle
                manager.wait_for_next_cycle()
        
            except Exception as e:
                manager.handle_error(e)
                continue

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()