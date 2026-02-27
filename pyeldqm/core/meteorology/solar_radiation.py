"""
Solar Radiation and Insolation Calculations
============================================
Functions for calculating solar radiation flux and classifying insolation levels
for atmospheric stability and dispersion modeling.
"""

import numpy as np
from datetime import datetime

__all__ = ['solar_insolation', 'classify_insolation']


def solar_insolation(datetime_obj, latitude_deg, longitude_deg, cloudiness_index, timezone_offset_hrs):
    """
    Calculate solar insolation flux based on sun position and cloud cover.
    
    Parameters:
    -----------
    datetime_obj : datetime
        Current date and time
    latitude_deg : float
        Latitude in degrees (positive for North, negative for South)
    longitude_deg : float
        Longitude in degrees (positive for East, negative for West)
    cloudiness_index : int
        Cloud cover index (0-10, where 0=clear sky, 10=overcast)
    timezone_offset_hrs : float
        Timezone offset from UTC in hours
    
    Returns:
    --------
    tuple : (Fs, sin_phi_s)
        - Fs: Solar insolation flux (W/m²)
        - sin_phi_s: Sine of solar elevation angle
    
    Notes:
    ------
    - Based on solar position calculation using Julian day and hour angle
    - Includes cloud cover correction
    - Returns 0 when sun is below horizon (sin_phi_s <= 0.1)
    """
    deg2rad = 2 * np.pi / 360
    phi = latitude_deg * deg2rad
    J = datetime_obj.timetuple().tm_yday
    Z_local = datetime_obj.hour + datetime_obj.minute / 60 + datetime_obj.second / 3600
    
    # Calculate local solar time
    standard_meridian = timezone_offset_hrs * 15
    lst = Z_local + (4 * (standard_meridian - longitude_deg)) / 60
    
    # Solar declination
    delta = 23.45 * deg2rad * np.sin(deg2rad * 0.986 * (J - 80))
    
    # Hour angle
    H = deg2rad * 15 * (lst - 12)
    
    # Solar elevation angle
    sin_phi_s = np.sin(delta) * np.sin(phi) + np.cos(delta) * np.cos(phi) * np.cos(H)
    
    # Calculate solar flux with cloud correction
    if sin_phi_s > 0.1:
        Fs = 1111 * (1 - 0.0071 * cloudiness_index ** 2) * (sin_phi_s - 0.1)
    else:
        Fs = 0
    
    return Fs, sin_phi_s


def classify_insolation(Fs):
    """
    Classify solar insolation level for Pasquill-Gifford stability determination.
    
    Parameters:
    -----------
    Fs : float
        Solar insolation flux (W/m²)
    
    Returns:
    --------
    str or None
        Insolation category: 'strong', 'moderate', 'slight', or None (nighttime)
    
    Classification:
    ---------------
    - Strong: Fs > 851 W/m²
    - Moderate: 520 < Fs <= 851 W/m²
    - Slight: 176 < Fs <= 520 W/m²
    - None: Fs <= 176 W/m² (nighttime or heavily overcast)
    """
    if Fs > 851:
        return 'strong'
    elif 851 >= Fs > 520:
        return 'moderate'
    elif 520 >= Fs > 176:
        return 'slight'
    else:
        return None
