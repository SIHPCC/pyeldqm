"""
PAR (Population At Risk) Analysis callbacks:
 - calculate_par_results
 - reset_par_analysis
"""
import sys
import os
import dash
from dash import Input, Output, State, ALL, html, dcc
import dash_bootstrap_components as dbc
import numpy as np


def register(app):

    app.callback(
        [Output("par-map-container", "children"),
         Output("par-aegl3-count", "children"),
         Output("par-aegl2-count", "children"),
         Output("par-aegl1-count", "children"),
         Output("par-details", "children"),
         Output("par-aegl3-area", "children"),
         Output("par-aegl2-area", "children"),
         Output("par-aegl1-area", "children"),
         Output("par-max-distance", "children"),
         Output("par-aegl3-density", "children"),
         Output("par-aegl2-density", "children"),
         Output("par-aegl1-density", "children"),
         Output("par-density-assessment", "children"),
         Output("par-generated-script-store", "data")],
        [Input("calc-threat-btn", "n_clicks"),
         Input("calc-threat-btn-top", "n_clicks")],
        [State("main-tabs", "active_tab"),
         State("par-population-raster-path", "value"),
         State("critical-threshold", "value"),
         State("high-threshold", "value"),
         State("par-parameter-source-mode", "value"),
         State("threat-params-store", "data"),
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
    )(calculate_par_results)

    # Download PAR script
    app.callback(
        Output("par-script-download", "data"),
        Input("btn-download-par-script", "n_clicks"),
        State("par-generated-script-store", "data"),
        prevent_initial_call=True,
    )(download_par_script)

    app.callback(
        [Output("par-map-container", "children", allow_duplicate=True),
         Output("par-aegl3-count", "children", allow_duplicate=True),
         Output("par-aegl2-count", "children", allow_duplicate=True),
         Output("par-aegl1-count", "children", allow_duplicate=True),
         Output("par-details", "children", allow_duplicate=True),
         Output("latitude", "value", allow_duplicate=True),
         Output("longitude", "value", allow_duplicate=True),
         Output("chemical-select", "value", allow_duplicate=True),
         Output("release-type", "value", allow_duplicate=True),
         Output("num-sources", "value", allow_duplicate=True),
         Output("release-rate", "value", allow_duplicate=True),
         Output("tank-height", "value", allow_duplicate=True),
         Output("receptor-height", "value", allow_duplicate=True),
         Output("duration", "value", allow_duplicate=True),
         Output("mass-released", "value", allow_duplicate=True),
         Output("terrain-roughness", "value", allow_duplicate=True),
         Output("source-term-mode", "value", allow_duplicate=True),
         Output("weather-mode", "value", allow_duplicate=True),
         Output("wind-speed", "value", allow_duplicate=True),
         Output("wind-direction", "value", allow_duplicate=True),
         Output("temperature", "value", allow_duplicate=True),
         Output("humidity", "value", allow_duplicate=True),
         Output("cloud-cover", "value", allow_duplicate=True),
         Output("threat-datetime-mode", "value", allow_duplicate=True),
         Output("threat-specific-datetime", "value", allow_duplicate=True),
         Output("threat-timezone-offset-hrs", "value", allow_duplicate=True),
         Output("par-population-raster-path", "value", allow_duplicate=True),
         Output("critical-threshold", "value", allow_duplicate=True),
         Output("high-threshold", "value", allow_duplicate=True),
         Output("par-parameter-source-mode", "value", allow_duplicate=True),
         Output("par-aegl3-area", "children", allow_duplicate=True),
         Output("par-aegl2-area", "children", allow_duplicate=True),
         Output("par-aegl1-area", "children", allow_duplicate=True),
         Output("par-max-distance", "children", allow_duplicate=True),
         Output("par-aegl3-density", "children", allow_duplicate=True),
         Output("par-aegl2-density", "children", allow_duplicate=True),
         Output("par-aegl1-density", "children", allow_duplicate=True),
         Output("par-density-assessment", "children", allow_duplicate=True)],
        Input("reset-par-btn", "n_clicks"),
        State("main-tabs", "active_tab"),
        prevent_initial_call=True,
    )(reset_par_analysis)


# ─────────────────────────────────────────────────
# Callback bodies
# ─────────────────────────────────────────────────

def calculate_par_results(
    n_clicks, n_clicks_top, active_tab, raster_path, critical_threshold, high_threshold,
    par_parameter_source_mode, threat_params_store,
    release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
):
    """Calculate PAR outputs (map + AEGL population counts + geographic stats) for the PAR tab."""
    _NO = dash.no_update

    if active_tab != "tab-par-analysis":
        return [_NO] * 14
    if n_clicks is None and n_clicks_top is None:
        return [_NO] * 14

    source_note = "Using PAR-specific parameters."
    using_threat_params = False

    if par_parameter_source_mode == "threat" and isinstance(threat_params_store, dict):
        using_threat_params = True
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
    elif par_parameter_source_mode == "threat":
        source_note = "Threat parameter snapshot not found; using current sidebar values."

    # Validate raster
    def _raster_error(map_div, alert_text, color="warning"):
        return (map_div, "---", "---", "---",
                dbc.Alert(alert_text, color=color),
                "---", "---", "---", "---", "---", "---", "---", "", _NO)

    if not raster_path or not isinstance(raster_path, str) or raster_path.strip() == "":
        init_map = html.Div([
            html.I(className="fas fa-map fa-3x", style={"color": "#ff6b6b", "marginBottom": "1rem"}),
            html.H5("Population Raster Required"),
            html.P("Please select a population raster GeoTIFF file (.tif/.tiff) to calculate PAR."),
        ], style={"textAlign": "center", "padding": "3rem", "color": "#666"})
        return _raster_error(init_map, "Select a population raster (.tif/.tiff) to compute PAR.")

    if not raster_path.lower().endswith((".tif", ".tiff")):
        return _raster_error(_NO, f"Selected file is not a GeoTIFF: {raster_path}", "danger")

    if not os.path.exists(raster_path):
        return _raster_error(_NO, f"Cannot find raster file at: {raster_path}", "danger")

    print(f"[PAR] Mode: {par_parameter_source_mode}, Raster: {raster_path}", file=sys.stderr)

    from .threat_zones import calculate_threat_zones
    from core.utils.zone_extraction import extract_zones
    from ..utils.population import compute_par_counts_from_raster

    map_component, _, status, _, _, _, _, concentration_data, _ = calculate_threat_zones(
        n_clicks, n_clicks_top,
        release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
        weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
        wind_speed, wind_dir, temp, humidity, cloud_cover,
        lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
        multi_lats, multi_lons, multi_rates, multi_heights,
    )

    if not concentration_data or concentration_data is dash.no_update:
        warn = status if status not in (dash.no_update, None) else dbc.Alert(
            "PAR calculation could not complete. Please review inputs and try again.",
            color="warning",
        )
        return map_component, "---", "---", "---", warn, "---", "---", "---", "---", "---", "---", "---", "", _NO

    try:
        X = np.array(concentration_data.get("X"))
        Y = np.array(concentration_data.get("Y"))
        concentration = np.array(concentration_data.get("concentration"))
        thresholds = concentration_data.get("thresholds", {})
        wind_dir_local = concentration_data.get("wind_dir", 0)

        if release_type == "single":
            center_lat = lat if lat is not None else 31.6911
            center_lon = lon if lon is not None else 74.0822
        else:
            center_lat = float(np.mean(multi_lats)) if multi_lats else 31.6911
            center_lon = float(np.mean(multi_lons)) if multi_lons else 74.0822

        threat_zones = extract_zones(
            X, Y, concentration, thresholds, center_lat, center_lon, wind_dir=wind_dir_local
        )

        par_counts, par_note = compute_par_counts_from_raster(raster_path, threat_zones)

        aegl3 = par_counts.get("AEGL-3", 0)
        aegl2 = par_counts.get("AEGL-2", 0)
        aegl1 = par_counts.get("AEGL-1", 0)
        total_par = aegl3 + aegl2 + aegl1

        try:
            critical_val = float(critical_threshold) if critical_threshold is not None else 10000
        except (ValueError, TypeError):
            critical_val = 10000.0
        try:
            high_val = float(high_threshold) if high_threshold is not None else 5000
        except (ValueError, TypeError):
            high_val = 5000.0

        if total_par >= critical_val:
            risk_color, risk_label = "danger", "Critical"
        elif total_par >= high_val:
            risk_color, risk_label = "warning", "High"
        else:
            risk_color, risk_label = "success", "Moderate/Low"

        # ── Generate PAR script for download ──────────────────────────────────
        _par_script_data = _NO
        try:
            from ..utils.script_generator import generate_par_script
            import re as _re
            _chem_props_found = None
            try:
                from ..components.tabs.threat_zones import CHEMICAL_OPTIONS
                _chem_props_found = CHEMICAL_OPTIONS.get(chemical)
            except Exception:
                pass
            _mw = (_chem_props_found.get("molecular_weight") or _chem_props_found.get("MW")
                   if _chem_props_found else 17.03)
            _multi_sources_par = None
            if release_type == "multi":
                _multi_sources_par = [
                    {"lat": mlat, "lon": mlon,
                     "name": f"Source {i + 1}",
                     "height": float(mheight or 3.0),
                     "rate": float(mrate or 0.0)}
                    for i, (mlat, mlon, mrate, mheight) in enumerate(
                        zip(multi_lats, multi_lons, multi_rates, multi_heights)
                    )
                ]
            _aegl_thr = concentration_data.get("thresholds", {"AEGL-1": 30, "AEGL-2": 160, "AEGL-3": 1100})
            _par_script = generate_par_script(
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
                wind_speed=float(wind_speed or 2.5),
                wind_dir=float(wind_dir or 90),
                temperature_c=float(temp or 25),
                humidity_pct=float(humidity or 65),
                cloud_cover_pct=float(cloud_cover or 30),
                timezone_offset_hrs=float(timezone_offset_hrs or 5.0),
                datetime_mode=datetime_mode or "now",
                specific_datetime=specific_datetime,
                aegl_thresholds=_aegl_thr,
                x_max=int(concentration_data.get("x_max", 12000)),
                y_max=int(concentration_data.get("y_max", 4000)),
                raster_path=raster_path or "",
                critical_threshold=float(critical_threshold or 10000),
                high_threshold=float(high_threshold or 5000),
                multi_sources=_multi_sources_par,
            )
            _chem_slug = _re.sub(r"[^a-z0-9]+", "_", chemical.lower()).strip("_")[:40]
            from datetime import datetime as _dt
            _par_filename = f"{_chem_slug}_par_analysis_{_dt.now().strftime('%Y%m%d_%H%M%S')}.py"
            _par_script_data = {"content": _par_script, "filename": _par_filename, "type": "text/plain"}
        except Exception as _sg_err:
            import traceback
            print(f"[par_script_generator] Warning: {_sg_err}\n{traceback.format_exc()}",
                  file=sys.stderr)

        details = dbc.Alert([
            html.Div([
                html.I(className="fas fa-users", style={"marginRight": "0.5rem"}),
                html.Strong(f"Total PAR: {total_par:,} people"),
                html.Span(f"  |  Risk Level: {risk_label}", style={"marginLeft": "0.5rem"}),
            ]),
            html.Small(par_note),
            html.Br(),
            html.Small(source_note),
            html.Br(),
            dbc.Button([
                html.I(className="fas fa-file-download", style={"marginRight": "0.4rem"}),
                f"Download PAR Script ({_par_filename})" if _par_script_data is not _NO else "Download PAR Script",
            ], id="btn-download-par-script", color="light", size="sm",
               style={"marginTop": "0.4rem", "fontSize": "0.82rem"},
               disabled=(_par_script_data is _NO)),
        ], color=risk_color)

        # Geographic stats
        aegl3_area = aegl2_area = aegl1_area = "---"
        max_distance = "---"
        aegl3_density = aegl2_density = aegl1_density = "---"
        density_assessment = ""

        try:
            from shapely.geometry import Point
            source_point = (
                Point(lon if lon is not None else 74.0822, lat if lat is not None else 31.6911)
                if release_type == "single"
                else Point(
                    float(np.mean(multi_lons)) if multi_lons else 74.0822,
                    float(np.mean(multi_lats)) if multi_lats else 31.6911,
                )
            )
            zone_areas, zone_distances_m, densities = {}, {}, {}
            for zone_name in ["AEGL-3", "AEGL-2", "AEGL-1"]:
                zone_poly = threat_zones.get(zone_name)
                if zone_poly is None or zone_poly.is_empty:
                    zone_areas[zone_name] = 0
                    zone_distances_m[zone_name] = 0
                    densities[zone_name] = 0
                else:
                    bounds_z = zone_poly.bounds
                    lat_diff = bounds_z[3] - bounds_z[1]
                    lon_diff = bounds_z[2] - bounds_z[0]
                    approx_area = max(
                        (lat_diff * 111) * (lon_diff * 111 * np.cos(np.radians((bounds_z[1] + bounds_z[3]) / 2))),
                        0.01,
                    )
                    zone_areas[zone_name] = approx_area
                    max_dist = max(
                        source_point.distance(Point(coord)) * 111
                        for coord in zone_poly.exterior.coords
                    )
                    zone_distances_m[zone_name] = max_dist
                    pop = par_counts.get(zone_name, 0)
                    densities[zone_name] = pop / approx_area if approx_area > 0 else 0

            aegl3_area = f"{zone_areas.get('AEGL-3', 0):.2f}"
            aegl2_area = f"{zone_areas.get('AEGL-2', 0):.2f}"
            aegl1_area = f"{zone_areas.get('AEGL-1', 0):.2f}"
            max_distance = f"{zone_distances_m.get('AEGL-1', 0):.2f}"
            aegl3_density = f"{densities.get('AEGL-3', 0):,.0f}" if densities.get("AEGL-3", 0) > 0 else "---"
            aegl2_density = f"{densities.get('AEGL-2', 0):,.0f}" if densities.get("AEGL-2", 0) > 0 else "---"
            aegl1_density = f"{densities.get('AEGL-1', 0):,.0f}" if densities.get("AEGL-1", 0) > 0 else "---"

            avg_density = np.mean([d for d in densities.values() if d > 0]) if any(d > 0 for d in densities.values()) else 0
            if avg_density > 10000:
                density_assessment = "🔴 Very High Density: Urban area with dense population"
            elif avg_density > 5000:
                density_assessment = "🟠 High Density: Urban area with moderate-high population"
            elif avg_density > 1000:
                density_assessment = "🟡 Moderate Density: Mixed urban/suburban area"
            elif avg_density > 100:
                density_assessment = "🟢 Low Density: Suburban/rural area"
            else:
                density_assessment = "⚪ Very Low Density: Sparsely populated area"
        except Exception as geo_exc:
            print(f"[PAR_GEO] {geo_exc}", file=sys.stderr)

        return (
            map_component,
            f"{aegl3:,}", f"{aegl2:,}", f"{aegl1:,}",
            details,
            aegl3_area, aegl2_area, aegl1_area,
            max_distance,
            aegl3_density, aegl2_density, aegl1_density,
            density_assessment,
            _par_script_data,
        )
    except Exception as exc:
        detail = dbc.Alert(f"Error in PAR post-processing: {exc}", color="danger")
        return (map_component, "---", "---", "---", detail,
                "---", "---", "---", "---", "---", "---", "---", "", _NO)


def reset_par_analysis(n_clicks, active_tab):
    """Reset PAR analysis results and all sidebar settings to default values."""
    _NO = dash.no_update
    if active_tab != "tab-par-analysis":
        return [_NO] * 38
    if not n_clicks:
        return [_NO] * 38

    from ..components.tabs.threat_zones import DEFAULT_CHEMICAL

    initial_map = html.Div([
        html.I(className="fas fa-info-circle fa-3x",
               style={"color": "#28a745", "marginBottom": "1rem"}),
        html.H5("Population Raster Required"),
        html.P("Please select a population raster GeoTIFF file (.tif/.tiff) to calculate PAR."),
    ], style={"textAlign": "center", "padding": "3rem", "color": "#666"})

    return (
        initial_map, "---", "---", "---", "",
        31.6911, 74.0822, DEFAULT_CHEMICAL, "single", 2,
        800, 3.0, 1.5, 30, 500, "URBAN", "continuous",
        "manual", 3, 90, 25, 60, 25, "now", None, 5,
        "", 10000, 5000, "threat",
        "---", "---", "---", "---", "---", "---", "---", "",
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAR script download callback
# ─────────────────────────────────────────────────────────────────────────────

def download_par_script(n_clicks, script_data):
    """Send the generated PAR script to the browser as a .py file download."""
    if not n_clicks or not script_data:
        return dash.no_update
    content = script_data.get("content", "")
    filename = script_data.get("filename", "par_analysis_script.py")
    # Guard: filename must always use par_analysis naming
    if "threat_zones" in filename:
        filename = filename.replace("threat_zones", "par_analysis")
    return dcc.send_string(content, filename)

