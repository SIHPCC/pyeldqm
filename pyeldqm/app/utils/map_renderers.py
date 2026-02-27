"""
utils/map_renderers.py
======================
Folium map helper functions.  Zero Dash / callback imports.
"""

import folium


def render_route_layers(m, G, safe_gdf, unsafe_gdf, optimized_path, show_unsafe=True):
    """Render safe/unsafe road layers and the optimised route on a folium map.

    Parameters
    ----------
    m            : folium.Map instance (mutated in-place)
    G            : NetworkX graph (nodes contain 'x', 'y' attributes)
    safe_gdf     : GeoDataFrame of safe road segments
    unsafe_gdf   : GeoDataFrame of unsafe road segments
    optimized_path : list of node IDs for the optimised route
    show_unsafe  : whether to render the unsafe road layer
    """
    from shapely.geometry import LineString

    safe_fg = folium.FeatureGroup(name="Safe Roads", show=True)
    for _, row in safe_gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        if isinstance(geom, LineString):
            coords = [(lat, lon) for lon, lat in geom.coords]
            folium.PolyLine(
                coords, color="#00FC0D", weight=4, opacity=0.95, tooltip="Safe Road",
            ).add_to(safe_fg)
    safe_fg.add_to(m)

    if show_unsafe and len(unsafe_gdf) > 0:
        unsafe_fg = folium.FeatureGroup(name="Unsafe Roads", show=True)
        for _, row in unsafe_gdf.iterrows():
            geom = row.geometry
            if geom is None:
                continue
            if isinstance(geom, LineString):
                coords = [(lat, lon) for lon, lat in geom.coords]
                folium.PolyLine(
                    coords, color="#FF0000", weight=4, opacity=0.25,
                    tooltip="Unsafe Road (Threat Zone)",
                ).add_to(unsafe_fg)
        unsafe_fg.add_to(m)

    if optimized_path:
        route_fg = folium.FeatureGroup(name="Optimized Route", show=True)
        route_coords = [
            (G.nodes[n]["y"], G.nodes[n]["x"])
            for n in optimized_path if n in G.nodes
        ]
        if route_coords:
            folium.PolyLine(
                route_coords, color="#0066FF", weight=6, opacity=1.0,
                tooltip="Optimized Evacuation Route",
            ).add_to(route_fg)
        route_fg.add_to(m)


def path_length_m(G, path_nodes) -> float:
    """Return approximate geometric route length in metres from graph edge lengths.

    Parameters
    ----------
    G          : NetworkX graph with 'length' edge attributes (metres)
    path_nodes : ordered list of node IDs along the route
    """
    if not path_nodes or len(path_nodes) < 2:
        return 0.0
    total_m = 0.0
    for u, v in zip(path_nodes[:-1], path_nodes[1:]):
        edge_data = G.get_edge_data(u, v)
        if not edge_data:
            continue
        lengths = [float(attrs.get("length", 0.0)) for _, attrs in edge_data.items()]
        if lengths:
            total_m += min(lengths)
    return total_m


def render_shelter_action_zones(folium_map, threat_zones, shelter_analysis):
    """Render shelter-in-place vs evacuate recommendation polygons on a folium map.

    Parameters
    ----------
    folium_map      : folium.Map instance (mutated in-place)
    threat_zones    : dict mapping zone name → Shapely polygon
    shelter_analysis: dict mapping zone name → analysis result dict
    """
    shelter_fg = folium.FeatureGroup(name="SHELTER-IN-PLACE Zones", show=True)
    evacuate_fg = folium.FeatureGroup(name="EVACUATE Zones", show=True)

    for zone_name, zone_data in shelter_analysis.items():
        zone_poly = threat_zones.get(zone_name)
        if zone_poly is None or zone_poly.is_empty:
            continue

        primary_rec = zone_data.get("primary_recommendation", "EVACUATE")
        if primary_rec == "SHELTER":
            color = "#4CAF50"
            fg = shelter_fg
            label = (
                f"{zone_name}: SHELTER-IN-PLACE "
                f"({zone_data.get('shelter_percentage', 0):.0f}%)"
            )
        else:
            color = "#FF5722"
            fg = evacuate_fg
            label = (
                f"{zone_name}: EVACUATE "
                f"({zone_data.get('shelter_percentage', 0):.0f}% shelter)"
            )

        popup_html = (
            f'<div style="font-family: Arial; font-size: 11px;">'
            f"<b>{zone_name}</b><br>"
            f"<b>Primary Recommendation:</b> {primary_rec}<br>"
            f"Shelter: {zone_data.get('shelter_count', 0)} samples "
            f"({zone_data.get('shelter_percentage', 0):.1f}%)<br>"
            f"Evacuate: {zone_data.get('evacuate_count', 0)} samples"
            f"</div>"
        )

        folium.GeoJson(
            zone_poly,
            name=label,
            style_function=lambda x, c=color: {
                "fillColor": c,
                "color": c,
                "weight": 2,
                "fillOpacity": 0.3,
            },
            popup=folium.Popup(popup_html, max_width=250),
        ).add_to(fg)

    shelter_fg.add_to(folium_map)
    evacuate_fg.add_to(folium_map)
