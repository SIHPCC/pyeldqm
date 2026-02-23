"""
app1/components/__init__.py
===========================
Re-exports every public layout symbol so importers can do:

    from app1.components import create_header, CHEMICAL_OPTIONS, ...
"""

from .header import create_header
from .styles import (
    HEADER_STYLE,
    SIDEBAR_STYLE,
    CONTENT_STYLE,
    CARD_STYLE,
    TAB_STYLE,
    TAB_SELECTED_STYLE,
)
from .slider_controls import create_slider_with_range_control
from .weather_inputs import create_weather_manual_inputs, create_par_weather_manual_inputs
from .tabs import (
    create_threat_zones_content,
    create_chemical_properties_display,
    CHEMICAL_OPTIONS,
    DEFAULT_CHEMICAL,
    create_par_content,
    create_route_optimization_content,
    create_sensor_placement_content,
    create_shelter_analysis_content,
    create_health_impact_content,
)

__all__ = [
    "create_header",
    # styles
    "HEADER_STYLE",
    "SIDEBAR_STYLE",
    "CONTENT_STYLE",
    "CARD_STYLE",
    "TAB_STYLE",
    "TAB_SELECTED_STYLE",
    # controls
    "create_slider_with_range_control",
    "create_weather_manual_inputs",
    "create_par_weather_manual_inputs",
    # tab content
    "create_threat_zones_content",
    "create_chemical_properties_display",
    "CHEMICAL_OPTIONS",
    "DEFAULT_CHEMICAL",
    "create_par_content",
    "create_route_optimization_content",
    "create_sensor_placement_content",
    "create_shelter_analysis_content",
    "create_health_impact_content",
]
