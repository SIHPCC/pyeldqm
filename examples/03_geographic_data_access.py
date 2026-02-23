"""
Geographic Data Access Tutorial

This tutorial demonstrates how to use the geographic helper to fetch and manage
geographic information for pyELDQM simulations.

Geographic data needed for simulations:
- Latitude/Longitude (for weather, solar radiation, stability class)
- Elevation (for atmospheric calculations)
- Timezone (for time-dependent calculations)
- Surface roughness (for dispersion modeling)
- Terrain type (for hazard assessment)

Run this file in an IDE that supports cell execution (VS Code with Python extension,
Jupyter, or Spyder) or execute sections manually in an interactive Python session.
"""

from datetime import datetime
import sys
import os
from pathlib import Path
import pytz

# Add parent directories to path for proper imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import geographic helper from core.geography
from core.geography import ( 
    load_local_geographic_data,
    save_geographic_data,
    geocode_address,
    reverse_geocode,
    get_timezone,
    get_elevation,
    estimate_roughness,
    get_complete_geographic_info
)


# %%
# # 1. Load Local Geographic Data
# Read geographic data stored in geographic_data.json

print("=" * 80)
print("1. LOAD LOCAL GEOGRAPHIC DATA")
print("=" * 80)

local_data = load_local_geographic_data()

print("\nLocal Geographic Data:")
for key, value in local_data.items():
    print(f"  {key:20s}: {value}")

print("\nUse this for:")
print("  - Quick access to pre-configured site data")
print("  - Offline simulations")
print("  - Default values when online services unavailable")


# %%
# # 2. Geocode an Address
# Convert address or place name to latitude/longitude coordinates

print("\n" + "=" * 80)
print("2. GEOCODE ADDRESS TO COORDINATES")
print("=" * 80)

# Example addresses
addresses = [
    "Karachi Port, Pakistan",
    "Houston Ship Channel, Texas",
    "Singapore Port",
    "Rotterdam Port, Netherlands"
]

print("\nGeocoding addresses to coordinates:")
print("-" * 80)

geocoded_locations = {}
for address in addresses:
    coords = geocode_address(address)
    if coords:
        geocoded_locations[address] = coords
        print(f"[OK] {address:40s} -> ({coords[0]:.4f}, {coords[1]:.4f})")
    else:
        print(f"[FAIL] {address:40s} -> Failed")

print("\nNote: Uses OpenStreetMap Nominatim (free, no API key required)")


# %%
# # 3. Reverse Geocode Coordinates
# Get location information from latitude/longitude

print("\n" + "=" * 80)
print("3. REVERSE GEOCODE: COORDINATES TO LOCATION INFO")
print("=" * 80)

# Example coordinates
test_coords = [
    (24.85, 67.0, "Karachi Port"),
    (29.76, -95.37, "Houston Ship Channel"),
    (1.29, 103.85, "Singapore"),
]

print("\nReverse geocoding coordinates:")
print("-" * 80)

for lat, lon, name in test_coords:
    location_info = reverse_geocode(lat, lon)
    if location_info:
        print(f"\n{name} ({lat}°, {lon}°):")
        print(f"  City:     {location_info.get('city')}")
        print(f"  State:    {location_info.get('state')}")
        print(f"  Country:  {location_info.get('country')}")
        print(f"  Address:  {location_info.get('formatted')[:60]}...")
    else:
        print(f"\n{name}: Reverse geocoding failed")


# %%
# # 4. Get Timezone Information
# Determine timezone from coordinates for time-dependent calculations

print("\n" + "=" * 80)
print("4. GET TIMEZONE FROM COORDINATES")
print("=" * 80)

print("\nTimezone lookup for various locations:")
print("-" * 80)

timezone_locations = [
    (24.9, 67.1, "Karachi"),
    (40.7, -74.0, "New York"),
    (51.5, -0.1, "London"),
    (35.7, 139.7, "Tokyo"),
]

for lat, lon, city in timezone_locations:
    tz = get_timezone(lat, lon)
    if tz:
        print(f"  {city:20s} ({lat:6.2f}, {lon:7.2f}) -> {tz}")
    else:
        print(f"  {city:20s} -> Timezone lookup failed")

print("\nUse timezone for:")
print("  - Solar radiation calculations")
print("  - Time-dependent atmospheric stability")
print("  - Accurate time conversion in reports")


# %%
# # 5. Get Elevation Data
# Fetch elevation above sea level for atmospheric calculations

print("\n" + "=" * 80)
print("5. GET ELEVATION FROM COORDINATES")
print("=" * 80)

print("\nElevation lookup (using Open-Elevation API):")
print("-" * 80)

elevation_locations = [
    (24.9, 67.1, "Karachi (coastal)"),
    (29.76, -95.37, "Houston (coastal)"),
    (39.74, -104.99, "Denver (high altitude)"),
    (27.99, 86.93, "Mt. Everest Base Camp"),
]

for lat, lon, description in elevation_locations:
    elev = get_elevation(lat, lon)
    if elev is not None:
        print(f"  {description:30s} -> {elev:7.1f} m")
    else:
        print(f"  {description:30s} -> Elevation lookup failed")

print("\nUse elevation for:")
print("  - Atmospheric pressure calculations")
print("  - Air density corrections")
print("  - Terrain-aware dispersion modeling")


# %%
# # 6. Estimate Surface Roughness
# Determine roughness class for dispersion modeling

print("\n" + "=" * 80)
print("6. ESTIMATE SURFACE ROUGHNESS")
print("=" * 80)

print("\nRoughness estimation from land use type:")
print("-" * 80)

land_use_types = [
    "urban",
    "suburban",
    "rural",
    "forest",
    "industrial",
    "residential",
    "agricultural"
]

for land_use in land_use_types:
    roughness = estimate_roughness(land_use=land_use)
    print(f"  {land_use:20s} -> {roughness}")

print("\nRoughness Classes:")
print("  URBAN:     z0 ~ 1.0 m    (cities, industrial areas)")
print("  SUBURBAN:  z0 ~ 0.3 m    (residential, small towns)")
print("  RURAL:     z0 ~ 0.1 m    (farmland, grassland, water)")

print("\nUse in dispersion models:")
print("  - Affects vertical wind profile")
print("  - Influences plume spread")
print("  - Critical for accurate concentration predictions")


# %%
# # 7. Get Complete Geographic Information
# All-in-one function to fetch comprehensive data

print("\n" + "=" * 80)
print("7. GET COMPLETE GEOGRAPHIC INFORMATION")
print("=" * 80)

print("\nExample 1: From coordinates")
print("-" * 80)

info_karachi = get_complete_geographic_info(
    latitude=24.9,
    longitude=67.1,
    fetch_online=True
)

print(f"\nComplete Geographic Info for Karachi:")
print(f"  Latitude:       {info_karachi.get('latitude')}")
print(f"  Longitude:      {info_karachi.get('longitude')}")
print(f"  City:           {info_karachi.get('city')}")
print(f"  Country:        {info_karachi.get('country')}")
print(f"  Elevation:      {info_karachi.get('elevation_m')} m")
print(f"  Timezone:       {info_karachi.get('timezone')}")
print(f"  Terrain:        {info_karachi.get('terrain')}")
print(f"  Land Use:       {info_karachi.get('land_use')}")
print(f"  Roughness:      {info_karachi.get('roughness')}")

print("\n\nExample 2: From address")
print("-" * 80)

info_houston = get_complete_geographic_info(
    address="Houston Ship Channel, Texas",
    fetch_online=True
)

if info_houston:
    print(f"\nComplete Geographic Info for Houston:")
    print(f"  Latitude:       {info_houston.get('latitude')}")
    print(f"  Longitude:      {info_houston.get('longitude')}")
    print(f"  City:           {info_houston.get('city')}")
    print(f"  State:          {info_houston.get('state')}")
    print(f"  Country:        {info_houston.get('country')}")
    print(f"  Elevation:      {info_houston.get('elevation_m')} m")
    print(f"  Timezone:       {info_houston.get('timezone')}")
    print(f"  Roughness:      {info_houston.get('roughness')}")




# %%
# # 10. Date and Time Information with Timezone
# Get current date/time and demonstrate timezone conversions

print("\n" + "=" * 80)
print("9. DATE AND TIME INFORMATION WITH TIMEZONE")
print("=" * 80)

# Get current UTC time
utc_now = datetime.now(pytz.UTC)

# Get geographic data with timezone
site_info = get_complete_geographic_info(
    latitude=24.9,
    longitude=67.1,
    fetch_online=True
)
site_timezone_str = site_info.get('timezone', 'Asia/Karachi')

print(f"\nLocation: {site_info.get('city')}, {site_info.get('country')}")
print(f"Timezone: {site_timezone_str}")
print("-" * 80)

# Convert to local timezone
site_timezone = pytz.timezone(site_timezone_str)
local_time = utc_now.astimezone(site_timezone)

# Extract date and time components
print("\n1. DATE COMPONENTS:")
print(f"   Year:  {local_time.year}")
print(f"   Month: {local_time.month} ({local_time.strftime('%B')})")
print(f"   Date:  {local_time.day}")
print(f"   Full Date: {local_time.strftime('%Y-%m-%d')}")

print("\n2. TIME COMPONENTS:")
print(f"   Hour:   {local_time.hour}")
print(f"   Minute: {local_time.minute}")
print(f"   Second: {local_time.second}")

print("\n3. TIME FORMATS:")
# Military time format (1400 hrs)
military_time = local_time.strftime('%H%M')
print(f"   Military Time:   {military_time} hrs")
print(f"   24-Hour Format:  {local_time.strftime('%H:%M:%S')}")
print(f"   12-Hour Format:  {local_time.strftime('%I:%M:%S %p')}")

print("\n4. TIMEZONE CONVERSION:")
print(f"   UTC Time:        {utc_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"   Local Time:      {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"   Time Offset:     UTC{local_time.strftime('%z')}")

# Example: Time at different locations
print("\n5. MULTI-LOCATION TIME COMPARISON:")
print("-" * 80)

locations = [
    ("Karachi, Pakistan", 24.9, 67.1),
    ("Houston, Texas", 29.76, -95.37),
    ("Singapore", 1.35, 103.82),
    ("Rotterdam, Netherlands", 51.92, 4.48)
]

for location_name, lat, lon in locations:
    geo_info = get_complete_geographic_info(latitude=lat, longitude=lon, fetch_online=True)
    tz_str = geo_info.get('timezone', 'UTC')
    tz = pytz.timezone(tz_str)
    location_time = utc_now.astimezone(tz)
    
    print(f"   {location_name:25s}: {location_time.strftime('%H%M')} hrs ({location_time.strftime('%I:%M %p %Z')})")

print("\n6. USE IN SIMULATIONS:")
print("-" * 80)
print(f"   For solar radiation calculations:")
print(f"   - Date: {local_time.strftime('%Y-%m-%d')} (for solar declination)")
print(f"   - Time: {military_time} hrs (for solar angle)")
print(f"   - Hour angle = 15 deg * (solar_time - 12)")
print(f"")
print(f"   For stability class determination:")
print(f"   - Hour: {local_time.hour} (for day/night classification)")
print(f"   - Cloud cover time-dependent")
print(f"   - Solar radiation varies with time of day")


# %%
# # 9. Save Geographic Data Locally
# Store geographic data for offline use and faster access

print("\n" + "=" * 80)
print("8. SAVE GEOGRAPHIC DATA FOR REUSE")
print("=" * 80)

# Get current time for this facility
utc_time = datetime.now(pytz.UTC)
facility_tz = pytz.timezone('Asia/Karachi')
facility_local_time = utc_time.astimezone(facility_tz)

# Create custom geographic data for a facility
facility_data = {
    'facility_name': 'Karachi Chemical Complex',
    'latitude': 24.85,
    'longitude': 67.05,
    'elevation_m': 12.0,
    'timezone': 'Asia/Karachi',
    'terrain': 'flat',
    'land_use': 'industrial',
    'roughness': 'URBAN',
    'country': 'Pakistan',
    'city': 'Karachi',
    'date': facility_local_time.strftime('%Y-%m-%d'),
    'time': facility_local_time.strftime('%H%M'),
    'datetime_local': facility_local_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
    'notes': 'Coastal petrochemical facility'
}

print("\nSaving facility geographic data:")
for key, value in facility_data.items():
    print(f"  {key:20s}: {value}")

# Save to custom location
custom_path = Path(parent_dir) / 'data' / 'geographic_data' / 'facility_karachi.json'
success = save_geographic_data(facility_data, path=custom_path)

if success:
    print(f"\n[OK] Data saved to: {custom_path}")
else:
    print(f"\n[FAIL] Failed to save data")

print("\nBenefit: Faster load times, offline access, version control")

# %%
# # 10. Offline vs Online Mode
# Comparison of data access modes

print("\n" + "=" * 80)
print("10. OFFLINE VS ONLINE MODE COMPARISON")
print("=" * 80)

print("\nOFFLINE MODE (fetch_online=False):")
print("-" * 80)

offline_info = get_complete_geographic_info(fetch_online=False)
print("\nData from local JSON file only:")
for key, value in offline_info.items():
    print(f"  {key:20s}: {value}")

print("\n\nONLINE MODE (fetch_online=True):")
print("-" * 80)

online_info = get_complete_geographic_info(
    latitude=24.9,
    longitude=67.1,
    fetch_online=True
)
print("\nData fetched from online services:")
print(f"  Location:   {online_info.get('city')}, {online_info.get('country')}")
print(f"  Elevation:  {online_info.get('elevation_m')} m (from Open-Elevation API)")
print(f"  Timezone:   {online_info.get('timezone')} (from TimezoneFinder)")
print(f"  Address:    {online_info.get('address', 'N/A')[:60]}... (from Nominatim)")

