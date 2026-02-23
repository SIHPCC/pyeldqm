"""
Dynamic slider range-adjustment callback factory.

Each slider has increase/decrease buttons that expand or shrink the
min/max range while keeping the current value in view.
"""
import dash
from dash import Input, Output, State
import numpy as np


# ─────────────────────────────────────────────────
# Slider configuration registry
# ─────────────────────────────────────────────────

SLIDER_CONFIGS = {
    "wind-speed": {
        "range_increment": 5,
        "min_limit": 0,
        "max_limit": 50,
        "step": 0.5,
        "unit": " m/s",
    },
    "wind-direction": {
        "range_increment": 90,
        "min_limit": 0,
        "max_limit": 360,
        "step": 5,
        "unit": "°",
    },
    "temperature": {
        "range_increment": 10,
        "min_limit": -50,
        "max_limit": 100,
        "step": 1,
        "unit": "°C",
    },
    "humidity": {
        "range_increment": 20,
        "min_limit": 0,
        "max_limit": 100,
        "step": 5,
        "unit": "%",
    },
    "cloud-cover": {
        "range_increment": 20,
        "min_limit": 0,
        "max_limit": 100,
        "step": 5,
        "unit": "%",
    },
    "par-wind-speed": {
        "range_increment": 5,
        "min_limit": 0,
        "max_limit": 50,
        "step": 0.5,
        "unit": " m/s",
    },
    "par-wind-direction": {
        "range_increment": 90,
        "min_limit": 0,
        "max_limit": 360,
        "step": 5,
        "unit": "°",
    },
    "par-temperature": {
        "range_increment": 10,
        "min_limit": -50,
        "max_limit": 100,
        "step": 1,
        "unit": "°C",
    },
    "par-humidity": {
        "range_increment": 20,
        "min_limit": 0,
        "max_limit": 100,
        "step": 5,
        "unit": "%",
    },
    "par-cloud-cover": {
        "range_increment": 20,
        "min_limit": 0,
        "max_limit": 100,
        "step": 5,
        "unit": "%",
    },
    "release-rate": {
        "range_increment": 500,
        "min_limit": 10,
        "max_limit": 10000,
        "step": 10,
        "unit": " kg/hr",
    },
    "tank-height": {
        "range_increment": 5,
        "min_limit": 0.1,
        "max_limit": 100,
        "step": 0.1,
        "unit": " m",
    },
}


# ─────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────

def _make_marks(min_val, max_val, unit=""):
    """Generate 5 evenly-spaced slider marks between min_val and max_val."""
    steps = np.linspace(min_val, max_val, 5)
    return {float(v): f"{v:.4g}{unit}" for v in steps}


def create_range_adjustment_callback(app, slider_id, param_config):
    """
    Register a single slider range-adjustment callback.

    The callback reacts to increase / decrease button clicks and updates
    the slider's min, max, marks, and the paired ``{slider_id}-range`` Store.
    """
    range_increment = param_config.get("range_increment", 10)
    absolute_min = param_config.get("min_limit", 0)
    absolute_max = param_config.get("max_limit", 100)
    unit = param_config.get("unit", "")

    @app.callback(
        [Output(slider_id, "min"),
         Output(slider_id, "max"),
         Output(slider_id, "marks"),
         Output(f"{slider_id}-range", "data")],
        [Input(f"{slider_id}-increase", "n_clicks"),
         Input(f"{slider_id}-decrease", "n_clicks")],
        [State(f"{slider_id}-range", "data"),
         State(slider_id, "value")],
        prevent_initial_call=True,
    )
    def _adjust(_inc, _dec, range_data, current_value,
                _id=slider_id,
                _step=range_increment,
                _abs_min=absolute_min,
                _abs_max=absolute_max,
                _unit=unit):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        increasing = trigger_id == f"{_id}-increase"

        # Determine current range boundaries
        if isinstance(range_data, dict):
            current_min = float(range_data.get("min", _abs_min))
            current_max = float(range_data.get("max", _abs_max))
        else:
            current_min = float(_abs_min)
            current_max = float(_abs_max)

        if increasing:
            new_min = max(_abs_min, current_min - _step)
            new_max = min(_abs_max, current_max + _step)
        else:
            # Shrink range toward current value (don't cross the current value)
            cv = float(current_value) if current_value is not None else (current_min + current_max) / 2
            new_min = min(current_min + _step, cv)
            new_max = max(current_max - _step, cv)
            # Ensure at least a small range
            if new_max - new_min < _step:
                midpoint = (new_min + new_max) / 2
                new_min = max(_abs_min, midpoint - _step / 2)
                new_max = min(_abs_max, midpoint + _step / 2)

        new_marks = _make_marks(new_min, new_max, _unit)
        new_range_data = {"min": new_min, "max": new_max}
        return new_min, new_max, new_marks, new_range_data


def register(app):
    """Register all slider range-adjustment callbacks."""
    for slider_id, config in SLIDER_CONFIGS.items():
        create_range_adjustment_callback(app, slider_id, config)
