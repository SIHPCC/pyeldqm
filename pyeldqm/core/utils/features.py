import numpy as np
import folium
from folium import plugins


def add_wind_direction_arrow(map_obj, source_lat, source_lon, wind_direction, arrow_length=0.01):
    """
    Add a wind direction arrow to a Folium map.
    
    The arrow points in the direction the wind is coming FROM (meteorological convention).
    
    Parameters:
    -----------
    map_obj : folium.Map
        The Folium map object to add the arrow to
    source_lat : float
        Latitude of the source/starting point
    source_lon : float
        Longitude of the source/starting point
    wind_direction : float
        Wind direction in degrees (0° = from North, 90° = from East, etc.)
    arrow_length : float, optional
        Length of the arrow in degrees (default: 0.01)
    
    Returns:
    --------
    folium.FeatureGroup
        Feature group containing the wind direction arrow
    """
    wind_fg = folium.FeatureGroup(name='Wind Direction', show=True)
    
    # Calculate arrow endpoint using meteorological wind convention
    arrow_end_lat = source_lat + arrow_length * np.cos(np.radians(wind_direction))
    arrow_end_lon = source_lon + arrow_length * np.sin(np.radians(wind_direction))
    
    # Add AntPath (animated arrow line) instead of regular polyline
    plugins.AntPath(
        locations=[[source_lat, source_lon], [arrow_end_lat, arrow_end_lon]],
        color='green',
        weight=3,
        opacity=0.8,
        popup=f'Wind from {wind_direction:.0f}°',
        tooltip=f'Wind direction: {wind_direction:.0f}°'
    ).add_to(wind_fg)
    
    wind_fg.add_to(map_obj)
    return wind_fg


def setup_computational_grid(x_max, y_max, nx, ny):
    """Create computational grid in local coordinates (meters)."""
    x_vals = np.linspace(-x_max, x_max, nx)
    y_vals = np.linspace(-y_max, y_max, ny)
    X, Y = np.meshgrid(x_vals, y_vals)
    return X, Y, x_vals, y_vals
