"""Multi-source live population-at-risk analysis workflow.

Runs multi-source Gaussian dispersion, extracts AEGL zones, and calculates
combined population-at-risk exposure using geospatial raster operations.

Outputs include integrated threat mapping, source markers, and live PAR panels.
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
from typing import Dict, List, Optional
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
from core.dispersion_models.gaussian_model import multi_source_concentration
from core.meteorology.realtime_weather import get_weather
from core.meteorology.stability import get_stability_class
from core.meteorology.wind_profile import wind_speed as calc_wind_profile
from core.geography import get_complete_geographic_info
from core.visualization.folium_maps import create_live_threat_map, add_facility_markers, meters_to_latlon
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
    LOCATION_NAME = "Ammonia Industrial Complex - FFC Area"
    TIMEZONE_OFFSET_HRS = 5  # Pakistan Standard Time (UTC+5)

    # Chemical Properties (Ammonia)
    CHEMICAL_NAME = "Ammonia (NH3)"
    MOLECULAR_WEIGHT = 17.03  # g/mol

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

    # Real population raster
    POP_RASTER_PATH = r"D:\OneDrive - UET\After PhD\Research\pyELDQM\pyELDQM\data\population\data\population\pak_pop_2026_CN_100m_R2025A_v1.tif"

    # ============================================================================
    # MANUAL WEATHER OVERRIDE SETTINGS
    # ============================================================================
    
    USE_MANUAL_WEATHER = False  # Set to True to use manual weather conditions
    MANUAL_WIND_DIR_DEG = 270  # Wind direction in degrees (0°=N, 90°=E, 180°=S, 270°=W)
    MANUAL_WIND_SPEED_MS = 2.5  # Wind speed in m/s
    MANUAL_TEMPERATURE_K = 298.15  # Temperature in Kelvin (298.15K ≈ 25°C)
    MANUAL_HUMIDITY = 0.65  # Relative humidity (0-1)
    MANUAL_CLOUD_COVER = 0.30  # Cloud cover fraction (0-1)
    
    # ============================================================================
    # MULTIPLE DISPERSION SOURCES CONFIGURATION
    # ============================================================================
    # Define multiple ammonia release sources
    # Parameters: latitude, longitude, release_rate (g/s), height (m), name, color
    
    SOURCES = [
        {
            "name": "Tank A - Primary Storage",
            "lat": 31.691100,
            "lon": 74.082167,
            "rate": 800.0,  # g/s
            "height": 3.0,  # meters
            "color": "red",
        },
        {
            "name": "Tank B - Secondary Storage",
            "lat": 31.691300,
            "lon": 74.082400,
            "rate": 800.0,  # g/s
            "height": 3,  # meters
            "color": "orange",
        },
        {
            "name": "Process A - Production Unit",
            "lat": 31.691050,
            "lon": 74.081950,
            "rate": 800.0,  # g/s
            "height": 3,  # meters
            "color": "yellow",
        },
    ]


# ============================================================================
# THREAT ZONE EXTRACTION
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
        self.crs = self.dataset.crs
        self.nodata = self.dataset.nodata

        print("\n[PopulationRasterPAR] Loaded population raster:")
        print(f"  Path : {self.raster_path}")
        print(f"  CRS  : {self.crs}")
        print(f"  NoData: {self.nodata}")

    def polygon_to_raster_crs(self, poly_wgs84: Polygon) -> Polygon:
        """Convert polygon from EPSG:4326 to raster CRS."""
        gdf = gpd.GeoDataFrame(geometry=[poly_wgs84], crs="EPSG:4326")
        gdf_proj = gdf.to_crs(self.crs)
        return gdf_proj.geometry.iloc[0]

    def par_from_polygon(self, poly_wgs84: Optional[Polygon]) -> int:
        """Compute PAR by clipping population raster within polygon and summing."""
        if poly_wgs84 is None or poly_wgs84.is_empty:
            return 0

        try:
            poly_proj = self.polygon_to_raster_crs(poly_wgs84)

            out_image, _ = mask(
                self.dataset,
                [mapping(poly_proj)],
                crop=True,
                all_touched=True
            )

            pop = out_image[0].astype(np.float64)

            if self.nodata is not None:
                pop[pop == self.nodata] = np.nan

            pop = np.nan_to_num(pop, nan=0.0)
            total = int(np.sum(pop))

            return max(total, 0)

        except Exception:
            return 0


# ============================================================================
# LIVE MULTI-SOURCE PAR ANALYZER
# ============================================================================

class LiveMultiSourcePARAnalyzer:
    """
    Analyzes PAR for multiple simultaneous release sources with live updates.
    """

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

    def calculate_combined_concentration(
        self,
        weather: Dict,
        sources: List[Dict]
    ) -> tuple:
        """
        Calculate combined concentration from multiple sources.
        Returns: (concentration_grid, U_local, stability_class)
        """
        
        # Get stability class
        stability_class = get_stability_class(
            wind_speed=weather.get("wind_speed", 2.0),
            datetime_obj=datetime.now(),
            latitude=ScenarioConfig.TANK_LATITUDE,
            longitude=ScenarioConfig.TANK_LONGITUDE,
            cloudiness_index=weather.get("cloud_cover", 0.3),
            timezone_offset_hrs=ScenarioConfig.TIMEZONE_OFFSET_HRS
        )

        # Calculate wind profile at reference height
        U_local = calc_wind_profile(
            z_user=3.0,
            z0=3.0,
            U_user=weather.get("wind_speed", 2.0),
            stability_class=stability_class
        )

        # Prepare source data for multi-source model
        # Convert lat/lon sources to local x/y coordinates
        source_list = []
        for src in sources:
            lat_offset = (src["lat"] - ScenarioConfig.TANK_LATITUDE) * 111000  # meters
            lon_offset = (src["lon"] - ScenarioConfig.TANK_LONGITUDE) * 111000 * \
                         np.cos(np.radians(ScenarioConfig.TANK_LATITUDE))  # meters

            # Rotate to wind-aligned coordinates
            wind_dir_rad = np.radians(weather.get("wind_dir", 0))
            x_rotated = lon_offset * np.cos(wind_dir_rad) + lat_offset * np.sin(wind_dir_rad)
            y_rotated = -lon_offset * np.sin(wind_dir_rad) + lat_offset * np.cos(wind_dir_rad)

            source_list.append({
                "name": src["name"],
                "Q": src["rate"],
                "x0": x_rotated,
                "y0": y_rotated,
                "h_s": src["height"],
                "wind_dir": weather.get("wind_dir", 0),
            })

        # Calculate combined concentration using multi-source model
        C_total = multi_source_concentration(
            sources=source_list,
            x_grid=self.X,
            y_grid=self.Y,
            z=3,  # receptor height (m)
            t=600,  # release duration (s)
            t_r=600,
            U=U_local,
            stability_class=stability_class,
            roughness='URBAN',
            mode='continuous',
            grid_wind_direction=weather.get("wind_dir", 0)
        )

        # Convert to ppm
        T = weather.get("temperature_K", 298.15)
        R = 0.08206  # L·atm/(mol·K)
        Vm = R * T / 1.0  # L/mol at 1 atm
        C_ppm = C_total * (Vm / ScenarioConfig.MOLECULAR_WEIGHT) * 1000

        return C_ppm, U_local, stability_class

    def calculate_par(self, threat_zones: Dict[str, Optional[Polygon]]) -> Dict[str, Dict]:
        """Calculate PAR for each threat zone."""
        self.cycle_count += 1
        self.last_update_time = datetime.now()

        results = {}
        total_par = 0

        print(f"\n[{self.last_update_time.strftime('%H:%M:%S')}] Multi-Source Real PAR (Raster-based) Calculation:")

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
# MAIN EXECUTION
# ============================================================================

def initialize_system():
    print("\n" + "=" * 90)
    print("pyELDQM: MULTI-SOURCE LIVE PAR ANALYSIS (WorldPop/GHSL Raster)")
    print("=" * 90)
    print(f"Location: {ScenarioConfig.LOCATION_NAME}")
    print(f"Base Coordinates: {ScenarioConfig.TANK_LATITUDE}°N, {ScenarioConfig.TANK_LONGITUDE}°E")
    print(f"Chemical: {ScenarioConfig.CHEMICAL_NAME}")
    print(f"Number of Sources: {len(ScenarioConfig.SOURCES)}")
    
    total_release = sum(src["rate"] for src in ScenarioConfig.SOURCES)
    print(f"Combined Release Rate: {total_release} g/s")
    
    print(f"\nSources Configuration:")
    for i, src in enumerate(ScenarioConfig.SOURCES, 1):
        print(f"  {i}. {src['name']}: {src['rate']} g/s @ {src['height']}m height")
    
    if ScenarioConfig.USE_MANUAL_WEATHER:
        print(f"\n[MANUAL WEATHER MODE]")
        print(f"  Wind Speed: {ScenarioConfig.MANUAL_WIND_SPEED_MS} m/s")
        print(f"  Wind Direction: {ScenarioConfig.MANUAL_WIND_DIR_DEG}°")
        print(f"  Temperature: {ScenarioConfig.MANUAL_TEMPERATURE_K} K")
        print(f"  Humidity: {ScenarioConfig.MANUAL_HUMIDITY * 100}%")
        print(f"  Cloud Cover: {ScenarioConfig.MANUAL_CLOUD_COVER * 100}%")
    else:
        print(f"\n[AUTO WEATHER MODE - Using Open-Meteo API]")
    
    print(f"Update Interval: {ScenarioConfig.UPDATE_INTERVAL_SECONDS} seconds")
    print(f"Population Raster: {ScenarioConfig.POP_RASTER_PATH}")
    print("=" * 90 + "\n")


def run_live_multi_source_par_monitoring():
    initialize_system()

    # Initialize analyzer
    analyzer = LiveMultiSourcePARAnalyzer()

    # Local geo-info (optional)
    _ = get_complete_geographic_info(
        latitude=ScenarioConfig.TANK_LATITUDE,
        longitude=ScenarioConfig.TANK_LONGITUDE,
        fetch_online=False
    )

    temp_output_file = Path(tempfile.gettempdir()) / "live_multi_source_par.html"

    # Create live loop manager
    manager = LiveLoopManager(
        update_interval=ScenarioConfig.UPDATE_INTERVAL_SECONDS,
        output_file=temp_output_file,
        app_name="pyELDQM Multi-Source Live PAR"
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

            print(f"[Weather] Wind: {weather['wind_speed']:.1f} m/s @ {weather['wind_dir']:.0f}° | "
                  f"Temp: {weather.get('temperature_K', 298.15):.1f}K | "
                  f"Humidity: {weather.get('humidity', 0.5)*100:.1f}%")

            # Step 2: Multi-source dispersion model
            print("[Model] Running multi-source Gaussian dispersion...")
            concentration, U_local, stability_class = analyzer.calculate_combined_concentration(
                weather=weather,
                sources=ScenarioConfig.SOURCES
            )

            max_conc = np.nanmax(concentration) if not np.all(np.isnan(concentration)) else 0
            print(f"[Model] Stability: {stability_class} | U_local={U_local:.2f} m/s | MaxC={max_conc:.1f} ppm")

            # Step 3: Threat zones
            print("[Zones] Extracting AEGL polygons from combined concentration...")
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
            print("[Map] Building interactive multi-source map...")
            
            # Use primary source for map center
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
                tank_height=ScenarioConfig.SOURCES[0]["height"],
                release_rate=sum(src["rate"] for src in ScenarioConfig.SOURCES),
                aegl_thresholds=ScenarioConfig.AEGL_THRESHOLDS,
                update_interval_seconds=ScenarioConfig.UPDATE_INTERVAL_SECONDS,
                sources=[],  # Will add manually below
                markers=[]
            )

            # Add source markers for each release point
            source_markers = []
            for src in ScenarioConfig.SOURCES:
                source_markers.append({
                    'name': f"{src['name']} ({src['rate']} g/s)",
                    'lat': src['lat'],
                    'lon': src['lon'],
                    'type': 'industrial'
                })

            add_facility_markers(base_map, source_markers, group_name="Release Sources")

            # Add threat zones and PAR panel
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
                release_rate=sum(src["rate"] for src in ScenarioConfig.SOURCES),
                position='bottomleft'
            )

            # Add source information panel
            info_html = _build_sources_info_html(ScenarioConfig.SOURCES)
            folium.Marker(
                location=[ScenarioConfig.TANK_LATITUDE, ScenarioConfig.TANK_LONGITUDE],
                popup=folium.Popup(info_html, max_width=400),
                icon=folium.Icon(color='blue', icon='info-sign'),
                tooltip="Multi-Source Information"
            ).add_to(base_map)
            
            ensure_layer_control(base_map)

            base_map.save(str(temp_output_file))
            print(f"[Map] Saved: {temp_output_file}")

            manager.open_browser_once()
            manager.wait_for_next_cycle()

        except Exception as e:
            manager.handle_error(e)
            continue


def _build_sources_info_html(sources: List[Dict]) -> str:
    """Build HTML popup for sources information."""
    html = "<div style='font-family: Arial; font-size: 12px;'>"
    html += "<h4 style='margin: 5px 0;'>Multi-Source Configuration</h4>"
    html += "<hr style='margin: 5px 0;'>"
    
    total_rate = 0
    for src in sources:
        html += f"<b>{src['name']}</b><br>"
        html += f"  Release Rate: {src['rate']} g/s<br>"
        html += f"  Height: {src['height']} m<br>"
        html += f"  Location: {src['lat']:.6f}°N, {src['lon']:.6f}°E<br>"
        total_rate += src['rate']
        html += "<br>"
    
    html += f"<b>Total Release: {total_rate} g/s</b>"
    html += "</div>"
    
    return html


def main():
    """Main entry point."""
    run_live_multi_source_par_monitoring()


if __name__ == "__main__":
    main()
