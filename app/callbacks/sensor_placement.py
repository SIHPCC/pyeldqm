"""
Sensor Placement Optimization callbacks:
 - optimize_sensors
 - reset_sensor_placement
"""
import dash
from dash import Input, Output, State, ALL, html
import dash_bootstrap_components as dbc
import numpy as np
import re
from datetime import datetime


def register(app):

    app.callback(
        [Output("sensor-map-container", "children"),
         Output("sensor-deployed-count", "children"),
         Output("sensor-coverage-area", "children"),
         Output("sensor-estimated-cost", "children"),
         Output("sensor-active-strategy", "children"),
         Output("sensor-priority-breakdown", "children"),
         Output("sensor-network-summary", "children"),
         Output("sensor-details", "children"),
         Output("sensor-status", "children"),
         Output("sensor-status-top", "children"),
         Output("sensor-generated-script-store", "data")],
        [Input("calc-sensor-btn", "n_clicks"),
         Input("calc-sensor-btn-top", "n_clicks")],
        [State("main-tabs", "active_tab"),
         State("sensor-parameter-source-mode", "value"),
         State("threat-params-store", "data"),
         State("sensor-strategy", "value"),
         State("sensor-num-sensors", "value"),
         State("sensor-detection-range-m", "value"),
         State("sensor-min-spacing-m", "value"),
         State("sensor-cost-per-sensor", "value"),
         State("sensor-pop-raster-path", "value"),
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
    )(optimize_sensors)

    app.callback(
        Output("sensor-script-download", "data"),
        Input("btn-download-sensor-script", "n_clicks"),
        State("sensor-generated-script-store", "data"),
        prevent_initial_call=True,
    )(download_sensor_script)

    app.callback(
        [Output("sensor-map-container", "children", allow_duplicate=True),
         Output("sensor-deployed-count", "children", allow_duplicate=True),
         Output("sensor-coverage-area", "children", allow_duplicate=True),
         Output("sensor-estimated-cost", "children", allow_duplicate=True),
         Output("sensor-active-strategy", "children", allow_duplicate=True),
         Output("sensor-priority-breakdown", "children", allow_duplicate=True),
         Output("sensor-network-summary", "children", allow_duplicate=True),
         Output("sensor-details", "children", allow_duplicate=True),
         Output("sensor-status", "children", allow_duplicate=True),
         Output("sensor-status-top", "children", allow_duplicate=True),
         Output("sensor-strategy", "value", allow_duplicate=True),
         Output("sensor-num-sensors", "value", allow_duplicate=True),
         Output("sensor-detection-range-m", "value", allow_duplicate=True),
         Output("sensor-min-spacing-m", "value", allow_duplicate=True),
         Output("sensor-cost-per-sensor", "value", allow_duplicate=True),
         Output("sensor-pop-raster-path", "value", allow_duplicate=True),
         Output("sensor-parameter-source-mode", "value", allow_duplicate=True)],
        Input("reset-sensor-btn", "n_clicks"),
        State("main-tabs", "active_tab"),
        prevent_initial_call=True,
    )(reset_sensor_placement)


# ─────────────────────────────────────────────────
# Callback bodies
# ─────────────────────────────────────────────────

def optimize_sensors(
    n_clicks, n_clicks_top,
    active_tab, sensor_parameter_source_mode, threat_params_store,
    sensor_strategy, sensor_num_sensors, sensor_detection_range_m,
    sensor_min_spacing_m, sensor_cost_per_sensor, sensor_pop_raster_path,
    release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
):
    _NO = dash.no_update
    if active_tab != "tab-sensor-placement":
        return [_NO] * 11
    if n_clicks is None and n_clicks_top is None:
        return [_NO] * 11

    source_note = "Using Sensor Placement-specific parameters."
    if sensor_parameter_source_mode == "threat" and isinstance(threat_params_store, dict):
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
    elif sensor_parameter_source_mode == "threat":
        source_note = "Threat parameter snapshot not found; using current sidebar values."

    try:
        from .threat_zones import calculate_threat_zones
        from core.utils.zone_extraction import extract_zones
        from core.visualization import add_zone_polygons, ensure_layer_control, fit_map_to_polygons
        from core.utils.sensor_optimization import SensorPlacementOptimizer

        (map_component, _, status, _, _, _, _, concentration_data, _) = calculate_threat_zones(
            n_clicks, n_clicks_top, release_type, chemical,
            source_term_mode, terrain_roughness, receptor_height_m, weather_mode,
            datetime_mode, specific_datetime, timezone_offset_hrs,
            wind_speed, wind_dir, temp, humidity, cloud_cover,
            lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
            multi_lats, multi_lons, multi_rates, multi_heights,
        )

        if not concentration_data or concentration_data is dash.no_update:
            warn = dbc.Alert("Unable to generate threat zones for sensor placement.", color="warning")
            return map_component, "---", "---", "---", "---", "---", "---", warn, warn, warn, _NO

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

        threat_zones = extract_zones(X, Y, concentration, thresholds, center_lat, center_lon,
                                     wind_dir=wind_dir_local)

        num_sensors = int(sensor_num_sensors) if sensor_num_sensors is not None else 5
        strategy = str(sensor_strategy) if sensor_strategy else "boundary"
        detection_range = float(sensor_detection_range_m) if sensor_detection_range_m is not None else 500.0
        min_spacing = float(sensor_min_spacing_m) if sensor_min_spacing_m is not None else 200.0
        cost_per_sensor = float(sensor_cost_per_sensor) if sensor_cost_per_sensor is not None else 10000.0

        population_engine = None
        raster_path = sensor_pop_raster_path
        if raster_path and raster_path.strip():
            try:
                import rasterio
                from core.population import SensorPopulationEngine
                population_engine = SensorPopulationEngine(raster_path.strip())
            except Exception:
                population_engine = None

        config = {
            "detection_range_m": detection_range,
            "min_sensor_spacing_m": min_spacing,
            "cost_per_sensor": cost_per_sensor,
        }
        optimizer = SensorPlacementOptimizer(population_engine=population_engine, config=config)
        result = optimizer.optimize_sensor_placement(
            threat_zones, center_lat, center_lon,
            num_sensors=num_sensors, strategy=strategy,
            wind_direction=wind_dir_local,
        )

        import folium
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri", name="Satellite", overlay=False, control=True,
        ).add_to(m)

        folium.Marker([center_lat, center_lon], tooltip="Release Source",
                      icon=folium.Icon(color="red", icon="warning-sign")).add_to(m)

        add_zone_polygons(
            m,
            {k: v for k, v in threat_zones.items() if k in ["AEGL-1", "AEGL-2", "AEGL-3"]},
            thresholds_context={"AEGL": thresholds},
            name_prefix=None,
        )
        fit_map_to_polygons(m, threat_zones.values())

        sensors = result  # optimize_sensor_placement returns List[Dict] directly
        sensor_fg = folium.FeatureGroup(name="Sensor Network", show=True)
        for i, sensor in enumerate(sensors, start=1):
            slat = sensor.get("latitude", center_lat)
            slon = sensor.get("longitude", center_lon)
            spriority = sensor.get("priority", "medium").capitalize()
            folium.CircleMarker(
                [slat, slon],
                radius=8,
                color="#FF6B35",
                fill=True, fill_color="#FF6B35", fill_opacity=0.8,
                tooltip=f"Sensor {i} (Priority: {spriority})",
            ).add_to(sensor_fg)
            folium.Circle(
                [slat, slon], radius=detection_range,
                color="#FF6B35", fill=True, fill_opacity=0.1,
                weight=1, tooltip=f"Sensor {i} detection range",
            ).add_to(sensor_fg)
        sensor_fg.add_to(m)
        ensure_layer_control(m)

        metrics = optimizer.calculate_coverage_metrics(sensors, threat_zones)
        coverage_area = metrics.get("coverage_area_km2", 0.0)
        total_cost = cost_per_sensor * len(sensors)

        priority_counts = {}
        for sensor in sensors:
            prio = sensor.get("priority", "medium")
            priority_counts[prio] = priority_counts.get(prio, 0) + 1
        priority_breakdown = ", ".join(
            f"{cnt} {prio.capitalize()}"
            for prio, cnt in sorted(priority_counts.items())
        ) or "---"

        zone_cov = metrics.get("zone_coverage", {})
        coverage_pct = (
            sum(z.get("coverage_percent", 0.0) for z in zone_cov.values()) / len(zone_cov)
            if zone_cov else 0.0
        )
        network_summary = (
            f"Coverage: {coverage_pct:.1f}% of threat area. "
            f"Detection range: {detection_range:.0f} m per sensor."
        )

        _sensor_script_data = _NO
        _sensor_filename = ""
        try:
            from ..utils.script_generator import generate_sensor_script
            from ..components.tabs.threat_zones import CHEMICAL_OPTIONS

            _chem_props_found = CHEMICAL_OPTIONS.get(chemical, {})
            _mw = _chem_props_found.get("molecular_weight") or _chem_props_found.get("MW") or 17.03

            _multi_sources_sensor = None
            if release_type == "multi":
                _multi_sources_sensor = [
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

            _sensor_script = generate_sensor_script(
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
                sensor_strategy=strategy,
                sensor_num=int(num_sensors),
                sensor_detection_range_m=float(detection_range),
                sensor_min_spacing_m=float(min_spacing),
                sensor_cost_per_sensor=float(cost_per_sensor),
                sensor_population_raster_path=str(sensor_pop_raster_path or ""),
                multi_sources=_multi_sources_sensor,
            )

            _chem_slug = re.sub(r"[^a-z0-9]+", "_", chemical.lower()).strip("_")[:40]
            _sensor_filename = f"{_chem_slug}_sensor_placement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            _sensor_script_data = {"content": _sensor_script, "filename": _sensor_filename}
        except Exception as _sensor_sg_err:
            import traceback
            print(f"[sensor_script_generator] Warning: {_sensor_sg_err}\n{traceback.format_exc()}")

        sensor_map = html.Iframe(
            srcDoc=m._repr_html_(),
            style={"width": "100%", "height": "700px", "border": "none",
                   "display": "block", "overflow": "hidden"},
        )

        detail = dbc.Alert([
            html.Strong("Sensor network optimization completed."),
            html.Br(),
            html.Small(f"Strategy: {strategy.capitalize()}. {source_note}"),
            html.Br(),
            dbc.Button([
                html.I(className="fas fa-file-download", style={"marginRight": "0.4rem"}),
                f"Download Script ({_sensor_filename})" if _sensor_script_data is not _NO else "Download Script",
            ], id="btn-download-sensor-script", color="light", size="sm",
               style={"marginTop": "0.4rem", "fontSize": "0.82rem"},
               disabled=(_sensor_script_data is _NO)),
        ], color="success")

        status_msg = dbc.Alert([
            html.I(className="fas fa-check-circle", style={"marginRight": "0.5rem"}),
            f"Sensor placement optimized. {len(sensors)} sensors deployed.",
        ], color="success")

        return (
            sensor_map, str(len(sensors)), f"{coverage_area:.2f} km²",
            f"${total_cost:,.0f}", strategy.capitalize(),
            priority_breakdown, network_summary, detail,
            status_msg, status_msg, _sensor_script_data,
        )
    except Exception as exc:
        error_alert = dbc.Alert(f"Error in Sensor Placement calculation: {exc}", color="danger")
        return (dash.no_update, "---", "---", "---", "---", "---", "---",
                error_alert, error_alert, error_alert, _NO)


def download_sensor_script(n_clicks, script_data):
    """Send the generated Sensor Placement script to the browser as a .py file download."""
    if not n_clicks or not script_data:
        return dash.no_update
    content = script_data.get("content", "")
    filename = script_data.get("filename", "sensor_placement_script.py")
    return {"content": content, "filename": filename}


def reset_sensor_placement(n_clicks, active_tab):
    _NO = dash.no_update
    if active_tab != "tab-sensor-placement":
        return [_NO] * 17
    if not n_clicks:
        return [_NO] * 17

    initial_map = html.Div([
        html.I(className="fas fa-info-circle fa-3x", style={"color": "#17a2b8", "marginBottom": "1rem"}),
        html.H5("Configure parameters and click 'Optimize Sensor Network' to start"),
    ], style={"textAlign": "center", "padding": "3rem", "color": "#666"})

    return (
        initial_map, "---", "---", "---", "---", "---", "---", "", "", "",
        "boundary", 5, 500, 200, 10000, "", "threat",
    )
