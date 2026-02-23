"""
Health Impact Threshold Zone callbacks:
 - analyze_health_impact
 - reset_health_analysis
"""
import dash
from dash import Input, Output, State, ALL, html
import dash_bootstrap_components as dbc
import numpy as np
import re
from datetime import datetime


def register(app):

    app.callback(
        [Output("health-map-container", "children"),
         Output("health-max-concentration", "children"),
         Output("health-zones-count", "children"),
         Output("health-stability-class", "children"),
         Output("health-threshold-set", "children"),
         Output("health-threshold-table", "children"),
         Output("health-details", "children"),
         Output("health-status", "children"),
         Output("health-status-top", "children"),
         Output("health-generated-script-store", "data")],
        [Input("calc-health-btn", "n_clicks"),
         Input("calc-health-btn-top", "n_clicks")],
        [State("main-tabs", "active_tab"),
         State("health-parameter-source-mode", "value"),
         State("threat-params-store", "data"),
         State("health-threshold-sets", "value"),
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
         State({"type": "multi-height", "index": ALL}, "value")],
        prevent_initial_call=True,
    )(analyze_health_impact)

    app.callback(
        Output("health-script-download", "data"),
        Input("btn-download-health-script", "n_clicks"),
        State("health-generated-script-store", "data"),
        prevent_initial_call=True,
    )(download_health_script)

    app.callback(
        [Output("health-map-container", "children", allow_duplicate=True),
         Output("health-max-concentration", "children", allow_duplicate=True),
         Output("health-zones-count", "children", allow_duplicate=True),
         Output("health-stability-class", "children", allow_duplicate=True),
         Output("health-threshold-set", "children", allow_duplicate=True),
         Output("health-threshold-table", "children", allow_duplicate=True),
         Output("health-details", "children", allow_duplicate=True),
         Output("health-status", "children", allow_duplicate=True),
         Output("health-status-top", "children", allow_duplicate=True)],
        Input("reset-health-btn", "n_clicks"),
        State("main-tabs", "active_tab"),
        prevent_initial_call=True,
    )(reset_health_analysis)


# ─────────────────────────────────────────────────
# Threshold color mapping
# ─────────────────────────────────────────────────

_THRESHOLD_COLORS = {
    "AEGL-1": "#FFFF66",   # bright yellow
    "AEGL-2": "#FFB84D",   # orange
    "AEGL-3": "#FF6666",   # light red
    "ERPG-1": "#ADD8E6",   # light blue (unchanged)
    "ERPG-2": "#5599FF",   # medium-light blue
    "ERPG-3": "#CC77CC",   # light purple
    "PAC-1": "#90EE90",    # light green (unchanged)
    "PAC-2": "#33BB66",    # medium-light green
    "PAC-3": "#2D8A5E",    # lighter dark green
    "IDLH": "#CC3333",     # lighter dark red
}

_THRESHOLD_DESCRIPTIONS = {
    "AEGL-1": "Notable discomfort; non-disabling effects",
    "AEGL-2": "Irreversible or serious, long-lasting adverse health effects",
    "AEGL-3": "Life-threatening health effects",
    "ERPG-1": "Mild transient health effects",
    "ERPG-2": "Serious health effects; may impair ability to take protective action",
    "ERPG-3": "Life-threatening health effects",
    "PAC-1": "Mild transient adverse health effects",
    "PAC-2": "Irreversible injury or serious acute effects",
    "PAC-3": "Life-threatening effects",
    "IDLH": "Immediately Dangerous to Life or Health",
}


def _build_threshold_table(chemical, threshold_sets):
    from core.health_thresholds import (
        get_aegl_thresholds, get_erpg_thresholds, get_pac_thresholds, get_idlh_threshold,
    )

    rows = []
    all_thresholds = {}

    if threshold_sets and "aegl" in threshold_sets:
        try:
            aegl = get_aegl_thresholds(chemical)
            all_thresholds.update(aegl)
        except Exception:
            pass
    if threshold_sets and "erpg" in threshold_sets:
        try:
            erpg = get_erpg_thresholds(chemical)
            all_thresholds.update(erpg)
        except Exception:
            pass
    if threshold_sets and "pac" in threshold_sets:
        try:
            pac = get_pac_thresholds(chemical)
            all_thresholds.update(pac)
        except Exception:
            pass
    if threshold_sets and "idlh" in threshold_sets:
        try:
            idlh_val = get_idlh_threshold(chemical)
            if idlh_val is not None:
                all_thresholds["IDLH"] = idlh_val
        except Exception:
            pass

    # Filter out None / non-numeric values before sorting
    numeric_thresholds = []
    for k, v in all_thresholds.items():
        try:
            numeric_thresholds.append((k, float(v)))
        except (TypeError, ValueError):
            pass  # skip None or non-numeric entries

    for threshold_name, threshold_ppm in sorted(numeric_thresholds, key=lambda x: x[1]):
        color = _THRESHOLD_COLORS.get(threshold_name, "#cccccc")
        desc = _THRESHOLD_DESCRIPTIONS.get(threshold_name, "")
        rows.append(html.Tr([
            html.Td(
                html.Span(
                    threshold_name,
                    style={"backgroundColor": color, "color": "black",
                           "padding": "2px 8px", "borderRadius": "4px",
                           "fontSize": "0.8rem", "fontWeight": "bold"},
                ),
                style={"padding": "4px 8px"},
            ),
            html.Td(f"{threshold_ppm:.2f} ppm", style={"padding": "4px 8px"}),
            html.Td(desc, style={"padding": "4px 8px", "fontSize": "0.8rem", "color": "#555"}),
        ]))

    if not rows:
        rows = [html.Tr([html.Td("No thresholds found", colSpan=3, style={"padding": "8px"})])]

    table = dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Threshold", style={"padding": "6px 8px"}),
                html.Th("Value (ppm)", style={"padding": "6px 8px"}),
                html.Th("Health Effect", style={"padding": "6px 8px"}),
            ])),
            html.Tbody(rows),
        ],
        bordered=True, striped=True, size="sm", responsive=True,
    )
    return table, dict(numeric_thresholds)


def analyze_health_impact(
    n_clicks, n_clicks_top,
    active_tab, health_parameter_source_mode, threat_params_store,
    health_threshold_sets,
    release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
):
    _NO = dash.no_update
    if active_tab != "tab-health-impact":
        return [_NO] * 10
    if n_clicks is None and n_clicks_top is None:
        return [_NO] * 10

    source_note = "Using Health Impact-specific parameters."
    if health_parameter_source_mode == "threat" and isinstance(threat_params_store, dict):
        ts = threat_params_store
        release_type = ts.get("release_type", release_type)
        chemical = ts.get("chemical", chemical)
        source_term_mode = ts.get("source_term_mode", source_term_mode)
        terrain_roughness = ts.get("terrain_roughness", terrain_roughness)
        receptor_height_m = ts.get("receptor_height_m", receptor_height_m)
        weather_mode = ts.get("weather_mode", weather_mode)
        datetime_mode = ts.get("datetime_mode", datetime_mode)
        specific_datetime = ts.get("specific_datetime", specific_datetime)
        timezone_offset_hrs = ts.get("timezone_offset_hrs", timezone_offset_hrs)
        wind_speed = ts.get("wind_speed", wind_speed)
        wind_dir = ts.get("wind_dir", wind_dir)
        temp = ts.get("temp", temp)
        humidity = ts.get("humidity", humidity)
        cloud_cover = ts.get("cloud_cover", cloud_cover)
        lat = ts.get("lat", lat)
        lon = ts.get("lon", lon)
        release_rate = ts.get("release_rate", release_rate)
        duration_minutes = ts.get("duration_minutes", duration_minutes)
        mass_released_kg = ts.get("mass_released_kg", mass_released_kg)
        tank_height = ts.get("tank_height", tank_height)
        multi_lats = ts.get("multi_lats", multi_lats)
        multi_lons = ts.get("multi_lons", multi_lons)
        multi_rates = ts.get("multi_rates", multi_rates)
        multi_heights = ts.get("multi_heights", multi_heights)
        source_note = f"Using Chemical Threat Zones parameters (captured: {ts.get('captured_at', 'latest')})."
    elif health_parameter_source_mode == "threat":
        source_note = "Threat parameter snapshot not found; using current sidebar values."

    if not health_threshold_sets:
        warn = dbc.Alert("Please select at least one threshold set (AEGL, ERPG, PAC, or IDLH).", color="warning")
        return dash.no_update, "---", "---", "---", "---", "---", warn, warn, warn, _NO

    try:
        from .threat_zones import calculate_threat_zones
        from core.utils.zone_extraction import extract_zones
        from core.visualization import add_zone_polygons, ensure_layer_control, fit_map_to_polygons

        (map_component, _, status, _, _, _, _, concentration_data, _) = calculate_threat_zones(
            n_clicks, n_clicks_top, release_type, chemical,
            source_term_mode, terrain_roughness, receptor_height_m, weather_mode,
            datetime_mode, specific_datetime, timezone_offset_hrs,
            wind_speed, wind_dir, temp, humidity, cloud_cover,
            lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
            multi_lats, multi_lons, multi_rates, multi_heights,
        )

        if not concentration_data or concentration_data is dash.no_update:
            warn = dbc.Alert("Unable to generate threat zones for health impact analysis.", color="warning")
            return map_component, "---", "---", "---", "---", "---", warn, warn, warn, _NO

        X = np.array(concentration_data.get("X"))
        Y = np.array(concentration_data.get("Y"))
        concentration = np.array(concentration_data.get("concentration"))
        thresholds = concentration_data.get("thresholds", {})
        wind_dir_local = concentration_data.get("wind_dir", 0)
        stability_class = concentration_data.get("stability_class", "---")
        max_conc = float(np.nanmax(concentration)) if concentration.size > 0 else 0.0

        if release_type == "single":
            center_lat = lat if lat is not None else 31.6911
            center_lon = lon if lon is not None else 74.0822
        else:
            center_lat = float(np.mean(multi_lats)) if multi_lats else 31.6911
            center_lon = float(np.mean(multi_lons)) if multi_lons else 74.0822

        # Build all health threshold zones
        threshold_table, all_health_thresholds = _build_threshold_table(chemical, health_threshold_sets)

        all_zones = {}
        for threshold_name, threshold_value in all_health_thresholds.items():
            zones = extract_zones(
                X, Y, concentration,
                {threshold_name: threshold_value},
                center_lat, center_lon,
                wind_dir=wind_dir_local,
            )
            all_zones.update(zones)

        import folium
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri", name="Satellite", overlay=False, control=True,
        ).add_to(m)
        folium.Marker([center_lat, center_lon], tooltip="Release Source",
                      icon=folium.Icon(color="red", icon="warning-sign")).add_to(m)

        # Style each zone by its color
        for zone_name, zone_poly in all_zones.items():
            if zone_poly is None:
                continue
            from shapely.geometry import mapping as geom_mapping
            color = _THRESHOLD_COLORS.get(zone_name, "#888888")
            folium.GeoJson(
                {"type": "Feature", "geometry": geom_mapping(zone_poly), "properties": {}},
                style_function=lambda _, c=color: {
                    "fillColor": c, "color": c, "weight": 2, "fillOpacity": 0.3,
                },
                tooltip=zone_name,
                name=zone_name,
            ).add_to(m)

        if all_zones:
            fit_map_to_polygons(m, all_zones.values())
        ensure_layer_control(m)

        health_map = html.Iframe(
            srcDoc=m._repr_html_(),
            style={"width": "100%", "height": "700px", "border": "none",
                   "display": "block", "overflow": "hidden"},
        )

        selected_sets_str = ", ".join(s.upper() for s in health_threshold_sets) if health_threshold_sets else "---"

        _health_script_data = _NO
        _health_filename = ""
        try:
            from ..utils.script_generator import generate_health_impact_script
            from ..components.tabs.threat_zones import CHEMICAL_OPTIONS

            _chem_props_found = CHEMICAL_OPTIONS.get(chemical, {})
            _mw = _chem_props_found.get("molecular_weight") or _chem_props_found.get("MW") or 17.03

            _multi_sources_health = None
            if release_type == "multi":
                _multi_sources_health = [
                    {
                        "lat": mlat,
                        "lon": mlon,
                        "name": f"Source {i + 1}",
                        "height": float(mheight or 3.0),
                        "rate": float(mrate or 0.0),
                    }
                    for i, (mlat, mlon, mrate, mheight) in enumerate(
                        zip(multi_lats or [], multi_lons or [], multi_rates or [], multi_heights or [])
                    )
                    if mlat is not None and mlon is not None
                ]

            _health_script = generate_health_impact_script(
                chemical=chemical,
                molecular_weight=float(_mw),
                release_type=release_type,
                source_term_mode=source_term_mode,
                lat=float(lat or 0),
                lon=float(lon or 0),
                release_rate=float(release_rate or 0.0),
                tank_height=float(tank_height or 3.0),
                duration_minutes=float(duration_minutes or 30.0),
                mass_released_kg=float(mass_released_kg or 500.0),
                terrain_roughness=terrain_roughness or "URBAN",
                receptor_height_m=float(receptor_height_m or 1.5),
                weather_mode=weather_mode or "manual",
                wind_speed=float(wind_speed or 3),
                wind_dir=float(wind_dir or 90),
                temperature_c=float(temp or 25),
                humidity_pct=float(humidity or 60),
                cloud_cover_pct=float(cloud_cover or 25),
                timezone_offset_hrs=float(timezone_offset_hrs or 5),
                datetime_mode=datetime_mode or "now",
                specific_datetime=specific_datetime,
                aegl_thresholds=thresholds or {"AEGL-1": 30, "AEGL-2": 160, "AEGL-3": 1100},
                x_max=int(concentration_data.get("x_max", 12000)),
                y_max=int(concentration_data.get("y_max", 4000)),
                selected_threshold_sets=list(health_threshold_sets or ["aegl"]),
                multi_sources=_multi_sources_health,
            )

            _chem_slug = re.sub(r"[^a-z0-9]+", "_", chemical.lower()).strip("_")[:40]
            _health_filename = f"{_chem_slug}_health_impact_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            _health_script_data = {"content": _health_script, "filename": _health_filename}
        except Exception as _health_sg_err:
            import traceback
            print(f"[health_script_generator] Warning: {_health_sg_err}\n{traceback.format_exc()}")

        detail = dbc.Alert([
            html.Strong("Health impact threshold zone analysis completed."),
            html.Br(),
            html.Small(f"Threshold sets: {selected_sets_str}. {source_note}"),
            html.Br(),
            html.Small(f"Max concentration: {max_conc:.4f} ppm. Stability class: {stability_class}."),
            html.Br(),
            dbc.Button([
                html.I(className="fas fa-file-download", style={"marginRight": "0.4rem"}),
                f"Download Script ({_health_filename})" if _health_script_data is not _NO else "Download Script",
            ], id="btn-download-health-script", color="light", size="sm",
               style={"marginTop": "0.4rem", "fontSize": "0.82rem"},
               disabled=(_health_script_data is _NO)),
        ], color="success")

        status_msg = dbc.Alert([
            html.I(className="fas fa-check-circle", style={"marginRight": "0.5rem"}),
            "Health impact analysis completed.",
        ], color="success")

        max_conc_str = f"{max_conc:.4g} ppm" if max_conc > 0 else "---"

        return (
            health_map, max_conc_str, str(len(all_zones)),
            str(stability_class), selected_sets_str,
            threshold_table, detail, status_msg, status_msg, _health_script_data,
        )
    except Exception as exc:
        error_alert = dbc.Alert(f"Error in Health Impact analysis: {exc}", color="danger")
        return (dash.no_update, "---", "---", "---", "---", "---",
                error_alert, error_alert, error_alert, _NO)


def reset_health_analysis(n_clicks, active_tab):
    _NO = dash.no_update
    if active_tab != "tab-health-impact":
        return [_NO] * 9
    if not n_clicks:
        return [_NO] * 9

    initial_map = html.Div([
        html.I(className="fas fa-info-circle fa-3x", style={"color": "#17a2b8", "marginBottom": "1rem"}),
        html.H5("Configure parameters and click 'Analyze Health Impact' to start"),
    ], style={"textAlign": "center", "padding": "3rem", "color": "#666"})

    return initial_map, "---", "---", "---", "---", "---", "", "", ""


def download_health_script(n_clicks, script_data):
    """Send the generated Health Impact script to the browser as a .py file download."""
    if not n_clicks or not script_data:
        return dash.no_update
    content = script_data.get("content", "")
    filename = script_data.get("filename", "health_impact_script.py")
    return {"content": content, "filename": filename}
