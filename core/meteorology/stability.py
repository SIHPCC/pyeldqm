"""
Atmospheric Stability Classification
=====================================
Functions for determining Pasquill-Gifford atmospheric stability classes
based on meteorological conditions.
"""

import numpy as np
from datetime import datetime
from .solar_radiation import solar_insolation, classify_insolation

__all__ = ['get_stability_class']


def get_stability_class(wind_speed, datetime_obj, latitude, longitude, cloudiness_index, timezone_offset_hrs=5):
    """
    Determine Pasquill-Gifford atmospheric stability class.
    
    Parameters:
    -----------
    wind_speed : float
        Wind speed (m/s) at 10 m height
    datetime_obj : datetime
        Current date and time
    latitude : float
        Latitude in degrees
    longitude : float
        Longitude in degrees
    cloudiness_index : int
        Cloud cover index (0-10)
    timezone_offset_hrs : float, optional
        Timezone offset from UTC (default: 5)
    
    Returns:
    --------
    str : Stability class ('A' through 'F')
        A - Extremely unstable
        B - Moderately unstable
        C - Slightly unstable
        D - Neutral
        E - Slightly stable
        F - Moderately stable
    """
    stability_table = {
        'day': {
            'strong':   ['A', 'B', 'B', 'C', 'C'],
            'moderate': ['B', 'B', 'C', 'D', 'D'],
            'slight':   ['B', 'C', 'C', 'D', 'D']
        },
        'night': {
            '>50%':     ['E', 'E', 'D', 'D', 'D'],
            '<50%':     ['F', 'F', 'E', 'D', 'D']
        }
    }
    if wind_speed < 2:
        idx = 0
    elif wind_speed < 3:
        idx = 1
    elif wind_speed < 5:
        idx = 2
    elif wind_speed < 6:
        idx = 3
    else:
        idx = 4
    Fs, _ = solar_insolation(datetime_obj, latitude, longitude, cloudiness_index, timezone_offset_hrs)
    insolation_category = classify_insolation(Fs)
    if insolation_category:
        return stability_table['day'][insolation_category][idx]
    else:
        cloud_cat = '>50%' if cloudiness_index >= 5 else '<50%'
        return stability_table['night'][cloud_cat][idx]
