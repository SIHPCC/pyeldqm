"""
Shelter Analysis callbacks:
 - analyze_shelters
 - reset_shelter_analysis
"""
import dash
from dash import Input, Output, State, ALL, html
import dash_bootstrap_components as dbc
import numpy as np
import re
from datetime import datetime


def register(app):

    app.callback(
        [Output("shelter-map-container", "children"),
         Output("shelter-primary-recommendation", "children"),
         Output("shelter-shelter-zones-count", "children"),
         Output("shelter-evacuate-zones-count", "children"),
         Output("shelter-sampled-points", "children"),
         Output("shelter-zone-breakdown", "children"),
         Output("shelter-details", "children"),
         Output("shelter-status", "children"),
         Output("shelter-status-top", "children"),
         Output("shelter-generated-script-store", "data")],
        [Input("calc-shelter-btn", "n_clicks"),
         Input("calc-shelter-btn-top", "n_clicks")],
        [State("main-tabs", "active_tab"),
         State("shelter-parameter-source-mode", "value"),
         State("threat-params-store", "data"),
         State("shelter-building-type", "value"),
         State("shelter-sheltering-time-min", "value"),
         State("shelter-evacuation-time-min", "value"),
         State("shelter-sample-grid-points", "value"),
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
    )(analyze_shelters)

    app.callback(
        Output("shelter-script-download", "data"),
        Input("btn-download-shelter-script", "n_clicks"),
        State("shelter-generated-script-store", "data"),
        prevent_initial_call=True,
    )(download_shelter_script)

    app.callback(
        [Output("shelter-map-container", "children", allow_duplicate=True),
         Output("shelter-primary-recommendation", "children", allow_duplicate=True),
         Output("shelter-shelter-zones-count", "children", allow_duplicate=True),
         Output("shelter-evacuate-zones-count", "children", allow_duplicate=True),
         Output("shelter-sampled-points", "children", allow_duplicate=True),
         Output("shelter-zone-breakdown", "children", allow_duplicate=True),
         Output("shelter-details", "children", allow_duplicate=True),
         Output("shelter-status", "children", allow_duplicate=True),
         Output("shelter-status-top", "children", allow_duplicate=True),
         Output("shelter-building-type", "value", allow_duplicate=True),
         Output("shelter-sheltering-time-min", "value", allow_duplicate=True),
         Output("shelter-evacuation-time-min", "value", allow_duplicate=True),
         Output("shelter-sample-grid-points", "value", allow_duplicate=True),
         Output("shelter-parameter-source-mode", "value", allow_duplicate=True)],
        Input("reset-shelter-btn", "n_clicks"),
        State("main-tabs", "active_tab"),
        prevent_initial_call=True,
    )(reset_shelter_analysis)


# ─────────────────────────────────────────────────
# Callback bodies
# ─────────────────────────────────────────────────

def _render_shelter_action_zones(m, shelter_result):
    """Render shelter/evacuate zone polygons onto a folium map."""
    import folium

    shelter_zones = shelter_result.get("shelter_zones", [])
    evacuate_zones = shelter_result.get("evacuate_zones", [])

    shelter_fg = folium.FeatureGroup(name="Shelter-in-Place Zones", show=True)
    for zone in shelter_zones:
        poly = zone.get("polygon")
        if poly is None:
            continue
        from shapely.geometry import mapping
        geo_json = mapping(poly)
        folium.GeoJson(
            {
                "type": "Feature",
                "geometry": geo_json,
                "properties": {"zone_name": zone.get("name", "Shelter Zone")},
            },
            style_function=lambda _: {
                "fillColor": "#90EE90", "color": "#228B22",
                "weight": 2, "fillOpacity": 0.35,
            },
            tooltip=zone.get("name", "Shelter Zone"),
        ).add_to(shelter_fg)
    shelter_fg.add_to(m)

    evacuate_fg = folium.FeatureGroup(name="Evacuation Zones", show=True)
    for zone in evacuate_zones:
        poly = zone.get("polygon")
        if poly is None:
            continue
        from shapely.geometry import mapping
        geo_json = mapping(poly)
        folium.GeoJson(
            {
                "type": "Feature",
                "geometry": geo_json,
                "properties": {"zone_name": zone.get("name", "Evacuate Zone")},
            },
            style_function=lambda _: {
                "fillColor": "#FF6347", "color": "#B22222",
                "weight": 2, "fillOpacity": 0.35,
            },
            tooltip=zone.get("name", "Evacuate Zone"),
        ).add_to(evacuate_fg)
    evacuate_fg.add_to(m)


def analyze_shelters(
    n_clicks, n_clicks_top,
    active_tab, shelter_parameter_source_mode, threat_params_store,
    shelter_building_type, shelter_sheltering_time_min, shelter_evacuation_time_min,
    shelter_sample_grid_points,
    release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
):
    _NO = dash.no_update
    if active_tab != "tab-shelter-analysis":
        return [_NO] * 10
    if n_clicks is None and n_clicks_top is None:
        return [_NO] * 10

    source_note = "Using Shelter Analysis-specific parameters."
    if shelter_parameter_source_mode == "threat" and isinstance(threat_params_store, dict):
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
    elif shelter_parameter_source_mode == "threat":
        source_note = "Threat parameter snapshot not found; using current sidebar values."

    try:
        from .threat_zones import calculate_threat_zones
        from core.utils.zone_extraction import extract_zones
        from core.visualization import add_zone_polygons, ensure_layer_control, fit_map_to_polygons
        from core.protective_actions import analyze_shelter_zones

        (map_component, _, status, _, _, _, _, concentration_data, _) = calculate_threat_zones(
            n_clicks, n_clicks_top, release_type, chemical,
            source_term_mode, terrain_roughness, receptor_height_m, weather_mode,
            datetime_mode, specific_datetime, timezone_offset_hrs,
            wind_speed, wind_dir, temp, humidity, cloud_cover,
            lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
            multi_lats, multi_lons, multi_rates, multi_heights,
        )

        if not concentration_data or concentration_data is dash.no_update:
            warn = status if status not in (dash.no_update, None) else dbc.Alert(
                "Unable to generate threat zones for shelter analysis.",
                color="warning",
            )
            return map_component, "---", "---", "---", "---", "---", warn, warn, warn, _NO

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

        building_type = str(shelter_building_type) if shelter_building_type else "industrial"
        sheltering_time = float(shelter_sheltering_time_min) if shelter_sheltering_time_min is not None else 60.0
        evacuation_time = float(shelter_evacuation_time_min) if shelter_evacuation_time_min is not None else 15.0
        grid_points = int(shelter_sample_grid_points) if shelter_sample_grid_points is not None else 15

        shelter_result = analyze_shelter_zones(
            threat_zones=threat_zones,
            source_lat=center_lat,
            source_lon=center_lon,
            building_type=building_type,
            sheltering_time_minutes=sheltering_time,
            evacuation_time_minutes=evacuation_time,
            grid_points=grid_points,
        )

        # ── Transform analyze_shelter_zones output into the format expected by
        #    the rest of the callback (lists of {name, polygon, area_km2} dicts).
        #    analyze_shelter_zones returns {zone_name: {primary_recommendation,
        #    shelter_count, evacuate_count, total_samples, ...}}.
        raw_shelter_zones = []
        raw_evacuate_zones = []
        total_sampled = 0
        total_shelter = 0
        total_evacuate = 0
        for zone_name, zone_info in shelter_result.items():
            poly = threat_zones.get(zone_name)
            try:
                area_km2 = poly.area * (111.32 ** 2) if poly and not poly.is_empty else 0.0
            except Exception:
                area_km2 = 0.0
            entry = {"name": zone_name, "polygon": poly, "area_km2": area_km2}
            rec = zone_info.get("primary_recommendation", "SHELTER")
            total_sampled += zone_info.get("total_samples", 0)
            total_shelter += zone_info.get("shelter_count", 0)
            total_evacuate += zone_info.get("evacuate_count", 0)
            if rec == "EVACUATE":
                raw_evacuate_zones.append(entry)
            else:
                raw_shelter_zones.append(entry)

        overall_primary = "EVACUATE" if total_evacuate > total_shelter else "SHELTER IN PLACE"
        shelter_result_normalized = {
            "shelter_zones": raw_shelter_zones,
            "evacuate_zones": raw_evacuate_zones,
            "primary_recommendation": overall_primary,
            "sampled_points": total_sampled if total_sampled > 0 else grid_points ** 2,
        }

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
        _render_shelter_action_zones(m, shelter_result_normalized)
        ensure_layer_control(m)

        shelter_zones = shelter_result_normalized.get("shelter_zones", [])
        evacuate_zones = shelter_result_normalized.get("evacuate_zones", [])
        primary = shelter_result_normalized.get("primary_recommendation", "SHELTER IN PLACE")
        sampled_pts = shelter_result_normalized.get("sampled_points", grid_points ** 2)

        # Breakdown table
        breakdown_rows = []
        for zone in shelter_zones:
            breakdown_rows.append(html.Tr([
                html.Td(zone.get("name", "Zone"), style={"padding": "4px 8px"}),
                html.Td(dbc.Badge("SHELTER", color="success"), style={"padding": "4px 8px"}),
                html.Td(f"{zone.get('area_km2', 0):.2f} km²", style={"padding": "4px 8px"}),
            ]))
        for zone in evacuate_zones:
            breakdown_rows.append(html.Tr([
                html.Td(zone.get("name", "Zone"), style={"padding": "4px 8px"}),
                html.Td(dbc.Badge("EVACUATE", color="danger"), style={"padding": "4px 8px"}),
                html.Td(f"{zone.get('area_km2', 0):.2f} km²", style={"padding": "4px 8px"}),
            ]))
        zone_breakdown_table = dbc.Table(
            [
                html.Thead(html.Tr([html.Th("Zone"), html.Th("Action"), html.Th("Area")])),
                html.Tbody(breakdown_rows if breakdown_rows else [html.Tr([html.Td("No zones", colSpan=3)])]),
            ],
            bordered=True, striped=True, size="sm", responsive=True,
        )

        primary_color = "success" if "shelter" in primary.lower() else "danger"
        primary_card = dbc.Alert(
            [html.I(className="fas fa-home", style={"marginRight": "0.5rem"}), primary],
            color=primary_color,
        )

        _shelter_script_data = _NO
        _shelter_filename = ""
        try:
            from ..utils.script_generator import generate_shelter_script
            from ..components.tabs.threat_zones import CHEMICAL_OPTIONS

            _chem_props_found = CHEMICAL_OPTIONS.get(chemical, {})
            _mw = _chem_props_found.get("molecular_weight") or _chem_props_found.get("MW") or 17.03

            _multi_sources_shelter = None
            if release_type == "multi":
                _multi_sources_shelter = [
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

            _shelter_script = generate_shelter_script(
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
                building_type=building_type,
                sheltering_time_min=float(sheltering_time),
                evacuation_time_min=float(evacuation_time),
                sample_grid_points=int(grid_points),
                multi_sources=_multi_sources_shelter,
            )

            _chem_slug = re.sub(r"[^a-z0-9]+", "_", chemical.lower()).strip("_")[:40]
            _shelter_filename = f"{_chem_slug}_shelter_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            _shelter_script_data = {"content": _shelter_script, "filename": _shelter_filename}
        except Exception as _shelter_sg_err:
            import traceback
            print(f"[shelter_script_generator] Warning: {_shelter_sg_err}\n{traceback.format_exc()}")

        shelter_map = html.Iframe(
            srcDoc=m._repr_html_(),
            style={"width": "100%", "height": "700px", "border": "none",
                   "display": "block", "overflow": "hidden"},
        )

        detail = dbc.Alert([
            html.Strong("Shelter analysis completed."),
            html.Br(),
            html.Small(f"Building type: {building_type.capitalize()}. {source_note}"),
            html.Br(),
            html.Small(f"Sheltering time: {sheltering_time:.0f} min, Evacuation time: {evacuation_time:.0f} min."),
            html.Br(),
            dbc.Button([
                html.I(className="fas fa-file-download", style={"marginRight": "0.4rem"}),
                f"Download Script ({_shelter_filename})" if _shelter_script_data is not _NO else "Download Script",
            ], id="btn-download-shelter-script", color="light", size="sm",
               style={"marginTop": "0.4rem", "fontSize": "0.82rem"},
               disabled=(_shelter_script_data is _NO)),
        ], color="success")

        status_msg = dbc.Alert([
            html.I(className="fas fa-check-circle", style={"marginRight": "0.5rem"}),
            "Shelter analysis completed.",
        ], color="success")

        return (
            shelter_map, primary_card,
            str(len(shelter_zones)), str(len(evacuate_zones)),
            str(sampled_pts), zone_breakdown_table,
            detail, status_msg, status_msg, _shelter_script_data,
        )
    except Exception as exc:
        error_alert = dbc.Alert(f"Error in Shelter Analysis calculation: {exc}", color="danger")
        return (dash.no_update, "---", "---", "---", "---", "---",
                error_alert, error_alert, error_alert, _NO)


def reset_shelter_analysis(n_clicks, active_tab):
    _NO = dash.no_update
    if active_tab != "tab-shelter-analysis":
        return [_NO] * 14
    if not n_clicks:
        return [_NO] * 14

    initial_map = html.Div([
        html.I(className="fas fa-info-circle fa-3x", style={"color": "#17a2b8", "marginBottom": "1rem"}),
        html.H5("Configure parameters and click 'Analyze Shelter Options' to start"),
    ], style={"textAlign": "center", "padding": "3rem", "color": "#666"})

    return (
        initial_map, "---", "---", "---", "---", "---", "", "", "",
        "industrial", 60, 15, 15, "threat",
    )


def download_shelter_script(n_clicks, script_data):
    """Send the generated Shelter Analysis script to the browser as a .py file download."""
    if not n_clicks or not script_data:
        return dash.no_update
    content = script_data.get("content", "")
    filename = script_data.get("filename", "shelter_analysis_script.py")
    return {"content": content, "filename": filename}
