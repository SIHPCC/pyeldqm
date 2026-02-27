"""
Chemical Threat Zones callbacks:
 - calculate_threat_zones  (main calculation, called externally by other tabs)
 - display_chemical_properties
 - render_concentration_plots
 - auto_refresh_threat_zones
"""
import re
import warnings
import sys
import os
from datetime import datetime

import dash
from dash import Input, Output, State, ALL, html
import dash_bootstrap_components as dbc
import numpy as np

warnings.filterwarnings("ignore")


# ── Shared sidebar states list (reused by auto-refresh) ─────────────────────
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

_CALC_OUTPUTS = [
    Output("threat-map-container", "children", allow_duplicate=True),
    Output("zone-statistics", "children", allow_duplicate=True),
    Output("calc-status", "children", allow_duplicate=True),
    Output("calc-status-top", "children", allow_duplicate=True),
    Output("manual-calc-done", "data"),
    Output("simulation-conditions-container", "children"),
    Output("zone-distances-container", "children"),
    Output("concentration-data-store", "data"),
    Output("generated-script-store", "data"),
]


def register(app):

    # Main calculation button
    app.callback(
        _CALC_OUTPUTS,
        [Input("calc-threat-btn", "n_clicks"),
         Input("calc-threat-btn-top", "n_clicks")],
        [State("main-tabs", "active_tab")] + _SIDEBAR_STATES,
        prevent_initial_call=True,
    )(calculate_threat_zones_from_ui)

    # Chemical properties panel
    app.callback(
        Output("chemical-properties-container", "children"),
        [Input("calc-threat-btn", "n_clicks"),
         Input("calc-threat-btn-top", "n_clicks"),
         State("chemical-select", "value")],
        prevent_initial_call=True,
    )(display_chemical_properties)

    # Concentration analytics plots
    app.callback(
        Output("concentration-plots-container", "children"),
        Input("concentration-data-store", "data"),
        prevent_initial_call=True,
    )(render_concentration_plots)

    # Script download
    app.callback(
        Output("script-download", "data"),
        Input("btn-download-script", "n_clicks"),
        State("generated-script-store", "data"),
        prevent_initial_call=True,
    )(download_generated_script)

    # Auto-refresh (triggers from interval component)
    app.callback(
        [Output("threat-map-container", "children", allow_duplicate=True),
         Output("zone-statistics", "children", allow_duplicate=True),
         Output("calc-status", "children", allow_duplicate=True),
         Output("calc-status-top", "children", allow_duplicate=True),
         Output("simulation-conditions-container", "children", allow_duplicate=True),
         Output("zone-distances-container", "children", allow_duplicate=True),
         Output("concentration-data-store", "data", allow_duplicate=True)],
        Input("auto-refresh-interval", "n_intervals"),
        _SIDEBAR_STATES + [
            State("auto-refresh-enabled", "value"),
            State("manual-calc-done", "data"),
        ],
        prevent_initial_call=True,
    )(auto_refresh_threat_zones)


# ─────────────────────────────────────────────────────────────────────────────
# Core calculation function (also imported and called by other tab callbacks)
# ─────────────────────────────────────────────────────────────────────────────

def calculate_threat_zones_from_ui(
    n_clicks, n_clicks_top, active_tab,
    release_type, chemical,
    source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
):
    """UI callback wrapper: only run Threat-Zones outputs on its own tab."""
    if active_tab != "tab-threat-zones":
        return (dash.no_update,) * 9
    return calculate_threat_zones(
        n_clicks, n_clicks_top,
        release_type, chemical,
        source_term_mode, terrain_roughness, receptor_height_m,
        weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
        wind_speed, wind_dir, temp, humidity, cloud_cover,
        lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
        multi_lats, multi_lons, multi_rates, multi_heights,
    )

def calculate_threat_zones(
    n_clicks, n_clicks_top,
    release_type, chemical,
    source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
):
    """Calculate and display chemical threat zones (Gaussian dispersion)."""
    _NO = dash.no_update
    _generated_script_data = None

    if n_clicks is None and n_clicks_top is None:
        return _NO, _NO, _NO, _NO, _NO, _NO, _NO, _NO, _NO

    # ── lazy imports ──────────────────────────────────────────────────────────
    try:
        from pyeldqm.core.dispersion_models.gaussian_model import (
            calculate_gaussian_dispersion, multi_source_concentration,
        )
        from pyeldqm.core.meteorology.realtime_weather import get_weather
        from pyeldqm.core.meteorology.stability import get_stability_class
        from pyeldqm.core.meteorology.wind_profile import wind_speed as calc_wind_profile
        from pyeldqm.core.visualization.folium_maps import (
            create_dispersion_map, meters_to_latlon,
            add_facility_markers, calculate_optimal_zoom_level,
        )
        from pyeldqm.core.visualization import (
            add_zone_polygons, ensure_layer_control,
            fit_map_to_polygons,
        )
        from pyeldqm.core.utils.features import setup_computational_grid
        from pyeldqm.core.utils.chemical_phase import determine_phase
        from pyeldqm.core.utils.zone_extraction import extract_zones
        from ..components.tabs.threat_zones import CHEMICAL_OPTIONS
        from ..utils.display_builders import (
            create_simulation_conditions_display,
            create_zone_distances_display,
        )
    except Exception as import_err:
        err = dbc.Alert(f"Import error: {import_err}", color="danger")
        return _NO, _NO, err, err, _NO, _NO, _NO, _NO, _NO

    try:
        chem_props = CHEMICAL_OPTIONS.get(chemical)
        if not chem_props:
            err = dbc.Alert(f"Chemical '{chemical}' not found in database", color="danger")
            return _NO, _NO, err, err, _NO, _NO, _NO, _NO, _NO

        molecular_weight = chem_props.get("molecular_weight") or chem_props.get("MW")
        if not molecular_weight:
            err = dbc.Alert(f"Molecular weight not available for '{chemical}'", color="warning")
            return _NO, _NO, err, err, _NO, _NO, _NO, _NO, _NO

        # ── Resolve datetime ───────────────────────────────────────────────────
        selected_datetime = datetime.now()
        if datetime_mode == "specific":
            if specific_datetime:
                try:
                    selected_datetime = datetime.fromisoformat(specific_datetime)
                except (ValueError, TypeError):
                    err = dbc.Alert("Invalid specific datetime format.", color="danger")
                    return _NO, _NO, err, err, _NO, _NO, _NO, _NO, _NO
            else:
                err = dbc.Alert("Please select a specific datetime or switch to 'Datetime Now'.", color="warning")
                return _NO, _NO, err, err, _NO, _NO, _NO, _NO, _NO

        # ── Normalise scalars ──────────────────────────────────────────────────
        try:
            timezone_offset_hrs = float(timezone_offset_hrs) if timezone_offset_hrs is not None else 5.0
        except (ValueError, TypeError):
            timezone_offset_hrs = 5.0

        terrain_roughness = (terrain_roughness or "URBAN").upper()
        if terrain_roughness not in ["URBAN", "RURAL"]:
            terrain_roughness = "URBAN"

        try:
            receptor_height_m = float(receptor_height_m) if receptor_height_m is not None else 1.5
        except (ValueError, TypeError):
            receptor_height_m = 1.5
        receptor_height_m = max(receptor_height_m, 0.0)

        source_term_mode = (source_term_mode or "continuous").lower()
        if source_term_mode not in ["continuous", "instantaneous"]:
            source_term_mode = "continuous"

        duration_minutes = float(duration_minutes) if duration_minutes is not None else 30.0
        duration_minutes = max(duration_minutes, 0.1)
        release_duration_seconds = duration_minutes * 60.0
        mass_released_kg = float(mass_released_kg) if mass_released_kg is not None else 500.0
        mass_released_kg = max(mass_released_kg, 0.001)
        total_mass_g = mass_released_kg * 1000.0

        # ── AEGL thresholds from chemical database ─────────────────────────────
        aegl_thresholds = {}
        for i, aegl_key in enumerate(["aegl1_60min", "aegl2_60min", "aegl3_60min"], 1):
            aegl_val = chem_props.get(aegl_key)
            if aegl_val:
                try:
                    if isinstance(aegl_val, str):
                        match = re.search(r"[\d.]+", aegl_val)
                        aegl_thresholds[i] = float(match.group()) if match else 100 * i
                    else:
                        aegl_thresholds[i] = float(aegl_val)
                except Exception:
                    aegl_thresholds[i] = 100 * i
            else:
                aegl_thresholds[i] = 100 * i

        # ── Centre location ────────────────────────────────────────────────────
        if release_type == "single":
            center_lat, center_lon = lat, lon
        else:
            center_lat = np.mean(multi_lats) if multi_lats else 31.6911
            center_lon = np.mean(multi_lons) if multi_lons else 74.0822

        # ── Dynamic grid sizing ────────────────────────────────────────────────
        if source_term_mode == "continuous":
            max_release_rate = release_rate if release_type == "single" else (max(multi_rates) if multi_rates else 1.0)
        else:
            max_release_rate = max(total_mass_g / 60.0, 1.0)
        wind_speed_est = wind_speed or 2.5 if weather_mode == "manual" else 2.5
        base_grid = 5000
        rate_factor = max(0.6, min(np.log10(max(max_release_rate, 0.1)) / np.log10(10.0) + 1.0, 2.0))
        wind_factor = max(0.8, min(3.0 / max(wind_speed_est, 1.0), 2.0))
        x_max = max(3000, min(int(base_grid * rate_factor * wind_factor), 15000))
        y_max = max(2000, min(int(base_grid * 0.8), 10000))

        X, Y, _, _ = setup_computational_grid(x_max=x_max, y_max=y_max, nx=500, ny=500)

        # ── Fetch weather ──────────────────────────────────────────────────────
        if weather_mode == "auto":
            weather = get_weather(latitude=center_lat, longitude=center_lon, source="open_meteo")
        else:
            weather = {
                "wind_speed": wind_speed or 2.5,
                "wind_dir": wind_dir or 90,
                "temperature_K": (temp or 25) + 273.15,
                "humidity": (humidity or 65) / 100.0,
                "cloud_cover": (cloud_cover or 30) / 100.0,
                "source": "manual",
            }

        # ── Phase check (Gaussian model assumes gas) ───────────────────────
        temp_c = (weather.get("temperature_K") or 298.15) - 273.15
        phase_info = determine_phase(chemical, temp_c)
        if phase_info.get("is_gas") is True:
            phase_label = "Gas"
        elif phase_info.get("is_gas") is False:
            phase_label = phase_info.get("phase", "Non-gas").title()
        else:
            phase_label = "Unknown"
        if phase_info.get("is_gas") is False:
            phase = phase_info.get("phase", "non-gas")
            boil_c = phase_info.get("boiling_c")
            boil_note = f" (boiling point: {boil_c:.1f} °C)" if isinstance(boil_c, (int, float)) else ""
            warn = dbc.Alert(
                f"{chemical} is {phase} at {temp_c:.1f} °C{boil_note}. "
                "Gaussian dispersion is valid for gas phase only. "
                "Adjust conditions or choose a gas-phase chemical.",
                color="warning",
            )
            return _NO, _NO, warn, warn, _NO, _NO, _NO, _NO, _NO

        # ── Dispersion ─────────────────────────────────────────────────────────
        if release_type == "single":
            source_q = total_mass_g if source_term_mode == "instantaneous" else release_rate
            dispersion_mode = "instantaneous" if source_term_mode == "instantaneous" else "continuous"
            concentration, U_local, stability_class, resolved_sources = calculate_gaussian_dispersion(
                weather=weather, X=X, Y=Y,
                source_lat=lat, source_lon=lon,
                molecular_weight=molecular_weight,
                default_release_rate=source_q,
                default_height=tank_height,
                z_ref=3.0, z_measurement=receptor_height_m,
                t=release_duration_seconds, t_r=release_duration_seconds,
                mode=dispersion_mode,
                sources=[{"lat": lat, "lon": lon, "name": "Release Source",
                          "height": tank_height, "rate": source_q, "color": "red"}],
                latitude=lat, longitude=lon,
                timezone_offset_hrs=timezone_offset_hrs,
                roughness=terrain_roughness,
                datetime_obj=selected_datetime,
            )
        else:
            stability_class = get_stability_class(
                wind_speed=weather["wind_speed"],
                datetime_obj=selected_datetime,
                latitude=center_lat,
                longitude=center_lon,
                cloudiness_index=weather.get("cloud_cover", 0) * 10,
                timezone_offset_hrs=timezone_offset_hrs,
            )
            default_height = multi_heights[0] if multi_heights else 3.0
            U_local = calc_wind_profile(
                z_user=default_height, z0=3.0,
                U_user=weather["wind_speed"], stability_class=stability_class,
            )
            rate_sum = sum(max(float(r or 0), 0.0) for r in (multi_rates or []))
            sources = []
            for i, (mlat, mlon, mrate, mheight) in enumerate(
                zip(multi_lats, multi_lons, multi_rates, multi_heights)
            ):
                lat_diff = (mlat - center_lat) * 111000
                lon_diff = (mlon - center_lon) * 111000 * np.cos(np.radians(center_lat))
                if source_term_mode == "instantaneous":
                    source_q = (total_mass_g * max(float(mrate or 0), 0.0) / rate_sum
                                if rate_sum > 0 else total_mass_g / max(len(multi_lats), 1))
                else:
                    source_q = mrate
                sources.append({
                    "name": f"Source {i + 1}",
                    "Q": source_q,
                    "x0": lon_diff, "y0": lat_diff,
                    "h_s": mheight,
                    "wind_dir": weather["wind_dir"],
                })
            concentration = multi_source_concentration(
                sources=sources, x_grid=X, y_grid=Y,
                z=receptor_height_m,
                t=release_duration_seconds, t_r=release_duration_seconds,
                U=U_local, stability_class=stability_class,
                roughness=terrain_roughness,
                mode=source_term_mode,
                grid_wind_direction=weather["wind_dir"],
            )
            R = 0.08206
            T = weather["temperature_K"]
            Vm = R * T / 1.0
            concentration = concentration * (Vm / molecular_weight) * 1000
            resolved_sources = [{
                "lat": mlat, "lon": mlon,
                "name": f"Source {i + 1}",
                "height": mheight, "rate": mrate,
                "color": ["red", "blue", "green", "orange", "purple",
                          "brown", "pink", "gray", "olive", "cyan"][i % 10],
            } for i, (mlat, mlon, mrate, mheight) in enumerate(
                zip(multi_lats, multi_lons, multi_rates, multi_heights)
            )]

        # ── Extract zones ──────────────────────────────────────────────────────
        aegl_thresholds_ppm = {
            "AEGL-3": aegl_thresholds.get(3, 1100),
            "AEGL-2": aegl_thresholds.get(2, 160),
            "AEGL-1": aegl_thresholds.get(1, 30),
        }
        threat_zones = extract_zones(
            X, Y, concentration, aegl_thresholds_ppm,
            center_lat, center_lon, wind_dir=weather["wind_dir"],
        )

        # ── Create map ─────────────────────────────────────────────────────────
        lat_grid, lon_grid = meters_to_latlon(X, Y, center_lat, center_lon, weather["wind_dir"])
        min_threshold = min(aegl_thresholds_ppm.values())
        zoom_level, bounds = calculate_optimal_zoom_level(
            lat_grid, lon_grid, concentration, threshold=min_threshold
        )
        display_height = tank_height if release_type == "single" else (multi_heights[0] if multi_heights else 3.0)
        m = create_dispersion_map(
            source_lat=center_lat, source_lon=center_lon,
            x_grid=X, y_grid=Y,
            concentration=concentration,
            thresholds=aegl_thresholds_ppm,
            wind_direction=weather["wind_dir"],
            zoom_start=zoom_level,
            chemical_name=chemical,
            source_height=display_height,
            wind_speed=weather["wind_speed"],
            stability_class=stability_class,
            include_heatmap=True,
            include_compass=True,
        )
        if m is None:
            err = dbc.Alert("Failed to create dispersion map. Please check your inputs.", color="danger")
            return _NO, _NO, err, err, _NO, _NO, _NO, _NO, _NO

        if resolved_sources:
            result_map = add_facility_markers(m, resolved_sources)
            if result_map is not None:
                m = result_map

        if bounds[0] is not None and bounds != (None, None, None, None):
            try:
                m.fit_bounds(
                    [[bounds[1], bounds[3]], [bounds[0], bounds[2]]],
                    padding=(0.1, 0.1), max_zoom=18,
                )
            except Exception:
                pass

        map_html = m._repr_html_()
        map_component = html.Iframe(
            srcDoc=map_html,
            style={"width": "100%", "height": "700px", "border": "none",
                   "display": "block", "overflow": "hidden"},
        )

        timestamp = datetime.now().strftime("%H:%M:%S")
        status = dbc.Alert([
            html.I(className="fas fa-check-circle", style={"marginRight": "0.5rem"}),
            f"Threat zones calculated successfully! (Last updated: {timestamp})",
        ], color="success")

        # ── Simulation conditions & zone distances displays ────────────────────
        if release_type == "single":
            sim_conditions = create_simulation_conditions_display(
                weather=weather, stability_class=stability_class,
                release_rate=release_rate, tank_height=tank_height,
                is_multi_source=False,
                simulation_datetime=selected_datetime,
                datetime_mode=datetime_mode,
                timezone_offset_hrs=timezone_offset_hrs,
                terrain_roughness=terrain_roughness,
                source_term_mode=source_term_mode,
                duration_minutes=duration_minutes,
                mass_released_kg=mass_released_kg,
                receptor_height_m=receptor_height_m,
                phase_label=phase_label,
            )
            zone_distances = create_zone_distances_display(
                threat_zones=threat_zones,
                thresholds=aegl_thresholds_ppm,
                source_lat=center_lat,
                source_lon=center_lon,
                is_multi_source=False,
            )
        else:
            sources_info = [
                {"rate": mrate, "height": mheight, "name": f"Source {i + 1}"}
                for i, (mrate, mheight) in enumerate(zip(multi_rates, multi_heights))
            ]
            sim_conditions = create_simulation_conditions_display(
                weather=weather, stability_class=stability_class,
                sources=sources_info, is_multi_source=True,
                simulation_datetime=selected_datetime,
                datetime_mode=datetime_mode,
                timezone_offset_hrs=timezone_offset_hrs,
                terrain_roughness=terrain_roughness,
                source_term_mode=source_term_mode,
                duration_minutes=duration_minutes,
                mass_released_kg=mass_released_kg,
                receptor_height_m=receptor_height_m,
                phase_label=phase_label,
            )
            sources_for_distances = [
                {"lat": mlat, "lon": mlon, "name": f"Source {i + 1}"}
                for i, (mlat, mlon) in enumerate(zip(multi_lats, multi_lons))
            ]
            zone_distances = create_zone_distances_display(
                threat_zones=threat_zones,
                thresholds=aegl_thresholds_ppm,
                sources=sources_for_distances,
                is_multi_source=True,
            )

        concentration_data = {
            "X": X.tolist(),
            "Y": Y.tolist(),
            "concentration": concentration.tolist(),
            "thresholds": aegl_thresholds_ppm,
            "wind_dir": weather["wind_dir"],
            "stability_class": stability_class,
            "x_max": int(x_max),
            "y_max": int(y_max),
        }

        # ── Generate standalone example script (available for download) ────────
        try:
            from ..utils.script_generator import generate_threat_zones_script
            _multi_sources = None
            if release_type == "multi":
                _multi_sources = [
                    {
                        "lat": mlat, "lon": mlon,
                        "name": f"Source {i + 1}",
                        "height": float(mheight or 3.0),
                        "rate": float(mrate or 0.0),
                    }
                    for i, (mlat, mlon, mrate, mheight) in enumerate(
                        zip(multi_lats, multi_lons, multi_rates, multi_heights)
                    )
                ]
            _script = generate_threat_zones_script(
                chemical=chemical,
                molecular_weight=float(molecular_weight),
                release_type=release_type,
                source_term_mode=source_term_mode,
                lat=float(lat),
                lon=float(lon),
                release_rate=float(release_rate or 0.0),
                tank_height=float(tank_height or 3.0),
                duration_minutes=float(duration_minutes),
                mass_released_kg=float(mass_released_kg),
                terrain_roughness=terrain_roughness,
                receptor_height_m=float(receptor_height_m),
                weather_mode=weather_mode,
                wind_speed=float(weather.get("wind_speed", wind_speed or 2.5)),
                wind_dir=float(weather.get("wind_dir", wind_dir or 90)),
                temperature_c=float(weather.get("temperature_K", 298.15)) - 273.15,
                humidity_pct=float(weather.get("humidity", 0.65)) * 100,
                cloud_cover_pct=float(weather.get("cloud_cover", 0.3)) * 100,
                timezone_offset_hrs=float(timezone_offset_hrs),
                datetime_mode=datetime_mode,
                specific_datetime=specific_datetime,
                aegl_thresholds=aegl_thresholds_ppm,
                x_max=int(x_max),
                y_max=int(y_max),
                multi_sources=_multi_sources,
            )
            _chem_slug = re.sub(r"[^a-z0-9]+", "_", chemical.lower()).strip("_")[:40]
            _script_filename = f"{_chem_slug}_threat_zones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            _generated_script_data = {"content": _script, "filename": _script_filename}
            status = dbc.Alert([
                html.I(className="fas fa-check-circle", style={"marginRight": "0.5rem"}),
                f"Threat zones calculated successfully! (Last updated: {timestamp})",
                html.Br(),
                dbc.Button([
                    html.I(className="fas fa-file-download", style={"marginRight": "0.4rem"}),
                    f"Download Script ({_script_filename})",
                ], id="btn-download-script", color="light", size="sm",
                   style={"marginTop": "0.4rem", "fontSize": "0.82rem"}),
            ], color="success")
        except Exception as _sg_err:
            # Script generation is non-critical — keep original success status
            import traceback
            print(f"[script_generator] Warning: {_sg_err}\n{traceback.format_exc()}")

        stats = html.Div()
        return map_component, stats, status, status, True, sim_conditions, zone_distances, concentration_data, _generated_script_data

    except Exception as exc:
        err = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle", style={"marginRight": "0.5rem"}),
            f"Error: {exc}",
        ], color="danger")
        return _NO, _NO, err, err, _NO, _NO, _NO, _NO, _NO


def display_chemical_properties(n_clicks, n_clicks_top, chemical_name):
    if (n_clicks is None and n_clicks_top is None) or chemical_name is None:
        return dash.no_update
    try:
        from ..components.tabs.threat_zones import create_chemical_properties_display
        return create_chemical_properties_display(chemical_name)
    except Exception as exc:
        return dbc.Alert(f"Error displaying chemical properties: {exc}", color="danger")


def render_concentration_plots(concentration_data_json):
    if not concentration_data_json or concentration_data_json.get("concentration") is None:
        return html.Div([
            html.I(className="fas fa-info-circle fa-2x",
                   style={"color": "#6c757d", "marginBottom": "1rem"}),
            html.P("Configure parameters and click 'Calculate Threat Zones' to view analytics"),
        ], style={"textAlign": "center", "padding": "2rem", "color": "#6c757d"})

    try:
        from dash import dcc
        from ..utils.plot_builders import (
            create_centerline_concentration_plot,
            create_crosswind_concentration_plot,
            create_concentration_contour_plot,
            create_concentration_statistics,
            create_distance_vs_concentration_plot,
        )

        X = np.array(concentration_data_json["X"])
        Y = np.array(concentration_data_json["Y"])
        concentration = np.array(concentration_data_json["concentration"])
        thresholds = concentration_data_json["thresholds"]
        wind_dir = concentration_data_json.get("wind_dir", 0)

        fig_centerline = create_centerline_concentration_plot(X, Y, concentration, wind_dir)
        fig_crosswind = create_crosswind_concentration_plot(X, Y, concentration)
        fig_contour = create_concentration_contour_plot(X, Y, concentration, thresholds, wind_dir)
        fig_stats = create_concentration_statistics(concentration, thresholds)
        fig_distance = create_distance_vs_concentration_plot(X, Y, concentration, thresholds)

        tab_style = {"padding": "0.5rem 0.75rem", "fontSize": "0.85rem"}
        sel_style = {**tab_style, "fontWeight": "600"}

        return dcc.Tabs(
            id="analytics-plots-tabs",
            value="centerline-tab",
            style={"fontSize": "0.85rem"},
            children=[
                dcc.Tab(label="📈 Centerline Profile", value="centerline-tab",
                        style=tab_style, selected_style=sel_style,
                        children=[dcc.Graph(figure=fig_centerline,
                                            config={"responsive": True, "displayModeBar": True})]),
                dcc.Tab(label="↔️ Crosswind Profiles", value="crosswind-tab",
                        style=tab_style, selected_style=sel_style,
                        children=[dcc.Graph(figure=fig_crosswind,
                                            config={"responsive": True, "displayModeBar": True})]),
                dcc.Tab(label="🗺️ 2D Concentration Map", value="contour-tab",
                        style=tab_style, selected_style=sel_style,
                        children=[dcc.Graph(figure=fig_contour,
                                            config={"responsive": True, "displayModeBar": True})]),
                dcc.Tab(label="📊 Statistics & Impact", value="stats-tab",
                        style=tab_style, selected_style=sel_style,
                        children=[dcc.Graph(figure=fig_stats,
                                            config={"responsive": True, "displayModeBar": True})]),
                dcc.Tab(label="📉 Distance Profile", value="distance-tab",
                        style=tab_style, selected_style=sel_style,
                        children=[dcc.Graph(figure=fig_distance,
                                            config={"responsive": True, "displayModeBar": True})]),
            ],
        )
    except Exception as exc:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle", style={"marginRight": "0.5rem"}),
            f"Error rendering analytics: {exc}",
        ], color="danger")


def auto_refresh_threat_zones(
    n_intervals,
    release_type, chemical,
    source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
    auto_refresh_enabled, manual_calc_done,
):
    _NO = dash.no_update
    if (weather_mode != "auto"
            or "enabled" not in (auto_refresh_enabled or [])
            or not manual_calc_done):
        return _NO, _NO, _NO, _NO, _NO, _NO, _NO

    (map_out, _, status_out, status_top, _, sim_cond, zone_dist, conc_data, _) = calculate_threat_zones(
        n_intervals, None,
        release_type, chemical,
        source_term_mode, terrain_roughness, receptor_height_m,
        weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
        wind_speed, wind_dir, temp, humidity, cloud_cover,
        lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
        multi_lats, multi_lons, multi_rates, multi_heights,
    )
    return map_out, status_out, status_top, sim_cond, zone_dist, conc_data, conc_data  # last column = store update


# ─────────────────────────────────────────────────────────────────────────────
# Script download callback
# ─────────────────────────────────────────────────────────────────────────────

def download_generated_script(n_clicks, script_data):
    """Send the generated standalone script to the browser as a .py download."""
    if not n_clicks or not script_data:
        return dash.no_update
    content = script_data.get("content", "")
    filename = script_data.get("filename", "threat_zones_script.py")
    return {"content": content, "filename": filename}
