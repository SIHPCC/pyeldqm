"""
Weather + source-parameter callbacks:
 - update_weather_inputs / update_par_weather_inputs
 - update_equivalent_mass
 - update_source_parameters (dynamic single/multi source inputs)
 - geolocation callbacks
 - auto-refresh visibility / settings
"""
import dash
from dash import Input, Output, State, ALL, html
import dash_bootstrap_components as dbc
from datetime import datetime


def register(app):  # noqa: C901

    # ── Weather panel (main sidebar) ─────────────────────────────────────────
    app.callback(
        Output("weather-inputs", "children"),
        Input("weather-mode", "value"),
    )(update_weather_inputs)

    # ── Weather panel (PAR sidebar) ──────────────────────────────────────────
    app.callback(
        Output("par-weather-inputs", "children"),
        Input("par-weather-mode", "value"),
    )(update_par_weather_inputs)

    # ── Equivalent mass note ─────────────────────────────────────────────────
    app.callback(
        [Output("mass-released", "value"),
         Output("mass-equivalence-note", "children")],
        [Input("source-term-mode", "value"),
         Input("release-type", "value"),
         Input("release-rate", "value"),
         Input("duration", "value"),
         Input({"type": "multi-release-rate", "index": ALL}, "value")],
        State("mass-released", "value"),
        prevent_initial_call=False,
    )(update_equivalent_mass)

    # ── Dynamic source-parameters container ──────────────────────────────────
    app.callback(
        Output("source-parameters-container", "children"),
        [Input("release-type", "value"),
         Input("num-sources", "value")],
    )(update_source_parameters)

    # ── Geolocation ───────────────────────────────────────────────────────────
    app.callback(
        Output("geolocation", "update_now"),
        Input("location-mode", "value"),
        prevent_initial_call=False,
    )(trigger_geolocation_update)

    app.callback(
        [Output("manual-location-inputs", "style"),
         Output("current-location-display", "style"),
         Output("latitude", "value"),
         Output("longitude", "value")],
        [Input("location-mode", "value"),
         Input("geolocation", "position")],
        [State("latitude", "value"),
         State("longitude", "value")],
        prevent_initial_call=False,
    )(update_location_based_on_mode)

    app.callback(
        Output("current-location-display", "children"),
        [Input("geolocation", "position"),
         Input("geolocation", "position_error"),
         Input("location-mode", "value")],
        prevent_initial_call=False,
    )(update_current_location_display)

    # ── Auto-refresh ──────────────────────────────────────────────────────────
    app.callback(
        Output("auto-refresh-container", "style"),
        Input("weather-mode", "value"),
    )(toggle_auto_refresh_visibility)

    app.callback(
        [Output("auto-refresh-interval", "disabled"),
         Output("auto-refresh-interval", "interval"),
         Output("auto-refresh-interval", "n_intervals"),
         Output("auto-refresh-status", "children")],
        [Input("auto-refresh-enabled", "value"),
         Input("refresh-interval", "value"),
         Input("weather-mode", "value")],
        prevent_initial_call=False,
    )(update_auto_refresh_settings)

    # ── Reset-app (page reload) ───────────────────────────────────────────────
    app.callback(
        Output("app-location", "href"),
        Input("reset-app-btn", "n_clicks"),
        State("app-location", "href"),
        prevent_initial_call=True,
    )(reset_app_state)


# ─────────────────────────────────────────────────
# Pure callback functions
# ─────────────────────────────────────────────────

def update_weather_inputs(mode):
    from ..components.weather_inputs import create_weather_manual_inputs
    if mode == "manual":
        return html.Div([create_weather_manual_inputs()])
    return html.Div([
        dbc.Alert([
            html.I(className="fas fa-cloud-download-alt", style={"marginRight": "0.5rem"}),
            "Fetching weather from Open-Meteo API...",
        ], color="info"),
        html.Div([create_weather_manual_inputs()], style={"display": "none"}),
    ])


def update_par_weather_inputs(mode):
    from ..components.weather_inputs import create_par_weather_manual_inputs
    if mode == "manual":
        return html.Div([create_par_weather_manual_inputs()])
    return html.Div([
        dbc.Alert([
            html.I(className="fas fa-cloud-download-alt", style={"marginRight": "0.5rem"}),
            "Fetching weather from Open-Meteo API...",
        ], color="info"),
        html.Div([create_par_weather_manual_inputs()], style={"display": "none"}),
    ])


def update_equivalent_mass(source_term_mode, release_type, release_rate, duration_minutes, multi_rates, current_mass):
    try:
        duration_min = float(duration_minutes) if duration_minutes is not None else 30.0
    except (ValueError, TypeError):
        duration_min = 30.0
    duration_min = max(duration_min, 0.0)

    if release_type == "multi":
        total_rate = sum(max(float(r or 0), 0.0) for r in (multi_rates or []))
    else:
        try:
            total_rate = max(float(release_rate or 0), 0.0)
        except (ValueError, TypeError):
            total_rate = 0.0

    equivalent_mass_kg = (total_rate * duration_min * 60.0) / 1000.0
    note = html.Small(
        f"Equivalent mass for same total release: {equivalent_mass_kg:.2f} kg (Mass = Rate × Duration).",
        style={"color": "#6c757d"},
    )
    if source_term_mode == "instantaneous":
        return round(equivalent_mass_kg, 3), note
    return current_mass, note


def update_source_parameters(release_type, num_sources):
    from ..components.slider_controls import create_slider_with_range_control
    from dash import dcc

    if num_sources is None or num_sources < 2:
        num_sources = 2

    multi_sources = []
    for i in range(int(num_sources)):
        source_num = i + 1
        multi_sources.append(html.Div([
            html.Div([
                html.I(className="fas fa-map-pin", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                f"Source {source_num}",
            ], style={"fontSize": "0.9rem", "fontWeight": "700", "color": "#1f77b4",
                      "marginTop": "0.75rem", "marginBottom": "0.5rem"}),
            html.Hr(style={"margin": "0.5rem 0", "borderTop": "2px solid #1f77b4"}),
            html.Div([
                html.I(className="fas fa-map-marker-alt", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                "Location Settings",
            ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.5rem"}),
            html.Hr(style={"margin": "0.5rem 0"}),
            html.Label("Latitude", style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
            dbc.Input(id={"type": "multi-latitude", "index": i}, type="number",
                      value=31.6911 + i * 0.001, step=0.0001,
                      style={"marginBottom": "0.5rem", "fontSize": "0.85rem"}),
            html.Label("Longitude", style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
            dbc.Input(id={"type": "multi-longitude", "index": i}, type="number",
                      value=74.0822 + i * 0.001, step=0.0001,
                      style={"marginBottom": "0.75rem", "fontSize": "0.85rem"}),
            html.Div([
                html.I(className="fas fa-wind", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                "Release Parameters",
            ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
            html.Hr(style={"margin": "0.5rem 0"}),
            html.Label("Release Rate (g/s)", style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
            dbc.Input(id={"type": "multi-release-rate", "index": i}, type="number",
                      value=800, min=10, max=2000, step=10,
                      style={"marginBottom": "0.5rem", "fontSize": "0.85rem"}),
            html.Label("Source Height (m)", style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
            dbc.Input(id={"type": "multi-height", "index": i}, type="number",
                      value=3.0, min=1, max=20, step=0.5,
                      style={"marginBottom": "0.75rem", "fontSize": "0.85rem"}),
        ], style={
            "paddingLeft": "1rem",
            "borderLeft": "3px solid #1f77b4",
            "marginBottom": "1rem",
            "paddingBottom": "0.5rem",
            "backgroundColor": "#f8f9fa" if i % 2 == 0 else "white",
            "padding": "0.75rem",
            "borderRadius": "4px",
        }))

    return html.Div([
        # Single-source inputs
        html.Div([
            html.Div([
                html.I(className="fas fa-map-marker-alt", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                "Location Settings",
            ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
            html.Hr(style={"margin": "0.5rem 0"}),
            dbc.RadioItems(
                id="location-mode",
                options=[
                    {"label": "Current Location", "value": "current"},
                    {"label": "Manual Location", "value": "manual"},
                ],
                value="manual",
                inline=True,
                style={"marginBottom": "0.5rem", "fontSize": "0.85rem"},
            ),
            dcc.Geolocation(id="geolocation", high_accuracy=True),
            html.Div(id="manual-location-inputs", children=[
                html.Label("Latitude", style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                dbc.Input(id="latitude", type="number", value=31.6911, step=0.0001,
                          style={"marginBottom": "0.5rem", "fontSize": "0.85rem"}),
                html.Label("Longitude", style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                dbc.Input(id="longitude", type="number", value=74.0822, step=0.0001,
                          style={"marginBottom": "0.75rem", "fontSize": "0.85rem"}),
            ]),
            html.Div(id="current-location-display", children=[
                dbc.Alert([
                    html.I(className="fas fa-crosshairs", style={"marginRight": "0.5rem"}),
                    "Detecting your location...",
                ], color="info", style={"fontSize": "0.85rem", "marginBottom": "0.75rem"}),
            ], style={"display": "none"}),
            html.Div([
                html.I(className="fas fa-wind", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                "Release Parameters",
            ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
            html.Hr(style={"margin": "0.5rem 0"}),
            create_slider_with_range_control(
                "release-rate", "Release Rate (g/s)",
                10, 2000, 800, 10,
                {10: "10", 500: "500", 1000: "1000", 1500: "1500", 2000: "2000"},
            ),
            create_slider_with_range_control(
                "tank-height", "Source Height (m)",
                1, 20, 3.0, 0.5,
                {1: "1", 5: "5", 10: "10", 15: "15", 20: "20"},
            ),
        ], style={"display": "block" if release_type == "single" else "none"}),
        # Multi-source inputs
        html.Div(multi_sources, style={"display": "none" if release_type == "single" else "block"}),
    ])


def trigger_geolocation_update(location_mode):
    return location_mode == "current"


def update_location_based_on_mode(location_mode, geolocation_position, current_lat, current_lon):
    if location_mode == "manual":
        return {"display": "block"}, {"display": "none"}, current_lat, current_lon

    if geolocation_position:
        lat = geolocation_position.get("lat", current_lat)
        lon = geolocation_position.get("lon", current_lon)
        return {"display": "none"}, {"display": "block"}, lat, lon

    return {"display": "none"}, {"display": "block"}, current_lat, current_lon


def update_current_location_display(geolocation_position, position_error, location_mode):
    if location_mode != "current":
        return dash.no_update

    if position_error:
        message = position_error.get("message", "Location permission denied or unavailable.")
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle", style={"marginRight": "0.5rem"}),
            f"Unable to get location: {message}",
        ], color="warning", style={"fontSize": "0.85rem", "marginBottom": "0.75rem"})

    if geolocation_position:
        lat = geolocation_position.get("lat")
        lon = geolocation_position.get("lon")
        if lat is not None and lon is not None:
            return dbc.Alert([
                html.I(className="fas fa-map-marked-alt", style={"marginRight": "0.5rem"}),
                html.Div([
                    html.Strong("Current Location Detected:"),
                    html.Br(),
                    f"Latitude: {lat:.4f}",
                    html.Br(),
                    f"Longitude: {lon:.4f}",
                ]),
            ], color="success", style={"fontSize": "0.85rem", "marginBottom": "0.75rem"})

    return dbc.Alert([
        html.I(className="fas fa-crosshairs fa-spin", style={"marginRight": "0.5rem"}),
        "Detecting your location... Please allow location access in your browser.",
    ], color="info", style={"fontSize": "0.85rem", "marginBottom": "0.75rem"})


def toggle_auto_refresh_visibility(weather_mode):
    if weather_mode == "auto":
        return {"display": "block"}
    return {"display": "none"}


def update_auto_refresh_settings(enabled, interval_seconds, weather_mode):
    is_enabled = "enabled" in (enabled or []) and weather_mode == "auto"
    interval_ms = max(30, min(600, interval_seconds or 60)) * 1000
    current_time = datetime.now().strftime("%H:%M:%S")

    if is_enabled:
        status = html.Span([
            html.I(className="fas fa-sync fa-spin", style={"marginRight": "0.3rem", "color": "#28a745"}),
            f"Auto-updating every {interval_ms // 1000}s (Active since {current_time})",
        ], style={"color": "#28a745"})
    else:
        status = html.Span([
            html.I(className="fas fa-pause-circle", style={"marginRight": "0.3rem", "color": "#6c757d"}),
            f"Auto-refresh paused at {current_time}",
        ], style={"color": "#6c757d"})

    return not is_enabled, interval_ms, 0, status


def reset_app_state(n_clicks, current_href):
    if not n_clicks:
        return dash.no_update
    base_href = current_href.split("?")[0] if current_href else "/"
    return f"{base_href}?reset={int(datetime.now().timestamp())}"
