"""
Callback registry.

Call ``register_all_callbacks(app)`` once from the app factory after
``app.layout`` has been set.  Each sub-module exposes a ``register(app)``
function that contains all its callback definitions.
"""

from . import (
    routing,
    shared_state,
    threat_zones,
    par_analysis,
    route_optimization,
    sensor_placement,
    shelter_analysis,
    health_impact,
    weather,
    ui_toggles,
    slider_factory,
)


def register_all_callbacks(app):
    """Register every callback module with the Dash app instance."""
    routing.register(app)
    shared_state.register(app)
    threat_zones.register(app)
    par_analysis.register(app)
    route_optimization.register(app)
    sensor_placement.register(app)
    shelter_analysis.register(app)
    health_impact.register(app)
    weather.register(app)
    ui_toggles.register(app)
    slider_factory.register(app)   # must be last — registers 12 dynamic callbacks
