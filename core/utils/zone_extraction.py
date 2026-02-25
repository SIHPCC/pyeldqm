"""
Zone Extraction Utilities for pyELDQM

Provides universal functions for extracting threat zone polygons from 
concentration fields using contour analysis and bilinear interpolation.

Functions:
----------
- extract_zones() : Universal zone extraction with bilinear interpolation
- parse_threshold() : Parse threshold values from various formats
- bilinear_interpolate_coords() : Smooth coordinate interpolation
"""

from typing import Dict, Optional, Tuple
import logging
import numpy as np
from shapely.geometry import Polygon
from skimage import measure

logger = logging.getLogger(__name__)


def parse_threshold(threshold_val: Optional[float]) -> Optional[float]:
    """
    Parse threshold value from various formats.
    
    Handles:
    - None values
    - Numeric strings with/without " ppm" suffix
    - Direct float/int values
    
    Parameters:
    -----------
    threshold_val : float, str, or None
        Threshold value in various formats
    
    Returns:
    --------
    Optional[float]
        Parsed threshold value, or None if invalid
    
    Examples:
    ---------
    >>> parse_threshold(30)
    30.0
    >>> parse_threshold("160 ppm")
    160.0
    >>> parse_threshold("1100")
    1100.0
    >>> parse_threshold(None)
    None
    """
    if threshold_val is None:
        return None
    
    try:
        # Convert to string, remove " ppm" suffix if present
        val_str = str(threshold_val).replace(" ppm", "").strip()
        return float(val_str)
    except (ValueError, TypeError, AttributeError):
        return None


def bilinear_interpolate_coords(
    i: float,
    j: float,
    lat_grid: np.ndarray,
    lon_grid: np.ndarray
) -> Tuple[float, float]:
    """
    Bilinear interpolation for smooth contour coordinates.
    
    Interpolates latitude and longitude at fractional grid indices
    using bilinear interpolation from 4 neighboring grid points.
    
    Parameters:
    -----------
    i, j : float
        Fractional grid indices (from contour tracing)
    lat_grid, lon_grid : np.ndarray
        2D arrays of latitude/longitude values
    
    Returns:
    --------
    Tuple[float, float]
        Interpolated (latitude, longitude)
    """
    i0, j0 = int(np.floor(i)), int(np.floor(j))
    i1 = min(i0 + 1, lat_grid.shape[0] - 1)
    j1 = min(j0 + 1, lat_grid.shape[1] - 1)
    
    # Bounds check
    if not (0 <= i0 < lat_grid.shape[0] and 0 <= j0 < lat_grid.shape[1]):
        return None, None
    
    # Interpolation weights
    wi, wj = i - i0, j - j0
    
    # Bilinear interpolation formula
    lat = ((1 - wi) * (1 - wj) * lat_grid[i0, j0] +
           (1 - wi) * wj * lat_grid[i0, j1] +
           wi * (1 - wj) * lat_grid[i1, j0] +
           wi * wj * lat_grid[i1, j1])
    
    lon = ((1 - wi) * (1 - wj) * lon_grid[i0, j0] +
           (1 - wi) * wj * lon_grid[i0, j1] +
           wi * (1 - wj) * lon_grid[i1, j0] +
           wi * wj * lon_grid[i1, j1])
    
    return lat, lon


def extract_zones(
    X: np.ndarray,
    Y: np.ndarray,
    C: np.ndarray,
    thresholds: Dict[str, float],
    src_lat: float,
    src_lon: float,
    wind_dir: float,
    verbose: bool = True
) -> Dict[str, Optional[Polygon]]:
    """
    Extract threat zone polygons from concentration field using contour analysis.
    
    This is the universal zone extraction function used by all examples.
    
    Algorithm:
    1. Convert grid coordinates (meters) to lat/lon using wind direction
    2. For each threshold:
       - Find contours at threshold level using scikit-image
       - Select largest contour (closest to source)
       - Apply bilinear interpolation for smooth coordinates
       - Create Polygon from smoothed contour points
    
    Parameters:
    -----------
    X, Y : np.ndarray
        Computational grid arrays (in meters)
        Shape: (NX, NY) for 2D grids
    
    C : np.ndarray
        Concentration field (ppm)
        Shape: (NY, NX) - note transposed for contour finding
    
    thresholds : Dict[str, float]
        Threshold values as {zone_name: ppm_value}
        Examples: {"AEGL-3": 1100, "AEGL-2": 160, "AEGL-1": 30}
        Values can be: float, int, "str", or "value ppm"
    
    src_lat, src_lon : float
        Source location (degrees)
    
    wind_dir : float
        Wind direction in degrees (0-360)
        Used for coordinate rotation
    
    verbose : bool
        If True, print zone extraction progress
    
    Returns:
    --------
    Dict[str, Optional[Polygon]]
        Extracted zones as {zone_name: Polygon or None}
        Polygons are in lat/lon coordinates, ready for mapping
    
    Raises:
    -------
    ImportError
        If core visualization module not available
    
    Examples:
    ---------
    Extract AEGL zones from concentration field:
    
    >>> from core.utils.features import setup_computational_grid
    >>> from core.dispersion_models.gaussian_model import calculate_gaussian_dispersion
    >>> from core.utils.zone_extraction import extract_zones
    >>> 
    >>> # Setup grid and get concentration
    >>> X, Y, _, _ = setup_computational_grid(5000, 5000, 800, 800)
    >>> C, _, _, _ = calculate_gaussian_dispersion(...)
    >>> 
    >>> # Extract zones
    >>> thresholds = {"AEGL-3": 1100, "AEGL-2": 160, "AEGL-1": 30}
    >>> zones = extract_zones(X, Y, C, thresholds, 31.691, 74.082, 270)
    >>> 
    >>> # Use zones for mapping
    >>> for name, poly in zones.items():
    ...     if poly and not poly.is_empty:
    ...         print(f"{name}: {poly.bounds}")
    """
    from ..visualization.folium_maps import meters_to_latlon
    
    zones: Dict[str, Optional[Polygon]] = {}
    
    if verbose:
        logger.debug("Extracting threat zones (wind: %.0f°)", wind_dir)
        logger.debug(
            "Concentration field: min=%.2f max=%.2f ppm",
            np.nanmin(C), np.nanmax(C),
        )
    
    # Convert grid to lat/lon using wind direction rotation
    lat_grid, lon_grid = meters_to_latlon(X, Y, src_lat, src_lon, wind_dir)
    
    max_conc = np.nanmax(C)
    n_thresholds = len(thresholds)
    n_zones_found = 0
    
    for zone_idx, (name, threshold_val) in enumerate(thresholds.items(), 1):
        # Parse threshold value (handles multiple formats)
        threshold = parse_threshold(threshold_val)
        
        if threshold is None or threshold <= 0:
            zones[name] = None
            if verbose:
                logger.debug("%s: invalid/no threshold", name)
            continue
        
        # Skip if threshold exceeds maximum concentration
        if threshold > max_conc:
            zones[name] = None
            if verbose:
                logger.debug("%s (%.1f ppm) > max (%.1f ppm)", name, threshold, max_conc)
            continue
        
        try:
            # Find contours at threshold level
            contours = measure.find_contours(C, threshold)
            
            if not contours:
                zones[name] = None
                if verbose:
                    logger.debug("%s: no contours at %.1f ppm", name, threshold)
                continue
            
            # Use largest contour (closest to source at center)
            largest = max(contours, key=len)
            
            # Apply bilinear interpolation to get smooth coordinates
            coords = []
            for pt in largest:
                i, j = float(pt[0]), float(pt[1])
                lat, lon = bilinear_interpolate_coords(i, j, lat_grid, lon_grid)
                
                if lat is not None and lon is not None:
                    coords.append((lon, lat))
            
            # Create polygon from coordinates
            if len(coords) >= 4:
                zones[name] = Polygon(coords)
                n_zones_found += 1
                if verbose:
                    bounds = zones[name].bounds
                    logger.debug(
                        "%s: %d points, bounds: (%.4f, %.4f) to (%.4f, %.4f)",
                        name, len(coords), bounds[0], bounds[1], bounds[2], bounds[3],
                    )
            else:
                zones[name] = None
                if verbose:
                    logger.debug("%s: insufficient points (%d)", name, len(coords))
        
        except Exception as e:
            zones[name] = None
            if verbose:
                logger.warning("%s: extraction error — %s", name, e)
    
    if verbose:
        logger.debug(
            "Zone extraction complete: %d/%d zones extracted", n_zones_found, n_thresholds
        )
    
    return zones


# Aliases for backward compatibility with different example naming conventions
# Backward compatibility alias
extract_threat_zones_from_concentration = extract_zones
