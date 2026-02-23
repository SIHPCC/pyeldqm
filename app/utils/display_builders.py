"""
utils/display_builders.py
=========================
Pure Dash layout builders (html.Div / dbc.Card).
No callbacks or app imports.
"""

from math import radians, cos, sin, asin, sqrt
from datetime import datetime

from dash import html
import dash_bootstrap_components as dbc


# ---------------------------------------------------------------------------
# SIMULATION CONDITIONS DISPLAY
# ---------------------------------------------------------------------------

def create_simulation_conditions_display(
    weather,
    stability_class,
    release_rate=None,
    tank_height=None,
    sources=None,
    is_multi_source=False,
    simulation_datetime=None,
    datetime_mode="now",
    timezone_offset_hrs=5.0,
    terrain_roughness="URBAN",
    source_term_mode="continuous",
    duration_minutes=None,
    mass_released_kg=None,
    receptor_height_m=1.5,
):
    """Return an ``html.Div`` summarising meteorology + release parameters."""
    wind_speed = weather.get("wind_speed", 0)
    wind_dir = weather.get("wind_dir", 0)
    temp_c = weather.get("temperature_K", 273.15) - 273.15
    humidity = weather.get("humidity", 0) * 100
    cloud_cover = weather.get("cloud_cover", 0) * 100
    weather_source = weather.get("source", "unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    simulation_datetime_str = (simulation_datetime or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    datetime_mode_label = "Specific Datetime" if datetime_mode == "specific" else "Datetime Now"
    source_term_mode_label = "Instantaneous/Puff" if source_term_mode == "instantaneous" else "Continuous"

    if is_multi_source and sources:
        release_params: list[tuple] = []
        for i, src in enumerate(sources, 1):
            release_params.append((f"Source {i} Rate", f"{src.get('rate', 0)} g/s"))
            release_params.append((f"Source {i} Height", f"{src.get('height', 0)} m"))
        release_params.extend([
            ("Data Source", weather_source.title()),
            ("Terrain Roughness", terrain_roughness),
            ("Receptor Height", f"{receptor_height_m:.1f} m"),
            ("Source Term Mode", source_term_mode_label),
            ("Duration", f"{duration_minutes:.1f} min" if duration_minutes is not None else "—"),
            ("Mass Released", f"{mass_released_kg:.1f} kg" if mass_released_kg is not None else "—"),
            ("Datetime Mode", datetime_mode_label),
            ("Simulation Datetime", simulation_datetime_str),
            ("Timezone Offset", f"{timezone_offset_hrs:+.1f} hrs"),
            ("Last Updated", timestamp),
        ])
    else:
        release_params = [
            ("Release Rate", f"{release_rate} g/s"),
            ("Source Height", f"{tank_height} m"),
            ("Data Source", weather_source.title()),
            ("Terrain Roughness", terrain_roughness),
            ("Receptor Height", f"{receptor_height_m:.1f} m"),
            ("Source Term Mode", source_term_mode_label),
            ("Duration", f"{duration_minutes:.1f} min" if duration_minutes is not None else "—"),
            ("Mass Released", f"{mass_released_kg:.1f} kg" if mass_released_kg is not None else "—"),
            ("Datetime Mode", datetime_mode_label),
            ("Simulation Datetime", simulation_datetime_str),
            ("Timezone Offset", f"{timezone_offset_hrs:+.1f} hrs"),
            ("Last Updated", timestamp),
        ]

    property_groups = {
        "Meteorological Conditions": [
            ("Wind Speed", f"{wind_speed:.1f} m/s"),
            ("Wind Direction", f"{wind_dir:.0f}°"),
            ("Temperature", f"{temp_c:.1f}°C"),
            ("Humidity", f"{humidity:.0f}%"),
            ("Cloud Cover", f"{cloud_cover:.0f}%"),
            ("Stability Class", stability_class),
        ],
        "Release Parameters": release_params,
    }

    colors = {
        "Meteorological Conditions": "#1f77b4",
        "Release Parameters": "#2ca02c",
    }

    sections = []
    for section_title, properties in property_groups.items():
        col_size = (len(properties) + 3) // 4
        cols = []
        for col_idx in range(4):
            start_idx = col_idx * col_size
            end_idx = min((col_idx + 1) * col_size, len(properties))
            col_props = properties[start_idx:end_idx]
            if col_props:
                col_content = [
                    html.Div([
                        html.Div(prop[0], style={
                            "fontSize": "0.75rem", "fontWeight": "500", "color": "#34495e",
                            "marginBottom": "0.08rem", "letterSpacing": "0.3px",
                        }),
                        html.Div(prop[1], style={
                            "fontSize": "0.85rem", "fontWeight": "600", "color": "#2c3e50",
                            "marginBottom": "0.5rem", "paddingBottom": "0.3rem",
                            "borderBottom": "1px solid #ecf0f1",
                        }),
                    ], style={"marginBottom": "0.3rem"})
                    for prop in col_props
                ]
                cols.append(dbc.Col(col_content, width=3, style={"paddingRight": "0.5rem"}))

        section_color = colors[section_title]
        sections.append(dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.I(className="fas fa-layer-group", style={
                        "marginRight": "0.4rem", "color": section_color, "fontSize": "0.85rem",
                    }),
                    section_title,
                ], style={"fontSize": "0.9rem", "fontWeight": "700", "color": section_color,
                          "letterSpacing": "0.5px"}),
                style={"backgroundColor": "transparent",
                       "borderBottom": f"2px solid {section_color}",
                       "padding": "0.5rem 0.75rem"},
            ),
            dbc.CardBody([
                dbc.Row(cols, style={"margin": "0px", "rowGap": "0px"}),
            ], style={"padding": "0.6rem 0.6rem", "backgroundColor": "#f8f9fa"}),
        ], style={"marginBottom": "0.75rem", "border": "1px solid #dee2e6",
                  "boxShadow": "0 1px 2px rgba(0,0,0,0.04)"}))

    return html.Div(sections, style={"backgroundColor": "#ffffff", "borderRadius": "4px", "padding": "0px"})


# ---------------------------------------------------------------------------
# ZONE DISTANCES DISPLAY
# ---------------------------------------------------------------------------

def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * asin(sqrt(a)) * 6371.0


def _max_dist_from_source(polygon, src_lat: float, src_lon: float):
    if polygon is None or polygon.is_empty:
        return None
    max_d = 0.0
    try:
        for lon, lat in polygon.exterior.coords:
            d = _haversine_distance(src_lat, src_lon, lat, lon)
            if d > max_d:
                max_d = d
    except Exception:
        return None
    return max_d if max_d > 0 else None


def _zone_prop_cols(zone_properties):
    """Build three dbc.Col objects for zone-name / threshold / distance."""
    from dash import html
    cell_style = {
        "fontSize": "0.85rem", "fontWeight": "600", "color": "#2c3e50",
        "marginBottom": "0.5rem", "paddingBottom": "0.3rem",
        "borderBottom": "1px solid #ecf0f1",
    }
    label_style = {
        "fontSize": "0.75rem", "fontWeight": "500", "color": "#34495e",
        "marginBottom": "0.08rem", "letterSpacing": "0.3px",
    }

    def _zone_cell(prop):
        return html.Div([
            html.Div("Zone Level", style=label_style),
            html.Div([
                html.Span("●", style={"color": prop[3], "marginRight": "0.3rem", "fontSize": "1rem"}),
                prop[0].replace("● ", ""),
            ], style=cell_style),
        ], style={"marginBottom": "0.3rem"})

    def _thresh_cell(prop):
        return html.Div([
            html.Div("Threshold", style=label_style),
            html.Div(prop[1], style=cell_style),
        ], style={"marginBottom": "0.3rem"})

    def _dist_cell(prop):
        dist_color = "#d32f2f" if prop[2] != "—" else "#adb5bd"
        return html.Div([
            html.Div("Max Distance", style=label_style),
            html.Div(prop[2], style={**cell_style, "color": dist_color}),
        ], style={"marginBottom": "0.3rem"})

    return [
        dbc.Col([_zone_cell(p) for p in zone_properties],  width=4, style={"paddingRight": "0.5rem"}),
        dbc.Col([_thresh_cell(p) for p in zone_properties], width=4, style={"paddingRight": "0.5rem"}),
        dbc.Col([_dist_cell(p) for p in zone_properties],  width=4, style={"paddingRight": "0.5rem"}),
    ]


_ZONE_COLORS = {"AEGL-1": "#FFFF00", "AEGL-2": "#FFA500", "AEGL-3": "#FF0000"}
_ZONE_ORDER = ["AEGL-3", "AEGL-2", "AEGL-1"]
_SECTION_HEADER_STYLE = {
    "backgroundColor": "transparent",
    "borderBottom": "2px solid #d62728",
    "padding": "0.5rem 0.75rem",
}
_CARD_STYLE = {"marginBottom": "0.75rem", "border": "1px solid #dee2e6",
               "boxShadow": "0 1px 2px rgba(0,0,0,0.04)"}


def _collect_zone_properties(threat_zones, thresholds, src_lat, src_lon):
    props = []
    for zone_name in _ZONE_ORDER:
        zone_poly = threat_zones.get(zone_name)
        dist_km = _max_dist_from_source(zone_poly, src_lat, src_lon) if zone_poly else None
        threshold_val = thresholds.get(zone_name, "N/A")
        threshold_str = f"{threshold_val:.0f} ppm" if isinstance(threshold_val, (int, float)) else str(threshold_val)
        dist_str = f"{dist_km:.3f} km" if dist_km is not None else "—"
        props.append((f"● {zone_name}", threshold_str, dist_str, _ZONE_COLORS.get(zone_name, "#999")))
    return props


def create_zone_distances_display(
    threat_zones,
    thresholds,
    source_lat=None,
    source_lon=None,
    sources=None,
    is_multi_source=False,
):
    """Return an ``html.Div`` showing max distances from source(s) to each AEGL zone."""

    title_div = html.Div([
        html.I(className="fas fa-layer-group",
               style={"marginRight": "0.4rem", "color": "#d62728", "fontSize": "0.85rem"}),
        "AEGL Threat Zone Distances from Source",
    ], style={"fontSize": "0.9rem", "fontWeight": "700", "color": "#d62728", "letterSpacing": "0.5px"})

    if is_multi_source and sources:
        source_cards = []
        for src in sources:
            props = _collect_zone_properties(threat_zones, thresholds, src["lat"], src["lon"])
            cols = _zone_prop_cols(props)
            source_cards.append(dbc.Card([
                dbc.CardHeader(
                    html.Div([
                        html.I(className="fas fa-map-marker-alt",
                               style={"marginRight": "0.4rem", "color": "#1976d2", "fontSize": "0.85rem"}),
                        src.get("name", "Source"),
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#1976d2",
                              "letterSpacing": "0.3px"}),
                    style={"backgroundColor": "#e3f2fd", "borderBottom": "1px solid #90caf9",
                           "padding": "0.4rem 0.6rem"},
                ),
                dbc.CardBody([
                    dbc.Row(cols, style={"margin": "0px", "rowGap": "0px"}),
                ], style={"padding": "0.6rem 0.6rem", "backgroundColor": "#fafafa"}),
            ], style={"marginBottom": "0.5rem", "border": "1px solid #dee2e6",
                      "boxShadow": "0 1px 2px rgba(0,0,0,0.04)"}))

        # Multi-source wrapper card
        title_div_multi = html.Div([
            html.I(className="fas fa-layer-group",
                   style={"marginRight": "0.4rem", "color": "#d62728", "fontSize": "0.85rem"}),
            "AEGL Threat Zone Distances from Each Source",
        ], style={"fontSize": "0.9rem", "fontWeight": "700", "color": "#d62728", "letterSpacing": "0.5px"})

        return html.Div([
            dbc.Card([
                dbc.CardHeader(title_div_multi, style=_SECTION_HEADER_STYLE),
                dbc.CardBody(source_cards, style={"padding": "0.6rem", "backgroundColor": "#f8f9fa"}),
            ], style=_CARD_STYLE),
        ], style={"backgroundColor": "#ffffff", "borderRadius": "4px", "padding": "0px"})

    # Single source
    props = _collect_zone_properties(threat_zones, thresholds, source_lat, source_lon)
    cols = _zone_prop_cols(props)
    return html.Div([
        dbc.Card([
            dbc.CardHeader(title_div, style=_SECTION_HEADER_STYLE),
            dbc.CardBody([
                dbc.Row(cols, style={"margin": "0px", "rowGap": "0px"}),
            ], style={"padding": "0.6rem 0.6rem", "backgroundColor": "#f8f9fa"}),
        ], style=_CARD_STYLE),
    ], style={"backgroundColor": "#ffffff", "borderRadius": "4px", "padding": "0px"})
