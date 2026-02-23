"""
Live Population at Risk (PAR) Analysis Integrated with Real-time Threat Zones
=============================================================================

Real-time PAR analysis integrated with the ammonia tank dispersion simulation.
This tool uses live threat zones from the dispersion model and calculates the
population at risk (PAR) for each zone in real-time.

Features:
- Integrates with 06_realtime_ammonia_threat_zones.py simulation
- Uses real-time weather data and dispersion modeling
- Calculates population density in dynamic threat zones
- Real-time PAR updates synchronized with simulation cycles
- Interactive Folium map with "PAR map" layer showing affected population
- Live population statistics for each threat zone
- Direct browser display (no folder saving)

Use Case:
Emergency response planning and real-time hazard monitoring with population
impact assessment for industrial facilities.

To Run:
    python 07_live_PAR_analysis.py

To Stop:
    Press Ctrl+C in the terminal

Dependencies:
    pip install geopandas folium scikit-image branca requests numpy

Author: pyELDQM Development Team
Date: 2026
"""

# ============================================================================
# IMPORTS
# ============================================================================

# Standard library imports
import sys
import os
import json
import tempfile
import webbrowser
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import warnings

# Third-party imports
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
from shapely.geometry import Point, Polygon, mapping, box
from shapely.ops import unary_union
from scipy.ndimage import label
from pyproj import CRS, Transformer
import shapely.ops

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
from core.visualization import add_par_info_panel, ensure_layer_control
from core.utils.features import setup_computational_grid
from core.utils.zone_extraction import extract_zones
from core.utils import LiveLoopManager
from core.population import calculate_population_in_zone

warnings.filterwarnings('ignore')


# ============================================================================
# SCENARIO CONFIGURATION
# ============================================================================

class ScenarioConfig:
    """Configuration parameters for the ammonia release scenario."""
    
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
    TANK_HEIGHT = 3.0  # meters above ground
    Z_REF = 3.0  # Reference height for wind speed (m)
    
    # Computational Grid
    X_MAX = 5000  # meters (downwind extent)
    Y_MAX = 5000  # meters (crosswind extent)
    NX = 1000  # grid points in x-direction
    NY = 1000  # grid points in y-direction
    
    # AEGL Thresholds (ppm)
    AEGL_THRESHOLDS = {
        'AEGL-1': 30,      # Mild discomfort threshold
        'AEGL-2': 160,     # Irreversible effects threshold
        'AEGL-3': 1100,    # Life-threatening threshold
    }
    
    # Population & PAR Settings
    BASE_POPULATION_DENSITY = 500  # people per km²
    UPDATE_INTERVAL_SECONDS = 60  # seconds between updates

    # Manual Weather Override (set to True to disable automatic fetch)
    USE_MANUAL_WEATHER = True
    MANUAL_WIND_DIR_DEG = 270  # degrees from north
    MANUAL_WIND_SPEED_MS = 1.0   # m/s
    MANUAL_TEMPERATURE_K = 298.15  # ~25°C
    MANUAL_HUMIDITY = 0.60  # 60%
    MANUAL_CLOUD_COVER = 0.20  # 20%


# ============================================================================
# THREAT ZONE EXTRACTION FROM CONCENTRATION FIELD
# ============================================================================

# extract_threat_zones_from_concentration() is now imported from core.utils.zone_extraction


# ============================================================================
# POPULATION DENSITY CALCULATION
# ============================================================================



# ============================================================================
# LIVE PAR CALCULATION
# ============================================================================

class LivePARAnalyzer:
    """Real-time PAR analyzer integrated with dispersion simulation."""
    
    def __init__(self):
        """Initialize analyzer."""
        self.cycle_count = 0
        self.last_update_time = None
        self.par_history = []
        self.X = None
        self.Y = None
        self.threat_zones_gdf = None
        
        # Initialize computational grid
        self.X, self.Y, _, _ = setup_computational_grid(
            ScenarioConfig.X_MAX,
            ScenarioConfig.Y_MAX,
            ScenarioConfig.NX,
            ScenarioConfig.NY
        )
    
    def calculate_par_cycle(
        self,
        concentration: np.ndarray,
        threat_zones: Dict[str, Polygon]
    ) -> Dict[str, Dict]:
        """
        Execute one PAR analysis cycle using current threat zones.
        
        Parameters:
        -----------
        concentration : np.ndarray
            Concentration field from dispersion model
        threat_zones : Dict[str, Polygon]
            Threat zones from concentration field
        
        Returns:
        --------
        Dict[str, Dict]
            PAR results by zone with detailed statistics
        """
        self.cycle_count += 1
        self.last_update_time = datetime.now()
        
        results = {}
        total_par = 0

        print(f"[{self.last_update_time.strftime('%H:%M:%S')}] Calculating PAR...")
        print(f"  DEBUG: Received {len(threat_zones)} zones")
        for zone_name, zone_poly in threat_zones.items():
            if zone_poly is None:
                print(f"    {zone_name}: None (no threat zone)")
            else:
                print(f"    {zone_name}: Polygon with {len(zone_poly.exterior.coords)} points")
                print(f"      Bounds: {zone_poly.bounds}")

        # Calculate PAR for each AEGL zone
        for zone_name, zone_poly in threat_zones.items():
            if zone_poly is None:
                results[zone_name] = {
                    'par': 0,
                    'population_points': [],
                    'zone_area_km2': 0,
                    'geometry': None,
                }
                continue

            # Calculate population in this zone
            par, pop_points = calculate_population_in_zone(
                zone_poly=zone_poly,
                base_density=ScenarioConfig.BASE_POPULATION_DENSITY,
                leak_lat=ScenarioConfig.TANK_LATITUDE,
                leak_lon=ScenarioConfig.TANK_LONGITUDE
            )

            total_par += par
            
            # Store results
            results[zone_name] = {
                'par': par,
                'population_points': pop_points,
                'zone_area_km2': zone_poly.area * 111.32 * 110.57,
                'geometry': zone_poly,
            }
            
            # Print zone summary
            status = "CRITICAL" if par > 10000 else ("HIGH" if par > 5000 else "OK")
            print(f"    {zone_name:12s}: {par:>8,} people [{status}]")

        print(f"  TOTAL PAR: {total_par:,} people")
        
        # Store in history
        self.par_history.append({
            'cycle': self.cycle_count,
            'timestamp': self.last_update_time.isoformat(),
            'total_par': total_par,
            'par_by_zone': {zone: results[zone]['par'] for zone in results},
            'leak_location': (ScenarioConfig.TANK_LATITUDE, ScenarioConfig.TANK_LONGITUDE)
        })
        
        return results


# ============================================================================
# FOLIUM MAP VISUALIZATION
# ============================================================================

def augment_map_with_par(
    base_map: folium.Map,
    analyzer: LivePARAnalyzer,
    par_results: Dict[str, Dict],
    weather: Dict
) -> folium.Map:
    """
    Augment an existing live threat map with PAR layers and info panel.
    
    Adds:
    - Population distribution feature layer (PAR Map)
    - Bottom-left population summary panel
    """
    # PAR MAP LAYER - Population Distribution
    par_fg = folium.FeatureGroup(
        name='PAR Map',
        show=True
    )
    
    print(f"  DEBUG PAR Visualization:")
    total_points = 0
    
    for zone_name, zone_data in par_results.items():
        pop_points = zone_data['population_points']
        color = {'AEGL-1': '#FFFF00', 'AEGL-2': '#FFA500', 'AEGL-3': '#FF0000'}.get(zone_name, '#999999')
        
        print(f"    {zone_name}: {len(pop_points)} population points")
        if len(pop_points) > 0:
            print(f"      First point: lat={pop_points[0]['latitude']:.6f}, lon={pop_points[0]['longitude']:.6f}")
            print(f"      Last point: lat={pop_points[-1]['latitude']:.6f}, lon={pop_points[-1]['longitude']:.6f}")
        
        for point_data in pop_points:
            lat = point_data['latitude']
            lon = point_data['longitude']
            pop = point_data['population']
            
            # Scale radius by population, but keep minimum visibility
            radius = min(15, max(3, np.sqrt(pop / 50)))
            
            popup_html = f"""
            <div style="font-family: Arial; font-size: 12px; width: 250px;">
                <div style="background: linear-gradient(135deg, {color}dd 0%, {color}99 100%); 
                            padding: 10px; border-radius: 5px 5px 0 0; margin: -5px -5px 10px -5px; color: #000;">
                    <b style="font-size: 13px;">Population Cluster - {zone_name}</b>
                </div>
                <table style="width: 100%;">
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 8px; font-weight: bold;">Population</td>
                        <td style="text-align: right; padding: 8px; font-weight: bold; color: #d32f2f;">{pop} people</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">Latitude</td>
                        <td style="text-align: right; padding: 8px; font-family: monospace; font-size: 11px;">{lat:.6f}°</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px;">Longitude</td>
                        <td style="text-align: right; padding: 8px; font-family: monospace; font-size: 11px;">{lon:.6f}°</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px;">Density</td>
                        <td style="text-align: right; padding: 8px;">{point_data['density']:.0f} people/km²</td>
                    </tr>
                </table>
            </div>
            """
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=280),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.8,
                weight=2,
                tooltip=f"{pop} people - {zone_name}"
            ).add_to(par_fg)
            
            total_points += 1
    
    print(f"    Total population markers placed: {total_points}")
    par_fg.add_to(base_map)
    
    # Bottom-left LIVE PAR SUMMARY PANEL via centralized helper
    add_par_info_panel(
        base_map,
        par_results,
        analyzer=analyzer,
        weather=weather,
        location={"lat": ScenarioConfig.TANK_LATITUDE, "lon": ScenarioConfig.TANK_LONGITUDE},
        base_density=getattr(ScenarioConfig, 'BASE_POPULATION_DENSITY', None),
        theme="live",
        position="bottomleft",
    )
    ensure_layer_control(base_map)
    print("  ✓ Added PAR layer and bottom-left info panel")
    return base_map


# ============================================================================
# MAIN EXECUTION & MONITORING
# ============================================================================

def initialize_system():
    """Initialize monitoring system."""
    print(f"\n{'='*90}")
    print("LIVE PAR ANALYSIS INTEGRATED WITH REAL-TIME DISPERSION SIMULATION")
    print(f"{'='*90}")
    print(f"Location: {ScenarioConfig.LOCATION_NAME}")
    print(f"Coordinates: {ScenarioConfig.TANK_LATITUDE}°N, {ScenarioConfig.TANK_LONGITUDE}°E")
    print(f"Chemical: {ScenarioConfig.CHEMICAL_NAME}")
    print(f"Release Rate: {ScenarioConfig.RELEASE_RATE} g/s")
    print(f"Base Population Density: {ScenarioConfig.BASE_POPULATION_DENSITY} people/km²")
    print(f"Update Interval: {ScenarioConfig.UPDATE_INTERVAL_SECONDS} seconds")
    if ScenarioConfig.USE_MANUAL_WEATHER:
        print("Weather Mode: MANUAL (automatic fetching disabled)")
        print(f"Manual Wind: {ScenarioConfig.MANUAL_WIND_SPEED_MS:.1f} m/s @ {ScenarioConfig.MANUAL_WIND_DIR_DEG:.0f}°")
    else:
        print("Weather Mode: AUTOMATIC (Open-Meteo)")
    print(f"{'='*90}\n")


def run_live_par_monitoring():
    """
    Run integrated live PAR analysis with real-time dispersion simulation.
    
    Integrates with real-time weather data and Gaussian dispersion model
    to calculate dynamic threat zones and population at risk.
    """
    initialize_system()
    
    # Initialize analyzer and geo info
    analyzer = LivePARAnalyzer()
    
    geo_info = get_complete_geographic_info(
        latitude=ScenarioConfig.TANK_LATITUDE,
        longitude=ScenarioConfig.TANK_LONGITUDE,
        fetch_online=False
    )
    
    temp_output_file = Path(tempfile.gettempdir()) / "live_par_analysis.html"
    
    # Create live loop manager
    manager = LiveLoopManager(
        update_interval=ScenarioConfig.UPDATE_INTERVAL_SECONDS,
        output_file=temp_output_file,
        app_name="pyELDQM Live PAR Analysis"
    )
    
    for cycle in manager.run():
        try:
                # Step 1: Fetch real-time weather
                if ScenarioConfig.USE_MANUAL_WEATHER:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Using MANUAL weather settings...")
                    weather = {
                        'source': 'manual',
                        'wind_speed': ScenarioConfig.MANUAL_WIND_SPEED_MS,
                        'wind_dir': ScenarioConfig.MANUAL_WIND_DIR_DEG,
                        'temperature_K': ScenarioConfig.MANUAL_TEMPERATURE_K,
                        'humidity': ScenarioConfig.MANUAL_HUMIDITY,
                        'cloud_cover': ScenarioConfig.MANUAL_CLOUD_COVER,
                    }
                    print(f"  ✓ Wind (manual): {weather['wind_speed']:.1f} m/s from {weather['wind_dir']:.0f}°")
                    print(f"  ✓ Temperature (manual): {weather['temperature_K'] - 273.15:.1f}°C")
                    print(f"  ✓ Humidity (manual): {weather['humidity']*100:.0f}%")
                else:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Fetching real-time weather...")
                    weather = get_weather(
                        latitude=ScenarioConfig.TANK_LATITUDE,
                        longitude=ScenarioConfig.TANK_LONGITUDE,
                        source='open_meteo'
                    )
                    print(f"  ✓ Wind: {weather['wind_speed']:.1f} m/s from {weather['wind_dir']:.0f}°")
                    print(f"  ✓ Temperature: {weather['temperature_K'] - 273.15:.1f}°C")
                    print(f"  ✓ Humidity: {weather['humidity']*100:.0f}%")
                
                # Step 2: Calculate dispersion field
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running Gaussian dispersion model...")
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
                        'lat': ScenarioConfig.TANK_LATITUDE,
                        'lon': ScenarioConfig.TANK_LONGITUDE,
                        'name': 'Primary Tank',
                        'height': ScenarioConfig.TANK_HEIGHT,
                        'rate': ScenarioConfig.RELEASE_RATE,
                        'color': 'red'
                    }],
                    latitude=ScenarioConfig.TANK_LATITUDE,
                    longitude=ScenarioConfig.TANK_LONGITUDE,
                    timezone_offset_hrs=ScenarioConfig.TIMEZONE_OFFSET_HRS
                )
                print(f"  ✓ Stability class: {stability_class}")
                print(f"  ✓ Local wind speed: {U_local:.2f} m/s")
                print(f"  ✓ Max concentration: {np.nanmax(concentration):.1f} ppm")
                
                # Step 3: Extract threat zones from concentration field
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Extracting threat zones...")
                threat_zones = extract_zones(
                    analyzer.X,
                    analyzer.Y,
                    concentration,
                    ScenarioConfig.AEGL_THRESHOLDS,
                    ScenarioConfig.TANK_LATITUDE,
                    ScenarioConfig.TANK_LONGITUDE,
                    wind_dir=weather['wind_dir']  # Pass wind direction for coordinate rotation
                )
                
                # DEBUG: Print threat zones summary with coordinates for verification
                print(f"  DEBUG: Threat zones returned (wind: {weather['wind_dir']:.0f}°):")
                for zone_name, zone_poly in threat_zones.items():
                    if zone_poly is None:
                        print(f"    {zone_name}: None")
                    else:
                        bounds = zone_poly.bounds
                        print(f"    {zone_name}: Polygon at (lon:{bounds[0]:.6f}-{bounds[2]:.6f}, lat:{bounds[1]:.6f}-{bounds[3]:.6f})")
                
                # Step 4: Calculate PAR
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Calculating Population at Risk (PAR)...")
                par_results = analyzer.calculate_par_cycle(concentration, threat_zones)
                
                # Step 5: Create base threat map and augment with PAR
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Creating interactive map...")
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
                final_map = augment_map_with_par(base_map, analyzer, par_results, weather)
                final_map.save(str(temp_output_file))
                print(f"  ✓ Threat map augmented with PAR layer")
                
                # Step 6: Open browser on first update
                manager.open_browser_once()
                
                # Step 7: Wait for next update
                manager.wait_for_next_cycle()
                
        except Exception as e:
            manager.handle_error(e)
            continue


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for live PAR analysis."""
    # Display banner
    print("=" * 90)
    print("pyELDQM: LIVE POPULATION AT RISK (PAR) ANALYSIS")
    print("Integrated with Real-time Dispersion Modeling")
    print("=" * 90)
    
    try:
        run_live_par_monitoring()
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
