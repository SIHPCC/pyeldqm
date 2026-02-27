"""
app/utils/script_generator
===========================
Package that produces standalone, runnable Python example scripts for each
analysis tab in the pyELDQM Dash application.

Exports
-------
generate_threat_zones_script  – Chemical Threat Zones tab
generate_par_script           – Population At Risk tab
generate_route_script         – Emergency Routes tab
generate_sensor_script        – Sensor Placement tab
generate_health_impact_script – Health Impact tab
generate_shelter_script       – Shelter Status tab
"""

from .threat_zones import generate_threat_zones_script
from .par_analysis import generate_par_script
from .route_optimization import generate_route_script
from .sensor_placement import generate_sensor_script
from .health_impact import generate_health_impact_script
from .shelter_analysis import generate_shelter_script

__all__ = [
    "generate_threat_zones_script",
    "generate_par_script",
    "generate_route_script",
    "generate_sensor_script",
    "generate_health_impact_script",
    "generate_shelter_script",
]
