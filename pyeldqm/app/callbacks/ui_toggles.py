"""
UI toggle/collapse callbacks — show/hide sections, collapse panels,
receptor height range adjustment.
"""
import dash
from dash import Input, Output, State, ALL, ctx, html


def register(app):  # noqa: C901

    # ── Datetime input visibility ─────────────────────────────────────────────
    app.callback(
        Output("threat-datetime-input-container", "style"),
        Input("threat-datetime-mode", "value"),
    )(toggle_threat_datetime_input)

    # ── Source-term mode: show duration vs mass-released ─────────────────────
    app.callback(
        [Output("duration-container", "style"),
         Output("mass-released-container", "style")],
        Input("source-term-mode", "value"),
    )(toggle_source_term_inputs)

    # ── Number-of-sources visibility ─────────────────────────────────────────
    app.callback(
        Output("num-sources-container", "style"),
        Input("release-type", "value"),
    )(toggle_num_sources)

    # ── Receptor height range controls ────────────────────────────────────────
    app.callback(
        [Output("receptor-height", "min"),
         Output("receptor-height", "max"),
         Output("receptor-height-range", "data")],
        [Input("receptor-height-increase", "n_clicks"),
         Input("receptor-height-decrease", "n_clicks")],
        [State("receptor-height-range", "data")],
        prevent_initial_call=True,
    )(adjust_receptor_height_range)

    app.callback(
        Output("receptor-height", "marks"),
        Input("receptor-height-range", "data"),
    )(update_receptor_height_marks)

    # ── Map / section collapse toggles ────────────────────────────────────────
    for toggle_id, collapse_id in [
        ("threat-zone-map-toggle", "threat-zone-map-collapse"),
        ("par-map-toggle", "par-map-collapse"),
        ("route-map-toggle", "route-map-collapse"),
        ("sensor-map-toggle", "sensor-map-collapse"),
        ("shelter-map-toggle", "shelter-map-collapse"),
        ("health-map-toggle", "health-map-collapse"),
        ("chem-properties-toggle", "chem-properties-collapse"),
        ("sim-conditions-toggle", "sim-conditions-collapse"),
        ("zone-distances-toggle", "zone-distances-collapse"),
        ("analytics-toggle", "analytics-collapse"),
    ]:
        _register_collapse_toggle(app, toggle_id, collapse_id)

    # ── Health-impact advanced container style ───────────────────────────────
    app.callback(
        [Output("health-advanced-parameters-container", "style")],
        Input("health-parameter-source-mode", "value"),
        prevent_initial_call=True,
    )(_update_health_advanced_container_style)


# ─────────────────────────────────────────────────
# Pure helper functions
# ─────────────────────────────────────────────────

def toggle_threat_datetime_input(datetime_mode):
    if datetime_mode == "specific":
        return {"display": "block", "marginBottom": "0.5rem"}
    return {"display": "none", "marginBottom": "0.5rem"}


def toggle_source_term_inputs(source_term_mode):
    if source_term_mode == "instantaneous":
        return {"display": "none"}, {"display": "block"}
    return {"display": "block"}, {"display": "none"}


def toggle_num_sources(release_type):
    if release_type == "multi":
        return {"display": "block"}
    return {"display": "none"}


def adjust_receptor_height_range(inc_clicks, dec_clicks, range_data):
    if range_data is None:
        range_data = {"min": 0.01, "max": 10, "step": 0.1}

    current_min = range_data.get("min", 0.01)
    current_max = range_data.get("max", 10)
    step = range_data.get("step", 0.1)

    if ctx.triggered_id == "receptor-height-increase":
        new_min = max(current_min - step, 0.001)
        new_max = min(current_max + step, 20)
    elif ctx.triggered_id == "receptor-height-decrease":
        new_min = min(current_min + step, current_max - step)
        new_max = max(current_max - step, current_min + step)
    else:
        new_min = current_min
        new_max = current_max

    new_range_data = {"min": new_min, "max": new_max, "step": step}
    return new_min, new_max, new_range_data


def update_receptor_height_marks(range_data):
    if range_data is None:
        range_data = {"min": 0.01, "max": 10, "step": 0.1}

    min_val = range_data.get("min", 0.01)
    max_val = range_data.get("max", 10)

    marks = {}
    marks[round(min_val, 2)] = f"{round(min_val, 2)}"
    current = 2
    while current < max_val:
        marks[current] = str(current)
        current += 2
    marks[round(max_val, 2)] = f"{round(max_val, 2)}"
    return marks


def _update_health_advanced_container_style(source_mode):
    if source_mode == "threat":
        return [{"pointerEvents": "none", "opacity": "0.55"}]
    return [{}]


def _register_collapse_toggle(app, toggle_id, collapse_id):
    """Register a pair of (toggle-button, collapse) callbacks."""

    @app.callback(
        [Output(collapse_id, "is_open"),
         Output(toggle_id, "children")],
        Input(toggle_id, "n_clicks"),
        State(collapse_id, "is_open"),
        prevent_initial_call=True,
    )
    def _toggle(n_clicks, is_open, _tid=toggle_id):  # _tid captures binding
        if n_clicks is None:
            return is_open, html.I(className="fas fa-chevron-up", style={"fontSize": "0.8rem"})
        new_state = not is_open
        icon_cls = "fas fa-chevron-down" if new_state else "fas fa-chevron-up"
        return new_state, html.I(className=icon_cls, style={"fontSize": "0.8rem"})
