"""
Zone Layer Rendering Utilities

Provides centralized helpers to render shapely polygon zones onto Folium maps
with consistent color mapping and styles for AEGL, ERPG, PAC, and IDLH.
"""

from typing import Dict, Optional, Any
import folium
from shapely.geometry import Polygon

from ..utils.zone_extraction import parse_threshold


# Color maps
AEGL_COLORS = {"AEGL-1": "#FFFF00", "AEGL-2": "#FFA500", "AEGL-3": "#FF0000"}
ERPG_COLORS = {"ERPG-1": "#00FF00", "ERPG-2": "#FF00FF", "ERPG-3": "#8B0000"}
PAC_COLORS = {"PAC-1": "#1E90FF", "PAC-2": "#DC143C", "PAC-3": "#800080"}
IDLH_COLOR = "#0000FF"


def _style_for_zone(zone_name: str) -> Dict[str, Any]:
    """Return a default style dict based on zone type name."""
    if zone_name.startswith("AEGL"):
        color = AEGL_COLORS.get(zone_name, "#999999")
        return {"color": color, "fillColor": color, "weight": 2, "opacity": 0.8, "fillOpacity": 0.25}
    if zone_name.startswith("ERPG"):
        color = ERPG_COLORS.get(zone_name, "#999999")
        return {"color": color, "fillColor": color, "weight": 3, "opacity": 0.9, "fillOpacity": 0.15, "dashArray": "10, 5"}
    if zone_name.startswith("PAC"):
        color = PAC_COLORS.get(zone_name, "#999999")
        return {"color": color, "fillColor": color, "weight": 2, "opacity": 0.85, "fillOpacity": 0.12, "dashArray": "8, 3, 2, 3"}
    if zone_name == "IDLH":
        return {"color": IDLH_COLOR, "fillColor": IDLH_COLOR, "weight": 4, "opacity": 1.0, "fillOpacity": 0.10, "dashArray": "2, 8"}
    return {"color": "#999999", "fillColor": "#999999", "weight": 2, "opacity": 0.8, "fillOpacity": 0.2}


def add_zone_polygons(
    folium_map: folium.Map,
    zones: Dict[str, Optional[Polygon]],
    *,
    thresholds_context: Optional[Dict[str, Any]] = None,
    name_prefix: Optional[str] = None
) -> None:
    """
    Render zones to a Folium map with consistent styling.

    Parameters
    - zones: dict mapping zone name to shapely Polygon
    - thresholds_context: optional dict providing threshold values per type:
        { 'AEGL': {'AEGL-1': val, ...}, 'ERPG': {...}, 'PAC': {...}, 'IDLH': val }
    - name_prefix: optional layer name prefix
    """
    for zone_name, zone_poly in zones.items():
        if zone_poly is None or getattr(zone_poly, "is_empty", True):
            continue

        style = _style_for_zone(zone_name)
        display_name = f"{name_prefix} {zone_name}" if name_prefix else f"{zone_name} Zone"

        # Build popup with threshold (if available)
        threshold_val = None
        if thresholds_context:
            if zone_name.startswith("AEGL"):
                threshold_val = thresholds_context.get("AEGL", {}).get(zone_name)
            elif zone_name.startswith("ERPG"):
                threshold_val = thresholds_context.get("ERPG", {}).get(zone_name)
            elif zone_name.startswith("PAC"):
                threshold_val = thresholds_context.get("PAC", {}).get(zone_name)
            elif zone_name == "IDLH":
                threshold_val = thresholds_context.get("IDLH")

        threshold_num = parse_threshold(threshold_val) if threshold_val is not None else None
        threshold_str = f"{threshold_num:.1f}" if threshold_num is not None else "N/A"

        popup_html = f"""
        <div style="font-family: Arial; font-size: 11px;">
            <b>{zone_name}</b><br>
            Threshold: {threshold_str} ppm
        </div>
        """

        folium.GeoJson(
            zone_poly,
            name=display_name,
            style_function=lambda x, s=style: {
                "fillColor": s.get("fillColor", s.get("color", "#999")),
                "color": s.get("color", "#999"),
                "weight": s.get("weight", 2),
                "fillOpacity": s.get("fillOpacity", 0.2),
                "opacity": s.get("opacity", 0.8),
                "dashArray": s.get("dashArray")
            },
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(folium_map)
