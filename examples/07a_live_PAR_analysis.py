"""
07_live_PAR_worldpop.py
=======================

Live Population at Risk (PAR) Analysis using REAL Population Raster (WorldPop / GHSL)

This script integrates:
✅ Real-time dispersion simulation (Gaussian model)
✅ Threat zone extraction (AEGL contours)
✅ Real-world PAR computation using population raster clipping + summation
✅ Interactive Folium map with:
   - Threat zones
   - PAR population overlay
   - Live summary panel

Author: pyELDQM Development Team
Date: 2026
"""

# ============================================================================
# IMPORTS
# ============================================================================

import os
import sys
import time
import tempfile
import webbrowser
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import warnings

import numpy as np
import geopandas as gpd
import folium
from shapely.geometry import Polygon, mapping
from skimage import measure

import rasterio
from rasterio.mask import mask

warnings.filterwarnings("ignore")

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
from core.visualization import add_threat_zones_and_par_panel, ensure_layer_control
from core.utils.features import setup_computational_grid
from core.utils.zone_extraction import extract_zones
from core.utils import LiveLoopManager


# ============================================================================
# SCENARIO CONFIGURATION
# ============================================================================

class ScenarioConfig:
    # Location Information
    TANK_LATITUDE = 31.691100
    TANK_LONGITUDE = 74.082167
    LOCATION_NAME = "Ammonia Tank - FFC Industrial Area"
    TIMEZONE_OFFSET_HRS = 12  # Pakistan Standard Time (UTC+5)

    # Chemical Properties
    CHEMICAL_NAME = "Ammonia (NH3)"
    MOLECULAR_WEIGHT = 17.03  # g/mol

    # Release Parameters
    RELEASE_RATE = 800.0  # g/s
    TANK_HEIGHT = 3.0     # meters
    Z_REF = 3.0           # meters

    # Computational Grid
    X_MAX = 5000
    Y_MAX = 5000
    NX = 1000
    NY = 1000

    # AEGL Thresholds (ppm)
    AEGL_THRESHOLDS = {
        "AEGL-1": 30,
        "AEGL-2": 160,
        "AEGL-3": 1100,
    }

    # Update interval
    UPDATE_INTERVAL_SECONDS = 60

    # ✅ REAL POPULATION RASTER
    # Provide a local WorldPop/GHSL population count raster path
    # Example: r"D:\GIS\WorldPop\pak_ppp_2020_100m.tif"
    POP_RASTER_PATH = r"D:\OneDrive - UET\After PhD\Research\pyELDQM\pyELDQM\data\population\data\population\pak_pop_2026_CN_100m_R2025A_v1.tif"
    # POP_RASTER_PATH = r"D:\OneDrive - UET\After PhD\Research\pyELDQM\pyELDQM\data\population\data\population\pak_pop_2026_CN_1km_R2025A_UA_v1.tif"

    # Manual Weather Override
    USE_MANUAL_WEATHER = False
    MANUAL_WIND_DIR_DEG = 270
    MANUAL_WIND_SPEED_MS = 1.5
    MANUAL_TEMPERATURE_K = 298.15
    MANUAL_HUMIDITY = 0.60
    MANUAL_CLOUD_COVER = 0.20


# ============================================================================
# THREAT ZONE EXTRACTION
# ============================================================================

# extract_threat_zones_from_concentration now imported from core.utils.zone_extraction

# ============================================================================
# ✅ REAL POPULATION PAR (WorldPop/GHSL Raster Clipping)
# ============================================================================

class PopulationRasterPAR:
    """
    Professional PAR calculator using real-world population raster:
    PAR(zone) = sum(population pixels within polygon)
    """

    def __init__(self, raster_path: str):
        if not os.path.exists(raster_path):
            raise FileNotFoundError(
                f"Population raster not found:\n{raster_path}\n\n"
                f"Please set ScenarioConfig.POP_RASTER_PATH correctly."
            )

        self.raster_path = raster_path
        self.dataset = rasterio.open(raster_path)

        # useful metadata
        self.crs = self.dataset.crs
        self.nodata = self.dataset.nodata

        print("\n[PopulationRasterPAR] Loaded population raster:")
        print(f"  Path : {self.raster_path}")
        print(f"  CRS  : {self.crs}")
        print(f"  NoData: {self.nodata}")

    def polygon_to_raster_crs(self, poly_wgs84: Polygon) -> Polygon:
        """
        Convert polygon from EPSG:4326 to raster CRS.
        """
        gdf = gpd.GeoDataFrame(geometry=[poly_wgs84], crs="EPSG:4326")
        gdf_proj = gdf.to_crs(self.crs)
        return gdf_proj.geometry.iloc[0]

    def par_from_polygon(self, poly_wgs84: Optional[Polygon]) -> int:
        """
        Compute PAR by clipping population raster within polygon and summing.
        """
        if poly_wgs84 is None or poly_wgs84.is_empty:
            return 0

        try:
            poly_proj = self.polygon_to_raster_crs(poly_wgs84)

            out_image, _ = mask(
                self.dataset,
                [mapping(poly_proj)],
                crop=True,
                all_touched=True  # safer for narrow threat zones
            )

            pop = out_image[0].astype(np.float64)

            if self.nodata is not None:
                pop[pop == self.nodata] = np.nan

            pop = np.nan_to_num(pop, nan=0.0)

            # Most WorldPop rasters are population count per pixel → sum directly
            total = int(np.sum(pop))

            return max(total, 0)

        except Exception:
            return 0


# ============================================================================
# LIVE PAR ANALYZER (WorldPop)
# ============================================================================

class LivePARAnalyzerWorldPop:
    def __init__(self):
        self.cycle_count = 0
        self.last_update_time = None

        self.X, self.Y, _, _ = setup_computational_grid(
            ScenarioConfig.X_MAX,
            ScenarioConfig.Y_MAX,
            ScenarioConfig.NX,
            ScenarioConfig.NY
        )

        self.population_engine = PopulationRasterPAR(ScenarioConfig.POP_RASTER_PATH)

    def calculate_par(self, threat_zones: Dict[str, Optional[Polygon]]) -> Dict[str, Dict]:
        self.cycle_count += 1
        self.last_update_time = datetime.now()

        results = {}
        total_par = 0

        print(f"\n[{self.last_update_time.strftime('%H:%M:%S')}] Real PAR (Raster-based) Calculation:")

        for zone_name in ["AEGL-3", "AEGL-2", "AEGL-1"]:
            poly = threat_zones.get(zone_name)

            par = self.population_engine.par_from_polygon(poly)
            total_par += par

            results[zone_name] = {
                "par": par,
                "geometry": poly
            }

            status = "CRITICAL" if par > 10000 else ("HIGH" if par > 5000 else "OK")
            print(f"  {zone_name:8s}: {par:>10,} people [{status}]")

        results["TOTAL"] = {"par": total_par, "geometry": None}
        print(f"  TOTAL   : {total_par:>10,} people")

        return results


# ============================================================================
# MAP AUGMENTATION
# ============================================================================

        


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def initialize_system():
    print("\n" + "=" * 90)
    print("pyELDQM: LIVE REAL-WORLD PAR (WorldPop/GHSL Raster)")
    print("=" * 90)
    print(f"Location: {ScenarioConfig.LOCATION_NAME}")
    print(f"Tank: {ScenarioConfig.TANK_LATITUDE}°N, {ScenarioConfig.TANK_LONGITUDE}°E")
    print(f"Chemical: {ScenarioConfig.CHEMICAL_NAME}")
    print(f"Release Rate: {ScenarioConfig.RELEASE_RATE} g/s")
    print(f"Update Interval: {ScenarioConfig.UPDATE_INTERVAL_SECONDS} seconds")
    print(f"Population Raster: {ScenarioConfig.POP_RASTER_PATH}")
    print("=" * 90 + "\n")


def run_live_par_monitoring_worldpop():
    initialize_system()

    # Initialize analyzer
    analyzer = LivePARAnalyzerWorldPop()

    # Local geo-info (optional)
    _ = get_complete_geographic_info(
        latitude=ScenarioConfig.TANK_LATITUDE,
        longitude=ScenarioConfig.TANK_LONGITUDE,
        fetch_online=False
    )

    temp_output_file = Path(tempfile.gettempdir()) / "live_par_worldpop.html"

    # Create live loop manager
    manager = LiveLoopManager(
        update_interval=ScenarioConfig.UPDATE_INTERVAL_SECONDS,
        output_file=temp_output_file,
        app_name="pyELDQM Live PAR WorldPop"
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

            print(f"[Weather] Wind: {weather['wind_speed']:.1f} m/s @ {weather['wind_dir']:.0f}°")

            # Step 2: Dispersion model
            print("[Model] Running Gaussian dispersion...")
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

            print(f"[Model] Stability: {stability_class} | U_local={U_local:.2f} m/s | MaxC={np.nanmax(concentration):.1f} ppm")

            # Step 3: Threat zones
            print("[Zones] Extracting AEGL polygons...")
            threat_zones = extract_zones(
                analyzer.X, analyzer.Y,
                concentration,
                ScenarioConfig.AEGL_THRESHOLDS,
                ScenarioConfig.TANK_LATITUDE,
                ScenarioConfig.TANK_LONGITUDE,
                wind_dir=weather["wind_dir"]
            )

            # Step 4: Real PAR from raster
            par_results = analyzer.calculate_par(threat_zones)

            # Step 5: Map
            print("[Map] Building interactive map...")
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

            add_threat_zones_and_par_panel(
                base_map,
                threat_zones,
                {k: v for k, v in par_results.items() if k in ["AEGL-1", "AEGL-2", "AEGL-3"]},
                weather=weather,
                chemical_name=ScenarioConfig.CHEMICAL_NAME,
                thresholds=ScenarioConfig.AEGL_THRESHOLDS,
                source_lat=ScenarioConfig.TANK_LATITUDE,
                source_lon=ScenarioConfig.TANK_LONGITUDE,
                stability_class=stability_class,
                release_rate=ScenarioConfig.RELEASE_RATE,
                position='bottomleft'
            )
            
            ensure_layer_control(base_map)

            base_map.save(str(temp_output_file))
            print(f"[Map] Saved: {temp_output_file}")

            manager.open_browser_once()
            manager.wait_for_next_cycle()

        except Exception as e:
            manager.handle_error(e)
            continue


def main():
    run_live_par_monitoring_worldpop()


if __name__ == "__main__":
    main()
