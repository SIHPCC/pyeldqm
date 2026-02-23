"""
Shelter-in-Place Analysis for pyELDQM

Determines when sheltering indoors is safer than evacuation based on:
- Indoor concentration buildup over time
- Building air exchange rates and protection factors
- Distance from source and outdoor concentration
- Exposure reduction comparison

References:
- EPA 452/R-99-013: Building Air Exchange Rates
- FEMA CPG 1-8A: Guide for All-Hazard Emergency Operations Planning
"""
from typing import Dict, Optional, Tuple
import math
import numpy as np
from shapely.geometry import Point, Polygon


# Building types with typical air exchange rates (ACH - Air Changes per Hour)
BUILDING_TYPES = {
    "residential_tight": {
        "ach_normal": 0.5,      # Tight modern construction
        "ach_sealed": 0.2,      # Windows/doors sealed, HVAC off
        "protection_factor": 10  # Outdoor/indoor concentration ratio when sealed
    },
    "residential_leaky": {
        "ach_normal": 1.5,      # Older construction
        "ach_sealed": 0.5,
        "protection_factor": 5
    },
    "commercial": {
        "ach_normal": 2.0,      # Office/retail
        "ach_sealed": 0.8,
        "protection_factor": 3
    },
    "industrial": {
        "ach_normal": 4.0,      # Warehouse/factory
        "ach_sealed": 1.5,
        "protection_factor": 2
    }
}


def calculate_indoor_concentration(
    outdoor_conc: float,
    time_minutes: float,
    ach: float = 0.5,
    initial_indoor_conc: float = 0.0
) -> float:
    """
    Calculate indoor concentration buildup over time.
    
    Uses exponential buildup model:
    C_in(t) = C_out * (1 - exp(-ACH * t)) + C_in(0) * exp(-ACH * t)
    
    Parameters:
    -----------
    outdoor_conc : float
        Outdoor concentration (ppm or mg/m³)
    time_minutes : float
        Exposure time (minutes)
    ach : float
        Air Changes per Hour
    initial_indoor_conc : float
        Initial indoor concentration (default 0)
    
    Returns:
    --------
    float : Indoor concentration at time t
    """
    time_hours = time_minutes / 60.0
    decay_factor = math.exp(-ach * time_hours)
    
    C_in = outdoor_conc * (1 - decay_factor) + initial_indoor_conc * decay_factor
    return C_in


def shelter_protection_factor(
    outdoor_conc: float,
    building_type: str = "residential_tight",
    time_minutes: float = 60.0,
    sealed: bool = True
) -> Dict:
    """
    Calculate protection provided by sheltering indoors.
    
    Parameters:
    -----------
    outdoor_conc : float
        Peak outdoor concentration (ppm)
    building_type : str
        Type of building (see BUILDING_TYPES)
    time_minutes : float
        Duration of sheltering (minutes)
    sealed : bool
        Whether building is sealed (windows closed, HVAC off)
    
    Returns:
    --------
    dict with keys:
        - indoor_conc: Indoor concentration after time_minutes
        - protection_factor: Outdoor/indoor ratio
        - dose_reduction: % reduction in cumulative dose
        - building_type: Building type used
    """
    if building_type not in BUILDING_TYPES:
        building_type = "residential_tight"
    
    bldg = BUILDING_TYPES[building_type]
    ach = bldg["ach_sealed"] if sealed else bldg["ach_normal"]
    
    # Calculate indoor concentration
    indoor_conc = calculate_indoor_concentration(outdoor_conc, time_minutes, ach)
    
    # Protection factor
    if indoor_conc > 0:
        pf = outdoor_conc / indoor_conc
    else:
        pf = bldg["protection_factor"]
    
    # Dose reduction (simplified: assumes constant outdoor conc)
    # Integrated dose over time
    time_hours = time_minutes / 60.0
    outdoor_dose = outdoor_conc * time_hours
    
    # Indoor dose with exponential buildup
    if ach > 0:
        indoor_dose = outdoor_conc * (time_hours - (1 - math.exp(-ach * time_hours)) / ach)
    else:
        indoor_dose = 0
    
    dose_reduction_pct = ((outdoor_dose - indoor_dose) / outdoor_dose * 100) if outdoor_dose > 0 else 0
    
    return {
        "indoor_conc": indoor_conc,
        "outdoor_conc": outdoor_conc,
        "protection_factor": pf,
        "dose_reduction_pct": dose_reduction_pct,
        "building_type": building_type,
        "ach": ach,
        "time_minutes": time_minutes
    }


def compare_protective_actions(
    outdoor_conc: float,
    distance_from_source_m: float,
    building_type: str = "residential_tight",
    evacuation_time_minutes: float = 15.0,
    sheltering_time_minutes: float = 60.0
) -> Dict:
    """
    Compare shelter-in-place vs evacuation.
    
    Parameters:
    -----------
    outdoor_conc : float
        Peak outdoor concentration at this location (ppm)
    distance_from_source_m : float
        Distance from hazard source (meters)
    building_type : str
        Building type for sheltering
    evacuation_time_minutes : float
        Time to evacuate (minutes) - exposed to outdoor conc during travel
    sheltering_time_minutes : float
        Duration of sheltering (minutes)
    
    Returns:
    --------
    dict with recommendation and comparison metrics
    """
    # Shelter-in-place analysis
    shelter_result = shelter_protection_factor(
        outdoor_conc, building_type, sheltering_time_minutes, sealed=True
    )
    
    # Evacuation exposure (assume full outdoor exposure during travel)
    evac_dose = outdoor_conc * (evacuation_time_minutes / 60.0)
    
    # Shelter dose
    time_hours = sheltering_time_minutes / 60.0
    ach = shelter_result["ach"]
    if ach > 0:
        shelter_dose = outdoor_conc * (time_hours - (1 - math.exp(-ach * time_hours)) / ach)
    else:
        shelter_dose = 0
    
    # Decision thresholds
    # If very close to source (< 200m) or very high conc, evacuate
    # If sheltering provides > 3x protection, shelter
    if distance_from_source_m < 200:
        recommendation = "EVACUATE"
        reason = "Too close to source - evacuate immediately"
    elif outdoor_conc > 1000:  # Very high concentration
        recommendation = "EVACUATE"
        reason = "Extremely high concentration - evacuate if safe route available"
    elif shelter_result["protection_factor"] > 3 and shelter_dose < evac_dose:
        recommendation = "SHELTER-IN-PLACE"
        reason = f"Sheltering provides {shelter_result['protection_factor']:.1f}x protection"
    elif shelter_dose < evac_dose * 0.7:
        recommendation = "SHELTER-IN-PLACE"
        reason = "Sheltering reduces exposure significantly"
    else:
        recommendation = "EVACUATE"
        reason = "Evacuation preferred - safer to leave area"
    
    return {
        "recommendation": recommendation,
        "reason": reason,
        "shelter_dose": shelter_dose,
        "evacuation_dose": evac_dose,
        "dose_ratio": evac_dose / shelter_dose if shelter_dose > 0 else float('inf'),
        "protection_factor": shelter_result["protection_factor"],
        "indoor_conc": shelter_result["indoor_conc"],
        "outdoor_conc": outdoor_conc,
        "distance_m": distance_from_source_m
    }


def recommend_protective_action(
    point: Tuple[float, float],
    source_lat: float,
    source_lon: float,
    concentration_at_point: float,
    aegl_level: Optional[str] = None,
    building_type: str = "residential_tight",
    evacuation_time_minutes: float = 15.0,
    sheltering_time_minutes: float = 60.0
) -> Dict:
    """
    Recommend protective action for a specific location.
    
    Parameters:
    -----------
    point : Tuple[float, float]
        (latitude, longitude) of location
    source_lat, source_lon : float
        Hazard source coordinates
    concentration_at_point : float
        Concentration at this point (ppm)
    aegl_level : str, optional
        AEGL zone (AEGL-1, AEGL-2, AEGL-3)
    building_type : str
        Building type for shelter analysis
    
    Returns:
    --------
    dict with recommendation and details
    """
    # Calculate distance (Haversine approximation)
    lat1, lon1 = math.radians(point[0]), math.radians(point[1])
    lat2, lon2 = math.radians(source_lat), math.radians(source_lon)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance_m = 6371000 * c  # Earth radius in meters
    
    # Compare actions
    comparison = compare_protective_actions(
        outdoor_conc=concentration_at_point,
        distance_from_source_m=distance_m,
        building_type=building_type,
        evacuation_time_minutes=evacuation_time_minutes,
        sheltering_time_minutes=sheltering_time_minutes
    )
    
    comparison["aegl_level"] = aegl_level
    comparison["location"] = {"lat": point[0], "lon": point[1]}
    
    return comparison


def analyze_shelter_zones(
    threat_zones: Dict[str, Optional[Polygon]],
    source_lat: float,
    source_lon: float,
    grid_points: int = 20,
    building_type: str = "residential_tight",
    evacuation_time_minutes: float = 15.0,
    sheltering_time_minutes: float = 60.0
) -> Dict:
    """
    Analyze protective action recommendations across threat zones.
    
    Parameters:
    -----------
    threat_zones : dict
        AEGL threat zone polygons {zone_name: Polygon}
    source_lat, source_lon : float
        Hazard source coordinates
    grid_points : int
        Number of sample points per zone
    building_type : str
        Building type for analysis
    
    Returns:
    --------
    dict with zone-by-zone recommendations and statistics
    """
    results = {}
    
    for zone_name, zone_poly in threat_zones.items():
        if zone_poly is None or zone_poly.is_empty:
            continue
        
        # Sample points within zone
        bounds = zone_poly.bounds  # (minx, miny, maxx, maxy)
        sample_lats = np.linspace(bounds[1], bounds[3], grid_points)
        sample_lons = np.linspace(bounds[0], bounds[2], grid_points)
        
        shelter_count = 0
        evacuate_count = 0
        samples = []
        
        for lat in sample_lats:
            for lon in sample_lons:
                pt = Point(lon, lat)
                if zone_poly.contains(pt):
                    # Estimate concentration based on zone
                    if zone_name == "AEGL-3":
                        conc = 1100  # ppm
                    elif zone_name == "AEGL-2":
                        conc = 160
                    elif zone_name == "AEGL-1":
                        conc = 30
                    else:
                        conc = 10
                    
                    rec = recommend_protective_action(
                        (lat, lon), source_lat, source_lon, conc, zone_name, building_type,
                        evacuation_time_minutes=evacuation_time_minutes,
                        sheltering_time_minutes=sheltering_time_minutes
                    )
                    
                    samples.append(rec)
                    if rec["recommendation"] == "SHELTER-IN-PLACE":
                        shelter_count += 1
                    else:
                        evacuate_count += 1
        
        total = shelter_count + evacuate_count
        
        results[zone_name] = {
            "total_samples": total,
            "shelter_count": shelter_count,
            "evacuate_count": evacuate_count,
            "shelter_percentage": (shelter_count / total * 100) if total > 0 else 0,
            "primary_recommendation": "SHELTER" if shelter_count > evacuate_count else "EVACUATE",
            "sample_recommendations": samples[:5]  # First 5 for inspection
        }
    
    return results
