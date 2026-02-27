"""
Real-time weather data module for pyELDQM.

Supports multiple weather data sources:
1. LOCAL: Read from sample CSV files
2. OPEN_METEO: Free API from open-meteo.com (no auth needed)
3. OPENWEATHERMAP: pyowm package (requires API key)
4. WEATHERAPI: weatherapi.com API (requires API key)
5. NOAA: US National Weather Service (free, US only)
"""
import csv
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parents[2] / 'data' / 'weather_samples'

# Default weather values (fallback)
DEFAULT_WEATHER = {
    'wind_speed': 5.0,
    'wind_dir': 270,
    'temperature_K': 298.15,
    'humidity': 0.5,
    'pressure': 101325,
    'cloud_cover': 0.5,  # fraction (0-1)
    'source': 'default'
}


def latest_sample() -> Dict[str, Any]:
    """Read from local sample CSV files (existing method)."""
    files = sorted(DATA_PATH.glob('*.csv'))
    if not files:
        logger.warning("No local CSV files found, using default values")
        return DEFAULT_WEATHER
    
    with files[-1].open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            logger.warning("Empty CSV file, using default values")
            return DEFAULT_WEATHER
        last = rows[-1]
        return {
            'wind_speed': float(last.get('wind_speed', 5.0)),
            'wind_dir': float(last.get('wind_dir', 270)),
            'temperature_K': float(last.get('temperature_K', 298.15)),
            'humidity': float(last.get('humidity', 0.5)),
            'pressure': float(last.get('pressure', 101325)),
            'cloud_cover': float(last.get('cloud_cover', 0.5)),
            'source': 'local_csv'
        }


def get_weather_open_meteo(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Fetch weather from Open-Meteo API (free, no authentication required).
    
    Parameters:
    -----------
    latitude : float
        Location latitude
    longitude : float
        Location longitude
    
    Returns:
    --------
    dict : Weather parameters including wind_speed, wind_dir, temperature_K, humidity, pressure
    """
    try:
        import requests
    except ImportError:
        logger.error("requests package not found. Install with: pip install requests")
        return DEFAULT_WEATHER
    
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m,wind_direction_10m,pressure_msl,cloud_cover",
            "temperature_unit": "celsius",
            "wind_speed_unit": "ms",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data['current']
        
        return {
            'wind_speed': float(current.get('wind_speed_10m', 5.0)),
            'wind_dir': float(current.get('wind_direction_10m', 270)),
            'temperature_K': float(current.get('temperature_2m', 25.0)) + 273.15,
            'humidity': float(current.get('relative_humidity_2m', 50)) / 100,
            'pressure': float(current.get('pressure_msl', 101325)) * 100,  # Convert hPa to Pa
            'cloud_cover': float(current.get('cloud_cover', 50)) / 100,
            'source': 'open_meteo'
        }
    except Exception as e:
        logger.error(f"Error fetching from Open-Meteo: {e}")
        return DEFAULT_WEATHER


def get_weather_openweathermap(latitude: float, longitude: float, api_key: str) -> Dict[str, Any]:
    """
    Fetch weather from OpenWeatherMap API using pyowm package.
    
    Requires: pip install pyowm
    Get API key from: https://openweathermap.org/api
    
    Parameters:
    -----------
    latitude : float
        Location latitude
    longitude : float
        Location longitude
    api_key : str
        OpenWeatherMap API key
    
    Returns:
    --------
    dict : Weather parameters
    """
    try:
        from pyowm import OWM
    except ImportError:
        logger.error("pyowm package not found. Install with: pip install pyowm")
        return DEFAULT_WEATHER
    
    try:
        owm = OWM(api_key)
        mgr = owm.weather_manager()
        observation = mgr.weather_at_coords(latitude, longitude)
        weather = observation.weather
        
        return {
            'wind_speed': float(weather.wind().get('speed', 5.0)),
            'wind_dir': float(weather.wind().get('deg', 270)),
            'temperature_K': float(weather.temperature('kelvin').get('temp', 298.15)),
            'humidity': float(weather.humidity) / 100,
            'pressure': float(weather.pressure.get('press', 1013.25)) * 100,  # Convert hPa to Pa
            'cloud_cover': float(weather.clouds or 0) / 100,
            'source': 'openweathermap'
        }
    except Exception as e:
        logger.error(f"Error fetching from OpenWeatherMap: {e}")
        return DEFAULT_WEATHER


def get_weather_weatherapi(latitude: float, longitude: float, api_key: str) -> Dict[str, Any]:
    """
    Fetch weather from weatherapi.com API.
    
    Requires: pip install requests
    Get API key from: https://www.weatherapi.com/
    
    Parameters:
    -----------
    latitude : float
        Location latitude
    longitude : float
        Location longitude
    api_key : str
        WeatherAPI API key
    
    Returns:
    --------
    dict : Weather parameters
    """
    try:
        import requests
    except ImportError:
        logger.error("requests package not found. Install with: pip install requests")
        return DEFAULT_WEATHER
    
    try:
        url = "http://api.weatherapi.com/v1/current.json"
        params = {
            "key": api_key,
            "q": f"{latitude},{longitude}",
            "aqi": "no"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data['current']
        
        return {
            'wind_speed': float(current.get('wind_mps', 5.0)),
            'wind_dir': float(current.get('wind_degree', 270)),
            'temperature_K': float(current.get('temp_c', 25)) + 273.15,
            'humidity': float(current.get('humidity', 50)) / 100,
            'pressure': float(current.get('pressure_mb', 1013.25)) * 100,  # Convert mb to Pa
            'cloud_cover': float(current.get('cloud', 0)) / 100,
            'source': 'weatherapi'
        }
    except Exception as e:
        logger.error(f"Error fetching from WeatherAPI: {e}")
        return DEFAULT_WEATHER


def get_weather_noaa(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Fetch weather from NOAA (US National Weather Service).
    Works best for locations within the USA.
    
    Requires: pip install requests
    
    Parameters:
    -----------
    latitude : float
        Location latitude
    longitude : float
        Location longitude
    
    Returns:
    --------
    dict : Weather parameters
    """
    try:
        import requests
    except ImportError:
        logger.error("requests package not found. Install with: pip install requests")
        return DEFAULT_WEATHER
    
    try:
        # First, get the grid point for the coordinates
        points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
        points_response = requests.get(points_url, timeout=10)
        points_response.raise_for_status()
        points_data = points_response.json()
        
        # Get the forecast URL from the points data
        forecast_url = points_data['properties']['forecast']
        forecast_response = requests.get(forecast_url, timeout=10)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        
        current = forecast_data['properties']['periods'][0]
        
        # Extract wind speed and direction from text
        wind_text = current.get('windSpeed', '5 mph')
        wind_speed_mph = float(wind_text.split()[0]) if wind_text else 5.0
        wind_speed = wind_speed_mph * 0.44704  # Convert mph to m/s
        
        wind_dir_text = current.get('windDirection', 'W')
        wind_directions = {'N': 0, 'NE': 45, 'E': 90, 'SE': 135, 
                          'S': 180, 'SW': 225, 'W': 270, 'NW': 315}
        wind_dir = float(wind_directions.get(wind_dir_text, 270))
        
        return {
            'wind_speed': wind_speed,
            'wind_dir': wind_dir,
            'temperature_K': float(current.get('temperature', 25)) + 273.15,
            'humidity': 0.5,  # NOAA API doesn't always provide humidity
            'pressure': 101325,
            'cloud_cover': 0.5,
            'source': 'noaa'
        }
    except Exception as e:
        logger.error(f"Error fetching from NOAA: {e}")
        return DEFAULT_WEATHER


def get_weather(
    source: str = 'local',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified weather fetching function.
    
    Parameters:
    -----------
    source : str, optional
        Weather data source: 'local', 'open_meteo', 'openweathermap', 'weatherapi', 'noaa'
        Default: 'local'
    latitude : float, optional
        Location latitude (required for API sources)
    longitude : float, optional
        Location longitude (required for API sources)
    api_key : str, optional
        API key (required for openweathermap and weatherapi)
    
    Returns:
    --------
    dict : Weather parameters
    
    Examples:
    ---------
    # Local CSV
    weather = get_weather(source='local')
    
    # Open-Meteo (free, no key needed)
    weather = get_weather(source='open_meteo', latitude=24.9, longitude=67.1)
    
    # OpenWeatherMap (requires API key)
    weather = get_weather(source='openweathermap', latitude=24.9, longitude=67.1, 
                         api_key='your_api_key')
    """
    source = source.lower()
    
    if source == 'local':
        return latest_sample()
    elif source == 'open_meteo':
        if latitude is None or longitude is None:
            logger.error("latitude and longitude required for open_meteo source")
            return DEFAULT_WEATHER
        return get_weather_open_meteo(latitude, longitude)
    elif source == 'openweathermap':
        if latitude is None or longitude is None or api_key is None:
            logger.error("latitude, longitude, and api_key required for openweathermap source")
            return DEFAULT_WEATHER
        return get_weather_openweathermap(latitude, longitude, api_key)
    elif source == 'weatherapi':
        if latitude is None or longitude is None or api_key is None:
            logger.error("latitude, longitude, and api_key required for weatherapi source")
            return DEFAULT_WEATHER
        return get_weather_weatherapi(latitude, longitude, api_key)
    elif source == 'noaa':
        if latitude is None or longitude is None:
            logger.error("latitude and longitude required for noaa source")
            return DEFAULT_WEATHER
        return get_weather_noaa(latitude, longitude)
    else:
        logger.error(f"Unknown weather source: {source}")
        return DEFAULT_WEATHER
