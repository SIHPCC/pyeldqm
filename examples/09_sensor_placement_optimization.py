"""Sensor placement optimization workflow.

Evaluates boundary, coverage, population-weighted, wind-aware, and hybrid
strategies for chemical detection network design around industrial facilities.

Run:
`python 09_sensor_placement_optimization.py`

Dependencies:
`numpy`, `shapely`, `geopandas`, `folium`, `scikit-image`, `rasterio`,
`scikit-learn`.
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
from typing import Dict, Optional, List
from datetime import datetime
import warnings

import numpy as np
import geopandas as gpd
import folium
from shapely.geometry import Polygon, Point, mapping
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
from core.visualization import (
    add_zone_polygons,
    ensure_layer_control,
    add_sensor_optimization_panel,
    fit_map_to_polygons,
)
from core.utils.features import setup_computational_grid
from core.utils.sensor_optimization import SensorPlacementOptimizer, calculate_coverage_metrics
from core.utils.zone_extraction import extract_zones


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

    # Sensor Optimization Settings
    NUM_SENSORS = 5
    SENSOR_STRATEGIES = ["boundary", "coverage", "population", "wind_aware", "hybrid"]
    CURRENT_STRATEGY = "boundary"  # Change this to test different strategies
    
    # Sensor Configuration
    SENSOR_DETECTION_RANGE_M = 500  # Detection radius in meters
    MIN_SENSOR_SPACING_M = 200      # Minimum spacing between sensors
    COST_PER_SENSOR = 10000         # USD per sensor (for cost optimization)
    
    # Population Raster
    POP_RASTER_PATH = r"D:\OneDrive - UET\After PhD\Research\pyELDQM\pyELDQM\data\population\data\population\pak_pop_2026_CN_100m_R2025A_v1.tif"

    # Weather Settings
    USE_MANUAL_WEATHER = False
    MANUAL_WIND_DIR_DEG = 90
    MANUAL_WIND_SPEED_MS = 1.5
    MANUAL_TEMPERATURE_K = 298.15
    MANUAL_HUMIDITY = 0.60
    MANUAL_CLOUD_COVER = 0.20


# ============================================================================
# THREAT ZONE EXTRACTION
# ============================================================================

    # extract_threat_zones_from_concentration now imported from core.utils.zone_extraction

    # return threat_zones


# ============================================================================
# POPULATION RASTER ENGINE
# ============================================================================

class PopulationRasterPAR:
    """
    Population at Risk calculator using real-world raster data.
    """

    def __init__(self, raster_path: str):
        if not os.path.exists(raster_path):
            raise FileNotFoundError(f"Population raster not found: {raster_path}")

        self.raster_path = raster_path
        self.dataset = rasterio.open(raster_path)
        self.crs = self.dataset.crs
        self.nodata = self.dataset.nodata

        print(f"[Population Engine] Loaded: {Path(raster_path).name}")
        print(f"  CRS: {self.crs}, NoData: {self.nodata}")

    def polygon_to_raster_crs(self, poly_wgs84: Polygon) -> Polygon:
        """Convert polygon from EPSG:4326 to raster CRS."""
        gdf = gpd.GeoDataFrame(geometry=[poly_wgs84], crs="EPSG:4326")
        gdf_proj = gdf.to_crs(self.crs)
        return gdf_proj.geometry.iloc[0]

    def par_from_polygon(self, poly_wgs84: Optional[Polygon]) -> int:
        """Compute PAR by clipping raster within polygon."""
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
# SENSOR OPTIMIZATION MANAGER
# ============================================================================

class SensorOptimizationManager:
    """
    Manages sensor placement optimization and visualization.
    """
    
    def __init__(self, population_engine: PopulationRasterPAR):
        self.population_engine = population_engine
        
        sensor_config = {
            'detection_range_m': ScenarioConfig.SENSOR_DETECTION_RANGE_M,
            'min_spacing_m': ScenarioConfig.MIN_SENSOR_SPACING_M,
            'max_sensors': 50,
            'cost_per_sensor': ScenarioConfig.COST_PER_SENSOR
        }
        
        self.optimizer = SensorPlacementOptimizer(
            population_engine=population_engine,
            config=sensor_config
        )
    
    def optimize_all_strategies(
        self,
        threat_zones: Dict[str, Optional[Polygon]],
        source_lat: float,
        source_lon: float,
        wind_direction: float,
        num_sensors: int = 10
    ) -> Dict[str, List[Dict]]:
        """
        Run all optimization strategies for comparison.
        """
        results = {}
        
        print("\n" + "=" * 80)
        print("RUNNING ALL SENSOR OPTIMIZATION STRATEGIES")
        print("=" * 80)
        
        for strategy in ScenarioConfig.SENSOR_STRATEGIES:
            print(f"\n[{strategy.upper()}] Optimizing {num_sensors} sensor placement...")
            
            try:
                wind_dir = wind_direction if strategy == "wind_aware" else None
                
                sensors = self.optimizer.optimize_sensor_placement(
                    threat_zones=threat_zones,
                    source_lat=source_lat,
                    source_lon=source_lon,
                    num_sensors=num_sensors,
                    strategy=strategy,
                    wind_direction=wind_dir
                )
                
                # Calculate metrics
                metrics = self.optimizer.calculate_coverage_metrics(sensors, threat_zones)
                
                results[strategy] = {
                    'sensors': sensors,
                    'metrics': metrics
                }
                
                print(f"  ✓ Placed {len(sensors)} sensors")
                print(f"  ✓ Coverage Area: {metrics['coverage_area_km2']:.2f} km²")
                
                # Show sample sensors
                for s in sensors[:2]:
                    
                    print(f"    • {s['id']}: {s['priority']} priority - {s['purpose']}")
                
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                results[strategy] = None
        
        return results
    
    def create_comparison_map(
        self,
        all_results: Dict[str, Dict],
        threat_zones: Dict[str, Optional[Polygon]],
        source_lat: float,
        source_lon: float,
        strategy_to_display: str
    ) -> folium.Map:
        """
        Create Folium map showing selected sensor strategy.
        """
        
        # Create base map
        m = folium.Map(
            location=[source_lat, source_lon],
            zoom_start=13,
            tiles='OpenStreetMap'
        )
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        
        # Add source marker
        folium.Marker(
            [source_lat, source_lon],
            popup="<b>Chemical Source</b><br>Ammonia Tank",
            icon=folium.Icon(color='red', icon='warning-sign'),
            tooltip="Release Source"
        ).add_to(m)
        
        # Add threat zones (centralized renderer)
        add_zone_polygons(
            m,
            {k: v for k, v in threat_zones.items() if k in ["AEGL-1", "AEGL-2", "AEGL-3"]},
            thresholds_context={"AEGL": ScenarioConfig.AEGL_THRESHOLDS},
            name_prefix=None,
        )
        # Auto-zoom to fit all threat zones
        fit_map_to_polygons(m, threat_zones.values())
        
        # Add selected sensor strategy
        if strategy_to_display in all_results and all_results[strategy_to_display]:
            sensors = all_results[strategy_to_display]['sensors']
            self.optimizer.add_sensors_to_map(
                m, 
                sensors,
                layer_name=f"Sensors ({strategy_to_display.title()})"
            )
        
        # Add combined info panel (bottom-left)
        add_sensor_optimization_panel(
            m,
            all_results,
            active_strategy=strategy_to_display,
            available_strategies=ScenarioConfig.SENSOR_STRATEGIES,
            cost_per_sensor=ScenarioConfig.COST_PER_SENSOR,
            detection_range_m=ScenarioConfig.SENSOR_DETECTION_RANGE_M,
            position="bottomleft"
        )
        
        # Layer control (centralized ensure)
        ensure_layer_control(m)
        
        return m
    



# ============================================================================
# MAIN EXECUTION
# ============================================================================

def initialize_system():
    print("\n" + "=" * 90)
    print("pyELDQM: SENSOR PLACEMENT OPTIMIZATION")
    print("=" * 90)
    print(f"Location: {ScenarioConfig.LOCATION_NAME}")
    print(f"Coordinates: {ScenarioConfig.TANK_LATITUDE}°N, {ScenarioConfig.TANK_LONGITUDE}°E")
    print(f"Chemical: {ScenarioConfig.CHEMICAL_NAME}")
    print(f"Target Sensors: {ScenarioConfig.NUM_SENSORS}")
    print(f"Detection Range: {ScenarioConfig.SENSOR_DETECTION_RANGE_M}m")
    print(f"Current Strategy: {ScenarioConfig.CURRENT_STRATEGY.upper()}")
    print("=" * 90 + "\n")


def run_sensor_optimization_demo():
    """
    Main demonstration of sensor optimization capabilities.
    """
    
    initialize_system()
    
    # Setup computational grid
    X, Y, _, _ = setup_computational_grid(
        ScenarioConfig.X_MAX,
        ScenarioConfig.Y_MAX,
        ScenarioConfig.NX,
        ScenarioConfig.NY
    )
    
    # Load population data
    print("[Population] Loading raster data...")
    population_engine = PopulationRasterPAR(ScenarioConfig.POP_RASTER_PATH)
    
    # Initialize sensor optimizer
    print("[Sensors] Initializing optimization manager...")
    sensor_manager = SensorOptimizationManager(population_engine)
    
    # Get weather
    print("\n[Weather] Fetching conditions...")
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
    
    print(f"  Wind: {weather['wind_speed']:.1f} m/s @ {weather['wind_dir']:.0f}°")
    print(f"  Temperature: {weather['temperature_K']-273.15:.1f}°C")
    
    # Run dispersion model
    print("\n[Dispersion] Running Gaussian model...")
    concentration, U_local, stability_class, resolved_sources = calculate_gaussian_dispersion(
        weather=weather,
        X=X,
        Y=Y,
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
    
    print(f"  Stability: {stability_class}")
    print(f"  Max Concentration: {np.nanmax(concentration):.1f} ppm")
    
    # Extract threat zones
    print("\n[Zones] Extracting AEGL threat zones...")
    threat_zones = extract_zones(
        X, Y,
        concentration,
        ScenarioConfig.AEGL_THRESHOLDS,
        ScenarioConfig.TANK_LATITUDE,
        ScenarioConfig.TANK_LONGITUDE,
        wind_dir=weather["wind_dir"]
    )
    
    for zone_name, zone_poly in threat_zones.items():
        if zone_poly and not zone_poly.is_empty:
            area_km2 = zone_poly.area * 111.32 * 110.57
            print(f"  {zone_name}: {area_km2:.2f} km²")
    
    # Run all optimization strategies
    all_results = sensor_manager.optimize_all_strategies(
        threat_zones=threat_zones,
        source_lat=ScenarioConfig.TANK_LATITUDE,
        source_lon=ScenarioConfig.TANK_LONGITUDE,
        wind_direction=weather["wind_dir"],
        num_sensors=ScenarioConfig.NUM_SENSORS
    )
    
    # Create comparison map
    print("\n[Map] Creating visualization...")
    comparison_map = sensor_manager.create_comparison_map(
        all_results=all_results,
        threat_zones=threat_zones,
        source_lat=ScenarioConfig.TANK_LATITUDE,
        source_lon=ScenarioConfig.TANK_LONGITUDE,
        strategy_to_display=ScenarioConfig.CURRENT_STRATEGY
    )
    
    # Save and display
    output_file = Path(tempfile.gettempdir()) / "sensor_optimization_demo.html"
    comparison_map.save(str(output_file))
    print(f"  Map saved: {output_file}")
    
    try:
        webbrowser.open(f"file:///{output_file}")
        print("  Browser opened successfully!")
    except Exception as e:
        print(f"  Could not open browser: {e}")
    
    # Print summary report
    print("\n" + "=" * 90)
    print("OPTIMIZATION SUMMARY REPORT")
    print("=" * 90)
    
    for strategy in ScenarioConfig.SENSOR_STRATEGIES:
        if strategy not in all_results or all_results[strategy] is None:
            continue
        
        metrics = all_results[strategy]['metrics']
        sensors = all_results[strategy]['sensors']
        
        print(f"\n{strategy.upper()} Strategy:")
        print(f"  Total Sensors: {metrics['total_sensors']}")
        print(f"  Coverage Area: {metrics['coverage_area_km2']:.2f} km²")
        print(f"  Estimated Cost: ${metrics['total_sensors'] * ScenarioConfig.COST_PER_SENSOR:,}")
        
        # Zone coverage
        for zone_name, zone_metrics in metrics['zone_coverage'].items():
            print(f"  {zone_name} Coverage: {zone_metrics['coverage_percent']:.1f}%")
        
        # Priority distribution
        priority_counts = {}
        for sensor in sensors:
            p = sensor.get('priority', 'unknown')
            priority_counts[p] = priority_counts.get(p, 0) + 1
        
        print(f"  Priority Distribution: {priority_counts}")
    
    print("\n" + "=" * 90)
    print(f"Recommended Strategy: {ScenarioConfig.CURRENT_STRATEGY.upper()}")
    print("=" * 90)
    
    print("\n✓ Demo completed successfully!")
    print(f"  To test other strategies, change ScenarioConfig.CURRENT_STRATEGY")
    print(f"  Available: {', '.join(ScenarioConfig.SENSOR_STRATEGIES)}")


def main():
    """Entry point"""
    try:
        run_sensor_optimization_demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
