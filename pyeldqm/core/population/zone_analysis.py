"""
Zone-based population analysis utilities.

Provides functions for calculating population distribution in hazard zones
using density-based approaches with improved grid distribution strategies.
"""

from typing import Tuple, List, Dict, Optional
import numpy as np
from shapely.geometry import Point, Polygon


def calculate_population_in_zone(
    zone_poly: Polygon,
    base_density: float = 600,
    leak_lat: Optional[float] = None,
    leak_lon: Optional[float] = None,
    verbose: bool = False
) -> Tuple[int, List[Dict]]:
    """
    Calculate population in a threat zone using density-based approach with improved
    grid distribution for consistent and even point placement across all zone types.
    
    Key improvements:
    - Uses stratified uniform sampling instead of arange (more consistent)
    - Adaptive grid refinement for narrow/small zones
    - Better handling of irregular zone geometries
    - Guaranteed point coverage across entire zone
    - Robust fallback strategies for edge cases
    
    Parameters:
    -----------
    zone_poly : Polygon
        Threat zone polygon (in lat/lon coordinates)
    base_density : float
        Base population density (people per km²), default 600
    leak_lat, leak_lon : float, optional
        Leak location for density modulation (creates hotspot effect)
    verbose : bool
        Print detailed information about grid generation and point distribution
    
    Returns:
    --------
    Tuple[int, List[Dict]]
        (total_population, list_of_population_points)
        
    Each population point contains:
    - geometry: Point object
    - population: Number of people at that point
    - latitude: Latitude coordinate
    - longitude: Longitude coordinate
    - density: Population density at that point
    """
    if zone_poly is None or zone_poly.is_empty:
        return 0, []
    
    # Get zone bounds (in lat/lon)
    bounds = zone_poly.bounds  # (lon_min, lat_min, lon_max, lat_max)
    lon_min, lat_min, lon_max, lat_max = bounds
    
    # Calculate zone area in km²
    center_lat = (lat_min + lat_max) / 2.0
    lat_to_km = 110.57
    lon_to_km = 111.32 * np.cos(np.radians(center_lat))
    
    width_km = (lon_max - lon_min) * lon_to_km
    height_km = (lat_max - lat_min) * lat_to_km
    area_km2 = width_km * height_km
    
    # Calculate total population from density
    total_pop = int(area_km2 * base_density)
    
    if verbose:
        print(f"    Zone bounds: ({lon_min:.6f}, {lat_min:.6f}) to ({lon_max:.6f}, {lat_max:.6f})")
        print(f"    Zone area: {area_km2:.3f} km²")
        print(f"    Base total population: {total_pop} people")
    
    if total_pop == 0:
        if verbose:
            print(f"    Total population: 0 (zone too small)")
        return 0, []
    
    # ====== IMPROVED GRID GENERATION ======
    # Adaptive grid resolution: ensure minimum coverage even for narrow zones
    # Target at least 30-40 points for consistent distribution
    target_points_per_axis = max(40, int(np.sqrt(area_km2) * 4))
    
    # Use linspace for UNIFORM distribution (better than arange)
    # This ensures even spacing regardless of zone size or shape
    lons = np.linspace(lon_min + 1e-6, lon_max - 1e-6, target_points_per_axis)
    lats = np.linspace(lat_min + 1e-6, lat_max - 1e-6, target_points_per_axis)
    
    if verbose:
        print(f"    Grid resolution: {target_points_per_axis} × {target_points_per_axis} points")
        print(f"    Grid spacing: ~{(width_km / target_points_per_axis):.3f} km (lon) × ~{(height_km / target_points_per_axis):.3f} km (lat)")
    
    # ====== MULTI-STRATEGY POINT COLLECTION ======
    # Strategy 1: Regular grid points within zone (primary)
    points_in_zone = []
    for lon in lons:
        for lat in lats:
            point = Point(lon, lat)
            if point.within(zone_poly) or point.touches(zone_poly):
                points_in_zone.append((lon, lat, point))
    
    if verbose:
        print(f"    Regular grid points within zone: {len(points_in_zone)}")
    
    # Strategy 2: If too few points, use denser grid (for narrow/small zones)
    if len(points_in_zone) < 15:
        if verbose:
            print(f"    ⚠ Low point count detected, increasing grid density...")
        target_points_per_axis_dense = target_points_per_axis * 2
        lons_dense = np.linspace(lon_min + 1e-8, lon_max - 1e-8, target_points_per_axis_dense)
        lats_dense = np.linspace(lat_min + 1e-8, lat_max - 1e-8, target_points_per_axis_dense)
        
        points_in_zone = []
        for lon in lons_dense:
            for lat in lats_dense:
                point = Point(lon, lat)
                if point.within(zone_poly) or point.touches(zone_poly):
                    points_in_zone.append((lon, lat, point))
        if verbose:
            print(f"    Dense grid points within zone: {len(points_in_zone)}")
    
    # Strategy 3: If still no points, use interior point + random sampling
    if len(points_in_zone) == 0:
        if verbose:
            print(f"    ✗ No grid points found in zone - using interior point + random sampling")
        
        # Get interior point
        try:
            interior_point = zone_poly.representative_point()
        except:
            interior_point = zone_poly.centroid
        
        # Random sampling with stratified approach
        minx, miny, maxx, maxy = zone_poly.bounds
        n_samples = max(20, int(area_km2 * 10))
        
        sample_lons = np.random.uniform(minx, maxx, n_samples * 3)
        sample_lats = np.random.uniform(miny, maxy, n_samples * 3)
        
        for lon, lat in zip(sample_lons, sample_lats):
            point = Point(lon, lat)
            if point.within(zone_poly):
                points_in_zone.append((lon, lat, point))
            if len(points_in_zone) >= n_samples:
                break
        
        if verbose:
            print(f"    Random sampled points: {len(points_in_zone)}")
    
    # Strategy 4: Absolute fallback - use centroid only
    if len(points_in_zone) == 0:
        if verbose:
            print(f"    ✗✗ All strategies failed - using zone centroid as fallback")
        centroid = zone_poly.centroid
        points_in_zone = [(centroid.x, centroid.y, centroid)]
    
    # ====== POPULATION DISTRIBUTION ======
    population_points = []
    total_pop_distributed = 0
    
    # Distribute population uniformly across all collected points
    n_points = len(points_in_zone)
    pop_per_point = total_pop // n_points
    remainder = total_pop % n_points
    
    if verbose:
        print(f"    Final grid points for distribution: {n_points}")
        print(f"    Population per point: {pop_per_point} (base) + up to 1 (remainder)")
    
    for idx, (lon, lat, point) in enumerate(points_in_zone):
        # Distribute remainder evenly across points
        pop_at_point = pop_per_point + (1 if idx < remainder else 0)
        
        # Apply density hotspot effect near leak
        density = base_density
        if leak_lat is not None and leak_lon is not None:
            dlat_km = (lat - leak_lat) * lat_to_km
            dlon_km = (lon - leak_lon) * lon_to_km
            dist_km = np.sqrt(dlat_km**2 + dlon_km**2)
            
            # Exponential decay with distance (falloff at ~2km)
            hotspot_effect = 1.5 * np.exp(-dist_km / 2.0)
            density = base_density * (1 + hotspot_effect)
        
        if pop_at_point > 0:
            population_points.append({
                'geometry': point,
                'population': pop_at_point,
                'latitude': lat,
                'longitude': lon,
                'density': density
            })
            total_pop_distributed += pop_at_point
    
    if verbose:
        print(f"    Population points created: {len(population_points)}")
        print(f"    Total population distributed: {total_pop_distributed}")
    
    return total_pop_distributed, population_points
