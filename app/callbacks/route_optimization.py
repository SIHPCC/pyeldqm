"""
Emergency Route Optimization callbacks:
 - calculate_route_optimization
 - reset_route_analysis
"""
import dash
from dash import Input, Output, State, ALL, html
import dash_bootstrap_components as dbc
import numpy as np
import folium
import re
from datetime import datetime


def register(app):

    app.callback(
        [Output("route-map-container", "children"),
         Output("route-best-shelter", "children"),
         Output("route-distance", "children"),
         Output("route-cost", "children"),
         Output("route-safe-segments", "children"),
         Output("route-unsafe-segments", "children"),
         Output("route-ranking", "children"),
         Output("route-details", "children"),
         Output("route-status", "children"),
         Output("route-status-top", "children"),
         Output("route-generated-script-store", "data")],
        [Input("calc-route-btn", "n_clicks"),
         Input("calc-route-btn-top", "n_clicks")],
        [State("main-tabs", "active_tab"),
         State("route-parameter-source-mode", "value"),
         State("threat-params-store", "data"),
         State("route-radius-m", "value"),
         State("route-proximity-buffer-m", "value"),
         State("route-show-all-roads", "value"),
         State("route-num-shelters", "value"),
         State({"type": "route-shelter-name", "index": ALL}, "value"),
         State({"type": "route-shelter-lat", "index": ALL}, "value"),
         State({"type": "route-shelter-lon", "index": ALL}, "value"),
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
    )(calculate_route_optimization)

    app.callback(
        Output("route-script-download", "data"),
        Input("btn-download-route-script", "n_clicks"),
        State("route-generated-script-store", "data"),
        prevent_initial_call=True,
    )(download_route_script)

    app.callback(
        [Output("route-map-container", "children", allow_duplicate=True),
         Output("route-best-shelter", "children", allow_duplicate=True),
         Output("route-distance", "children", allow_duplicate=True),
         Output("route-cost", "children", allow_duplicate=True),
         Output("route-safe-segments", "children", allow_duplicate=True),
         Output("route-unsafe-segments", "children", allow_duplicate=True),
         Output("route-ranking", "children", allow_duplicate=True),
         Output("route-details", "children", allow_duplicate=True),
         Output("route-status", "children", allow_duplicate=True),
         Output("route-status-top", "children", allow_duplicate=True),
         Output("route-parameter-source-mode", "value", allow_duplicate=True),
         Output("route-radius-m", "value", allow_duplicate=True),
         Output("route-proximity-buffer-m", "value", allow_duplicate=True),
         Output("route-show-all-roads", "value", allow_duplicate=True),
         Output("route-num-shelters", "value", allow_duplicate=True),
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
         Output("threat-timezone-offset-hrs", "value", allow_duplicate=True)],
        Input("reset-route-btn", "n_clicks"),
        State("main-tabs", "active_tab"),
        prevent_initial_call=True,
    )(reset_route_analysis)


# ─────────────────────────────────────────────────
# Callback bodies
# ─────────────────────────────────────────────────

def _path_length_m(G, path_nodes):
    if not path_nodes or len(path_nodes) < 2:
        return 0.0
    total = 0.0
    for u, v in zip(path_nodes[:-1], path_nodes[1:]):
        edge_data = G.get_edge_data(u, v)
        if not edge_data:
            continue
        lengths = [float(attrs.get("length", 0.0)) for _, attrs in edge_data.items()]
        if lengths:
            total += min(lengths)
    return total


def _render_route_layers(m, G, safe_gdf, unsafe_gdf, optimized_path, show_unsafe=True):
    from shapely.geometry import LineString
    safe_fg = folium.FeatureGroup(name="Safe Roads", show=True)
    for _, row in safe_gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        if isinstance(geom, LineString):
            coords = [(lat, lon) for lon, lat in geom.coords]
            folium.PolyLine(coords, color="#00FC0D", weight=4, opacity=0.95, tooltip="Safe Road").add_to(safe_fg)
    safe_fg.add_to(m)

    if show_unsafe and len(unsafe_gdf) > 0:
        unsafe_fg = folium.FeatureGroup(name="Unsafe Roads", show=True)
        for _, row in unsafe_gdf.iterrows():
            geom = row.geometry
            if geom is None:
                continue
            if isinstance(geom, LineString):
                coords = [(lat, lon) for lon, lat in geom.coords]
                folium.PolyLine(coords, color="#FF0000", weight=4, opacity=0.25,
                                tooltip="Unsafe Road (Threat Zone)").add_to(unsafe_fg)
        unsafe_fg.add_to(m)

    if optimized_path:
        route_fg = folium.FeatureGroup(name="Optimized Route", show=True)
        route_coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in optimized_path if n in G.nodes]
        if route_coords:
            folium.PolyLine(route_coords, color="#0066FF", weight=6, opacity=1.0,
                            tooltip="Optimized Evacuation Route").add_to(route_fg)
            route_fg.add_to(m)


def calculate_route_optimization(
    n_clicks, n_clicks_top,
    active_tab, route_parameter_source_mode, threat_params_store,
    route_radius_m, route_proximity_buffer_m, route_show_all_roads,
    route_num_shelters, route_shelter_names, route_shelter_lats, route_shelter_lons,
    release_type, chemical, source_term_mode, terrain_roughness, receptor_height_m,
    weather_mode, datetime_mode, specific_datetime, timezone_offset_hrs,
    wind_speed, wind_dir, temp, humidity, cloud_cover,
    lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
    multi_lats, multi_lons, multi_rates, multi_heights,
):
    _NO = dash.no_update
    if active_tab != "tab-route-optimization":
        return [_NO] * 11
    if n_clicks is None and n_clicks_top is None:
        return [_NO] * 11

    source_note = "Using Emergency Routes-specific parameters."
    if route_parameter_source_mode == "threat" and isinstance(threat_params_store, dict):
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
    elif route_parameter_source_mode == "threat":
        source_note = "Threat parameter snapshot not found; using current sidebar values."

    try:
        from .threat_zones import calculate_threat_zones
        from core.utils.zone_extraction import extract_zones
        from core.visualization import add_zone_polygons, ensure_layer_control, fit_map_to_polygons
        from core.evacuation import build_road_graph, classify_edges_with_risk, rank_shelters

        map_component, _, status, _, _, _, _, concentration_data, _ = calculate_threat_zones(
            n_clicks, n_clicks_top, release_type, chemical,
            source_term_mode, terrain_roughness, receptor_height_m, weather_mode,
            datetime_mode, specific_datetime, timezone_offset_hrs,
            wind_speed, wind_dir, temp, humidity, cloud_cover,
            lat, lon, release_rate, duration_minutes, mass_released_kg, tank_height,
            multi_lats, multi_lons, multi_rates, multi_heights,
        )

        if not concentration_data or concentration_data is dash.no_update:
            warn = dbc.Alert("Unable to generate threat zones for route optimization.", color="warning")
            return map_component, "---", "---", "---", "---", "---", "---", warn, warn, warn, _NO

        X = np.array(concentration_data.get("X"))
        Y = np.array(concentration_data.get("Y"))
        concentration = np.array(concentration_data.get("concentration"))
        thresholds = concentration_data.get("thresholds", {})
        wind_dir_local = concentration_data.get("wind_dir", 0)

        if release_type == "single":
            center_lat = lat if lat is not None else 31.6911
            center_lon = lon if lon is not None else 74.0822
            source_points = [(center_lat, center_lon, "Source")]
        else:
            center_lat = float(np.mean(multi_lats)) if multi_lats else 31.6911
            center_lon = float(np.mean(multi_lons)) if multi_lons else 74.0822
            source_points = [
                (mlat, mlon, f"Source {i + 1}")
                for i, (mlat, mlon) in enumerate(zip(multi_lats or [], multi_lons or []))
                if mlat is not None and mlon is not None
            ] or [(center_lat, center_lon, "Source")]

        threat_zones = extract_zones(X, Y, concentration, thresholds, center_lat, center_lon, wind_dir=wind_dir_local)

        route_radius = float(route_radius_m) if route_radius_m is not None else 4000.0
        route_buffer = float(route_proximity_buffer_m) if route_proximity_buffer_m is not None else 150.0
        show_unsafe = isinstance(route_show_all_roads, list) and "show" in route_show_all_roads

        try:
            parsed_shelter_count = float(route_num_shelters)
        except (TypeError, ValueError):
            parsed_shelter_count = None

        if parsed_shelter_count is None or not float(parsed_shelter_count).is_integer() or parsed_shelter_count <= 0:
            warn = dbc.Alert("Number of shelters must be an integer greater than zero.", color="warning")
            return map_component, "---", "---", "---", "---", "---", "---", warn, warn, warn, _NO

        shelter_count = int(parsed_shelter_count)
        route_shelter_names = route_shelter_names or []
        route_shelter_lats = route_shelter_lats or []
        route_shelter_lons = route_shelter_lons or []

        shelters_catalog = []
        for i in range(shelter_count):
            sname = route_shelter_names[i] if i < len(route_shelter_names) else f"Shelter {i + 1}"
            slat = route_shelter_lats[i] if i < len(route_shelter_lats) else None
            slon = route_shelter_lons[i] if i < len(route_shelter_lons) else None
            if slat is None or slon is None:
                continue
            shelters_catalog.append((float(slat), float(slon), str(sname or f"Shelter {i + 1}")))

        if not shelters_catalog:
            warn = dbc.Alert("No valid shelter coordinates provided.", color="warning")
            return map_component, "---", "---", "---", "---", "---", "---", warn, warn, warn, _NO

        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri", name="Satellite", overlay=False, control=True,
        ).add_to(m)

        for sp_lat, sp_lon, sp_name in source_points:
            folium.Marker([sp_lat, sp_lon], tooltip=sp_name,
                          icon=folium.Icon(color="red", icon="warning-sign")).add_to(m)

        add_zone_polygons(
            m,
            {k: v for k, v in threat_zones.items() if k in ["AEGL-1", "AEGL-2", "AEGL-3"]},
            thresholds_context={"AEGL": thresholds},
            name_prefix=None,
        )
        fit_map_to_polygons(m, threat_zones.values())

        G = build_road_graph(center_lat, center_lon, route_radius)
        safe_gdf, unsafe_gdf = classify_edges_with_risk(G, threat_zones, proximity_buffer_m=route_buffer)
        shelter_points = [(slat, slon) for slat, slon, _ in shelters_catalog]
        ranking = rank_shelters(G, (center_lat, center_lon), shelter_points)
        best = next((r for r in ranking if "path" in r), None)

        best_name = "---"
        best_distance = "---"
        best_cost = "---"
        if best:
            for slat, slon, sname in shelters_catalog:
                if abs(slat - best["lat"]) < 1e-9 and abs(slon - best["lon"]) < 1e-9:
                    best_name = sname
                    break
            best_cost = f"{best['cost']:.0f}"
            best_distance_m = _path_length_m(G, best.get("path", []))
            best_distance = f"{best_distance_m / 1000:.2f} km"

        for slat, slon, sname in shelters_catalog:
            is_best = best and abs(slat - best["lat"]) < 1e-9 and abs(slon - best["lon"]) < 1e-9
            folium.Marker(
                [slat, slon],
                tooltip=f"🏆 RECOMMENDED: {sname}" if is_best else sname,
                icon=folium.Icon(
                    color="green" if is_best else "blue",
                    icon="home" if is_best else "map-marker",
                ),
            ).add_to(m)

        _render_route_layers(m, G, safe_gdf, unsafe_gdf,
                             best.get("path") if best else None, show_unsafe=show_unsafe)
        ensure_layer_control(m)

        route_map = html.Iframe(
            srcDoc=m._repr_html_(),
            style={"width": "100%", "height": "700px", "border": "none",
                   "display": "block", "overflow": "hidden"},
        )

        ranking_items = []
        for idx, entry in enumerate(ranking, start=1):
            sname_r = next(
                (n for slat, slon, n in shelters_catalog
                 if abs(slat - entry.get("lat", -999)) < 1e-9 and abs(slon - entry.get("lon", -999)) < 1e-9),
                f"Shelter {idx}",
            )
            if "error" in entry:
                ranking_items.append(html.Li(f"{idx}. {sname_r}: unavailable ({entry['error']})"))
            else:
                ranking_items.append(html.Li(f"{idx}. {sname_r}: cost {entry.get('cost', 0):.0f}"))

        ranking_view = html.Ul(ranking_items, style={"marginBottom": "0"}) if ranking_items else "---"

        _route_script_data = _NO
        _route_filename = ""
        try:
            from ..utils.script_generator import generate_route_script
            from ..components.tabs.threat_zones import CHEMICAL_OPTIONS

            _chem_props_found = CHEMICAL_OPTIONS.get(chemical, {})
            _mw = _chem_props_found.get("molecular_weight") or _chem_props_found.get("MW") or 17.03
            _multi_sources_route = None
            if release_type == "multi":
                _multi_sources_route = [
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

            _route_script = generate_route_script(
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
                route_radius_m=route_radius,
                route_proximity_buffer_m=route_buffer,
                show_unsafe_roads=show_unsafe,
                shelters=[{"lat": slat, "lon": slon, "name": sname} for slat, slon, sname in shelters_catalog],
                multi_sources=_multi_sources_route,
            )

            _chem_slug = re.sub(r"[^a-z0-9]+", "_", chemical.lower()).strip("_")[:40]
            _route_filename = f"{_chem_slug}_route_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            _route_script_data = {"content": _route_script, "filename": _route_filename}
        except Exception as _route_sg_err:
            import traceback
            print(f"[route_script_generator] Warning: {_route_sg_err}\n{traceback.format_exc()}")

        detail = dbc.Alert([
            html.Strong("Emergency route optimization completed."),
            html.Br(),
            html.Small(f"Mode: {route_parameter_source_mode}. {source_note}"),
            html.Br(),
            html.Small(f"Road segments classified: {len(safe_gdf)} safe, {len(unsafe_gdf)} unsafe."),
            html.Br(),
            dbc.Button([
                html.I(className="fas fa-file-download", style={"marginRight": "0.4rem"}),
                f"Download Script ({_route_filename})" if _route_script_data is not _NO else "Download Script",
            ], id="btn-download-route-script", color="light", size="sm",
               style={"marginTop": "0.4rem", "fontSize": "0.82rem"},
               disabled=(_route_script_data is _NO)),
        ], color="success")

        status_msg = dbc.Alert([
            html.I(className="fas fa-check-circle", style={"marginRight": "0.5rem"}),
            "Emergency routes calculated successfully.",
        ], color="success")

        return (
            route_map, best_name, best_distance, best_cost,
            f"{len(safe_gdf):,}", f"{len(unsafe_gdf):,}",
            ranking_view, detail, status_msg, status_msg, _route_script_data,
        )
    except Exception as exc:
        error_alert = dbc.Alert(f"Error in Emergency Routes calculation: {exc}", color="danger")
        return (dash.no_update, "---", "---", "---", "---", "---", "---",
                error_alert, error_alert, error_alert, _NO)


def download_route_script(n_clicks, script_data):
    """Send the generated Emergency Routes script to the browser as a .py file download."""
    if not n_clicks or not script_data:
        return dash.no_update
    content = script_data.get("content", "")
    filename = script_data.get("filename", "route_optimization_script.py")
    return {"content": content, "filename": filename}


def reset_route_analysis(n_clicks, active_tab):
    _NO = dash.no_update
    if active_tab != "tab-route-optimization":
        return [_NO] * 36
    if not n_clicks:
        return [_NO] * 36

    from ..components.tabs.threat_zones import DEFAULT_CHEMICAL

    initial_map = html.Div([
        html.I(className="fas fa-info-circle fa-3x", style={"color": "#17a2b8", "marginBottom": "1rem"}),
        html.H5("Configure parameters and click 'Calculate Emergency Routes' to start"),
    ], style={"textAlign": "center", "padding": "3rem", "color": "#666"})

    return (
        initial_map, "---", "---", "---", "---", "---", "---", "", "", "",
        "threat", 4000, 150, ["show"], 3,
        31.6911, 74.0822, DEFAULT_CHEMICAL, "single", 2,
        800, 3.0, 1.5, 30, 500, "URBAN", "continuous",
        "manual", 3, 90, 25, 60, 25, "now", None, 5,
    )
