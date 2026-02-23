"""
Shared-state callbacks — cache threat parameters for cross-tab reuse,
snapshot them on mode-switch, browse file dialogs, shelter inputs, and
mode-visibility toggles.
"""
from datetime import datetime
import dash
from dash import Input, Output, State, ALL, html
import dash_bootstrap_components as dbc

# Helper: build a threat-params dict from sidebar values
def _build_params_dict(
    release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
    **extra,
):
    d = {
        "release_type": release_type,
        "chemical": chemical,
        "source_term_mode": source_term_mode,
        "terrain_roughness": terrain_roughness,
        "receptor_height_m": receptor_height_m,
        "weather_mode": weather_mode,
        "datetime_mode": datetime_mode,
        "specific_datetime": specific_datetime,
        "timezone_offset_hrs": timezone_offset_hrs,
        "wind_speed": wind_speed,
        "wind_dir": wind_dir,
        "temp": temp,
        "humidity": humidity,
        "cloud_cover": cloud_cover,
        "lat": lat,
        "lon": lon,
        "release_rate": release_rate,
        "duration_minutes": duration_minutes,
        "mass_released_kg": mass_released_kg,
        "tank_height": tank_height,
        "multi_lats": multi_lats,
        "multi_lons": multi_lons,
        "multi_rates": multi_rates,
        "multi_heights": multi_heights,
        "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    d.update(extra)
    return d


_SIDEBAR_STATES = [
    State("release-type", "value"),
    State("chemical-select", "value"),
    State("source-term-mode", "value"),
    State("terrain-roughness", "value"),
    State("receptor-height", "value"),
    State("weather-mode", "value"),
    State("threat-datetime-mode", "value"),
    State("threat-specific-datetime", "value"),
    State("threat-timezone-offset-hrs", "value"),
    State("wind-speed", "value"),
    State("wind-direction", "value"),
    State("temperature", "value"),
    State("humidity", "value"),
    State("cloud-cover", "value"),
    State("latitude", "value"),
    State("longitude", "value"),
    State("release-rate", "value"),
    State("duration", "value"),
    State("mass-released", "value"),
    State("tank-height", "value"),
    State({"type": "multi-latitude", "index": ALL}, "value"),
    State({"type": "multi-longitude", "index": ALL}, "value"),
    State({"type": "multi-release-rate", "index": ALL}, "value"),
    State({"type": "multi-height", "index": ALL}, "value"),
]


def register(app):  # noqa: C901

    # ── 1. Cache when threat-zones calc button is clicked ──────────────────
    app.callback(
        Output("threat-params-store", "data"),
        [Input("calc-threat-btn", "n_clicks"),
         Input("calc-threat-btn-top", "n_clicks")],
        [State("main-tabs", "active_tab")] + _SIDEBAR_STATES,
        prevent_initial_call=True,
    )(cache_threat_parameters)

    # ── 2-5. Snapshots when mode-switch happens in each secondary tab ───────
    app.callback(
        Output("threat-params-store", "data", allow_duplicate=True),
        Input("par-parameter-source-mode", "value"),
        [State("main-tabs", "active_tab")] + _SIDEBAR_STATES,
        prevent_initial_call=True,
    )(snapshot_threat_params_before_par_edit)

    app.callback(
        Output("threat-params-store", "data", allow_duplicate=True),
        Input("route-parameter-source-mode", "value"),
        [State("main-tabs", "active_tab")] + _SIDEBAR_STATES,
        prevent_initial_call=True,
    )(snapshot_threat_params_before_route_edit)

    app.callback(
        Output("threat-params-store", "data", allow_duplicate=True),
        Input("sensor-parameter-source-mode", "value"),
        [State("main-tabs", "active_tab")] + _SIDEBAR_STATES,
        prevent_initial_call=True,
    )(snapshot_threat_params_before_sensor_edit)

    app.callback(
        Output("threat-params-store", "data", allow_duplicate=True),
        Input("shelter-parameter-source-mode", "value"),
        [State("main-tabs", "active_tab")] + _SIDEBAR_STATES,
        prevent_initial_call=True,
    )(snapshot_threat_params_before_shelter_edit)

    # ── 6-7. File-browse dialogs ─────────────────────────────────────────────
    app.callback(
        Output("par-population-raster-path", "value"),
        Input("par-browse-raster-btn", "n_clicks"),
        State("par-population-raster-path", "value"),
        prevent_initial_call=True,
    )(browse_population_raster_path)

    app.callback(
        Output("sensor-pop-raster-path", "value"),
        Input("sensor-browse-raster-btn", "n_clicks"),
        State("sensor-pop-raster-path", "value"),
        prevent_initial_call=True,
    )(browse_sensor_population_raster_path)

    # ── 8-11. Mode-visibility toggles (pointer-events / opacity) ────────────
    app.callback(
        Output("par-advanced-parameters-container", "style"),
        Input("par-parameter-source-mode", "value"),
        prevent_initial_call=True,
    )(toggle_par_parameter_mode_controls)

    app.callback(
        Output("route-advanced-parameters-container", "style"),
        Input("route-parameter-source-mode", "value"),
        prevent_initial_call=True,
    )(toggle_route_parameter_mode_controls)

    app.callback(
        Output("sensor-advanced-parameters-container", "style"),
        Input("sensor-parameter-source-mode", "value"),
        prevent_initial_call=True,
    )(toggle_sensor_parameter_mode_controls)

    app.callback(
        Output("shelter-advanced-parameters-container", "style"),
        Input("shelter-parameter-source-mode", "value"),
        prevent_initial_call=True,
    )(toggle_shelter_parameter_mode_controls)

    # ── 12. Dynamic shelter inputs for Route tab ─────────────────────────────
    app.callback(
        Output("route-shelter-inputs-container", "children"),
        Input("route-num-shelters", "value"),
    )(update_route_shelter_inputs)


# ─────────────────────────────────────────────────
# Pure functions (no Dash state; easy to test)
# ─────────────────────────────────────────────────

def cache_threat_parameters(
    n_clicks, n_clicks_top, active_tab,
    release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
):
    if active_tab != "tab-threat-zones":
        return dash.no_update
    if n_clicks is None and n_clicks_top is None:
        return dash.no_update
    return _build_params_dict(
        release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
        weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
        wind_speed, wind_dir, temp, humidity, cloud_cover,
        lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
        multi_lats, multi_lons, multi_rates, multi_heights,
    )


def snapshot_threat_params_before_par_edit(
    par_mode, active_tab,
    release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
):
    if active_tab != "tab-par-analysis":
        return dash.no_update
    if par_mode not in ["par", "threat"]:
        return dash.no_update
    return _build_params_dict(
        release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
        weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
        wind_speed, wind_dir, temp, humidity, cloud_cover,
        lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
        multi_lats, multi_lons, multi_rates, multi_heights,
        mode_snapshot=par_mode,
    )


def snapshot_threat_params_before_route_edit(
    route_mode, active_tab,
    release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
):
    if active_tab != "tab-route-optimization":
        return dash.no_update
    if route_mode not in ["route", "threat"]:
        return dash.no_update
    return _build_params_dict(
        release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
        weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
        wind_speed, wind_dir, temp, humidity, cloud_cover,
        lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
        multi_lats, multi_lons, multi_rates, multi_heights,
        mode_snapshot=route_mode,
    )


def snapshot_threat_params_before_sensor_edit(
    sensor_mode, active_tab,
    release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
):
    if active_tab != "tab-sensor-placement":
        return dash.no_update
    if sensor_mode not in ["sensor", "threat"]:
        return dash.no_update
    return _build_params_dict(
        release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
        weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
        wind_speed, wind_dir, temp, humidity, cloud_cover,
        lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
        multi_lats, multi_lons, multi_rates, multi_heights,
        mode_snapshot=sensor_mode,
    )


def snapshot_threat_params_before_shelter_edit(
    shelter_mode, active_tab,
    release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
):
    if active_tab != "tab-shelter-analysis":
        return dash.no_update
    if shelter_mode not in ["shelter", "threat"]:
        return dash.no_update
    return _build_params_dict(
        release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
        weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
        wind_speed, wind_dir, temp, humidity, cloud_cover,
        lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
        multi_lats, multi_lons, multi_rates, multi_heights,
        mode_snapshot=shelter_mode,
    )


def _open_file_dialog(title, current_path):
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askopenfilename(
            title=title,
            filetypes=[("GeoTIFF files", "*.tif *.tiff"), ("TIFF files", "*.tif"), ("All files", "*.*")],
        )
        root.destroy()

        if not selected:
            return current_path if current_path else dash.no_update
        if not selected.lower().endswith((".tif", ".tiff")):
            return current_path if current_path else dash.no_update
        return selected
    except Exception:
        return current_path if current_path else dash.no_update


def browse_population_raster_path(n_clicks, current_path):
    if not n_clicks:
        return dash.no_update
    return _open_file_dialog("Select WorldPop GeoTIFF Raster", current_path)


def browse_sensor_population_raster_path(n_clicks, current_path):
    if not n_clicks:
        return dash.no_update
    return _open_file_dialog("Select Population GeoTIFF Raster", current_path)


def toggle_par_parameter_mode_controls(mode):
    if mode == "threat":
        return {"pointerEvents": "none", "opacity": "0.55"}
    return {"pointerEvents": "auto", "opacity": "1.0"}


def toggle_route_parameter_mode_controls(mode):
    if mode == "threat":
        return {"pointerEvents": "none", "opacity": "0.55"}
    return {"pointerEvents": "auto", "opacity": "1.0"}


def toggle_sensor_parameter_mode_controls(mode):
    if mode == "threat":
        return {"pointerEvents": "none", "opacity": "0.55"}
    return {"pointerEvents": "auto", "opacity": "1.0"}


def toggle_shelter_parameter_mode_controls(mode):
    if mode == "threat":
        return {"pointerEvents": "none", "opacity": "0.55"}
    return {"pointerEvents": "auto", "opacity": "1.0"}


def update_route_shelter_inputs(num_shelters):
    """Render dynamic shelter name/lat/lon input rows for Emergency Routes tab."""
    defaults = [
        ("North-West", 31.7111, 74.0622),
        ("North", 31.7211, 74.0822),
        ("East-South", 31.6711, 74.1122),
    ]

    try:
        parsed = float(num_shelters) if num_shelters is not None else 3.0
    except (TypeError, ValueError):
        parsed = 3.0

    if not float(parsed).is_integer() or parsed <= 0:
        count = 1
    else:
        count = int(parsed)

    import dash_bootstrap_components as dbc
    from dash import html

    children = []
    for index in range(count):
        default_name, default_lat, default_lon = (
            defaults[index]
            if index < len(defaults)
            else (
                f"Shelter {index + 1}",
                31.6911 + 0.01 * (index + 1),
                74.0822 + 0.01 * (index + 1),
            )
        )
        children.extend([
            html.Label(
                f"Shelter {index + 1} Name",
                style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"},
            ),
            dbc.Input(
                id={"type": "route-shelter-name", "index": index},
                type="text",
                value=default_name,
                style={"fontSize": "0.85rem", "marginBottom": "0.35rem"},
            ),
            dbc.Row([
                dbc.Col(
                    dbc.Input(
                        id={"type": "route-shelter-lat", "index": index},
                        type="number",
                        value=default_lat,
                        step=0.0001,
                        style={"fontSize": "0.85rem"},
                    ),
                    width=6,
                ),
                dbc.Col(
                    dbc.Input(
                        id={"type": "route-shelter-lon", "index": index},
                        type="number",
                        value=default_lon,
                        step=0.0001,
                        style={"fontSize": "0.85rem"},
                    ),
                    width=6,
                ),
            ], className="g-2", style={"marginBottom": "0.5rem"}),
        ])

    return children
