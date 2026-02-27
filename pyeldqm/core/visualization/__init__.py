"""
Visualization module for pyELDQM.

Provides interactive and static visualization tools for dispersion modeling results.
"""

from .folium_maps import (
    create_dispersion_map,
    meters_to_latlon,
    save_map,
    add_concentration_contour,
    add_wind_rose,
    get_hazard_color,
    create_heatmap_layer,
    add_facility_markers,
    fit_map_to_polygons,
)

from .info_panels import (
    ensure_layer_control,
    add_par_info_panel,
    add_evacuation_info_panel,
    add_shelter_in_place_panel,
    add_health_thresholds_panel,
    add_sensor_optimization_panel,
    add_threat_zones_info_panel,
    add_threat_zones_and_par_panel,
)
from .zone_layers import (
    add_zone_polygons,
)

__all__ = [
    'create_dispersion_map',
    'meters_to_latlon',
    'save_map',
    'add_concentration_contour',
    'add_wind_rose',
    'get_hazard_color',
    'create_heatmap_layer',
    'add_facility_markers',
    'fit_map_to_polygons',
    'ensure_layer_control',
    'add_par_info_panel',
    'add_evacuation_info_panel',
    'add_shelter_in_place_panel',
    'add_health_thresholds_panel',
    'add_sensor_optimization_panel',
    'add_threat_zones_info_panel',
    'add_threat_zones_and_par_panel',
    'add_zone_polygons',
]
