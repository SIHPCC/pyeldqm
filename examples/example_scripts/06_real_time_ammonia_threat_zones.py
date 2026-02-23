"""Real-time ammonia threat zone workflow.

Implements continuous dispersion updates using live or manual weather inputs and
renders AEGL-based threat zones for operational monitoring.

Run:
`python 06_real_time_ammonia_threat_zones.py`

Dependencies:
`folium`, `scikit-image`, `branca`, `requests`, `numpy`.
"""

# ============================================================================
# IMPORTS
# ============================================================================

# Standard library imports
import sys
import os
import time
import webbrowser
import tempfile
from pathlib import Path
from datetime import datetime

# Third-party imports
import numpy as np
import folium
from folium import plugins

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# pyELDQM imports
from core.dispersion_models.gaussian_model import calculate_gaussian_dispersion
from core.meteorology.realtime_weather import get_weather
from core.geography import get_complete_geographic_info
from core.visualization.folium_maps import create_live_threat_map
from core.visualization.info_panels import add_threat_zones_info_panel
from core.utils.features import setup_computational_grid
from core.utils.zone_extraction import extract_zones
from core.utils import LiveLoopManager

# ============================================================================
# CONFIGURATION PARAMETERS
# ============================================================================

class ScenarioConfig:
    """Configuration parameters for the ammonia release scenario."""
    
    # Location Information
    TANK_LATITUDE = 31.691100
    TANK_LONGITUDE = 74.082167
    LOCATION_NAME = "Ammonia Tank - FFC Industrial Area"
    TIMEZONE_OFFSET_HRS = 5  # Pakistan Standard Time (UTC+5)
    
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
    NX = 500  # grid points in x-direction
    NY = 500  # grid points in y-direction
    
    # AEGL Thresholds (ppm)
    AEGL_THRESHOLDS = {
        'AEGL-1': 30,      # Mild discomfort threshold
        'AEGL-2': 160,     # Irreversible effects threshold
        'AEGL-3': 1100,    # Life-threatening threshold
    }
    
    # Monitoring Settings
    UPDATE_INTERVAL_SECONDS = 60  # Map refresh interval (1 minute)
    
    # Weather Settings
    USE_MANUAL_WEATHER = False  # Set to True for manual weather, False for realtime
    MANUAL_WIND_SPEED_MS = 1.5
    MANUAL_WIND_DIR_DEG = 90  # degrees (90 = from East)
    MANUAL_TEMPERATURE_K = 298.15  # Kelvin (25°C)
    MANUAL_HUMIDITY = 0.60  # 60%
    MANUAL_CLOUD_COVER = 0.20  # 20%


# Release Sources Configuration
RELEASE_SOURCES = [
    {
        'lat': ScenarioConfig.TANK_LATITUDE,
        'lon': ScenarioConfig.TANK_LONGITUDE,
        'name': 'Primary Ammonia Tank',
        'height': ScenarioConfig.TANK_HEIGHT,
        'rate': ScenarioConfig.RELEASE_RATE,
        'color': 'red'
    },
    # Additional sources can be added here
    # Example:
    # {
    #     'lat': ScenarioConfig.TANK_LATITUDE + 0.002,
    #     'lon': ScenarioConfig.TANK_LONGITUDE - 0.003,
    #     'name': 'Secondary Tank',
    #     'height': 2.5,
    #     'rate': 600,
    #     'color': 'orange'
    # }
]

# Points of Interest (POI) Configuration
POINTS_OF_INTEREST = [
    {
        'lat': 31.691100,
        'lon': 74.082167 + 0.01,
        'name': 'Central Hospital',
        'color': 'green',
        'icon': 'plus',
        'popup': 'Central Hospital - 500 beds<br>ICU available'
    },
    {
        'lat': 31.691100 + 0.009,
        'lon': 74.082167 + 0.009,
        'name': 'Primary School',
        'color': 'green',
        'icon': 'book',
        'popup': 'Primary School - 300 students'
    },
    {
        'lat': 31.691100 + 0.007,
        'lon': 74.082167 + 0.007,
        'name': 'Evacuation Zone A',
        'color': 'purple',
        'icon': 'arrow-right',
        'popup': 'Safe evacuation zone A<br>Capacity: 500 persons'
    },
    {
        'lat': 31.691100 + 0.015,
        'lon': 74.082167 + 0.015,
        'name': 'Fire Station',
        'color': 'darkred',
        'icon': 'fire',
        'popup': 'Fire Station - Emergency Response'
    },
    {
        'lat': 31.691100 + 0.01,
        'lon': 74.082167 + 0.01,
        'name': 'Monitoring Station',
        'color': 'blue',
        'icon': 'eye-open',
        'popup': 'Air Quality Monitoring Station'
    }
]

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def initialize_monitoring_system():
    """
    Initialize the monitoring system with geographic info and computational grid.
    
    Returns:
    --------
    tuple: (X, Y, output_html_path, geo_info)
        - X, Y: Computational grid arrays
        - output_html_path: Path to save HTML output
        - geo_info: Geographic information dictionary
    """
    print(f"\n{'='*90}")
    print("INITIALIZING REAL-TIME THREAT ZONE MONITORING SYSTEM")
    print(f"{'='*90}")
    print(f"Location: {ScenarioConfig.LOCATION_NAME}")
    print(f"Coordinates: {ScenarioConfig.TANK_LATITUDE}°N, {ScenarioConfig.TANK_LONGITUDE}°E")
    print(f"Update interval: {ScenarioConfig.UPDATE_INTERVAL_SECONDS} seconds")
    print(f"Weather mode: {'MANUAL' if ScenarioConfig.USE_MANUAL_WEATHER else 'REALTIME'}")
    print(f"Chemical: {ScenarioConfig.CHEMICAL_NAME}")
    print(f"Release rate: {ScenarioConfig.RELEASE_RATE} g/s")
    print(f"Press Ctrl+C to stop\n")
    
    # Get geographic information
    geo_info = get_complete_geographic_info(
        latitude=ScenarioConfig.TANK_LATITUDE,
        longitude=ScenarioConfig.TANK_LONGITUDE,
        fetch_online=False
    )
    print(f"Geographic Information:")
    print(f"  • Terrain: {geo_info.get('terrain', 'flat')}")
    print(f"  • Land use: {geo_info.get('land_use', 'urban')}")
    
    # Setup computational grid
    X, Y, _, _ = setup_computational_grid(
        ScenarioConfig.X_MAX,
        ScenarioConfig.Y_MAX,
        ScenarioConfig.NX,
        ScenarioConfig.NY
    )
    print(f"\nComputational Grid:")
    print(f"  • Extent: ±{ScenarioConfig.X_MAX}m × ±{ScenarioConfig.Y_MAX}m")
    print(f"  • Resolution: {ScenarioConfig.NX} × {ScenarioConfig.NY} points")
    print(f"  • Grid spacing: {2*ScenarioConfig.X_MAX/ScenarioConfig.NX:.1f}m")
    
    # Setup output file location
    temp_dir = tempfile.gettempdir()
    output_html = Path(temp_dir) / "ammonia_threat_zones_live.html"
    print(f"\nOutput location: {output_html}\n")
    
    return X, Y, output_html, geo_info


def fetch_realtime_weather(cycle=1):
    """
    Fetch current weather conditions from Open-Meteo API or use manual settings.
    
    Parameters:
    -----------
    cycle : int
        Current monitoring cycle number (optional, for demo purposes)
    
    Returns:
    --------
    dict: Weather data including wind speed, direction, temperature, etc.
    """
    if ScenarioConfig.USE_MANUAL_WEATHER:
        # Use manual weather settings
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Using manual weather settings...")
        
        # Optional: rotate wind direction for demo (can be disabled)
        # wind_dir = (ScenarioConfig.MANUAL_WIND_DIR_DEG + (cycle - 1) * 15) % 360
        wind_dir = ScenarioConfig.MANUAL_WIND_DIR_DEG
        
        weather = {
            'source': 'manual',
            'wind_speed': ScenarioConfig.MANUAL_WIND_SPEED_MS,
            'wind_dir': wind_dir,
            'temperature_K': ScenarioConfig.MANUAL_TEMPERATURE_K,
            'humidity': ScenarioConfig.MANUAL_HUMIDITY,
            'cloud_cover': ScenarioConfig.MANUAL_CLOUD_COVER,
        }
    else:
        # Fetch real-time weather from API
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Fetching real-time weather...")
        
        weather = get_weather(
            latitude=ScenarioConfig.TANK_LATITUDE,
            longitude=ScenarioConfig.TANK_LONGITUDE,
            source='open_meteo'
        )
    
    # Display weather information
    print(f"  ✓ Weather source: {weather.get('source', 'unknown')}")
    print(f"  • Wind: {weather['wind_speed']:.1f} m/s from {weather['wind_dir']:.0f}°")
    print(f"  • Temperature: {weather['temperature_K'] - 273.15:.1f}°C")
    print(f"  • Humidity: {weather['humidity']*100:.0f}%")
    print(f"  • Cloud cover: {weather['cloud_cover']*100:.0f}%")
    
    return weather


def calculate_dispersion_field(weather, X, Y):
    """
    Calculate concentration field using Gaussian dispersion model.
    
    Parameters:
    -----------
    weather : dict
        Weather data
    X, Y : ndarray
        Computational grid arrays
    
    Returns:
    --------
    tuple: (concentration, U_local, stability_class, resolved_sources)
    """
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
        sources=RELEASE_SOURCES,
        latitude=ScenarioConfig.TANK_LATITUDE,
        longitude=ScenarioConfig.TANK_LONGITUDE,
        timezone_offset_hrs=ScenarioConfig.TIMEZONE_OFFSET_HRS
    )
    
    return concentration, U_local, stability_class, resolved_sources


def generate_threat_map(weather, X, Y, concentration, U_local, stability_class, resolved_sources):
    """
    Generate interactive Folium threat zone map.
    
    Parameters:
    -----------
    weather : dict
        Weather data
    X, Y : ndarray
        Computational grid
    concentration : ndarray
        Concentration field (ppm)
    U_local : float
        Local wind speed
    stability_class : str
        Atmospheric stability class
    resolved_sources : list
        Source definitions with coordinates
    
    Returns:
    --------
    folium.Map: Interactive map object
    """
    map_obj = create_live_threat_map(
        weather=weather,
        X=X,
        Y=Y,
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
        markers=POINTS_OF_INTEREST
    )
    
    # Extract zones and add info panel
    zones = extract_zones(
        X, Y,
        concentration,
        ScenarioConfig.AEGL_THRESHOLDS,
        ScenarioConfig.TANK_LATITUDE,
        ScenarioConfig.TANK_LONGITUDE,
        wind_dir=weather['wind_dir'],
        verbose=False
    )
    
    add_threat_zones_info_panel(
        map_obj,
        zones,
        weather=weather,
        chemical_name=ScenarioConfig.CHEMICAL_NAME,
        thresholds=ScenarioConfig.AEGL_THRESHOLDS,
        source_lat=ScenarioConfig.TANK_LATITUDE,
        source_lon=ScenarioConfig.TANK_LONGITUDE,
        stability_class=stability_class,
        release_rate=ScenarioConfig.RELEASE_RATE,
        position='bottomleft'
    )
    
    return map_obj


def display_threat_summary(concentration, X, Y, weather):
    """
    Calculate and display threat zone summary using universal extract_zones.
    
    Parameters:
    -----------
    concentration : ndarray
        Concentration field (ppm)
    X, Y : ndarray
        Computational grid arrays
    weather : dict
        Weather data including wind direction
    """
    zones = extract_zones(
        X, Y,
        concentration,
        ScenarioConfig.AEGL_THRESHOLDS,
        ScenarioConfig.TANK_LATITUDE,
        ScenarioConfig.TANK_LONGITUDE,
        wind_dir=weather['wind_dir'],
        verbose=False
    )
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Threat Zone Summary:")
    for level, polygon in zones.items():
        if polygon is None:
            print(f"  • {level}: No threat zone detected")
        else:
            area_km2 = polygon.area * 111.32 * 110.57
            print(f"  • {level}: Active zone ({area_km2:.2f} km²)")


def run_monitoring_cycle():
    """
    Execute the main monitoring cycle with periodic updates.
    """
    # Initialize system
    X, Y, output_html, geo_info = initialize_monitoring_system()
    
    # Create live loop manager
    manager = LiveLoopManager(
        update_interval=ScenarioConfig.UPDATE_INTERVAL_SECONDS,
        output_file=output_html,
        app_name="pyELDQM Real-time Threat Zone Monitor"
    )
    
    for cycle in manager.run():
        try:
            # Step 1: Fetch weather (realtime or manual)
            weather = fetch_realtime_weather(cycle)
            
            # Step 2: Calculate dispersion
            concentration, U_local, stability_class, resolved_sources = calculate_dispersion_field(
                weather, X, Y
            )
            
            # Step 3: Display threat zone summary
            display_threat_summary(concentration, X, Y, weather)
            
            # Step 4: Generate and save map
            map_obj = generate_threat_map(
                weather, X, Y, concentration, U_local, stability_class, resolved_sources
            )
            map_obj.save(str(output_html))
            print(f"  ✓ Map updated: {output_html}")
            
            # Step 5: Open browser on first update
            manager.open_browser_once()
            
            # Step 6: Wait for next update
            manager.wait_for_next_cycle()
            
        except Exception as e:
            manager.handle_error(e)
            continue


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the real-time monitoring application."""
    # Display banner
    print("=" * 90)
    print("pyELDQM: REAL-TIME AMMONIA TANK THREAT ZONES")
    print("Live Weather Integration & Dynamic Hazard Mapping")
    print("=" * 90)
    
    try:
        run_monitoring_cycle()
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

