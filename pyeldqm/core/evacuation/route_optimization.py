"""
Route Optimization for Evacuation in pyELDQM

Capabilities:
- Download driveable road network around incident via OpenStreetMap (osmnx)
- Remove/penalize edges intersecting AEGL threat zones
- Risk-weighted shortest paths using NetworkX
- Rank multiple shelters by safest/fastest route
- Render routes on Folium maps

Optional dependencies: osmnx, networkx
Install: pip install osmnx networkx
"""
from typing import Dict, List, Tuple, Optional

import math
import warnings

import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from ..utils.geo_constants import METERS_PER_DEGREE_LAT

try:
    import osmnx as ox
    import networkx as nx
except Exception:
    ox = None
    nx = None
    warnings.warn(
        "osmnx/networkx not found. Install with: pip install osmnx networkx",
        RuntimeWarning
    )

HAZARD_PENALTY = {
    "AEGL-3": 10.0,   # very high risk
    "AEGL-2": 5.0,    # high risk
    "AEGL-1": 2.0     # medium risk
}


def _ensure_libs():
    if ox is None or nx is None:
        raise ImportError("Requires osmnx and networkx. Install with: pip install osmnx networkx")


def build_road_graph(lat: float, lon: float, radius_m: float = 4000) -> "nx.MultiDiGraph":
    """Download drive network around (lat,lon)."""
    _ensure_libs()
    G = ox.graph_from_point((lat, lon), dist=radius_m, network_type="drive")
    return G


def _unsafe_union(threat_zones: Dict[str, Optional[Polygon]]) -> Optional[Polygon]:
    polys = [p for p in threat_zones.values() if p is not None and not p.is_empty]
    if not polys:
        return None
    unsafe = polys[0]
    for p in polys[1:]:
        unsafe = unsafe.union(p)
    return unsafe


def classify_edges_with_risk(
    G: "nx.MultiDiGraph",
    threat_zones: Dict[str, Optional[Polygon]],
    proximity_buffer_m: float = 100.0
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Classify edges as safe/unsafe; compute risk-weight 'risk_weight' on each edge:
    - base: edge length (meters)
    - + penalty if intersects AEGL polygons
    - + proximity penalty if within proximity_buffer of unsafe union
    Returns (safe_edges_gdf, unsafe_edges_gdf) with added columns.
    """
    _ensure_libs()
    edges_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True, fill_edge_geometry=True)

    unsafe = _unsafe_union(threat_zones)
    if unsafe is None:
        # mark all as safe with base weight
        edges_gdf["risk_weight"] = edges_gdf["length"].fillna(1.0)
        return edges_gdf.copy(), edges_gdf.iloc[0:0].copy()

    # Precompute buffered unsafe area for proximity penalty
    # Approx convert meters to degrees at incident latitude by sampling first node
    any_node = list(G.nodes(data=True))[0][1]
    lat0 = any_node.get("y")
    m_to_deg_lat = 1.0 / METERS_PER_DEGREE_LAT
    buffer_deg = proximity_buffer_m * m_to_deg_lat
    unsafe_buffer = unsafe.buffer(buffer_deg)

    safe_rows = []
    unsafe_rows = []

    for _, row in edges_gdf.iterrows():
        geom: LineString = row.geometry
        length = float(row.get("length", 1.0))
        weight = length
        label = "safe"

        if geom is None:
            continue

        # Direct intersection with AEGL zones (apply max penalty across zones)
        max_penalty = 0.0
        for level, pen in HAZARD_PENALTY.items():
            poly = threat_zones.get(level)
            if poly is not None and not poly.is_empty and geom.intersects(poly):
                max_penalty = max(max_penalty, pen)
                label = "unsafe"

        # Proximity penalty if near unsafe union
        if unsafe_buffer.intersects(geom):
            max_penalty = max(max_penalty, 1.0)  # mild proximity penalty

        risk_weight = weight * (1.0 + max_penalty)

        enriched = row.copy()
        enriched["risk_weight"] = risk_weight
        enriched["risk_label"] = label

        if label == "unsafe":
            unsafe_rows.append(enriched)
        else:
            safe_rows.append(enriched)

    safe_gdf = gpd.GeoDataFrame(safe_rows, geometry="geometry", crs=edges_gdf.crs) if safe_rows else edges_gdf.iloc[0:0].copy()
    unsafe_gdf = gpd.GeoDataFrame(unsafe_rows, geometry="geometry", crs=edges_gdf.crs) if unsafe_rows else edges_gdf.iloc[0:0].copy()

    # Push weights back to graph
    for u, v, k, data in G.edges(keys=True, data=True):
        geom = data.get("geometry")
        length = float(data.get("length", 1.0))
        penalty = 0.0
        for level, pen in HAZARD_PENALTY.items():
            poly = threat_zones.get(level)
            if poly is not None and not poly.is_empty and geom and geom.intersects(poly):
                penalty = max(penalty, pen)
        if unsafe is not None and geom and unsafe_buffer.intersects(geom):
            penalty = max(penalty, 1.0)
        data["risk_weight"] = length * (1.0 + penalty)

    return safe_gdf, unsafe_gdf


def _nearest_node(G: "nx.MultiDiGraph", lat: float, lon: float) -> int:
    """Find the nearest graph node to (lat, lon) without requiring scikit-learn.
    Uses haversine distance for accuracy on unprojected (lat/lon) graphs."""
    import math
    best_node = None
    best_dist = math.inf
    for node, data in G.nodes(data=True):
        nlat = data.get("y", 0.0)
        nlon = data.get("x", 0.0)
        # Haversine distance
        dlat = math.radians(nlat - lat)
        dlon = math.radians(nlon - lon)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat)) * math.cos(math.radians(nlat))
             * math.sin(dlon / 2) ** 2)
        dist = 2 * math.asin(math.sqrt(a))
        if dist < best_dist:
            best_dist = dist
            best_node = node
    return best_node


def shortest_safe_route(
    G: "nx.MultiDiGraph",
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    weight: str = "risk_weight"
) -> Tuple[List[int], float]:
    """Compute risk-weighted shortest path between two points. Returns node path and total cost."""
    _ensure_libs()
    o = _nearest_node(G, origin_lat, origin_lon)
    d = _nearest_node(G, dest_lat, dest_lon)
    path = nx.shortest_path(G, source=o, target=d, weight=weight)
    cost = nx.shortest_path_length(G, source=o, target=d, weight=weight)
    return path, cost


def rank_shelters(
    G: "nx.MultiDiGraph",
    origin: Tuple[float, float],
    shelters: List[Tuple[float, float]]
) -> List[Dict]:
    """Rank shelters by safest route (lowest risk_weight)."""
    _ensure_libs()
    results = []
    for (lat, lon) in shelters:
        try:
            path, cost = shortest_safe_route(G, origin[0], origin[1], lat, lon)
            results.append({"lat": lat, "lon": lon, "cost": cost, "path": path})
        except Exception as e:
            results.append({"lat": lat, "lon": lon, "error": str(e)})
    results.sort(key=lambda r: r.get("cost", math.inf))
    return results


def _route_coords(G: "nx.MultiDiGraph", path_nodes: List[int]) -> List[Tuple[float, float]]:
    coords = []
    for n in path_nodes:
        data = G.nodes[n]
        coords.append((data["y"], data["x"]))
    return coords


def add_route_to_map(
    folium_map,
    G: "nx.MultiDiGraph",
    path_nodes: List[int],
    color: str = "#2E7D32",
    name: str = "Optimized Evacuation Route"
):
    """Render a path on the Folium map as a polyline."""
    try:
        import folium
    except Exception:
        raise ImportError("folium is required to render routes")

    coords = _route_coords(G, path_nodes)
    fg = folium.FeatureGroup(name=name, show=True)
    folium.PolyLine(
        coords,
        color=color,
        weight=5,
        opacity=0.9,
        tooltip=name
    ).add_to(fg)
    fg.add_to(folium_map)
    return fg
