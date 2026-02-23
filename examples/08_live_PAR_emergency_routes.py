"""
Live Population at Risk (PAR) + Emergency Routes Layer
======================================================

This is an extended example of:
07_live_PAR_analysis.py

New Feature Added:
✅ Emergency Routes Layer
- Shows SAFE roads outside threat zones
- Removes roads intersecting AEGL zones
- Highlights available escape roads

Layer Name in Folium:
✅ "Emergency Routes"

To Run:
    python 08_live_PAR_with_emergency_routes.py

Dependencies:
    pip install geopandas folium scikit-image branca requests numpy osmnx networkx
"""

# ============================================================================
# IMPORTS
# ============================================================================

import sys
import os
import tempfile
import webbrowser
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import warnings

import numpy as np
import geopandas as gpd
import folium
from shapely.geometry import Point, Polygon, LineString
from skimage import measure

import osmnx as ox
import networkx as nx

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# pyELDQM imports
from core.dispersion_models.gaussian_model import calculate_gaussian_dispersion
from core.meteorology.realtime_weather import get_weather
from core.geography import get_complete_geographic_info
from core.visualization.folium_maps import create_live_threat_map
from core.utils.features import setup_computational_grid
from core.utils.zone_extraction import extract_zones
from core.utils import LiveLoopManager
from core.visualization import add_par_info_panel, ensure_layer_control
from core.population import calculate_population_in_zone

warnings.filterwarnings("ignore")


# ============================================================================
# SCENARIO CONFIGURATION
# ============================================================================

class ScenarioConfig:
    TANK_LATITUDE = 31.691100
    TANK_LONGITUDE = 74.082167
    LOCATION_NAME = "Ammonia Tank - FFC Industrial Area"
    TIMEZONE_OFFSET_HRS = 12  # Pakistan Standard Time (UTC+5)

    CHEMICAL_NAME = "Ammonia (NH3)"
    MOLECULAR_WEIGHT = 17.03  # g/mol

    RELEASE_RATE = 800.0  # g/s
    TANK_HEIGHT = 3.0
    Z_REF = 3.0

    X_MAX = 5000
    Y_MAX = 5000
    NX = 1000
    NY = 1000

    AEGL_THRESHOLDS = {
        "AEGL-1": 30,
        "AEGL-2": 160,
        "AEGL-3": 1100,
    }

    BASE_POPULATION_DENSITY = 600
    UPDATE_INTERVAL_SECONDS = 60

    # Emergency Routes Settings
    ROUTE_SEARCH_RADIUS_METERS = 3500   # how far to load road network
    SHOW_SAFE_ROADS_ONLY = True         # if False → show all roads + unsafe marked

    # Manual Weather Override
    USE_MANUAL_WEATHER = False
    MANUAL_WIND_DIR_DEG = 70
    MANUAL_WIND_SPEED_MS = 1.0
    MANUAL_TEMPERATURE_K = 298.15
    MANUAL_HUMIDITY = 0.60
    MANUAL_CLOUD_COVER = 0.20


# ============================================================================
# THREAT ZONES EXTRACTION
# ============================================================================
# extract_threat_zones_from_concentration() is now imported from core.utils.zone_extraction


# ============================================================================
# POPULATION CALCULATION (UNCHANGED, SHORTENED)
# ============================================================================



# ============================================================================
# LIVE PAR ANALYZER
# ============================================================================

class LivePARAnalyzer:
    def __init__(self):
        self.cycle_count = 0
        self.last_update_time = None
        self.par_history = []
        self.X, self.Y, _, _ = setup_computational_grid(
            ScenarioConfig.X_MAX, ScenarioConfig.Y_MAX, ScenarioConfig.NX, ScenarioConfig.NY
        )

    def calculate_par_cycle(self, threat_zones: Dict[str, Polygon]) -> Dict[str, Dict]:
        self.cycle_count += 1
        self.last_update_time = datetime.now()

        results = {}
        for zone_name, zone_poly in threat_zones.items():
            if zone_poly is None:
                results[zone_name] = {
                    "par": 0,
                    "population_points": [],
                    "geometry": None,
                }
                continue

            par, pts = calculate_population_in_zone(
                zone_poly=zone_poly,
                base_density=ScenarioConfig.BASE_POPULATION_DENSITY
            )

            results[zone_name] = {
                "par": par,
                "population_points": pts,
                "geometry": zone_poly
            }

        return results


# ============================================================================
# 🚨 EMERGENCY ROUTES LAYER (NEW)
# ============================================================================

def build_emergency_routes_layer(
    base_map: folium.Map,
    leak_lat: float,
    leak_lon: float,
    threat_zones: Dict[str, Polygon],
    radius_m: float = 3500,
    show_safe_only: bool = True
) -> folium.FeatureGroup:
    """
    Emergency Routes layer:
    - downloads nearby road network from OpenStreetMap
    - removes segments intersecting threat zones
    - shows safe roads as highlighted polylines
    """

    emergency_fg = folium.FeatureGroup(name="Emergency Routes", show=True)

    # Merge all threat polygons into one "unsafe region"
    unsafe_polys = [p for p in threat_zones.values() if p is not None and not p.is_empty]
    if len(unsafe_polys) == 0:
        folium.Marker(
            [leak_lat, leak_lon],
            popup="No threat zones detected. All roads assumed safe.",
            icon=folium.Icon(color="green", icon="ok-sign")
        ).add_to(emergency_fg)
        emergency_fg.add_to(base_map)
        return emergency_fg

    unsafe_union = unsafe_polys[0]
    for p in unsafe_polys[1:]:
        unsafe_union = unsafe_union.union(p)

    print("  [Emergency Routes] Downloading roads from OpenStreetMap...")

    # Download road network
    G = ox.graph_from_point(
        (leak_lat, leak_lon),
        dist=radius_m,
        network_type="drive"
    )

    # Convert edges to GeoDataFrame
    edges_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True, fill_edge_geometry=True)

    safe_edges = []
    unsafe_edges = []

    for _, row in edges_gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue

        # classify road as unsafe if it intersects threat zone
        if geom.intersects(unsafe_union):
            unsafe_edges.append(geom)
        else:
            safe_edges.append(geom)

    print(f"  [Emergency Routes] Total road segments: {len(edges_gdf)}")
    print(f"  [Emergency Routes] SAFE road segments: {len(safe_edges)}")
    print(f"  [Emergency Routes] UNSAFE road segments: {len(unsafe_edges)}")

    # Plot safe roads
    for geom in safe_edges:
        if isinstance(geom, LineString):
            coords = [(lat, lon) for lon, lat in geom.coords]
            folium.PolyLine(
                coords,
                weight=4,
                opacity=0.9,
                tooltip="Safe Road"
            ).add_to(emergency_fg)

    # Optionally plot unsafe roads (dimmed)
    if not show_safe_only:
        for geom in unsafe_edges:
            if isinstance(geom, LineString):
                coords = [(lat, lon) for lon, lat in geom.coords]
                folium.PolyLine(
                    coords,
                    weight=3,
                    opacity=0.3,
                    tooltip="Unsafe Road (Inside Threat Zone)"
                ).add_to(emergency_fg)

    # Put marker for leak
    folium.Marker(
        [leak_lat, leak_lon],
        popup="Leak Source (Ammonia Tank)",
        icon=folium.Icon(color="red", icon="warning-sign")
    ).add_to(emergency_fg)

    emergency_fg.add_to(base_map)
    return emergency_fg


# ============================================================================
# MAP AUGMENTATION
# ============================================================================

def augment_map_with_par_and_routes(
    base_map: folium.Map,
    analyzer: LivePARAnalyzer,
    par_results: Dict[str, Dict],
    threat_zones: Dict[str, Polygon],
    weather: Dict
) -> folium.Map:
    """
    Adds:
    ✅ PAR Map layer
    ✅ Emergency Routes layer
    ✅ Summary panel
    ✅ LayerControl
    """

    # ---------------- PAR MAP ----------------
    par_fg = folium.FeatureGroup(name="PAR Map", show=True)

    for zone_name, zone_data in par_results.items():
        color = {"AEGL-1": "#FFFF00", "AEGL-2": "#FFA500", "AEGL-3": "#FF0000"}.get(zone_name, "#999999")

        for pt in zone_data["population_points"]:
            folium.CircleMarker(
                location=[pt["latitude"], pt["longitude"]],
                radius=4,
                color=color,
                fill=True,
                fillOpacity=0.8,
                tooltip=f"{pt['population']} people - {zone_name}"
            ).add_to(par_fg)

    par_fg.add_to(base_map)

    # ---------------- EMERGENCY ROUTES (NEW) ----------------
    build_emergency_routes_layer(
        base_map=base_map,
        leak_lat=ScenarioConfig.TANK_LATITUDE,
        leak_lon=ScenarioConfig.TANK_LONGITUDE,
        threat_zones=threat_zones,
        radius_m=ScenarioConfig.ROUTE_SEARCH_RADIUS_METERS,
        show_safe_only=ScenarioConfig.SHOW_SAFE_ROADS_ONLY
    )

    # ---------------- PAR SUMMARY PANEL (centralized) ----------------
    add_par_info_panel(
        base_map,
        par_results,
        analyzer=analyzer,
        weather=weather,
        theme="live",
        position="bottomleft",
    )

    # ---------------- LAYER CONTROL (centralized) ----------------
    ensure_layer_control(base_map)

    return base_map


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def initialize_system():
    print(f"\n{'='*90}")
    print("LIVE PAR + EMERGENCY ROUTES MONITORING")
    print(f"{'='*90}")
    print(f"Location: {ScenarioConfig.LOCATION_NAME}")
    print(f"Coordinates: {ScenarioConfig.TANK_LATITUDE}°N, {ScenarioConfig.TANK_LONGITUDE}°E")
    print(f"Chemical: {ScenarioConfig.CHEMICAL_NAME}")
    print(f"Update Interval: {ScenarioConfig.UPDATE_INTERVAL_SECONDS} s")
    print(f"Emergency Route Radius: {ScenarioConfig.ROUTE_SEARCH_RADIUS_METERS} m")
    print(f"{'='*90}\n")


def run_live_monitoring():
    initialize_system()

    analyzer = LivePARAnalyzer()

    _ = get_complete_geographic_info(
        latitude=ScenarioConfig.TANK_LATITUDE,
        longitude=ScenarioConfig.TANK_LONGITUDE,
        fetch_online=False
    )

    temp_output_file = Path(tempfile.gettempdir()) / "live_par_with_routes.html"

    # Create live loop manager
    manager = LiveLoopManager(
        update_interval=ScenarioConfig.UPDATE_INTERVAL_SECONDS,
        output_file=temp_output_file,
        app_name="pyELDQM PAR Emergency Routes"
    )

    for cycle in manager.run():
        try:
            # Step 1: Weather
            if ScenarioConfig.USE_MANUAL_WEATHER:
                weather = {
                    "source": "manual",
                    "wind_speed": ScenarioConfig.MANUAL_WIND_SPEED_MS,
                    "wind_dir": ScenarioConfig.MANUAL_WIND_DIR_DEG,
                    "temperature_K": ScenarioConfig.MANUAL_TEMPERATURE_K,
                    "humidity": ScenarioConfig.MANUAL_HUMIDITY,
                    "cloud_cover": ScenarioConfig.MANUAL_CLOUD_COVER,
                }
            else:
                weather = get_weather(
                    latitude=ScenarioConfig.TANK_LATITUDE,
                    longitude=ScenarioConfig.TANK_LONGITUDE,
                    source="open_meteo"
                )

            # Step 2: Dispersion model
            concentration, U_local, stability_class, resolved_sources = calculate_gaussian_dispersion(
                weather=weather,
                X=analyzer.X,
                Y=analyzer.Y,
                source_lat=ScenarioConfig.TANK_LATITUDE,
                source_lon=ScenarioConfig.TANK_LONGITUDE,
                molecular_weight=ScenarioConfig.MOLECULAR_WEIGHT,
                default_release_rate=ScenarioConfig.RELEASE_RATE,
                default_height=ScenarioConfig.TANK_HEIGHT,
                z_ref=ScenarioConfig.Z_REF,
                sources=[{
                    "lat": ScenarioConfig.TANK_LATITUDE,
                    "lon": ScenarioConfig.TANK_LONGITUDE,
                    "name": "Primary Tank",
                    "height": ScenarioConfig.TANK_HEIGHT,
                    "rate": ScenarioConfig.RELEASE_RATE,
                    "color": "red"
                }],
                latitude=ScenarioConfig.TANK_LATITUDE,
                longitude=ScenarioConfig.TANK_LONGITUDE,
                timezone_offset_hrs=ScenarioConfig.TIMEZONE_OFFSET_HRS
            )

            # Step 3: Threat zones
            threat_zones = extract_zones(
                analyzer.X, analyzer.Y,
                concentration,
                ScenarioConfig.AEGL_THRESHOLDS,
                ScenarioConfig.TANK_LATITUDE,
                ScenarioConfig.TANK_LONGITUDE,
                wind_dir=weather["wind_dir"]
            )

            # Step 4: PAR
            par_results = analyzer.calculate_par_cycle(threat_zones)

            # Step 5: Base map
            base_map = create_live_threat_map(
                weather=weather,
                X=analyzer.X,
                Y=analyzer.Y,
                concentration=concentration,
                U_local=U_local,
                stability_class=stability_class,
                source_lat=ScenarioConfig.TANK_LATITUDE,
                source_lon=ScenarioConfig.TANK_LONGITUDE,
                chemical_name=ScenarioConfig.CHEMICAL_NAME,
                tank_height=ScenarioConfig.TANK_HEIGHT,
                release_rate=ScenarioConfig.RELEASE_RATE,
                aegl_thresholds=ScenarioConfig.AEGL_THRESHOLDS,
                update_interval_seconds=ScenarioConfig.UPDATE_INTERVAL_SECONDS,
                sources=resolved_sources,
                markers=[]
            )

            final_map = augment_map_with_par_and_routes(
                base_map=base_map,
                analyzer=analyzer,
                par_results=par_results,
                threat_zones=threat_zones,
                weather=weather
            )

            final_map.save(str(temp_output_file))
            print(f"  ✓ Map updated: {temp_output_file}")

            manager.open_browser_once()
            manager.wait_for_next_cycle()

        except Exception as e:
            manager.handle_error(e)
            continue


def main():
    run_live_monitoring()


if __name__ == "__main__":
    main()
