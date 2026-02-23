"""
Gaussian Dispersion Model
=========================
Implements steady-state Gaussian plume dispersion for single- and multi-source
chemical releases.  Supports Pasquill–Gifford stability classes A–F, urban /
rural roughness categories, building downwash, and ground reflection.

Typical usage::

    from core.dispersion_models.gaussian_model import calculate_gaussian_dispersion
    result = calculate_gaussian_dispersion(config)
"""
import numpy as np
from scipy.special import erf
import logging
from .dispersion_utils import get_sigmas, gy, gz
from ..meteorology.stability import get_stability_class
from ..meteorology.wind_profile import wind_speed as calc_wind_profile
from ..utils.geo_constants import METERS_PER_DEGREE_LAT
from datetime import datetime

logger = logging.getLogger(__name__)

#: Universal gas constant in L·atm·mol⁻¹·K⁻¹ (used for g/m³ → ppm conversion)
R_LATM: float = 0.08206

__all__ = ['single_source_concentration', 'get_sigmas', 'multi_source_concentration', 'calculate_gaussian_dispersion']

def single_source_concentration(x, y, z, t, t_r, Q, U, sigma_x, sigma_y, sigma_z, h_s, mode='puff'):
    chi_val = (Q / U) * gy(y, sigma_y) * gz(z, sigma_z, h_s)
    if mode == 'continuous':
        return chi_val
    elif mode == 'puff':
        denom = sigma_x * np.sqrt(2)
        if t <= t_r:
            return (chi_val / 2) * (erf(x / denom) - erf((x - U * t) / denom))
        else:
            return (chi_val / 2) * (erf((x - U * (t - t_r)) / denom) - erf((x - U * t) / denom))
    elif mode == 'instantaneous':
        sigma_i = np.sqrt(2) * sigma_x
        factor = Q / ((2 * np.pi)**(3/2) * sigma_i**2 * sigma_z)
        return factor * np.exp(-x**2 / (2 * sigma_i**2)) * gy(y, sigma_i) * gz(z, sigma_z, h_s)
    else:
        raise ValueError("Invalid mode. Use 'continuous', 'puff', or 'instantaneous'.")


def multi_source_concentration(
    sources,
    x_grid,
    y_grid,
    z,
    t,
    t_r,
    U,
    stability_class,
    roughness='URBAN',
    mode='continuous',
    grid_wind_direction: float = None
):
    """Sum Gaussian contributions from multiple sources on a shared grid.

    Notes:
    - If `grid_wind_direction` is provided (meteorological degrees from North),
      `x_grid`/`y_grid` are assumed to be defined in that wind-aligned frame.
      For any source that specifies `wind_dir`, its contribution is computed by
      rotating coordinates from the grid frame to the source's wind frame.
    - If `grid_wind_direction` is None or a source has no `wind_dir`, the
      function falls back to treating the grid as already aligned for that
      source (legacy behavior).
    - A source may optionally provide its own wind speed `U`.
    """

    total = np.zeros_like(x_grid, dtype=float)

    # Precompute grid-frame rotation to ENU if needed
    cg = sg = None
    if grid_wind_direction is not None:
        theta_grid = np.radians((90.0 - grid_wind_direction) % 360.0)
        cg = np.cos(theta_grid)
        sg = np.sin(theta_grid)

    for src in sources:
        Q = src.get('Q')
        if Q is None:
            continue

        x0 = src.get('x0', 0.0)
        y0 = src.get('y0', 0.0)
        h_s = src.get('h_s', src.get('height', 0.0))
        U_src = src.get('U', U)

        # Coordinates relative to source in the grid frame
        x_rel_grid = x_grid - x0
        y_rel_grid = y_grid - y0

        wind_dir_src = src.get('wind_dir', None)

        if grid_wind_direction is not None and wind_dir_src is not None:
            # Transform from grid frame -> ENU
            x_e = x_rel_grid * cg - y_rel_grid * sg
            y_n = x_rel_grid * sg + y_rel_grid * cg

            # ENU -> source wind-aligned frame (rotate by -theta_src)
            theta_src = np.radians((90.0 - wind_dir_src) % 360.0)
            cs = np.cos(theta_src)
            ss = np.sin(theta_src)
            x_local = x_e * cs + y_n * ss
            y_local = -x_e * ss + y_n * cs
        else:
            # Legacy behavior: assume grid already aligned with this source
            x_local = x_rel_grid
            y_local = y_rel_grid

        if mode == 'instantaneous':
            mask = np.ones_like(x_local, dtype=bool)
            x_for_sigma = np.maximum(np.abs(x_local), 1e-6)
        else:
            mask = x_local > 0
            x_for_sigma = np.where(mask, np.maximum(x_local, 1e-6), 1e-6)

        if not np.any(mask):
            continue

        sig_x, sig_y, sig_z = get_sigmas(x_for_sigma, stability_class, roughness)

        contrib = single_source_concentration(
            x=np.where(mask, x_local, 0.0),
            y=y_local,
            z=z,
            t=t,
            t_r=t_r,
            Q=Q,
            U=U_src,
            sigma_x=sig_x,
            sigma_y=sig_y,
            sigma_z=sig_z,
            h_s=h_s,
            mode=mode
        )

        total = total + np.where(mask, contrib, 0.0)

    return total


def calculate_gaussian_dispersion(
    weather,
    X,
    Y,
    source_lat,
    source_lon,
    molecular_weight,
    default_release_rate,
    default_height,
    z_ref,
    sources=None,
    z_measurement=1.5,
    t=600,
    t_r=600,
    roughness='URBAN',
    mode='continuous',
    latitude=None,
    longitude=None,
    timezone_offset_hrs=0,
    datetime_obj=None
):
    """
    Calculate concentration field using Gaussian dispersion model with geographic sources.

    This function handles coordinate transformations between geographic (lat/lon) and 
    local wind-aligned coordinates, determines atmospheric stability, adjusts wind speeds,
    and calculates concentration fields in ppm.

    Parameters:
    -----------
    weather : dict
        Weather data with keys: 'wind_speed', 'wind_dir', 'temperature_K', 'humidity', 'cloud_cover'
    X : ndarray
        X-coordinates grid (meters) in wind-aligned frame
    Y : ndarray
        Y-coordinates grid (meters) in wind-aligned frame
    source_lat : float
        Primary source latitude (degrees)
    source_lon : float
        Primary source longitude (degrees)
    molecular_weight : float
        Molecular weight of chemical (g/mol)
    default_release_rate : float
        Default release rate (g/s)
    default_height : float
        Default release height (m)
    z_ref : float
        Reference height for wind speed (m)
    sources : list of dict, optional
        Source definitions. Each can have:
        - Local coords: 'x0' (m), 'y0' (m), 'Q' or 'rate' (g/s), 'h_s' or 'height' (m)
        - Geographic coords: 'lat' (deg), 'lon' (deg), 'Q' or 'rate' (g/s), 'h_s' or 'height' (m)
        - 'name': source name (optional)
        - 'color': marker color for visualization (optional)
    z_measurement : float, optional
        Measurement height (m), default 1.5
    t : float, optional
        Time since release start (s), default 600
    t_r : float, optional
        Release duration (s), default 600
    roughness : str, optional
        Surface roughness ('URBAN', 'RURAL', etc.), default 'URBAN'
    mode : str, optional
        Release mode ('continuous', 'puff', 'instantaneous'), default 'continuous'
    latitude : float, optional
        Latitude for stability calculation (defaults to source_lat)
    longitude : float, optional
        Longitude for stability calculation (defaults to source_lon)
    timezone_offset_hrs : float, optional
        Timezone offset in hours for stability calculation, default 0
    datetime_obj : datetime, optional
        Datetime used for atmospheric stability calculation.
        If None, current datetime is used.

    Returns:
    --------
    concentration_ppm : np.ndarray
        2D array of concentration values in ppm
    U_local : float
        Effective wind speed at source height (m/s)
    stability_class : str
        Atmospheric stability class (A-F)
    resolved_sources : list[dict]
        Sources with both local (x0, y0) and geographic (lat, lon) coordinates
    """
    U = weather['wind_speed']
    wind_dir = weather['wind_dir']
    T_k = weather['temperature_K']
    humidity = weather['humidity']
    cloud_cover = weather['cloud_cover']
    
    if latitude is None:
        latitude = source_lat
    if longitude is None:
        longitude = source_lon

    if datetime_obj is None:
        datetime_obj = datetime.now()
    
    logger.info("Calculating Gaussian dispersion...")
    
    # Determine stability class
    try:
        cloudiness_index = int(cloud_cover * 10)
        stability_class = get_stability_class(
            wind_speed=U,
            datetime_obj=datetime_obj,
            latitude=latitude,
            longitude=longitude,
            cloudiness_index=cloudiness_index,
            timezone_offset_hrs=timezone_offset_hrs
        )
    except Exception as e:
        logger.warning("Could not determine stability: %s — defaulting to class D", e)
        stability_class = 'D'
    
    logger.debug("Stability class: %s", stability_class)
    
    # Adjust wind speed for source height
    U_local = calc_wind_profile(
        z_user=default_height,
        z0=z_ref,
        U_user=U,
        stability_class=stability_class
    )
    logger.debug("Adjusted wind speed at %.1f m: %.2f m/s", default_height, U_local)

    # Coordinate transformation helpers
    lat_per_m = 1.0 / METERS_PER_DEGREE_LAT
    lon_per_m = 1.0 / (METERS_PER_DEGREE_LAT * np.cos(np.radians(source_lat)))
    theta = np.radians((90.0 - wind_dir) % 360.0)

    def latlon_to_local(lat, lon):
        """Convert geographic coords to local x,y (meters) aligned with wind."""
        y_rot = (lat - source_lat) / lat_per_m
        x_rot = (lon - source_lon) / lon_per_m
        x_local = x_rot * np.cos(theta) + y_rot * np.sin(theta)
        y_local = -x_rot * np.sin(theta) + y_rot * np.cos(theta)
        return x_local, y_local

    def local_to_latlon(x_local, y_local):
        """Convert local x,y back to geographic coords for mapping markers."""
        x_rot = x_local * np.cos(theta) - y_local * np.sin(theta)
        y_rot = x_local * np.sin(theta) + y_local * np.cos(theta)
        lat = source_lat + y_rot * lat_per_m
        lon = source_lon + x_rot * lon_per_m
        return float(lat), float(lon)

    # Build resolved source list
    resolved_sources = []
    input_sources = sources if sources else [
        {"name": "Default Source", "Q": default_release_rate, "x0": 0.0, "y0": 0.0, "h_s": default_height}
    ]

    for idx, src in enumerate(input_sources):
        Q = src.get("Q", src.get("rate", default_release_rate))
        h_s = src.get("h_s", src.get("height", default_height))

        if "x0" in src and "y0" in src:
            x0 = float(src["x0"])
            y0 = float(src["y0"])
            lat_s, lon_s = local_to_latlon(x0, y0)
        elif "lat" in src and "lon" in src:
            lat_s = float(src["lat"])
            lon_s = float(src["lon"])
            x0, y0 = latlon_to_local(lat_s, lon_s)
        else:
            x0, y0 = 0.0, 0.0
            lat_s, lon_s = source_lat, source_lon

        resolved_sources.append({
            "name": src.get("name", f"Source {idx+1}"),
            "Q": Q,
            "x0": x0,
            "y0": y0,
            "h_s": h_s,
            "U": U_local,
            "wind_dir": wind_dir,
            "lat": lat_s,
            "lon": lon_s,
            "color": src.get("color", "red")
        })

    # Model sources (local coordinates)
    model_sources = [
        {
            "name": s["name"],
            "Q": s["Q"],
            "x0": s["x0"],
            "y0": s["y0"],
            "h_s": s["h_s"],
            "U": U_local,
            "wind_dir": wind_dir
        }
        for s in resolved_sources
    ]
    
    # Calculate concentration field
    try:
        concentration_field = multi_source_concentration(
            sources=model_sources,
            x_grid=X,
            y_grid=Y,
            z=z_measurement,
            t=t,
            t_r=t_r,
            U=U_local,
            stability_class=stability_class,
            roughness=roughness,
            mode=mode,
            grid_wind_direction=wind_dir
        )
        
        # Convert from g/m³ to ppm
        Vm = R_LATM * T_k  # L·mol⁻¹ at 1 atm
        concentration_ppm = concentration_field * (Vm / molecular_weight) * 1000
        
        logger.info("Max concentration: %.1f ppm", concentration_ppm.max())
        if concentration_ppm.max() > 0:
            logger.debug(
                "Mean concentration (>0): %.1f ppm",
                concentration_ppm[concentration_ppm > 0].mean(),
            )
        
        return concentration_ppm, U_local, stability_class, resolved_sources
        
    except Exception as e:
        logger.exception("Error in dispersion calculation: %s", e)
        raise
