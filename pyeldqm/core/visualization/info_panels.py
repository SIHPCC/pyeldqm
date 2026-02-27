"""
Reusable Folium info panel helpers for pyELDQM maps.

This module centralizes HTML info panels (overlays) commonly used across
examples: PAR summaries, evacuation rankings, shelter-in-place guidance,
and multi-threshold health impact summaries. Panels are added as fixed
position HTML elements to Folium maps.
"""

from typing import Dict, List, Optional, Iterable, Any
from datetime import datetime

import folium
from ..utils.zone_extraction import parse_threshold as _parse_threshold


def ensure_layer_control(folium_map: folium.Map, collapsed: bool = False, position: str = "topright") -> None:
    """Ensure there's exactly one LayerControl on the map."""
    try:
        for key, child in list(folium_map._children.items()):
            if child.__class__.__name__ == "LayerControl":
                del folium_map._children[key]
    except Exception:
        pass
    folium.LayerControl(collapsed=collapsed, position=position).add_to(folium_map)


def _add_html_panel(folium_map: folium.Map, html: str) -> None:
    """Add raw HTML as a fixed-position panel to the map root."""
    folium_map.get_root().html.add_child(folium.Element(html))


def add_par_info_panel(
    folium_map: folium.Map,
    par_results: Dict[str, Dict[str, Any]],
    *,
    analyzer: Optional[Any] = None,
    weather: Optional[Dict[str, float]] = None,
    location: Optional[Dict[str, float]] = None,
    base_density: Optional[float] = None,
    theme: str = "live",
    position: str = "bottomleft"
) -> None:
    """
    Add a Population At Risk (PAR) summary panel.

    Parameters
    - par_results: mapping like { 'AEGL-1': {'par': int, ...}, ... }
    - analyzer: object with attributes cycle_count, last_update_time (optional)
    - weather: dict with keys wind_speed, wind_dir (optional)
    - location: dict with 'lat', 'lon' (optional)
    - base_density: numeric people/km^2 (optional)
    - theme: 'live' (green) | 'real' (blue)
    - position: CSS anchor; 'bottomleft' or 'bottomright'
    """

    total_par = sum([d.get("par", 0) for d in par_results.values() if d.get("par", 0) > 0])

    # Theme styling
    if theme == "real":
        gradient_header = "linear-gradient(135deg, #1565c0 0%, #42a5f5 100%)"
        gradient_info = "linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)"
        title_text = "🌍 REAL POPULATION AT RISK"
        subtitle = "Live Geographic Data"
    else:
        gradient_header = "linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%)"
        gradient_info = "linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)"
        title_text = "👥 POPULATION AT RISK (PAR)"
        subtitle = "Zone-based Risk Assessment"

    left_css = "left: 15px;" if position == "bottomleft" else "right: 15px;"

    header = f"""
    <div style="position: fixed; bottom: 15px; {left_css} width: 450px; max-height: 85vh; overflow-y: auto;
                background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
                border: none; z-index: 9999; font-size: 10px; padding: 0;
                border-radius: 12px; font-family: 'Segoe UI', Arial, sans-serif;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 2px 8px rgba(0,0,0,0.2);">
        <div style="background: {gradient_header};
                    padding: 15px; border-radius: 12px 12px 0 0; text-align: center;">
            <h3 style="margin: 0; color: white; font-size: 15px; font-weight: 600;">{title_text}</h3>
            <div style="color: rgba(255,255,255,0.9); font-size: 9px; margin-top: 4px;">{subtitle}</div>
        </div>
        <div style="padding: 12px;">
            <div style="background: {gradient_info};
                        padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                <div style="color: #2c3e50; font-size: 9px;">
                    <b>Total Population at Risk:</b><br>
                    <span style="font-size: 20px; font-weight: bold;">{total_par:,}</span> people
                </div>
            </div>
            <div style="background: white; border-radius: 8px; padding: 8px; margin-bottom: 10px;">
                <div style="font-size: 11px; font-weight: 600; color: #2c3e50; margin-bottom: 6px; border-bottom: 2px solid #2e7d32; padding-bottom: 4px;">🎯 Zone Breakdown</div>
                <table style="width: 100%; border-collapse: collapse; font-size: 9px;">
                    <tr style="background-color: #f5f5f5; font-weight: bold;">
                        <td style="padding: 5px; border-bottom: 1px solid #ddd;">Zone</td>
                        <td style="text-align: right; padding: 5px; border-bottom: 1px solid #ddd;">PAR</td>
                    </tr>
    """

    zone_order = ["AEGL-3", "AEGL-2", "AEGL-1"]
    color_map = {"AEGL-1": "#FFFF00", "AEGL-2": "#FFA500", "AEGL-3": "#FF0000"}

    rows = []
    for zone_name in zone_order:
        if zone_name not in par_results:
            continue
        par = par_results[zone_name].get("par", 0)
        status_color = "red" if par > 10000 else ("orange" if par > 5000 else "green")
        rows.append(
            f"""
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 5px;"><span style="color: {color_map.get(zone_name, '#999999')};"><b>●</b></span> {zone_name}</td>
                <td style="text-align: right; padding: 5px; font-weight: bold; color: {status_color};">{par:,}</td>
            </tr>
            """
        )

    footer_rows = f"""
                    <tr style="background: linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 100%); font-weight: bold;">
                        <td style="padding: 8px;">TOTAL</td>
                        <td style="text-align: right; padding: 8px; font-size: 13px;">{total_par:,}</td>
                    </tr>
                </table>
            </div>
    """

    meta_bits: List[str] = []
    if analyzer is not None:
        # Support both datetime and string for last_update_time
        ts = analyzer.last_update_time if getattr(analyzer, "last_update_time", None) else None
        if isinstance(ts, datetime):
            ts_str = ts.strftime('%H:%M:%S')
        else:
            ts_str = str(ts) if ts is not None else "N/A"
        meta_bits.append(f"<div><b>Cycle:</b> #{getattr(analyzer, 'cycle_count', '?')}</div>")
        meta_bits.append(f"<div><b>Updated:</b> {ts_str}</div>")
    if location is not None:
        lat = location.get("lat")
        lon = location.get("lon")
        if lat is not None and lon is not None:
            meta_bits.append(f"<div><b>Location:</b> {lat:.4f}°N, {lon:.4f}°E</div>")
    if base_density is not None:
        meta_bits.append(f"<div><b>Density:</b> {base_density} people/km²</div>")
    if weather is not None:
        if "wind_speed" in weather and "wind_dir" in weather:
            meta_bits.append(
                f"<div><b>Wind:</b> {weather['wind_speed']:.1f} m/s @ {weather['wind_dir']:.0f}°</div>"
            )

    meta_html = ""
    if meta_bits:
        meta_html = f"""
            <div style="background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%); padding: 10px; border-radius: 8px; font-size: 9px; color: #2c3e50;">
                {"".join(meta_bits)}
            </div>
        """

    tail = """
        </div>
    </div>
    """

    _add_html_panel(folium_map, header + "\n".join(rows) + footer_rows + meta_html + tail)


def add_evacuation_info_panel(
    folium_map: folium.Map,
    *,
    weather: Optional[Dict[str, float]] = None,
    stability: Optional[str] = None,
    shelter_ranking: Optional[List[Dict[str, Any]]] = None,
    shelters_catalog: Optional[List[tuple]] = None,
    position: str = "bottomleft"
) -> None:
    """Add optimized evacuation summary with top shelter rankings."""
    left_css = "left: 15px;" if position == "bottomleft" else "right: 15px;"

    rows = []
    if shelter_ranking:
        for idx, r in enumerate(shelter_ranking[:3]):
            status = "✓" if "path" in r else "✗"
            name = "Unknown"
            if shelters_catalog:
                try:
                    # shelters_catalog: [(lat, lon, name), ...]
                    latlon = (r.get("lat"), r.get("lon"))
                    name = next((nm for (lat, lon, nm) in shelters_catalog if lat == latlon[0] and lon == latlon[1]), name)
                except Exception:
                    pass
            cost_val = r.get("cost", "N/A")
            if isinstance(cost_val, (int, float)):
                cost_val = f"{cost_val:.0f}"
            bg = "#e8f5e9" if idx == 0 else "#f5f5f5"
            rows.append(
                f"""
                <tr style=\"background: {bg};\">
                    <td style=\"padding: 4px; font-weight: {'bold' if idx == 0 else 'normal'};\">{status} {name}</td>
                    <td style=\"padding: 4px; text-align: center; font-weight: {'bold' if idx == 0 else 'normal'};\">{cost_val}</td>
                </tr>
                """
            )

    wx_html = ""
    if weather is not None:
        wx_html = f"<b>Wind:</b> {weather.get('wind_dir', 0):.0f}° @ {weather.get('wind_speed', 0):.1f} m/s"
    stab_html = f"<b>Stability:</b> {stability}" if stability else ""

    html = f"""
    <div style="position: fixed; bottom: 15px; {left_css} width: 450px; max-height: 85vh; overflow-y: auto;
                background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
                border: none; z-index: 9999; font-size: 10px; padding: 0;
                border-radius: 12px; font-family: 'Segoe UI', Arial, sans-serif;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 2px 8px rgba(0,0,0,0.2);">
        <div style="background: linear-gradient(135deg, #0066FF 0%, #00C9FF 100%);
                    padding: 15px; border-radius: 12px 12px 0 0; text-align: center;">
            <h3 style="margin: 0; color: white; font-size: 15px; font-weight: 600;">🚀 OPTIMIZED EVACUATION</h3>
            <div style="color: rgba(255,255,255,0.9); font-size: 9px; margin-top: 4px;">Safe Route Analysis</div>
        </div>
        <div style="padding: 12px;">
            <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                        padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                <div style="color: #2c3e50; font-size: 9px;">
                    {wx_html}<br>{stab_html}
                </div>
            </div>
            <div style="background: white; border-radius: 8px; padding: 8px; margin-bottom: 10px;">
                <div style="font-size: 11px; font-weight: 600; color: #2c3e50; margin-bottom: 6px; border-bottom: 2px solid #0066FF; padding-bottom: 4px;">🏥 Shelter Rankings (by safest route)</div>
                <table style="width: 100%; border-collapse: collapse; font-size: 9px;">
                    <tr style="background: #f5f5f5; font-weight: bold;">
                        <td style="padding: 5px; border-bottom: 1px solid #ddd;">Shelter</td>
                        <td style="padding: 5px; border-bottom: 1px solid #ddd; text-align: center;">Cost</td>
                    </tr>
                    {''.join(rows)}
                </table>
            </div>
            <div style="background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%); padding: 10px; border-radius: 8px; font-size: 9px;">
                <div style="font-weight: 600; margin-bottom: 6px; color: #00796b;">📍 Route Legend:</div>
                <div style="color: #2c3e50;">
                    <b style="color: #0066FF;">🚀 Bright Blue</b> = Optimized Route<br>
                    <b style="color: #2E7D32;">Green</b> = Safe Roads<br>
                    <b style="color: #FF0000;">Red</b> = Hazard Zone Roads
                </div>
            </div>
        </div>
    </div>
    """
    _add_html_panel(folium_map, html)


def add_shelter_in_place_panel(
    folium_map: folium.Map,
    shelter_analysis: Dict[str, Dict[str, Any]],
    *,
    building_type: Optional[str] = None,
    shelter_time_min: Optional[int] = None,
    weather: Optional[Dict[str, float]] = None,
    position: str = "bottomleft"
) -> None:
    """Add shelter-in-place recommendations summary panel."""
    left_css = "left: 15px;" if position == "bottomleft" else "right: 15px;"

    zone_order = ["AEGL-3", "AEGL-2", "AEGL-1"]
    rows: List[str] = []
    for zone_name in zone_order:
        if zone_name not in shelter_analysis:
            continue
        data = shelter_analysis[zone_name]
        rec = data.get("primary_recommendation", "")
        rec_color = "#4CAF50" if rec.upper() == "SHELTER" else "#FF5722"
        rows.append(
            f"""
            <tr>
                <td style=\"padding: 4px;\">{zone_name}</td>
                <td style=\"padding: 4px; color: {rec_color}; font-weight: bold;\">{rec}</td>
                <td style=\"padding: 4px; text-align: center;\">{data.get('shelter_percentage', 0):.0f}%</td>
            </tr>
            """
        )

    wx_html = ""
    if weather is not None:
        wx_html = f"<b>Wind:</b> {weather.get('wind_dir', 0):.0f}° @ {weather.get('wind_speed', 0):.1f} m/s"

    header_bits: List[str] = []
    if building_type:
        header_bits.append(f"<b>Building Type:</b> {building_type}")
    if shelter_time_min is not None:
        header_bits.append(f"<b>Sheltering Time:</b> {shelter_time_min} min")
    if wx_html:
        header_bits.append(wx_html)

    html = f"""
    <div style="position: fixed; bottom: 15px; {left_css} width: 450px; max-height: 85vh; overflow-y: auto;
                background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
                border: none; z-index: 9999; font-size: 10px; padding: 0;
                border-radius: 12px; font-family: 'Segoe UI', Arial, sans-serif;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 2px 8px rgba(0,0,0,0.2);">
        <div style="background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
                    padding: 15px; border-radius: 12px 12px 0 0; text-align: center;">
            <h3 style="margin: 0; color: white; font-size: 15px; font-weight: 600;">🏠 SHELTER-IN-PLACE ANALYSIS</h3>
            <div style="color: rgba(255,255,255,0.9); font-size: 9px; margin-top: 4px;">Protective Action Recommendation</div>
        </div>
        <div style="padding: 12px;">
            <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                        padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                <div style="color: #2c3e50; font-size: 9px;">
                    {'<br>'.join(header_bits)}
                </div>
            </div>
            <div style="background: white; border-radius: 8px; padding: 8px; margin-bottom: 10px;">
                <div style="font-size: 11px; font-weight: 600; color: #2c3e50; margin-bottom: 6px; border-bottom: 2px solid #4CAF50; padding-bottom: 4px;">🎯 Zone Recommendations</div>
                <table style="width: 100%; border-collapse: collapse; font-size: 9px;">
                    <tr style="background: #f5f5f5; font-weight: bold;">
                        <td style="padding: 5px; border-bottom: 1px solid #ddd;">Zone</td>
                        <td style="padding: 5px; border-bottom: 1px solid #ddd;">Action</td>
                        <td style="padding: 5px; border-bottom: 1px solid #ddd; text-align: center;">Shelter %</td>
                    </tr>
                    {''.join(rows)}
                </table>
            </div>
            <div style="background: linear-gradient(135deg, #fff9c4 0%, #fff59d 100%); padding: 10px; border-radius: 8px; font-size: 9px; margin-bottom: 10px;">
                <div style="font-weight: 600; margin-bottom: 6px; color: #f57f17;">📋 Shelter-in-Place Instructions:</div>
                <div style="color: #2c3e50;">
                    • Close all windows and doors<br>
                    • Turn off HVAC/ventilation systems<br>
                    • Seal gaps with towels/tape<br>
                    • Move to interior room away from source<br>
                    • Monitor emergency broadcasts
                </div>
            </div>
            <div style="background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%); padding: 10px; border-radius: 8px; font-size: 9px;">
                <div style="font-weight: 600; margin-bottom: 6px; color: #00796b;">📍 Zone Legend:</div>
                <div style="color: #2c3e50;">
                    <b style="color: #4CAF50;">Green zones</b> = Shelter-in-Place recommended<br>
                    <b style="color: #FF5722;">Orange zones</b> = Evacuate recommended
                </div>
            </div>
        </div>
    </div>
    """
    _add_html_panel(folium_map, html)


def add_health_thresholds_panel(
    folium_map: folium.Map,
    *,
    chemical: str,
    weather: Optional[Dict[str, float]] = None,
    release_rate_gps: Optional[float] = None,
    max_concentration_ppm: Optional[float] = None,
    cycle: Optional[int] = None,
    aegl: Optional[Dict[str, Any]] = None,
    erpg: Optional[Dict[str, Any]] = None,
    pac: Optional[Dict[str, Any]] = None,
    idlh_value: Optional[Any] = None,
    zones_present: Optional[Iterable[str]] = None,
    position: str = "bottomleft"
) -> None:
    """Add multi-threshold health impact panel (AEGL, ERPG, PAC, IDLH)."""

    left_css = "left: 15px;" if position == "bottomleft" else "right: 15px;"

    rows: List[str] = []
    present = set(zones_present) if zones_present else set()

    if aegl:
        rows.append("<tr><td colspan='2' style='background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; font-weight:bold; padding:6px; font-size:10px;'>📊 AEGL (60 min)</td></tr>")
        for lvl, color in [("AEGL-1", "#FFFF00"), ("AEGL-2", "#FFA500"), ("AEGL-3", "#FF0000")]:
            num = _parse_threshold(aegl.get(lvl))
            num_str = f"{num:.1f}" if num is not None else "N/A"
            status = "<span style='color:#00C851;'>✓</span>" if lvl in present else "<span style='color:#ccc;'>—</span>"
            rows.append(f"<tr><td style='padding:5px;'>{status} <span style='color:{color};'>●</span> {lvl}</td><td style='padding:5px; text-align:right; font-weight:bold;'>{num_str} ppm</td></tr>")

    if erpg:
        rows.append("<tr><td colspan='2' style='background:linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color:white; font-weight:bold; padding:6px; font-size:10px; border-top:2px solid #ddd;'>🛡️ ERPG (1 hour)</td></tr>")
        for lvl, color in [("ERPG-1", "#00FF00"), ("ERPG-2", "#FF00FF"), ("ERPG-3", "#8B0000")]:
            num = _parse_threshold(erpg.get(lvl))
            num_str = f"{num:.1f}" if num is not None else "N/A"
            status = "<span style='color:#00C851;'>✓</span>" if lvl in present else "<span style='color:#ccc;'>—</span>"
            rows.append(f"<tr><td style='padding:5px;'>{status} <span style='color:{color};'>- -</span> {lvl}</td><td style='padding:5px; text-align:right; font-weight:bold;'>{num_str} ppm</td></tr>")

    if pac:
        rows.append("<tr><td colspan='2' style='background:linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color:white; font-weight:bold; padding:6px; font-size:10px; border-top:2px solid #ddd;'>💊 PAC (Protective Action Criteria)</td></tr>")
        for lvl, color in [("PAC-1", "#1E90FF"), ("PAC-2", "#DC143C"), ("PAC-3", "#800080")]:
            num = _parse_threshold(pac.get(lvl))
            num_str = f"{num:.1f}" if num is not None else "N/A"
            status = "<span style='color:#00C851;'>✓</span>" if lvl in present else "<span style='color:#ccc;'>—</span>"
            rows.append(f"<tr><td style='padding:5px;'>{status} <span style='color:{color};'>•-</span> {lvl}</td><td style='padding:5px; text-align:right; font-weight:bold;'>{num_str} ppm</td></tr>")

    if idlh_value is not None:
        rows.append("<tr><td colspan='2' style='background:linear-gradient(135deg, #FFB84D 0%, #FF6B6B 100%); color:white; font-weight:bold; padding:6px; font-size:10px; border-top:2px solid #ddd;'>⚠️ IDLH (30 min escape)</td></tr>")
        num = _parse_threshold(idlh_value)
        num_str = f"{num:.1f}" if num is not None else "N/A"
        status = "<span style='color:#00C851;'>✓</span>" if "IDLH" in present else "<span style='color:#ccc;'>—</span>"
        rows.append(f"<tr><td style='padding:5px;'>{status} <span style='color:#0000FF;'>· ·</span> IDLH</td><td style='padding:5px; text-align:right; font-weight:bold;'>{num_str} ppm</td></tr>")

    wx = ""
    if weather is not None:
        wx = f"{weather.get('wind_dir', 0):.0f}° @ {weather.get('wind_speed', 0):.1f} m/s"

    left_panel = f"""
    <div style=\"position: fixed; bottom: 15px; {left_css} width: 450px; max-height: 85vh; overflow-y: auto;
                background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
                border: none; z-index: 9999; font-size: 10px; padding: 0;
                border-radius: 12px; font-family: 'Segoe UI', Arial, sans-serif;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 2px 8px rgba(0,0,0,0.2);\"> 
        <div style=\"background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 15px; border-radius: 12px 12px 0 0; text-align: center;\">
            <h3 style=\"margin: 0; color: white; font-size: 15px; font-weight: 600;\">⚕️ HEALTH IMPACT ASSESSMENT</h3>
            <div style=\"color: rgba(255,255,255,0.9); font-size: 9px; margin-top: 4px;\">Chemical Threat Zone Analysis</div>
        </div>
        <div style=\"padding: 12px;\">
            <div style=\"background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                        padding: 10px; border-radius: 8px; margin-bottom: 10px;\">
                <div style=\"display: grid; grid-template-columns: 1fr 1fr; gap: 8px; color: #2c3e50; font-size: 9px;\">
                    <div><b>🧪 Chemical:</b><br><span style=\"font-size:11px; font-weight:bold;\">{chemical}</span></div>
                    <div><b>💨 Release Rate:</b><br><span style=\"font-size:11px; font-weight:bold;\">{release_rate_gps if release_rate_gps is not None else 'N/A'} g/s</span></div>
                    <div><b>🌬️ Wind:</b><br><span style=\"font-size:11px; font-weight:bold;\">{wx}</span></div>
                    <div><b>📈 Max Conc:</b><br><span style=\"font-size:11px; font-weight:bold; color:#d32f2f;\">{(max_concentration_ppm if max_concentration_ppm is not None else 'N/A')}</span></div>
                </div>
            </div>
            <div style=\"background: white; border-radius: 8px; padding: 8px; margin-bottom: 10px;\">
                <div style=\"font-size: 11px; font-weight: 600; color: #2c3e50; margin-bottom: 6px; border-bottom: 2px solid #667eea; padding-bottom: 4px;\">🎯 Health Thresholds</div>
                <table style=\"width: 100%; border-collapse: collapse; font-size: 9px;\">{''.join(rows)}</table>
            </div>
            <div style=\"background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%); padding: 10px; border-radius: 8px; font-size: 9px; margin-bottom: 10px;\">
                <div style=\"font-weight: 600; margin-bottom: 6px; color: #00796b;\">📍 Zone Legend:</div>
                <div style=\"display: grid; grid-template-columns: 1fr 1fr; gap: 4px;\">
                    <div><span style=\"color: #FFFF00; font-size:14px;\">●</span> AEGL - Solid</div>
                    <div><span style=\"color: #FF00FF; font-size:14px;\">━</span> ERPG - Dashed</div>
                    <div><span style=\"color: #1E90FF; font-size:14px;\">•-</span> PAC - Dot-dash</div>
                    <div><span style=\"color: #0000FF; font-size:14px;\">┉</span> IDLH - Dotted</div>
                </div>
            </div>
            <div style=\"font-size: 8px; color: #666; text-align: center; padding: 8px; background: #f5f5f5; border-radius: 8px;\">
                <div style=\"margin-bottom: 3px;\"><b>Cycle #{cycle if cycle is not None else '?'} </b></div>
            </div>
        </div>
    </div>
    """

    _add_html_panel(folium_map, left_panel)


def add_sensor_optimization_panel(
    folium_map: folium.Map,
    all_results: Dict[str, Dict],
    *,
    active_strategy: str,
    available_strategies: List[str],
    cost_per_sensor: float,
    detection_range_m: float,
    position: str = "bottomleft"
) -> None:
    """
    Add sensor optimization summary panel.
    
    Parameters
    ----------
    folium_map : folium.Map
        Map to add panel to
    all_results : dict
        Results for all strategies: {strategy: {'sensors': [...], 'metrics': {...}}}
    active_strategy : str
        Currently active/displayed strategy
    available_strategies : list
        List of all strategy names for comparison
    cost_per_sensor : float
        Cost per sensor unit in USD
    detection_range_m : float
        Detection range per sensor in meters
    position : str
        Panel position ('bottomleft' or 'bottomright')
    """
    if active_strategy not in all_results or all_results[active_strategy] is None:
        return
    
    left_css = "left: 15px;" if position == "bottomleft" else "right: 15px;"
    
    sensors = all_results[active_strategy]['sensors']
    metrics = all_results[active_strategy]['metrics']
    
    # Count sensors by priority
    priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for sensor in sensors:
        p = sensor.get('priority', 'low')
        if p in priority_counts:
            priority_counts[p] += 1
    
    # Build sensor list (show first 5)
    sensor_rows = []
    for i, sensor in enumerate(sensors[:5]):
        priority_colors = {
            "critical": "#d32f2f",
            "high": "#f57c00",
            "medium": "#fbc02d",
            "low": "#1976d2"
        }
        color = priority_colors.get(sensor.get('priority', 'low'), "#666")
        
        sensor_rows.append(f"""
        <tr style="font-size:9px;">
            <td style="padding:4px;">{sensor['id']}</td>
            <td style="padding:4px; color:{color}; font-weight:bold;">{sensor.get('priority', 'N/A').upper()}</td>
            <td style="padding:4px; font-size:8px;">{sensor.get('purpose', 'N/A')[:25]}...</td>
        </tr>
        """)
    
    sensor_table = "".join(sensor_rows)
    
    # Calculate total cost
    total_cost = len(sensors) * cost_per_sensor
    
    # Build comparison table for all strategies
    comparison_rows = []
    for strategy in available_strategies:
        if strategy not in all_results or all_results[strategy] is None:
            continue
        
        strat_metrics = all_results[strategy]['metrics']
        num_sensors = strat_metrics['total_sensors']
        coverage = strat_metrics['coverage_area_km2']
        
        is_active = strategy == active_strategy
        bg_color = "#e3f2fd" if is_active else "#fafafa"
        font_weight = "bold" if is_active else "normal"
        
        comparison_rows.append(f"""
        <tr style="background:{bg_color};">
            <td style="padding:4px; font-weight:{font_weight}; font-size:9px;">{strategy.title()}</td>
            <td style="padding:4px; text-align:center; font-size:9px;">{num_sensors}</td>
            <td style="padding:4px; text-align:center; font-size:9px;">{coverage:.1f}</td>
        </tr>
        """)
    
    comparison_table = "".join(comparison_rows)
    
    # Get active strategy details
    active_metrics_coverage = metrics.get('coverage_area_km2', 0)
    
    html = f"""
    <div style="position: fixed; bottom: 15px; {left_css} width: 450px; max-height: 85vh; overflow-y: auto;
                background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
                border: none; z-index: 9999; font-size: 10px; padding: 0;
                border-radius: 12px; font-family: 'Segoe UI', Arial, sans-serif;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 2px 8px rgba(0,0,0,0.2);">
        
        <!-- HEADER -->
        <div style="background: linear-gradient(135deg, #1565c0 0%, #42a5f5 100%);
                    padding: 15px; border-radius: 12px 12px 0 0; text-align: center;">
            <h3 style="margin: 0; color: white; font-size: 15px; font-weight: 600;">📡 SENSOR OPTIMIZATION</h3>
            <div style="color: rgba(255,255,255,0.9); font-size: 9px; margin-top: 4px;">Network Placement Analysis</div>
        </div>
        
        <div style="padding: 12px;">
            <!-- ACTIVE STRATEGY -->
            <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffe082 100%);
                        padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                <div style="color: #2c3e50; font-size: 9px;">
                    <b>Active Strategy:</b><br>
                    <span style="font-size:14px; font-weight:bold; color:#f57c00;">{active_strategy.upper()}</span>
                </div>
            </div>
            
            <!-- COMPARISON TABLE -->
            <div style="background: white; border-radius: 8px; padding: 8px; margin-bottom: 10px;">
                <div style="font-size: 11px; font-weight: 600; color: #2c3e50; margin-bottom: 6px; border-bottom: 2px solid #1565c0; padding-bottom: 4px;">🎯 Strategy Comparison</div>
                <table style="width:100%; border-collapse:collapse; font-size:9px;">
                    <tr style="background:#f5f5f5; font-weight:bold;">
                        <td style="padding:5px; border-bottom:1px solid #ddd;">Strategy</td>
                        <td style="padding:5px; border-bottom:1px solid #ddd; text-align:center;">Sensors</td>
                        <td style="padding:5px; border-bottom:1px solid #ddd; text-align:center;">Area (km²)</td>
                    </tr>
                    {comparison_table}
                </table>
            </div>
            
            <!-- NETWORK DETAILS -->
            <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                        padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                <div style="color: #2c3e50; font-size: 9px;">
                    <b>Total Sensors:</b> {len(sensors)}<br>
                    <b>Estimated Cost:</b> ${total_cost:,} USD<br>
                    <b>Coverage:</b> {active_metrics_coverage:.2f} km²
                </div>
            </div>
            
            <!-- PRIORITY DISTRIBUTION -->
            <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffcc80 100%);
                        padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                <div style="font-weight: 600; margin-bottom: 6px; color: #e65100; font-size: 10px;">🎯 Priority Distribution</div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:4px; color: #2c3e50; font-size:9px;">
                    <div>🔴 Critical: {priority_counts['critical']}</div>
                    <div>🟠 High: {priority_counts['high']}</div>
                    <div>🟡 Medium: {priority_counts['medium']}</div>
                    <div>🔵 Low: {priority_counts['low']}</div>
                </div>
            </div>
            
            <!-- SAMPLE SENSORS -->
            <div style="background: white; border-radius: 8px; padding: 8px; margin-bottom: 10px;">
                <div style="font-size: 11px; font-weight: 600; color: #2c3e50; margin-bottom: 6px; border-bottom: 2px solid #1565c0; padding-bottom: 4px;">📍 Sample Sensors (First 5)</div>
                <table style="width:100%; border-collapse:collapse; font-size:9px;">
                    <tr style="background:#f5f5f5; font-weight:bold;">
                        <td style="padding:5px; border-bottom:1px solid #ddd;">ID</td>
                        <td style="padding:5px; border-bottom:1px solid #ddd;">Priority</td>
                        <td style="padding:5px; border-bottom:1px solid #ddd;">Purpose</td>
                    </tr>
                    {sensor_table}
                </table>
                {f'<div style="font-size:8px; color:#666; margin-top:4px; text-align:center;">... and {len(sensors)-5} more sensors</div>' if len(sensors) > 5 else ''}
            </div>
            
            <!-- COVERAGE METRICS -->
            <div style="background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
                        padding: 10px; border-radius: 8px; font-size: 9px;">
                <div style="font-weight: 600; margin-bottom: 6px; color: #00796b;">📊 Coverage Metrics</div>
                <div style="color: #2c3e50;">
                    <b>Detection Range:</b> {detection_range_m}m per sensor<br>
                    Click sensor markers on map for details
                </div>
            </div>
        </div>
    </div>
    """
    
    _add_html_panel(folium_map, html)


def add_threat_zones_info_panel(
    folium_map: folium.Map,
    zones: Dict[str, Any],
    *,
    weather: Optional[Dict[str, float]] = None,
    chemical_name: str = "Chemical",
    thresholds: Optional[Dict[str, float]] = None,
    source_lat: Optional[float] = None,
    source_lon: Optional[float] = None,
    stability_class: Optional[str] = None,
    release_rate: Optional[float] = None,
    position: str = "bottomleft"
) -> None:
    """
    Add a comprehensive threat zones summary panel with distance and weather information.

    Parameters
    - zones: Dict mapping zone name to shapely Polygon or None
    - weather: dict with keys wind_speed, wind_dir, temperature_K
    - chemical_name: Name of the chemical
    - thresholds: Dict mapping zone name to ppm value
    - source_lat, source_lon: Source location for distance calculation
    - stability_class: Atmospheric stability class
    - release_rate: Release rate in g/s
    - position: 'bottomleft' or 'bottomright'
    """
    from datetime import datetime
    from math import radians, cos, sin, asin, sqrt
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate great circle distance between two points (km)."""
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r
    
    def get_max_distance_from_source(polygon, src_lat, src_lon):
        """Get maximum distance (km) from source to polygon boundary."""
        if polygon is None or polygon.is_empty:
            return None
        
        max_dist = 0
        # Get exterior coordinates (polygon boundary)
        try:
            coords = list(polygon.exterior.coords)
            for lon, lat in coords:  # Note: exterior.coords gives (lon, lat)
                dist = haversine_distance(src_lat, src_lon, lat, lon)
                max_dist = max(max_dist, dist)
        except Exception:
            return None
        
        return max_dist if max_dist > 0 else None
    
    # Calculate distances for each zone
    zone_distances = {}
    zone_colors = {
        'AEGL-1': '#FFFF00',
        'AEGL-2': '#FFA500',
        'AEGL-3': '#FF0000',
    }
    zone_order = ['AEGL-3', 'AEGL-2', 'AEGL-1']
    
    for zone_name in zone_order:
        if zone_name in zones:
            zone_poly = zones[zone_name]
            if zone_poly is not None and not zone_poly.is_empty and source_lat and source_lon:
                dist_km = get_max_distance_from_source(zone_poly, source_lat, source_lon)
                zone_distances[zone_name] = dist_km
    
    # Build zone rows
    zone_rows = []
    for zone_name in zone_order:
        if zone_name in zone_distances:
            dist = zone_distances[zone_name]
            threshold_val = thresholds.get(zone_name, 'N/A') if thresholds else 'N/A'
            threshold_str = f"{threshold_val:.0f}" if isinstance(threshold_val, (int, float)) else str(threshold_val)
            color = zone_colors.get(zone_name, '#999999')
            
            # Only show if distance is available
            if dist is not None:
                zone_rows.append(f"""
                <tr style="background: rgba(255, 255, 255, 0.5);">
                    <td style="padding: 6px; border-bottom: 1px solid #ddd; color: {color}; font-weight: bold; font-size: 11px;">{zone_name}</td>
                    <td style="padding: 6px; border-bottom: 1px solid #ddd; text-align: center; font-size: 10px;">{threshold_str} ppm</td>
                    <td style="padding: 6px; border-bottom: 1px solid #ddd; text-align: right; font-weight: bold; color: #d32f2f; font-size: 11px;">{dist:.2f} km</td>
                </tr>
                """)
            else:
                zone_rows.append(f"""
                <tr style="opacity: 0.5;">
                    <td style="padding: 6px; border-bottom: 1px solid #ddd; color: {color}; font-weight: bold; font-size: 11px;">{zone_name}</td>
                    <td style="padding: 6px; border-bottom: 1px solid #ddd; text-align: center; font-size: 10px;">—</td>
                    <td style="padding: 6px; border-bottom: 1px solid #ddd; text-align: center; color: #999; font-size: 10px;">No zone</td>
                </tr>
                """)
        else:
            color = zone_colors.get(zone_name, '#999999')
            zone_rows.append(f"""
            <tr style="opacity: 0.5;">
                <td style="padding: 6px; border-bottom: 1px solid #ddd; color: {color}; font-weight: bold; font-size: 11px;">{zone_name}</td>
                <td style="padding: 6px; border-bottom: 1px solid #ddd; text-align: center; font-size: 10px;">—</td>
                <td style="padding: 6px; border-bottom: 1px solid #ddd; text-align: center; color: #999; font-size: 10px;">No zone</td>
            </tr>
            """)
    
    zone_table = "".join(zone_rows)
    
    # Weather info
    weather_str = "—"
    wind_str = "—"
    temp_str = "—"
    humidity_str = "—"
    if weather:
        wind_speed = weather.get('wind_speed', 0)
        wind_dir = weather.get('wind_dir', 0)
        temp_c = weather.get('temperature_K', 273.15) - 273.15
        humidity = weather.get('humidity', 0)
        wind_str = f"{wind_speed:.1f} m/s @ {wind_dir:.0f}°"
        temp_str = f"{temp_c:.1f}°C"
        humidity_str = f"{humidity*100:.0f}%"
    
    # Stability and release info
    stability_str = stability_class if stability_class else "—"
    release_str = f"{release_rate:.0f} g/s" if release_rate else "—"
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    left_css = "left: 15px;" if position == "bottomleft" else "right: 15px;"
    
    html = f"""
    <div style="position: fixed; bottom: 15px; {left_css} width: 420px; max-height: 85vh; overflow-y: auto;
                background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
                border: 3px solid #d32f2f; z-index: 9999; font-size: 10px; padding: 0;
                border-radius: 8px; font-family: 'Segoe UI', Arial, sans-serif;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 2px 8px rgba(0,0,0,0.2);">
        
        <!-- HEADER -->
        <div style="background: linear-gradient(135deg, #c41c3b 0%, #d32f2f 100%);
                    padding: 12px; border-radius: 8px 8px 0 0; text-align: center;">
            <h3 style="margin: 0; color: white; font-size: 14px; font-weight: 600;">⚠️ LIVE THREAT ZONES</h3>
            <div style="color: rgba(255,255,255,0.95); font-size: 9px; margin-top: 3px;">{chemical_name} Release Event</div>
        </div>
        
        <div style="padding: 10px;">
            <!-- WEATHER CONDITIONS -->
            <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                        padding: 8px; border-radius: 6px; margin-bottom: 8px; font-size: 9px;">
                <div style="font-weight: 600; color: #1565c0; margin-bottom: 4px;">🌬️ Current Conditions</div>
                <table style="width: 100%; font-size: 9px; color: #2c3e50;">
                    <tr><td><b>Wind:</b></td><td style="text-align: right;">{wind_str}</td></tr>
                    <tr><td><b>Temp:</b></td><td style="text-align: right;">{temp_str}</td></tr>
                    <tr><td><b>Humidity:</b></td><td style="text-align: right;">{humidity_str}</td></tr>
                    <tr><td><b>Stability:</b></td><td style="text-align: right;">Class {stability_str}</td></tr>
                    <tr><td><b>Release Rate:</b></td><td style="text-align: right;">{release_str}</td></tr>
                </table>
            </div>
            
            <!-- ZONE TABLE -->
            <div style="background: white; border-radius: 6px; padding: 8px; margin-bottom: 8px; border: 1px solid #ddd;">
                <div style="font-size: 10px; font-weight: 600; color: #2c3e50; margin-bottom: 6px; 
                            border-bottom: 2px solid #d32f2f; padding-bottom: 4px;">🎯 Zone Distances from Source</div>
                <table style="width: 100%; border-collapse: collapse; font-size: 9px;">
                    <tr style="background-color: #f5f5f5; font-weight: bold;">
                        <td style="padding: 6px; border-bottom: 1px solid #ddd;">Zone</td>
                        <td style="padding: 6px; border-bottom: 1px solid #ddd; text-align: center;">Threshold</td>
                        <td style="padding: 6px; border-bottom: 1px solid #ddd; text-align: right;">Distance</td>
                    </tr>
                    {zone_table}
                </table>
            </div>
            
            <!-- TIMESTAMP -->
            <div style="background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%);
                        padding: 6px; border-radius: 6px; font-size: 8px; color: #666; text-align: center;">
                Updated: {timestamp}
            </div>
        </div>
    </div>
    """
    
    _add_html_panel(folium_map, html)


def add_threat_zones_and_par_panel(
    folium_map: folium.Map,
    zones: Dict[str, Any],
    par_results: Dict[str, Dict[str, Any]],
    *,
    weather: Optional[Dict[str, float]] = None,
    chemical_name: str = "Chemical",
    thresholds: Optional[Dict[str, float]] = None,
    source_lat: Optional[float] = None,
    source_lon: Optional[float] = None,
    stability_class: Optional[str] = None,
    release_rate: Optional[float] = None,
    position: str = "bottomleft"
) -> None:
    """
    Add a comprehensive merged panel with threat zones, weather, and population at risk.

    Parameters
    - zones: Dict mapping zone name to shapely Polygon or None
    - par_results: Dict mapping zone name to {'par': int, ...}
    - weather: dict with keys wind_speed, wind_dir, temperature_K
    - chemical_name: Name of the chemical
    - thresholds: Dict mapping zone name to ppm value
    - source_lat, source_lon: Source location for distance calculation
    - stability_class: Atmospheric stability class
    - release_rate: Release rate in g/s
    - position: 'bottomleft' or 'bottomright'
    """
    from datetime import datetime
    from math import radians, cos, sin, asin, sqrt
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate great circle distance between two points (km)."""
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r
    
    def get_max_distance_from_source(polygon, src_lat, src_lon):
        """Get maximum distance (km) from source to polygon boundary."""
        if polygon is None or polygon.is_empty:
            return None
        
        max_dist = 0
        try:
            coords = list(polygon.exterior.coords)
            for lon, lat in coords:
                dist = haversine_distance(src_lat, src_lon, lat, lon)
                max_dist = max(max_dist, dist)
        except Exception:
            return None
        
        return max_dist if max_dist > 0 else None
    
    # Calculate total PAR
    total_par = sum([d.get("par", 0) for d in par_results.values() if d.get("par", 0) > 0])
    
    # Calculate distances for each zone
    zone_distances = {}
    zone_colors = {
        'AEGL-1': '#FFFF00',
        'AEGL-2': '#FFA500',
        'AEGL-3': '#FF0000',
    }
    zone_order = ['AEGL-3', 'AEGL-2', 'AEGL-1']
    
    for zone_name in zone_order:
        if zone_name in zones:
            zone_poly = zones[zone_name]
            if zone_poly is not None and not zone_poly.is_empty and source_lat and source_lon:
                dist_km = get_max_distance_from_source(zone_poly, source_lat, source_lon)
                zone_distances[zone_name] = dist_km
    
    # Build comprehensive zone rows with both distance and PAR
    zone_rows = []
    for zone_name in zone_order:
        color = zone_colors.get(zone_name, '#999999')
        threshold_val = thresholds.get(zone_name, 'N/A') if thresholds else 'N/A'
        threshold_str = f"{threshold_val:.0f}" if isinstance(threshold_val, (int, float)) else str(threshold_val)
        
        dist = zone_distances.get(zone_name)
        par = par_results.get(zone_name, {}).get('par', 0) if zone_name in par_results else 0
        
        if dist is not None:
            par_color = "red" if par > 10000 else ("orange" if par > 5000 else "green")
            zone_rows.append(f"""
            <tr style="background: rgba(255, 255, 255, 0.5); border-bottom: 1px solid #ddd;">
                <td style="padding: 6px; color: {color}; font-weight: bold; font-size: 11px;">● {zone_name}</td>
                <td style="padding: 6px; text-align: center; font-size: 10px;">{threshold_str}</td>
                <td style="padding: 6px; text-align: right; font-weight: bold; color: #d32f2f; font-size: 11px;">{dist:.2f} km</td>
                <td style="padding: 6px; text-align: right; font-weight: bold; color: {par_color}; font-size: 10px;">{par:,}</td>
            </tr>
            """)
        else:
            zone_rows.append(f"""
            <tr style="opacity: 0.5; border-bottom: 1px solid #ddd;">
                <td style="padding: 6px; color: {color}; font-weight: bold; font-size: 11px;">● {zone_name}</td>
                <td style="padding: 6px; text-align: center; font-size: 10px;">—</td>
                <td style="padding: 6px; text-align: center; color: #999; font-size: 10px;">No zone</td>
                <td style="padding: 6px; text-align: center; color: #999; font-size: 10px;">—</td>
            </tr>
            """)
    
    zone_table = "".join(zone_rows)
    
    # Weather info
    wind_str = "—"
    temp_str = "—"
    humidity_str = "—"
    if weather:
        wind_speed = weather.get('wind_speed', 0)
        wind_dir = weather.get('wind_dir', 0)
        temp_c = weather.get('temperature_K', 273.15) - 273.15
        humidity = weather.get('humidity', 0)
        wind_str = f"{wind_speed:.1f} m/s @ {wind_dir:.0f}°"
        temp_str = f"{temp_c:.1f}°C"
        humidity_str = f"{humidity*100:.0f}%"
    
    stability_str = stability_class if stability_class else "—"
    release_str = f"{release_rate:.0f} g/s" if release_rate else "—"
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    left_css = "left: 15px;" if position == "bottomleft" else "right: 15px;"
    
    html = f"""
    <div style="position: fixed; bottom: 15px; {left_css} width: 520px; max-height: 85vh; overflow-y: auto;
                background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
                border: 3px solid #d32f2f; z-index: 9999; font-size: 10px; padding: 0;
                border-radius: 8px; font-family: 'Segoe UI', Arial, sans-serif;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 2px 8px rgba(0,0,0,0.2);">
        
        <!-- HEADER -->
        <div style="background: linear-gradient(135deg, #c41c3b 0%, #d32f2f 100%);
                    padding: 12px; border-radius: 8px 8px 0 0; text-align: center;">
            <h3 style="margin: 0; color: white; font-size: 14px; font-weight: 600;">⚠️ THREAT ZONES & RISK ASSESSMENT</h3>
            <div style="color: rgba(255,255,255,0.95); font-size: 9px; margin-top: 3px;">{chemical_name} Release Event</div>
        </div>
        
        <div style="padding: 10px;">
            <!-- WEATHER CONDITIONS -->
            <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                        padding: 8px; border-radius: 6px; margin-bottom: 8px; font-size: 9px;">
                <div style="font-weight: 600; color: #1565c0; margin-bottom: 4px;">🌬️ Current Conditions</div>
                <table style="width: 100%; font-size: 9px; color: #2c3e50;">
                    <tr><td><b>Wind:</b></td><td style="text-align: right;">{wind_str}</td></tr>
                    <tr><td><b>Temp:</b></td><td style="text-align: right;">{temp_str}</td></tr>
                    <tr><td><b>Humidity:</b></td><td style="text-align: right;">{humidity_str}</td></tr>
                    <tr><td><b>Stability:</b></td><td style="text-align: right;">Class {stability_str}</td></tr>
                    <tr><td><b>Release Rate:</b></td><td style="text-align: right;">{release_str}</td></tr>
                </table>
            </div>
            
            <!-- POPULATION AT RISK -->
            <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                        padding: 8px; border-radius: 6px; margin-bottom: 8px; font-size: 9px;">
                <div style="font-weight: 600; color: #2e7d32; margin-bottom: 4px;">👥 Population at Risk</div>
                <div style="color: #2c3e50;">
                    <span style="font-size: 16px; font-weight: bold; color: #d32f2f;">{total_par:,}</span>
                    <span style="font-size: 9px;"> people at risk</span>
                </div>
            </div>
            
            <!-- ZONE TABLE -->
            <div style="background: white; border-radius: 6px; padding: 8px; margin-bottom: 8px; border: 1px solid #ddd;">
                <div style="font-size: 10px; font-weight: 600; color: #2c3e50; margin-bottom: 6px; 
                            border-bottom: 2px solid #d32f2f; padding-bottom: 4px;">🎯 Zone Analysis</div>
                <table style="width: 100%; border-collapse: collapse; font-size: 9px;">
                    <tr style="background-color: #f5f5f5; font-weight: bold;">
                        <td style="padding: 6px; border-bottom: 1px solid #ddd;">Zone</td>
                        <td style="padding: 6px; border-bottom: 1px solid #ddd; text-align: center;">Threshold</td>
                        <td style="padding: 6px; border-bottom: 1px solid #ddd; text-align: right;">Distance</td>
                        <td style="padding: 6px; border-bottom: 1px solid #ddd; text-align: right;">Population</td>
                    </tr>
                    {zone_table}
                </table>
            </div>
            
            <!-- TIMESTAMP -->
            <div style="background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%);
                        padding: 6px; border-radius: 6px; font-size: 8px; color: #666; text-align: center;">
                Updated: {timestamp}
            </div>
        </div>
    </div>
    """
    
    _add_html_panel(folium_map, html)
