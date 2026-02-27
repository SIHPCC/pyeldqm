"""
Geographic Information Helper for pyELDQM

This module provides utilities to fetch geographic information needed for simulations:
- Latitude/Longitude (from address or facility name)
- Elevation
- Timezone
- Surface roughness estimation
- Terrain characteristics
- Local geographic data loading

Available Python packages for geographic data:
- geopy: Geocoding (address → lat/lon) and reverse geocoding
- timezonefinder: Get timezone from coordinates
- elevation: SRTM elevation data
- pytz: Timezone handling
- reverse_geocoder: Offline reverse geocoding

Installation:
    pip install geopy timezonefinder pytz

Optional (for elevation):
    pip install elevation
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Path to local geographic data JSON (now in data/geographic_data/)
GEO_DATA_PATH = Path(__file__).resolve().parents[2] / 'data' / 'geographic_data' / 'geographic_data.json'

# Default values
DEFAULT_GEO_DATA = {
    'terrain': 'flat',
    'land_use': 'urban',
    'elevation_m': 0.0,
    'latitude': None,
    'longitude': None,
    'timezone': 'UTC',
    'roughness': 'URBAN'
}


def load_local_geographic_data(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load geographic data from local JSON file.
    
    Parameters:
    -----------
    path : Optional[Path]
        Custom path to JSON file. If None, uses default path.
    
    Returns:
    --------
    dict : Geographic data with terrain, land_use, elevation, etc.
    """
    geo_path = path if path else GEO_DATA_PATH
    
    if not geo_path.exists():
        logger.warning(f"Geographic data file not found at {geo_path}, using defaults")
        return DEFAULT_GEO_DATA.copy()
    
    try:
        with open(geo_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Merge with defaults to ensure all keys exist
        return {**DEFAULT_GEO_DATA, **data}
    except Exception as e:
        logger.error(f"Failed to load geographic data: {e}")
        return DEFAULT_GEO_DATA.copy()


def save_geographic_data(data: Dict[str, Any], path: Optional[Path] = None) -> bool:
    """
    Save geographic data to local JSON file.
    
    Parameters:
    -----------
    data : dict
        Geographic data to save
    path : Optional[Path]
        Custom path to JSON file. If None, uses default path.
    
    Returns:
    --------
    bool : True if successful, False otherwise
    """
    geo_path = path if path else GEO_DATA_PATH
    
    try:
        with open(geo_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Geographic data saved to {geo_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save geographic data: {e}")
        return False


def geocode_address(address: str, provider: str = 'nominatim') -> Optional[Tuple[float, float]]:
    """
    Convert address to latitude/longitude coordinates.
    
    Requires: pip install geopy
    
    Parameters:
    -----------
    address : str
        Address or location name (e.g., "Karachi Port, Pakistan")
    provider : str
        Geocoding provider: 'nominatim' (free, OpenStreetMap), 
        'google' (requires API key), 'arcgis' (free)
    
    Returns:
    --------
    tuple : (latitude, longitude) or None if geocoding fails
    
    Examples:
    ---------
    coords = geocode_address("1600 Amphitheatre Parkway, Mountain View, CA")
    # Returns: (37.4224764, -122.0842499)
    """
    try:
        from geopy.geocoders import Nominatim, GoogleV3, ArcGIS
    except ImportError:
        logger.error("geopy not installed. Install with: pip install geopy")
        return None
    
    try:
        if provider == 'nominatim':
            geolocator = Nominatim(user_agent="pyELDQM")
        elif provider == 'google':
            # Requires GOOGLE_API_KEY environment variable
            import os
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                logger.error("GOOGLE_API_KEY not set in environment")
                return None
            geolocator = GoogleV3(api_key=api_key)
        elif provider == 'arcgis':
            geolocator = ArcGIS()
        else:
            logger.error(f"Unknown geocoding provider: {provider}")
            return None
        
        location = geolocator.geocode(address)
        if location:
            logger.info(f"Geocoded '{address}' to ({location.latitude}, {location.longitude})")
            return (location.latitude, location.longitude)
        else:
            logger.warning(f"Could not geocode address: {address}")
            return None
            
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return None


def reverse_geocode(latitude: float, longitude: float) -> Optional[Dict[str, str]]:
    """
    Get address information from coordinates.
    
    Requires: pip install geopy
    
    Parameters:
    -----------
    latitude : float
        Latitude in degrees
    longitude : float
        Longitude in degrees
    
    Returns:
    --------
    dict : Address components (country, state, city, etc.) or None
    
    Examples:
    ---------
    info = reverse_geocode(24.9, 67.1)
    # Returns: {'country': 'Pakistan', 'city': 'Karachi', ...}
    """
    try:
        from geopy.geocoders import Nominatim
    except ImportError:
        logger.error("geopy not installed. Install with: pip install geopy")
        return None
    
    try:
        geolocator = Nominatim(user_agent="pyELDQM")
        location = geolocator.reverse(f"{latitude}, {longitude}")
        
        if location and location.raw:
            address = location.raw.get('address', {})
            return {
                'country': address.get('country'),
                'state': address.get('state'),
                'city': address.get('city') or address.get('town') or address.get('village'),
                'postcode': address.get('postcode'),
                'formatted': location.address
            }
        return None
        
    except Exception as e:
        logger.error(f"Reverse geocoding error: {e}")
        return None


def get_timezone(latitude: float, longitude: float) -> Optional[str]:
    """
    Get timezone name from coordinates.
    
    Requires: pip install timezonefinder pytz
    
    Parameters:
    -----------
    latitude : float
        Latitude in degrees
    longitude : float
        Longitude in degrees
    
    Returns:
    --------
    str : Timezone name (e.g., 'Asia/Karachi') or None
    
    Examples:
    ---------
    tz = get_timezone(24.9, 67.1)
    # Returns: 'Asia/Karachi'
    """
    try:
        from timezonefinder import TimezoneFinder
    except ImportError:
        logger.error("timezonefinder not installed. Install with: pip install timezonefinder")
        return None
    
    try:
        tf = TimezoneFinder()
        timezone_name = tf.timezone_at(lat=latitude, lng=longitude)
        if timezone_name:
            logger.info(f"Timezone for ({latitude}, {longitude}): {timezone_name}")
        return timezone_name
    except Exception as e:
        logger.error(f"Timezone lookup error: {e}")
        return None


def get_elevation(latitude: float, longitude: float) -> Optional[float]:
    """
    Get elevation above sea level from coordinates.
    
    Requires: pip install elevation (and GDAL for some systems)
    Note: First use may download SRTM data tiles (~25MB per tile)
    
    Alternative: Use Open-Topo API without additional packages
    
    Parameters:
    -----------
    latitude : float
        Latitude in degrees
    longitude : float
        Longitude in degrees
    
    Returns:
    --------
    float : Elevation in meters or None
    
    Examples:
    ---------
    elev = get_elevation(24.9, 67.1)
    # Returns: ~10.0 (meters above sea level)
    """
    # Method 1: Use Open-Topo API (free, no packages needed)
    try:
        import requests
        
        url = f"https://api.open-elevation.com/api/v1/lookup"
        params = {
            "locations": f"{latitude},{longitude}"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['results']:
            elevation = data['results'][0]['elevation']
            logger.info(f"Elevation at ({latitude}, {longitude}): {elevation} m")
            return float(elevation)
    except Exception as e:
        logger.warning(f"Open-Elevation API error: {e}")
    
    # Method 2: Try SRTM elevation package if installed
    try:
        import elevation
        import tempfile
        from pathlib import Path
        
        # Create temporary file for DEM
        with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
            output_file = tmp.name
        
        # Download SRTM data
        bounds = (longitude - 0.01, latitude - 0.01, longitude + 0.01, latitude + 0.01)
        elevation.clip(bounds=bounds, output=output_file)
        
        # Read elevation value (requires rasterio)
        import rasterio
        with rasterio.open(output_file) as dataset:
            # Sample at the point
            vals = list(dataset.sample([(longitude, latitude)]))
            elev = float(vals[0][0])
            
        # Cleanup
        Path(output_file).unlink(missing_ok=True)
        logger.info(f"Elevation (SRTM) at ({latitude}, {longitude}): {elev} m")
        return elev
        
    except ImportError:
        logger.warning("elevation/rasterio not installed for SRTM data")
    except Exception as e:
        logger.error(f"SRTM elevation error: {e}")
    
    return None


def estimate_roughness(land_use: str = None, latitude: float = None, longitude: float = None) -> str:
    """
    Estimate surface roughness class for dispersion modeling.
    
    Parameters:
    -----------
    land_use : str, optional
        Land use type ('urban', 'suburban', 'rural', 'forest', 'water')
    latitude : float, optional
        Latitude (for automatic land use detection if available)
    longitude : float, optional
        Longitude (for automatic land use detection if available)
    
    Returns:
    --------
    str : Roughness class ('URBAN', 'SUBURBAN', 'RURAL')
    
    Mapping:
        urban → URBAN (z0 ~ 1 m)
        suburban → SUBURBAN (z0 ~ 0.3 m)
        rural/agricultural → RURAL (z0 ~ 0.1 m)
        forest → RURAL (z0 ~ 0.5-1 m)
        water/open → RURAL (z0 ~ 0.0002 m)
    """
    if land_use:
        land_use_lower = land_use.lower()
        if 'urban' in land_use_lower or 'city' in land_use_lower or 'industrial' in land_use_lower:
            return 'URBAN'
        elif 'suburb' in land_use_lower or 'residential' in land_use_lower:
            return 'SUBURBAN'
        else:
            return 'RURAL'
    
    # If coordinates provided, try to get land use from reverse geocoding
    if latitude and longitude:
        location_info = reverse_geocode(latitude, longitude)
        if location_info:
            city = location_info.get('city', '')
            if city:
                return 'URBAN'  # Has a city name -> likely urban
    
    # Default to suburban
    return 'SUBURBAN'


def get_complete_geographic_info(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    address: Optional[str] = None,
    fetch_online: bool = True
) -> Dict[str, Any]:
    """
    Get comprehensive geographic information for a location.
    
    Parameters:
    -----------
    latitude : float, optional
        Latitude in degrees
    longitude : float, optional
        Longitude in degrees
    address : str, optional
        Address to geocode (if lat/lon not provided)
    fetch_online : bool
        Whether to fetch data from online sources (elevation, timezone, etc.)
    
    Returns:
    --------
    dict : Complete geographic information including:
        - latitude, longitude
        - elevation_m
        - timezone
        - country, state, city
        - terrain
        - land_use
        - roughness
    
    Examples:
    ---------
    # Using coordinates
    info = get_complete_geographic_info(latitude=24.9, longitude=67.1)
    
    # Using address
    info = get_complete_geographic_info(address="Karachi Port, Pakistan")
    
    # Load from local file only
    info = get_complete_geographic_info(fetch_online=False)
    """
    # Start with local data
    geo_info = load_local_geographic_data()
    
    # Get coordinates
    if latitude is None or longitude is None:
        if address and fetch_online:
            coords = geocode_address(address)
            if coords:
                latitude, longitude = coords
                geo_info['latitude'] = latitude
                geo_info['longitude'] = longitude
        elif geo_info.get('latitude') and geo_info.get('longitude'):
            latitude = geo_info['latitude']
            longitude = geo_info['longitude']
    else:
        geo_info['latitude'] = latitude
        geo_info['longitude'] = longitude
    
    # Fetch additional data if coordinates available and online mode enabled
    if latitude and longitude and fetch_online:
        # Get location details
        location_info = reverse_geocode(latitude, longitude)
        if location_info:
            geo_info['country'] = location_info.get('country')
            geo_info['state'] = location_info.get('state')
            geo_info['city'] = location_info.get('city')
            geo_info['address'] = location_info.get('formatted')
        
        # Get timezone
        timezone = get_timezone(latitude, longitude)
        if timezone:
            geo_info['timezone'] = timezone
        
        # Get elevation
        elevation = get_elevation(latitude, longitude)
        if elevation is not None:
            geo_info['elevation_m'] = elevation
        
        # Estimate roughness if not already set
        if not geo_info.get('roughness') or geo_info['roughness'] == 'URBAN':
            geo_info['roughness'] = estimate_roughness(
                land_use=geo_info.get('land_use'),
                latitude=latitude,
                longitude=longitude
            )
    
    # Ensure roughness is set
    if not geo_info.get('roughness'):
        geo_info['roughness'] = estimate_roughness(land_use=geo_info.get('land_use'))
    
    return geo_info


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("Geographic Information Helper - Examples")
    print("=" * 80)
    
    # Example 1: Load local data
    print("\n1. Load local geographic data:")
    local_data = load_local_geographic_data()
    print(f"   {local_data}")
    
    # Example 2: Geocode an address
    print("\n2. Geocode address:")
    coords = geocode_address("Karachi Port, Pakistan")
    if coords:
        print(f"   Coordinates: {coords}")
    
    # Example 3: Get complete info
    print("\n3. Get complete geographic information:")
    info = get_complete_geographic_info(latitude=24.9, longitude=67.1, fetch_online=True)
    print(f"   Location: {info.get('city')}, {info.get('country')}")
    print(f"   Coordinates: ({info.get('latitude')}, {info.get('longitude')})")
    print(f"   Elevation: {info.get('elevation_m')} m")
    print(f"   Timezone: {info.get('timezone')}")
    print(f"   Roughness: {info.get('roughness')}")
    
    print("\n" + "=" * 80)
