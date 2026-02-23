"""
Weather Data Integration Guide for pyELDQM

This comprehensive example demonstrates how to fetch weather data from multiple
sources for use in pyELDQM simulations. Choose the source that best fits your
requirements: local files, free APIs, or professional weather services.

All methods return standardized weather parameters:
    - wind_speed (m/s)
    - wind_dir (degrees)
    - temperature_K (Kelvin)
    - humidity (0-1)
    - pressure (Pa)
    - source (data source identifier)

Quick Start:
    - Testing/Development:     Use 'local' or 'open_meteo'
    - Production (USA):        Use 'noaa' with 'open_meteo' backup
    - Production (Global):     Use 'open_meteo' with 'openweathermap' backup
    - No Internet:             Use 'local'

Run this file in an IDE that supports cell execution or interactive Python session.
"""

import sys
import os
from pathlib import Path

# Add parent directories to path for proper imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from pyELDQM.core.meteorology.realtime_weather import get_weather


# %%
# # 1. WEATHER SOURCE COMPARISON
# Quick overview of all available weather sources.

print("=" * 90)
print("WEATHER DATA SOURCES FOR pyELDQM SIMULATIONS")
print("=" * 90)

sources_overview = {
    'local': {
        'description': 'Local CSV files',
        'auth': 'None (use existing files)',
        'cost': 'Free',
        'coverage': 'Manual (your data)',
        'setup': 'Place CSV in data/weather_samples/',
        'best_for': 'Testing, reproducible scenarios',
        'key_advantage': 'Works offline, deterministic'
    },
    'open_meteo': {
        'description': 'Open-Meteo API (free)',
        'auth': 'None - completely free',
        'cost': 'Free',
        'coverage': 'Global',
        'setup': 'Just use it - pip install requests',
        'best_for': 'Development, research, global',
        'key_advantage': 'Free, no API key, reliable'
    },
    'openweathermap': {
        'description': 'OpenWeatherMap API',
        'auth': 'API Key required',
        'cost': 'Free (limited calls/day)',
        'coverage': 'Global',
        'setup': 'Get key at openweathermap.org, pip install pyowm',
        'best_for': 'Professional production systems',
        'key_advantage': 'High accuracy, professional support'
    },
    'weatherapi': {
        'description': 'WeatherAPI.com',
        'auth': 'API Key required',
        'cost': 'Free (limited calls/day)',
        'coverage': 'Global',
        'setup': 'Get key at weatherapi.com, pip install requests',
        'best_for': 'Production with cost control',
        'key_advantage': 'Good accuracy, affordable'
    },
    'noaa': {
        'description': 'NOAA Weather Service (USA)',
        'auth': 'None - completely free',
        'cost': 'Free',
        'coverage': 'USA only',
        'setup': 'Just use it - pip install requests',
        'best_for': 'USA emergency response, compliance',
        'key_advantage': 'Official govt data, no limits'
    }
}

print("\nSUMMARY TABLE:")
print("-" * 90)
print(f"{'Source':<18} {'Auth':<30} {'Cost':<30} {'Coverage':<15}")
print("-" * 90)

for source, info in sources_overview.items():
    print(f"{source:<18} {info['auth']:<30} {info['cost']:<30} {info['coverage']:<15}")
print("\n" + "=" * 90)
print("RECOMMENDATION MATRIX")
print("=" * 90)
print("""
Use Case                          | Recommended Sources
────────────────────────────────────────────────────────────────────────────────
Academic Research                 | open_meteo (primary), local (backup)
Development & Testing             | local or open_meteo
USA Emergency Response            | noaa (primary), open_meteo (backup)
International Emergency Response  | open_meteo (primary), weatherapi (backup)
Production System (Global)        | openweathermap or open_meteo + local
Offline Simulations               | local only
Cost-Critical Production          | open_meteo + weatherapi
High-Accuracy Requirements        | openweathermap + local validation
""")


# %%
# # 2. METHOD 1: LOCAL CSV FILES
# Best for: Testing, validation, offline operation, reproducible results

print("\n" + "=" * 90)
print("METHOD 1: LOCAL CSV FILES")
print("=" * 90)

print("\nUse Case: Testing and validation with known conditions")
print("Advantages: Offline, deterministic, full control")
print("Disadvantages: Manual data management, not real-time")

print("\n" + "-" * 90)
print("Example 1: Loading latest local weather data")
print("-" * 90)

weather_local = get_weather(source='local')

print(f"""
Weather Data Retrieved from Local CSV:
  Source:       {weather_local.get('source')}
  Wind Speed:   {weather_local['wind_speed']:.2f} m/s
  Wind Dir:     {weather_local['wind_dir']:.1f}°
  Temperature:  {weather_local['temperature_K']:.2f} K ({weather_local['temperature_K'] - 273.15:.1f}°C)
  Humidity:     {weather_local['humidity']:.1%}
  Pressure:     {weather_local['pressure']:.0f} Pa
""")

print("Setup Instructions:")
print("  1. Prepare CSV file with columns: wind_speed, wind_dir, temperature_K, humidity, pressure")
print("  2. Place in: pyELDQM/data/weather_samples/")
print("  3. Use latest file by date or specify manually")
print("\nExample CSV content:")
print("  wind_speed,wind_dir,temperature_K,humidity,pressure")
print("  5.0,270,298.15,0.65,101325")
print("  4.5,275,300.15,0.60,101200")

# %%
# # 3. METHOD 2: OPEN-METEO (FREE, NO AUTH)
# Best for: Development, research, global coverage without authentication

print("\n" + "=" * 90)
print("METHOD 2: OPEN-METEO API (FREE, NO AUTHENTICATION)")
print("=" * 90)

print("\nUse Case: Real-time global weather data with no setup")
print("Advantages: Free, no API key, global, reliable")
print("Disadvantages: Internet required, no historical data")

print("\n" + "-" * 90)
print("Example 2: Fetch real-time weather from Open-Meteo")
print("-" * 90)

# Multiple locations for demonstration
locations = {
    'Karachi, Pakistan': (24.9, 67.1),
    'Lahore, Pakistan': (31.5, 74.3),
    'Islamabad, Pakistan': (33.7, 73.1),
    'Dubai, UAE': (25.2, 55.3),
    'Beijing, China': (39.9, 116.4),
}

print("\nFetching weather for multiple locations...")
print()

weather_open_meteo = {}
for location_name, (lat, lon) in locations.items():
    weather = get_weather(source='open_meteo', latitude=lat, longitude=lon)
    weather_open_meteo[location_name] = weather
    
    status = "✓" if weather.get('source') == 'open_meteo' else "✗"
    print(f"{status} {location_name:25s} | Wind: {weather['wind_speed']:4.1f} m/s | "
          f"Temp: {weather['temperature_K'] - 273.15:5.1f}°C | Humidity: {weather['humidity']:5.0%}")

print("\nSetup Instructions:")
print("  1. Install requests: pip install requests")
print("  2. No API key needed!")
print("  3. Just call: get_weather(source='open_meteo', latitude=lat, longitude=lon)")

# %%
# # 4. METHOD 3: OPENWEATHERMAP (PROFESSIONAL)
# Best for: Production systems with professional requirements

print("\n" + "=" * 90)
print("METHOD 3: OPENWEATHERMAP API (PROFESSIONAL)")
print("=" * 90)

print("\nUse Case: Professional production systems")
print("Advantages: High accuracy, well-documented, global coverage")
print("Disadvantages: Requires API key, rate limits")

print("\n" + "-" * 90)
print("Example 3: Fetch weather from OpenWeatherMap")
print("-" * 90)

api_key_owm = os.getenv('OPENWEATHER_API_KEY', None)

if api_key_owm:
    weather_owm = get_weather(
        source='openweathermap',
        latitude=24.9,
        longitude=67.1,
        api_key=api_key_owm
    )
    
    print(f"""
OpenWeatherMap Weather Data:
  Wind Speed:   {weather_owm['wind_speed']:.2f} m/s
  Temperature:  {weather_owm['temperature_K'] - 273.15:.1f}°C
  Humidity:     {weather_owm['humidity']:.0%}
  Pressure:     {weather_owm['pressure'] / 100:.1f} hPa
  Source:       {weather_owm.get('source')}
""")
else:
    print("API Key not configured (OPENWEATHER_API_KEY environment variable)")
    print("Example data would be:")
    print("  Wind Speed:   5.23 m/s")
    print("  Temperature:  27.34°C")
    print("  Humidity:     68%")

print("\nSetup Instructions:")
print("  1. Go to https://openweathermap.org/api")
print("  2. Create free account")
print("  3. Get API key from dashboard")
print("  4. Set environment variable: set OPENWEATHER_API_KEY=your_key")
print("  5. Install pyowm: pip install pyowm")
print("  6. Call: get_weather(source='openweathermap', latitude, longitude, api_key)")

# %%
# # 5. METHOD 4: WEATHERAPI
# Best for: Cost-conscious production with good coverage

print("\n" + "=" * 90)
print("METHOD 4: WEATHERAPI (AFFORDABLE PROFESSIONAL)")
print("=" * 90)

print("\nUse Case: Production systems with cost optimization")
print("Advantages: Affordable pricing, good coverage, user-friendly")
print("Disadvantages: Requires API key, rate limits")

print("\n" + "-" * 90)
print("Example 4: Fetch weather from WeatherAPI")
print("-" * 90)

api_key_wa = os.getenv('WEATHERAPI_API_KEY', None)

if api_key_wa:
    weather_wa = get_weather(
        source='weatherapi',
        latitude=24.9,
        longitude=67.1,
        api_key=api_key_wa
    )
    
    print(f"""
WeatherAPI Weather Data:
  Wind Speed:   {weather_wa['wind_speed']:.2f} m/s
  Temperature:  {weather_wa['temperature_K'] - 273.15:.1f}°C
  Humidity:     {weather_wa['humidity']:.0%}
  Pressure:     {weather_wa['pressure'] / 100:.1f} hPa
  Source:       {weather_wa.get('source')}
""")
else:
    print("API Key not configured (WEATHERAPI_API_KEY environment variable)")
    print("Example data would be:")
    print("  Wind Speed:   4.89 m/s")
    print("  Temperature:  26.50°C")
    print("  Humidity:     65%")

print("\nSetup Instructions:")
print("  1. Go to https://www.weatherapi.com/")
print("  2. Create free account")
print("  3. Get API key from dashboard")
print("  4. Set environment variable: set WEATHERAPI_API_KEY=your_key")
print("  5. Install requests: pip install requests")
print("  6. Call: get_weather(source='weatherapi', latitude, longitude, api_key)")

# %%
# # 6. METHOD 5: NOAA (USA ONLY)
# Best for: USA-based operations, emergency response, regulatory compliance

print("\n" + "=" * 90)
print("METHOD 5: NOAA WEATHER SERVICE (USA ONLY)")
print("=" * 90)

print("\nUse Case: USA emergency response, compliance, official data")
print("Advantages: Official government data, free, no limits, no auth")
print("Disadvantages: USA only, no forecasting in basic implementation")

print("\n" + "-" * 90)
print("Example 5: Fetch weather from NOAA (US locations)")
print("-" * 90)

us_locations = {
    'Houston, TX': (29.8, -95.4),
    'Newark, NJ': (40.7, -74.2),
    'Memphis, TN': (35.1, -90.2),
}

print("\nFetching weather from NOAA for US locations...")
print()

for location_name, (lat, lon) in us_locations.items():
    weather = get_weather(source='noaa', latitude=lat, longitude=lon)
    status = "✓" if weather.get('source') == 'noaa' else "⚠"
    print(f"{status} {location_name:20s} | Wind: {weather['wind_speed']:4.1f} m/s | "
          f"Temp: {weather['temperature_K'] - 273.15:5.1f}°C")

print("\nSetup Instructions:")
print("  1. Install requests: pip install requests")
print("  2. No API key needed!")
print("  3. Just call: get_weather(source='noaa', latitude, longitude)")
print("\nLimitations:")
print("  • USA locations only (works within ~72°N, south of 25°N, -180° to 180°)")
print("  • NOAA coverage may be limited for international borders")
print("  • Use Open-Meteo for non-USA locations")


# %%
# # 7. PRACTICAL EXAMPLE: SIMULATIONS
# Show how to use weather data in actual dispersion simulations

print("\n" + "=" * 90)
print("PRACTICAL APPLICATION: CHEMICAL DISPERSION SIMULATION")
print("=" * 90)

print("\nScenario: Ammonia release simulation with real-time weather")
print("-" * 90)

# Get weather from best available source for this location (Karachi)
try:
    weather_sim = get_weather(source='open_meteo', latitude=24.9, longitude=67.1)
    source_used = weather_sim.get('source', 'unknown')
except:
    weather_sim = {
        'wind_speed': 5.0,
        'wind_dir': 270,
        'temperature_K': 298.15,
        'humidity': 0.5,
        'pressure': 101325,
        'source': 'default'
    }
    source_used = 'default (fallback)'

print(f"\nWeather Source Used: {source_used}")
print(f"""
Input Meteorological Conditions:
  Wind Speed:      {weather_sim['wind_speed']:.2f} m/s
  Wind Direction:  {weather_sim['wind_dir']:.1f}°
  Temperature:     {weather_sim['temperature_K']:.2f} K ({weather_sim['temperature_K'] - 273.15:.1f}°C)
  Humidity:        {weather_sim['humidity']:.1%}
  Pressure:        {weather_sim['pressure']:.0f} Pa
""")

# Simulate model parameters
print("Dispersion Model Parameters (Calculated):")
print(f"  Air Density:             {weather_sim['pressure'] / (287 * weather_sim['temperature_K']):.3f} kg/m³")
print(f"  Kinematic Viscosity:     1.5e-5 m²/s (temperature dependent)")
print(f"  Stability Class:         A-F (requires insolation data)")
print(f"  Plume Travel (1 hour):   ~{weather_sim['wind_speed'] * 3600 / 1000:.1f} km")


# %%
# # 8. HYBRID APPROACH: FALLBACK STRATEGY
# Recommended best practice for production systems

print("\n" + "=" * 90)
print("BEST PRACTICE: HYBRID WEATHER SYSTEM")
print("=" * 90)

print("""
Recommended Architecture for Reliability:

PRIMARY:       Open-Meteo (free, global, reliable)
    ↓ (if fails)
SECONDARY:     Local CSV or OpenWeatherMap (backup)
    ↓ (if fails)
FALLBACK:      Default values with warning

Implementation:
""")

def get_weather_reliable(latitude, longitude, location_name):
    """
    Example: Reliable weather fetching with fallback chain.
    """
    sources_to_try = [
        ('open_meteo', {'latitude': latitude, 'longitude': longitude}),
        ('local', {}),
    ]
    
    for source, kwargs in sources_to_try:
        try:
            weather = get_weather(source=source, **kwargs)
            if weather.get('source') != 'default':
                print(f"  ✓ {source:15s} succeeded")
                return weather
            else:
                print(f"  ✗ {source:15s} failed (trying next...)")
        except Exception as e:
            print(f"  ✗ {source:15s} error: {str(e)[:30]}...")
    
    print(f"  ✗ All sources failed, using defaults")
    return {
        'wind_speed': 5.0,
        'wind_dir': 270,
        'temperature_K': 298.15,
        'humidity': 0.5,
        'pressure': 101325,
        'source': 'default'
    }

print("\nFetching weather for Karachi with fallback chain:")
weather_hybrid = get_weather_reliable(24.9, 67.1, "Karachi Port")

print(f"\nFinal Weather Data (Source: {weather_hybrid.get('source')}):")
print(f"  Wind Speed:   {weather_hybrid['wind_speed']:.2f} m/s")
print(f"  Temperature:  {weather_hybrid['temperature_K'] - 273.15:.1f}°C")
