"""
Folium Interactive Mapping for pyELDQM
========================================

This module provides interactive web-based mapping capabilities using Folium
for visualizing dispersion model results on real geographic maps.

Features:
- Convert concentration grids to geographic coordinates
- Overlay AEGL/ERPG threshold contours on maps
- Add wind direction indicators
- Create heat maps of concentration distributions
- Export to interactive HTML for sharing and reporting

Dependencies:
    pip install folium scikit-image branca

Author: pyELDQM Development Team
"""

import folium
from folium import plugins
import numpy as np
from typing import Dict, Tuple, List, Optional, Any, Iterable
import logging
from ..utils.geo_constants import METERS_PER_DEGREE_LAT

logger = logging.getLogger(__name__)

# Color schemes for hazard levels
HAZARD_COLORS = {
    'AEGL-1': '#FFFF00',  # Yellow - Mild discomfort
    'AEGL-2': '#FFA500',  # Orange - Irreversible effects
    'AEGL-3': '#FF0000',  # Red - Life-threatening
    'ERPG-1': '#90EE90',  # Light green
    'ERPG-2': '#FFD700',  # Gold
    'ERPG-3': '#FF4500',  # Orange-red
    'IDLH': '#8B0000',    # Dark red - Immediately dangerous
    'LOC': '#FF69B4',     # Hot pink - Loss of consciousness
}


def create_dispersion_map(
    source_lat: float,
    source_lon: float,
    x_grid: np.ndarray,
    y_grid: np.ndarray,
    concentration: np.ndarray,
    thresholds: Dict[str, float],
    wind_direction: float = 0,
    zoom_start: int = 12,
    chemical_name: str = "Chemical",
    source_height: float = 0,
    wind_speed: float = None,
    stability_class: str = None,
    include_heatmap: bool = True,
    include_compass: bool = True
) -> folium.Map:
    """
    Create interactive Folium map with dispersion contours overlaid on real geography.
    
    Parameters:
    -----------
    source_lat : float
        Latitude of release source (degrees)
    source_lon : float
        Longitude of release source (degrees)
    x_grid : np.ndarray
        2D array of downwind distances (meters)
    y_grid : np.ndarray
        2D array of crosswind distances (meters)
    concentration : np.ndarray
        2D array of concentration values (ppm or mg/m³)
    thresholds : Dict[str, float]
        Dictionary of threshold levels, e.g., {'AEGL-1': 30, 'AEGL-2': 160}
    wind_direction : float, optional
        Wind direction in degrees from north (0=north, 90=east), default=0
    zoom_start : int, optional
        Initial zoom level for map, default=12
    chemical_name : str, optional
        Name of chemical for labeling
    source_height : float, optional
        Release height in meters
    wind_speed : float, optional
        Wind speed in m/s for display
    stability_class : str, optional
        Atmospheric stability class (A-F)
    include_heatmap : bool, optional
        Whether to include concentration heat map layer, default=True
    include_compass : bool, optional
        Whether to overlay a simple N/E/S/W compass, default=True
    
    Returns:
    --------
    folium.Map
        Interactive map object that can be saved to HTML
    
    Examples:
    ---------
    >>> m = create_dispersion_map(
    ...     source_lat=24.85,
    ...     source_lon=67.05,
    ...     x_grid=X,
    ...     y_grid=Y,
    ...     concentration=C_ppm,
    ...     thresholds={'AEGL-1': 30, 'AEGL-2': 160, 'AEGL-3': 1100},
    ...     wind_direction=45,
    ...     chemical_name='Ammonia'
    ... )
    >>> m.save('dispersion_map.html')
    """
    
    logger.info(f"Creating Folium map for {chemical_name} dispersion at ({source_lat}, {source_lon})")
    
    # Convert meter-based grid to geographic coordinates
    lat_grid, lon_grid = meters_to_latlon(
        x_grid, y_grid, source_lat, source_lon, wind_direction
    )
    
    # Create base map
    m = folium.Map(
        location=[source_lat, source_lon],
        zoom_start=zoom_start,
        tiles='CartoDB dark_matter',
        name='cartodbdarkmatter',
        control_scale=False
    )
    
    # Add alternative tile layers
    folium.TileLayer('CartoDB positron', name='Day Map').add_to(m)
    folium.TileLayer('OpenStreetMap', name='Street Map').add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Create feature groups for organization
    source_group = folium.FeatureGroup(name='Release Sources', show=True)
    wind_group = folium.FeatureGroup(name='Wind Direction', show=True)
    
    # Add source marker with detailed popup
    popup_html = f"""
    <div style="font-family: Arial; font-size: 12px; width: 200px;">
        <h4 style="margin: 0 0 10px 0; color: #d32f2f;">{chemical_name} Release</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><td><b>Location:</b></td><td>{source_lat:.4f}°N, {source_lon:.4f}°E</td></tr>
            <tr><td><b>Height:</b></td><td>{source_height} m</td></tr>
            {f'<tr><td><b>Wind Speed:</b></td><td>{wind_speed} m/s</td></tr>' if wind_speed else ''}
            {f'<tr><td><b>Stability:</b></td><td>Class {stability_class}</td></tr>' if stability_class else ''}
        </table>
    </div>
    """
    
    folium.Marker(
        [source_lat, source_lon],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=f'{chemical_name} Release Source',
        icon=folium.Icon(color='red', icon='warning-sign', prefix='glyphicon')
    ).add_to(source_group)
    
    # Add concentration contours for each threshold - each in its own feature group
    sorted_thresholds = sorted(thresholds.items(), key=lambda x: x[1], reverse=True)
    
    contour_groups = {}
    for threshold_name, threshold_value in sorted_thresholds:
        # Create individual feature group for each AEGL level
        contour_groups[threshold_name] = folium.FeatureGroup(
            name=f'{threshold_name} ({int(threshold_value)} ppm)',
            show=True
        )
        
        try:
            add_concentration_contour(
                contour_groups[threshold_name],
                lat_grid,
                lon_grid,
                concentration,
                threshold_value,
                threshold_name,
                chemical_name
            )
        except Exception as e:
            logger.warning(f"Failed to create contour for {threshold_name}: {e}")
    
    # Add heat map layer if requested
    if include_heatmap:
        try:
            heatmap_group = create_heatmap_layer(
                lat_grid, lon_grid, concentration, name=f'{chemical_name} Concentration'
            )
            heatmap_group.add_to(m)
        except Exception as e:
            logger.warning(f"Failed to create heat map: {e}")
    
    # Add wind direction indicator
    if wind_direction is not None:
        add_wind_rose(wind_group, source_lat, source_lon, wind_direction, wind_speed)
    
    # Add all feature groups to map
    source_group.add_to(m)
    
    # Add each AEGL contour group separately for individual control
    for contour_group in contour_groups.values():
        contour_group.add_to(m)
    
    wind_group.add_to(m)
    
    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Add legend
    add_legend(m, sorted_thresholds, chemical_name)

    # Add compass overlay for quick orientation with wind direction
    if include_compass:
        add_compass(m, position='topleft', wind_direction=wind_direction)
    
    logger.info("Folium map created successfully")
    return m


def add_compass(
    folium_map: folium.Map,
    position: str = 'topright',
    size: int = 60,
    wind_direction: float = None
):
    """Overlay a compass (N/E/S/W) with optional wind direction indicator."""

    # Position mapping to CSS anchors
    pos_map = {
        'topright': {'top': '10px', 'right': '10px'},
        'topleft': {'top': '10px', 'left': '50px'},
        'bottomright': {'bottom': '25px', 'right': '15px'},
        'bottomleft': {'bottom': '25px', 'left': '15px'},
    }
    anchor = pos_map.get(position, pos_map['topleft'])

    pos_style = [f"{k}: {v};" for k, v in anchor.items()]
    
    # Wind direction rotation (if provided)
    wind_rotation = (wind_direction) % 360 if wind_direction is not None else 0
    wind_arrow = f'<div style="position: absolute; width: 2px; height: 20px; background-color: #d32f2f; transform: rotate({wind_rotation}deg);"></div>' if wind_direction is not None else ''

    compass_html = f'''
    <div style="position: fixed; 
                {''.join(pos_style)}
                width: {size}px; height: {size}px;
                background-color: white; border: 2px solid #333;
                z-index:9999; border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                font-weight: bold; font-size: 14px; text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
        <div style="position: relative; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">
            <div style="position: absolute; top: 5px; color: #d32f2f;"><b>N</b></div>
            <div style="position: absolute; right: 5px; color: #333;"><b>E</b></div>
            <div style="position: absolute; bottom: 5px; color: #333;"><b>S</b></div>
            <div style="position: absolute; left: 5px; color: #333;"><b>W</b></div>
            {wind_arrow}
        </div>
    </div>
    '''

    folium_map.get_root().html.add_child(folium.Element(compass_html))


def meters_to_latlon(
    x_meters: np.ndarray,
    y_meters: np.ndarray,
    origin_lat: float,
    origin_lon: float,
    rotation_deg: float = 0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert local Cartesian coordinates (x,y in meters) to geographic coordinates (lat,lon).
    
    This function handles coordinate transformation from a local meter-based grid
    (centered at the release point) to WGS84 geographic coordinates, with optional
    rotation to align with wind direction.
    
    Parameters:
    -----------
    x_meters : np.ndarray
        Downwind distances in meters (can be 1D or 2D)
    y_meters : np.ndarray
        Crosswind distances in meters (can be 1D or 2D)
    origin_lat : float
        Latitude of origin point (degrees)
    origin_lon : float
        Longitude of origin point (degrees)
    rotation_deg : float, optional
        Clockwise rotation angle in degrees (wind direction), default=0
        0 = North, 90 = East, 180 = South, 270 = West
    
    Returns:
    --------
    Tuple[np.ndarray, np.ndarray]
        (lat_grid, lon_grid) in degrees
    
    Notes:
    ------
    - Uses simple equirectangular approximation (valid for distances < 100 km)
    - 1 degree latitude ≈ 111.32 km (constant)
    - 1 degree longitude ≈ 111.32 km × cos(latitude)
    """
    
    # Rotate grid by wind direction (meteorological: 0° = North, 90° = East)
    # Convert to math angle where 0 rad is East and positive is CCW
    theta = np.radians((90.0 - rotation_deg) % 360.0)
    x_rot = x_meters * np.cos(theta) - y_meters * np.sin(theta)
    y_rot = x_meters * np.sin(theta) + y_meters * np.cos(theta)
    
    # Convert meters to degrees
    lat_per_m = 1.0 / METERS_PER_DEGREE_LAT
    lon_per_m = 1.0 / (METERS_PER_DEGREE_LAT * np.cos(np.radians(origin_lat)))
    
    # North is +Y, East is +X in standard geographic convention
    lat_grid = origin_lat + y_rot * lat_per_m
    lon_grid = origin_lon + x_rot * lon_per_m
    
    return lat_grid, lon_grid


def add_concentration_contour(
    feature_group: folium.FeatureGroup,
    lat_grid: np.ndarray,
    lon_grid: np.ndarray,
    concentration: np.ndarray,
    threshold: float,
    label: str,
    chemical_name: str = "Chemical"
):
    """
    Add a single concentration contour as a polygon to the map.
    
    Parameters:
    -----------
    feature_group : folium.FeatureGroup
        Feature group to add contour to
    lat_grid : np.ndarray
        2D array of latitude values
    lon_grid : np.ndarray
        2D array of longitude values
    concentration : np.ndarray
        2D array of concentration values
    threshold : float
        Concentration threshold level
    label : str
        Label for this contour (e.g., 'AEGL-1')
    chemical_name : str, optional
        Chemical name for popup
    """
    
    try:
        from skimage import measure
    except ImportError:
        logger.error("scikit-image not installed. Install with: pip install scikit-image")
        return
    
    # Find contour at threshold level
    try:
        contours = measure.find_contours(concentration, threshold)
    except Exception as e:
        logger.warning(f"Could not find contours for {label}: {e}")
        return
    
    if len(contours) == 0:
        logger.info(f"No contours found for {label} at threshold {threshold}")
        return
    
    # Process each contour polygon
    for contour_idx, contour in enumerate(contours):
        coords = []
        
        # Map contour indices to lat/lon coordinates with interpolation for smoothness
        for point in contour:
            i, j = point[0], point[1]  # Keep as float for interpolation
            
            # Bilinear interpolation for smooth contours
            i0, j0 = int(np.floor(i)), int(np.floor(j))
            i1, j1 = min(i0 + 1, lat_grid.shape[0] - 1), min(j0 + 1, lat_grid.shape[1] - 1)
            
            # Check bounds
            if 0 <= i0 < lat_grid.shape[0] and 0 <= j0 < lon_grid.shape[1]:
                # Interpolation weights
                wi, wj = i - i0, j - j0
                
                # Interpolate latitude
                lat = (1 - wi) * (1 - wj) * lat_grid[i0, j0] + \
                      (1 - wi) * wj * lat_grid[i0, j1] + \
                      wi * (1 - wj) * lat_grid[i1, j0] + \
                      wi * wj * lat_grid[i1, j1]
                
                # Interpolate longitude
                lon = (1 - wi) * (1 - wj) * lon_grid[i0, j0] + \
                      (1 - wi) * wj * lon_grid[i0, j1] + \
                      wi * (1 - wj) * lon_grid[i1, j0] + \
                      wi * wj * lon_grid[i1, j1]
                
                coords.append([lat, lon])
        
        # Need at least 3 points to make a polygon
        if len(coords) < 3:
            continue
        
        # Get color for this hazard level
        color = get_hazard_color(label)
        
        # Create popup with information
        popup_html = f"""
        <div style="font-family: Arial; font-size: 11px;">
            <b>{label}</b><br>
            {chemical_name}: {threshold} ppm<br>
            Hazard Zone Boundary
        </div>
        """
        
        # Add polygon to map
        folium.Polygon(
            locations=coords,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.25,
            weight=2.5,
            opacity=0.8,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f'{label}: {threshold} ppm'
        ).add_to(feature_group)
    
    logger.debug(f"Added {len(contours)} contour(s) for {label}")


def add_wind_rose(
    feature_group: folium.FeatureGroup,
    lat: float,
    lon: float,
    wind_direction: float,
    wind_speed: Optional[float] = None
):
    """
    Add wind direction indicator to the map.
    
    Parameters:
    -----------
    feature_group : folium.FeatureGroup
        Feature group to add wind indicator to
    lat : float
        Latitude for wind rose placement
    lon : float
        Longitude for wind rose placement
    wind_direction : float
        Wind direction in degrees from north (0=north, 90=east)
    wind_speed : float, optional
        Wind speed in m/s
    """
    
    # Calculate endpoint of wind arrow (500m in wind direction)
    arrow_length_m = 500
    theta = np.radians(wind_direction)
    
    # Convert to lat/lon offset
    lat_per_m = 1.0 / METERS_PER_DEGREE_LAT
    lon_per_m = 1.0 / (METERS_PER_DEGREE_LAT * np.cos(np.radians(lat)))
    
    end_lat = lat + arrow_length_m * np.cos(theta) * lat_per_m
    end_lon = lon + arrow_length_m * np.sin(theta) * lon_per_m
    
    # Wind direction label
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    direction_idx = int((wind_direction + 11.25) / 22.5) % 16
    direction_label = directions[direction_idx]
    
    # Create popup text
    popup_text = f"Wind: {wind_direction:.0f}° ({direction_label})"
    if wind_speed:
        popup_text += f"<br>Speed: {wind_speed:.1f} m/s"
    
    # Add wind arrow as a polyline with arrow decorator
    arrow = folium.PolyLine(
        locations=[[lat, lon], [end_lat, end_lon]],
        color='blue',
        weight=3,
        opacity=0.8,
        popup=popup_text,
        tooltip=f"Wind from {direction_label}"
    )
    
    # Add arrow head using plugins
    plugins.PolyLineTextPath(
        arrow,
        '►',
        repeat=False,
        offset=12,
        attributes={'fill': 'blue', 'font-size': '18'}
    ).add_to(feature_group)
    
    arrow.add_to(feature_group)
    
    # Add wind marker at source
    folium.CircleMarker(
        [lat, lon],
        radius=6,
        color='blue',
        fill=True,
        fillColor='lightblue',
        fillOpacity=0.7,
        popup=popup_text,
        tooltip='Wind Direction'
    ).add_to(feature_group)


def create_heatmap_layer(
    lat_grid: np.ndarray,
    lon_grid: np.ndarray,
    concentration: np.ndarray,
    name: str = "Concentration Heat Map",
    subsample: int = 5
) -> folium.FeatureGroup:
    """
    Create a heat map layer showing concentration distribution.
    
    Parameters:
    -----------
    lat_grid : np.ndarray
        2D latitude grid
    lon_grid : np.ndarray
        2D longitude grid
    concentration : np.ndarray
        2D concentration values
    name : str
        Layer name
    subsample : int
        Subsample factor to reduce point count (higher = fewer points)
    
    Returns:
    --------
    folium.FeatureGroup
        Feature group containing heat map
    """
    
    # Subsample grid to reduce point count
    lat_sub = lat_grid[::subsample, ::subsample]
    lon_sub = lon_grid[::subsample, ::subsample]
    conc_sub = concentration[::subsample, ::subsample]
    
    # Create list of [lat, lon, intensity] for heat map
    heat_data = []
    for i in range(lat_sub.shape[0]):
        for j in range(lat_sub.shape[1]):
            if conc_sub[i, j] > 0:  # Only include non-zero concentrations
                heat_data.append([
                    lat_sub[i, j],
                    lon_sub[i, j],
                    float(conc_sub[i, j])
                ])
    
    # Create heat map
    feature_group = folium.FeatureGroup(name=name, show=False)
    
    if len(heat_data) > 0:
        plugins.HeatMap(
            heat_data,
            min_opacity=0.2,
            max_opacity=0.8,
            radius=15,
            blur=20,
            gradient={
                0.0: 'blue',
                0.3: 'cyan',
                0.5: 'lime',
                0.7: 'yellow',
                0.9: 'orange',
                1.0: 'red'
            }
        ).add_to(feature_group)
    
    return feature_group


def add_facility_markers(
    folium_map: folium.Map,
    facilities: List[Dict[str, Any]],
    group_name: str = "Facilities"
):
    """
    Add facility markers to the map.
    
    Parameters:
    -----------
    folium_map : folium.Map
        Map to add markers to
    facilities : List[Dict]
        List of facility dictionaries with 'name', 'lat', 'lon', 'type' keys
    group_name : str
        Name for facility feature group
    """
    
    facility_group = folium.FeatureGroup(name=group_name, show=True)
    
    icon_map = {
        'school': {'color': 'green', 'icon': 'education'},
        'hospital': {'color': 'red', 'icon': 'plus-sign'},
        'residential': {'color': 'blue', 'icon': 'home'},
        'industrial': {'color': 'orange', 'icon': 'oil'},
        'default': {'color': 'gray', 'icon': 'info-sign'}
    }
    
    for facility in facilities:
        icon_info = icon_map.get(facility.get('type', 'default'), icon_map['default'])
        
        folium.Marker(
            [facility['lat'], facility['lon']],
            popup=facility.get('name', 'Facility'),
            tooltip=facility.get('name', 'Facility'),
            icon=folium.Icon(
                color=icon_info['color'],
                icon=icon_info['icon'],
                prefix='glyphicon'
            )
        ).add_to(facility_group)
    
    facility_group.add_to(folium_map)


def get_hazard_color(label: str) -> str:
    """
    Get color for a hazard level label.
    
    Parameters:
    -----------
    label : str
        Hazard level label (e.g., 'AEGL-1', 'ERPG-2')
    
    Returns:
    --------
    str
        Hex color code
    """
    return HAZARD_COLORS.get(label, '#808080')  # Default gray


def add_legend(
    folium_map: folium.Map,
    thresholds: List[Tuple[str, float]],
    chemical_name: str
):
    """
    Add legend to the map.
    
    Parameters:
    -----------
    folium_map : folium.Map
        Map to add legend to
    thresholds : List[Tuple[str, float]]
        List of (label, value) tuples
    chemical_name : str
        Chemical name
    """
    
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 220px; 
                background-color: white; border: 2px solid grey; z-index: 9999; 
                font-size: 12px; padding: 10px; border-radius: 5px; 
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <h4 style="margin: 0 0 10px 0;">{chemical_name} Hazard Zones</h4>
    '''
    
    for label, value in thresholds:
        color = get_hazard_color(label)
        legend_html += f'''
        <div style="margin: 5px 0;">
            <span style="background-color: {color}; 
                         width: 20px; height: 15px; 
                         display: inline-block; 
                         border: 1px solid black; 
                         opacity: 0.7;"></span>
            <span style="margin-left: 5px;">{label}: {value} ppm</span>
        </div>
        '''
    
    legend_html += '</div>'
    
    folium_map.get_root().html.add_child(folium.Element(legend_html))


def calculate_optimal_zoom_level(lat_grid, lon_grid, concentration, threshold=0):
    """
    Calculate optimal zoom level based on threat zone extent.
    
    This function determines the geographic bounds of the threat zone and
    calculates an appropriate zoom level to display it prominently on the map.
    
    Parameters:
    -----------
    lat_grid : ndarray
        2D array of latitudes
    lon_grid : ndarray
        2D array of longitudes
    concentration : ndarray
        2D array of concentration values
    threshold : float, optional
        Minimum concentration threshold (default: 0, includes all)
    
    Returns:
    --------
    int: Optimal zoom level (3-20 range)
    tuple: ((north, south, east, west), zoom_level) - bounds and zoom
    """
    # Find indices where concentration exceeds threshold
    mask = concentration > threshold
    
    if not np.any(mask):
        # No threat zone, use default zoom
        return 12, (None, None, None, None)
    
    # Get geographic bounds of threat zone
    threat_lats = lat_grid[mask]
    threat_lons = lon_grid[mask]
    
    north = np.max(threat_lats)
    south = np.min(threat_lats)
    east = np.max(threat_lons)
    west = np.min(threat_lons)
    
    # Calculate geographic extent in degrees
    lat_extent = north - south
    lon_extent = east - west
    
    # Use the larger extent for zoom calculation
    max_extent = max(lat_extent, lon_extent)
    
    # Zoom level calculation based on geographic extent
    # This is an empirical formula that works well for threat zones
    if max_extent < 0.001:      # < 111 meters
        zoom = 18
    elif max_extent < 0.005:    # < 555 meters
        zoom = 16
    elif max_extent < 0.01:     # < 1.1 km
        zoom = 15
    elif max_extent < 0.02:     # < 2.2 km
        zoom = 14
    elif max_extent < 0.05:     # < 5.5 km
        zoom = 13
    elif max_extent < 0.1:      # < 11 km
        zoom = 12
    elif max_extent < 0.2:      # < 22 km
        zoom = 11
    else:                        # > 22 km
        zoom = 10
    
    bounds = (north, south, east, west)
    
    return zoom, bounds


def fit_map_to_polygons(folium_map: folium.Map, polygons: Iterable[Any]) -> None:
    """Fit a Folium map viewport to the bounds of provided polygons."""
    bounds = []
    for poly in polygons:
        if poly is None or getattr(poly, "is_empty", True):
            continue
        minx, miny, maxx, maxy = poly.bounds  # lon/lat order
        bounds.append((minx, miny, maxx, maxy))
    if bounds:
        west = min(b[0] for b in bounds)
        south = min(b[1] for b in bounds)
        east = max(b[2] for b in bounds)
        north = max(b[3] for b in bounds)
        folium_map.fit_bounds([[south, west], [north, east]])


def create_live_threat_map(
    weather,
    X,
    Y,
    concentration,
    U_local,
    stability_class,
    source_lat,
    source_lon,
    chemical_name,
    tank_height,
    release_rate,
    aegl_thresholds,
    update_interval_seconds,
    sources=None,
    markers=None
):
    """
    Create interactive Folium map with visible threat zones for real-time monitoring.
    
    Parameters:
    -----------
    weather : dict
        Weather data including wind speed, wind direction, temperature
    X : ndarray
        X-coordinates grid (meters)
    Y : ndarray
        Y-coordinates grid (meters)
    concentration : ndarray
        Concentration grid (ppm)
    U_local : float
        Local wind speed
    stability_class : str
        Atmospheric stability class
    source_lat : float
        Primary source latitude
    source_lon : float
        Primary source longitude
    chemical_name : str
        Name of the chemical (e.g., 'Ammonia (NH3)')
    tank_height : float
        Release height in meters
    release_rate : float
        Release rate in g/s
    aegl_thresholds : dict
        AEGL threshold values (e.g., {'AEGL-1': 30, 'AEGL-2': 160, 'AEGL-3': 1100})
    update_interval_seconds : int
        Map refresh interval in seconds
    sources : list of dict, optional
        Additional sources with 'lat', 'lon', 'name', 'height', 'rate', 'color'
    markers : list of dict, optional
        Custom markers with 'lat', 'lon', 'name', 'color', 'icon', 'popup'
    
    Returns:
    --------
    folium.Map
        Interactive Folium map object
    """
    from datetime import datetime
    from ..utils.features import add_wind_direction_arrow
    
    logger.info("Creating Folium map with threat zones...")
    
    try:
        # Convert grid coordinates to lat/lon using core module function
        lat_grid, lon_grid = meters_to_latlon(
            x_meters=X,
            y_meters=Y,
            origin_lat=source_lat,
            origin_lon=source_lon,
            rotation_deg=weather['wind_dir']
        )
        
        # Calculate optimal zoom level based on threat zone extent
        # Use AEGL-1 (minimum) threshold to determine overall threat zone size
        min_threshold = min(aegl_thresholds.values())
        zoom_level, bounds = calculate_optimal_zoom_level(
            lat_grid, lon_grid, concentration, threshold=min_threshold
        )
        
        logger.debug("Calculated zoom level: %d", zoom_level)
        if bounds[0] is not None:
            logger.debug(
                "Threat zone bounds: N=%.4f S=%.4f E=%.4f W=%.4f",
                bounds[0], bounds[1], bounds[2], bounds[3],
            )
        
        # Create base map with calculated zoom level
        m = folium.Map(
            location=[source_lat, source_lon],
            zoom_start=zoom_level,
            tiles='CartoDB dark_matter',
            name='Night Map',
            prefer_canvas=True
        )
        
        # Add alternative tile layers
        folium.TileLayer('CartoDB positron', name='Day Map').add_to(m)
        folium.TileLayer('OpenStreetMap', name='Street Map').add_to(m)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        

        # Add threat zone contours using proper polygon contours
        colors = {
            'AEGL-3': '#FF0000',  # Red - Life-threatening
            'AEGL-2': '#FFA500',  # Orange - Serious
            'AEGL-1': '#FFFF00',  # Yellow - Mild
        }
        
        try:
            from skimage import measure
            
            # Process each threshold in order (highest to lowest for proper layering)
            for threshold_name in ['AEGL-3', 'AEGL-2', 'AEGL-1']:
                if threshold_name not in aegl_thresholds:
                    continue
                    
                threshold_val = aegl_thresholds[threshold_name]
                
                # Create feature group for this threshold
                fg = folium.FeatureGroup(name=f'{threshold_name} ({threshold_val} ppm)', show=True)
                
                try:
                    # Find contours at threshold level using scikit-image
                    contours = measure.find_contours(concentration, threshold_val)
                    
                    if len(contours) == 0:
                        logger.info("No contours found for %s at %.1f ppm", threshold_name, threshold_val)
                        continue
                    
                    # Process each contour polygon
                    for contour_idx, contour in enumerate(contours):
                        coords = []
                        
                        # Map contour indices to lat/lon coordinates with interpolation
                        for point in contour:
                            i, j = point[0], point[1]  # Keep as float for interpolation
                            
                            # Bilinear interpolation for smooth contours
                            i0, j0 = int(np.floor(i)), int(np.floor(j))
                            i1, j1 = min(i0 + 1, lat_grid.shape[0] - 1), min(j0 + 1, lat_grid.shape[1] - 1)
                            
                            # Check bounds
                            if 0 <= i0 < lat_grid.shape[0] and 0 <= j0 < lon_grid.shape[1]:
                                # Interpolation weights
                                wi, wj = i - i0, j - j0
                                
                                # Interpolate latitude
                                lat = (1 - wi) * (1 - wj) * lat_grid[i0, j0] + \
                                      (1 - wi) * wj * lat_grid[i0, j1] + \
                                      wi * (1 - wj) * lat_grid[i1, j0] + \
                                      wi * wj * lat_grid[i1, j1]
                                
                                # Interpolate longitude
                                lon = (1 - wi) * (1 - wj) * lon_grid[i0, j0] + \
                                      (1 - wi) * wj * lon_grid[i0, j1] + \
                                      wi * (1 - wj) * lon_grid[i1, j0] + \
                                      wi * wj * lon_grid[i1, j1]
                                
                                coords.append([lat, lon])
                        
                        # Need at least 3 points to make a polygon
                        if len(coords) < 3:
                            continue
                        
                        # Create popup with information
                        popup_html = f"""
                        <div style="font-family: Arial; font-size: 11px;">
                            <b>{threshold_name}</b><br>
                            {chemical_name}: {threshold_val} ppm<br>
                            Hazard Zone Boundary
                        </div>
                        """
                        
                        # Add polygon to map
                        folium.Polygon(
                            locations=coords,
                            color=colors.get(threshold_name, '#999999'),
                            fill=True,
                            fillColor=colors.get(threshold_name, '#999999'),
                            fillOpacity=0.25,
                            weight=2.5,
                            opacity=0.8,
                            popup=folium.Popup(popup_html, max_width=200),
                            tooltip=f'{threshold_name}: {threshold_val} ppm'
                        ).add_to(fg)
                    
                    logger.debug("Added %d contour(s) for %s", len(contours), threshold_name)
                    
                except Exception as e:
                    logger.warning("Could not create contour for %s: %s", threshold_name, e)
                
                fg.add_to(m)
                
        except ImportError:
            logger.warning(
                "scikit-image not installed — install with: pip install scikit-image. "
                "Falling back to simple visualization."
            )
        
        # Add source markers (primary and additional sources)
        source_fg = folium.FeatureGroup(name='Release Sources', show=True)
        
        # Primary source
        popup_text = f"""
        <b>{chemical_name} Release Source</b><br>
        Location: {source_lat:.4f}°, {source_lon:.4f}°<br>
        Height: {tank_height} m<br>
        Release Rate: {release_rate} g/s<br>
        Wind: {weather['wind_speed']:.1f} m/s @ {weather['wind_dir']:.0f}°<br>
        Stability: Class {stability_class}
        """
        folium.Marker(
            [source_lat, source_lon],
            popup=popup_text,
            icon=folium.Icon(color='red', icon='warning-sign', prefix='glyphicon'),
            tooltip='Primary Release Source'
        ).add_to(source_fg)
        
        # Additional sources
        if sources:
            for i, src in enumerate(sources, 1):
                src_lat = src.get('lat', source_lat)
                src_lon = src.get('lon', source_lon)
                src_name = src.get('name', f'Source {i}')
                src_height = src.get('height', tank_height)
                src_rate = src.get('rate', release_rate)
                src_color = src.get('color', 'red')
                
                popup_src = f"""
                <b>{src_name}</b><br>
                Location: {src_lat:.4f}°, {src_lon:.4f}°<br>
                Height: {src_height} m<br>
                Release Rate: {src_rate} g/s<br>
                Wind: {weather['wind_speed']:.1f} m/s @ {weather['wind_dir']:.0f}°<br>
                Stability: Class {stability_class}
                """
                folium.Marker(
                    [src_lat, src_lon],
                    popup=popup_src,
                    icon=folium.Icon(color=src_color, icon='warning-sign', prefix='glyphicon'),
                    tooltip=src_name
                ).add_to(source_fg)
        
        source_fg.add_to(m)
        
        # Add custom markers if provided
        if markers:
            marker_fg = folium.FeatureGroup(name='Custom Markers', show=True)
            for marker in markers:
                marker_lat = marker.get('lat')
                marker_lon = marker.get('lon')
                marker_name = marker.get('name', 'Marker')
                marker_color = marker.get('color', 'blue')
                marker_icon = marker.get('icon', 'info-sign')
                marker_popup = marker.get('popup', marker_name)
                
                if marker_lat is not None and marker_lon is not None:
                    folium.Marker(
                        [marker_lat, marker_lon],
                        popup=marker_popup,
                        icon=folium.Icon(color=marker_color, icon=marker_icon, prefix='glyphicon'),
                        tooltip=marker_name
                    ).add_to(marker_fg)
            
            marker_fg.add_to(m)
        
        # Add wind direction arrow
        add_wind_direction_arrow(
            map_obj=m,
            source_lat=source_lat,
            source_lon=source_lon,
            wind_direction=weather['wind_dir'],
            arrow_length=0.01
        )
        
        # Add N E S W compass
        css_wind_rotation = (weather['wind_dir']) % 360
        
        compass_html = f'''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 60px; height: 60px;
                    background-color: white; border: 2px solid #333;
                    z-index:9999; border-radius: 50%;
                    display: flex; align-items: center; justify-content: center;
                    font-weight: bold; font-size: 14px; text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
            <div style="position: relative; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">
                <div style="position: absolute; top: 5px; color: #d32f2f;"><b>N</b></div>
                <div style="position: absolute; right: 5px; color: #333;"><b>E</b></div>
                <div style="position: absolute; bottom: 5px; color: #333;"><b>S</b></div>
                <div style="position: absolute; left: 5px; color: #333;"><b>W</b></div>
                <div style="position: absolute; width: 2px; height: 20px; background-color: #d32f2f; transform: rotate({css_wind_rotation}deg);"></div>
            </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(compass_html))
        
        # Fit map to threat zone bounds for optimal viewing
        if bounds[0] is not None and bounds != (None, None, None, None):
            # bounds = (north, south, east, west)
            m.fit_bounds(
                [[bounds[1], bounds[3]], [bounds[0], bounds[2]]],  # [[south, west], [north, east]]
                padding=(0.1, 0.1)
            )
            logger.debug("Map fitted to threat zone bounds")
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        logger.info("Folium map created with threat zones")
        
        return m
        
    except Exception as e:
        logger.exception("Error creating map: %s", e)
        raise


def save_map(folium_map: folium.Map, filepath: str):
    """
    Save interactive map to HTML file.
    
    Parameters:
    -----------
    folium_map : folium.Map
        Map object to save
    filepath : str
        Output file path (should end with .html)
    """
    
    folium_map.save(filepath)
    logger.info("Interactive map saved to: %s", filepath)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Folium Maps Module - pyELDQM")
    print("=" * 60)
    print("\nThis module provides interactive mapping for dispersion modeling.")
    print("\nExample usage:")
    print("""
    from core.visualization.folium_maps import create_dispersion_map
    
    # Create concentration grid (from dispersion model)
    X, Y = np.meshgrid(x_vals, y_vals)  # meters
    C = concentration_field  # ppm
    
    # Create interactive map
    m = create_dispersion_map(
        source_lat=24.85,
        source_lon=67.05,
        x_grid=X,
        y_grid=Y,
        concentration=C,
        thresholds={'AEGL-1': 30, 'AEGL-2': 160},
        wind_direction=45,
        chemical_name='Ammonia'
    )
    
    # Save to HTML
    m.save('dispersion_map.html')
    """)
