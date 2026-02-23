"""
layout/sidebar.py
=================
Unified sidebar factory used by all 6 tabs.
Extracted from app/components/threat_zones.py — no logic changes.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from ..components.styles import SIDEBAR_STYLE
from ..components.weather_inputs import create_weather_manual_inputs
from ..components.slider_controls import create_slider_with_range_control
from ..components.tabs.threat_zones import CHEMICAL_OPTIONS, DEFAULT_CHEMICAL


def create_threat_zones_sidebar(
    title="Threat Zone Parameters",
    is_par_analysis=False,
    is_route_analysis=False,
    is_sensor_analysis=False,
    is_shelter_analysis=False,
    is_health_impact_analysis=False,
):
    """Return the shared sidebar dbc.Card for all tabs."""
    # ---- derive per-tab IDs & labels -----------------------------------------
    advanced_container_id = (
        "par-advanced-parameters-container" if is_par_analysis else (
        "route-advanced-parameters-container" if is_route_analysis else (
        "sensor-advanced-parameters-container" if is_sensor_analysis else (
        "shelter-advanced-parameters-container" if is_shelter_analysis else (
        "health-advanced-parameters-container" if is_health_impact_analysis else
        "threat-advanced-parameters-container"))))
    )
    is_derived = (
        is_par_analysis or is_route_analysis or is_sensor_analysis
        or is_shelter_analysis or is_health_impact_analysis
    )
    advanced_container_style = (
        {"pointerEvents": "none", "opacity": "0.55"} if is_derived else {}
    )
    calc_button_id = (
        "calc-shelter-btn" if is_shelter_analysis else
        "calc-health-btn" if is_health_impact_analysis else
        "calc-sensor-btn" if is_sensor_analysis else
        "calc-route-btn" if is_route_analysis else
        "calc-threat-btn"
    )
    calc_button_label = (
        "Calculate Shelter Status" if is_shelter_analysis else
        "Estimate Health Impact" if is_health_impact_analysis else
        "Optimize Sensor Placement" if is_sensor_analysis else
        "Calculate Emergency Routes" if is_route_analysis else
        "Calculate PAR" if is_par_analysis else
        "Calculate Threat Zones"
    )
    calc_status_id = (
        "shelter-status" if is_shelter_analysis else
        "health-status" if is_health_impact_analysis else
        "sensor-status" if is_sensor_analysis else
        "route-status" if is_route_analysis else
        "calc-status"
    )
    calc_button_color = (
        "danger" if is_shelter_analysis else
        "secondary" if is_health_impact_analysis else
        "info" if is_sensor_analysis else
        "warning" if is_route_analysis else
        "success" if is_par_analysis else
        "primary"
    )

    return dbc.Card([
        dbc.CardHeader(
            html.Div([
                html.I(className="fas fa-sliders-h", style={"marginRight": "0.5rem"}),
                title,
            ], style={"fontSize": "0.95rem", "fontWeight": "600"}),
            style={"padding": "0.75rem 1rem", "background": "#e9ecef"},
        ),
        dbc.CardBody([
            # ----------------------------------------------------------------
            # PAR-only block
            # ----------------------------------------------------------------
            *([
                html.Div([
                    html.I(className="fas fa-database", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                    "Population Data",
                ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.5rem"}),
                html.Hr(style={"margin": "0.5rem 0"}),
                html.Label("Population Raster Path",
                           style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                dbc.InputGroup([
                    dbc.Input(
                        id="par-population-raster-path",
                        type="text",
                        placeholder="e.g., /data/worldpop/PHL_ppp_2020.tif",
                        style={"fontSize": "0.85rem"},
                    ),
                    dbc.Button("Browse", id="par-browse-raster-btn", color="secondary", outline=True),
                ], style={"marginBottom": "0.35rem"}),
                html.Small(
                    "Select the full path to a WorldPop GeoTIFF (.tif) raster for population estimation in PAR analysis.",
                    style={"color": "#6c757d"},
                ),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-balance-scale", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "PAR Risk Thresholds",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    html.Label("Critical Risk (people)",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="critical-threshold", type="number", value=10000, step=1000,
                              style={"fontSize": "0.85rem", "marginBottom": "0.5rem"}),
                    html.Label("High Risk (people)",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="high-threshold", type="number", value=5000, step=1000,
                              style={"fontSize": "0.85rem", "marginBottom": "0.25rem"}),
                ]),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-sliders-h", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "PAR Configuration Mode",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    dbc.RadioItems(
                        id="par-parameter-source-mode",
                        options=[
                            {"label": "Use Chemical Threat Zones Parameters", "value": "threat"},
                            {"label": "Use PAR-Specific Parameters", "value": "par"},
                        ],
                        value="threat",
                        style={"fontSize": "0.85rem", "marginBottom": "0.25rem"},
                    ),
                ]),
                html.Div(style={"marginBottom": "0.5rem"}),
            ] if is_par_analysis else []),

            # ----------------------------------------------------------------
            # Route-only block
            # ----------------------------------------------------------------
            *([
                html.Div([
                    html.I(className="fas fa-route", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                    "Emergency Routes Settings",
                ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.5rem"}),
                html.Hr(style={"margin": "0.5rem 0"}),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-road", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "Route Optimization Parameters",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    html.Label("Road Graph Radius (m)",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="route-radius-m", type="number", value=4000, min=500, max=15000, step=100,
                              style={"fontSize": "0.85rem", "marginBottom": "0.5rem"}),
                    html.Label("Hazard Proximity Buffer (m)",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="route-proximity-buffer-m", type="number", value=150, min=0, max=2000, step=10,
                              style={"fontSize": "0.85rem", "marginBottom": "0.5rem"}),
                    dbc.Checklist(
                        id="route-show-all-roads",
                        options=[{"label": " Show Unsafe Roads Layer", "value": "show"}],
                        value=["show"],
                        style={"fontSize": "0.85rem", "marginBottom": "0.25rem"},
                    ),
                ]),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-home", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "Candidate Shelters",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    html.Label("Number of Shelters",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="route-num-shelters", type="number", value=3, min=1, step=1,
                              style={"fontSize": "0.85rem", "marginBottom": "0.35rem"}),
                    html.Small("Enter an integer greater than zero.", style={"color": "#6c757d"}),
                    html.Div(id="route-shelter-inputs-container", style={"marginTop": "0.5rem"}),
                ]),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-sliders-h", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "Emergency Routes Configuration Mode",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    dbc.RadioItems(
                        id="route-parameter-source-mode",
                        options=[
                            {"label": "Use Chemical Threat Zones Parameters", "value": "threat"},
                            {"label": "Use Emergency Routes-Specific Parameters", "value": "route"},
                        ],
                        value="threat",
                        style={"fontSize": "0.85rem", "marginBottom": "0.25rem"},
                    ),
                ]),
                html.Div(style={"marginBottom": "0.5rem"}),
            ] if is_route_analysis else []),

            # ----------------------------------------------------------------
            # Sensor-only block
            # ----------------------------------------------------------------
            *([
                html.Div([
                    html.I(className="fas fa-satellite-dish", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                    "Sensor Placement Settings",
                ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.5rem"}),
                html.Hr(style={"margin": "0.5rem 0"}),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-cogs", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "Optimization Parameters",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    html.Label("Optimization Strategy",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dcc.Dropdown(
                        id="sensor-strategy",
                        options=[
                            {"label": "Boundary",   "value": "boundary"},
                            {"label": "Coverage",   "value": "coverage"},
                            {"label": "Population", "value": "population"},
                            {"label": "Wind Aware", "value": "wind_aware"},
                            {"label": "Hybrid",     "value": "hybrid"},
                        ],
                        value="boundary",
                        clearable=False,
                        style={"fontSize": "0.85rem", "marginBottom": "0.5rem"},
                    ),
                    html.Label("Number of Sensors",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="sensor-num-sensors", type="number", value=5, min=1, max=50, step=1,
                              style={"fontSize": "0.85rem", "marginBottom": "0.5rem"}),
                    html.Label("Detection Range (m)",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="sensor-detection-range-m", type="number", value=500, min=50, max=5000, step=10,
                              style={"fontSize": "0.85rem", "marginBottom": "0.5rem"}),
                    html.Label("Minimum Sensor Spacing (m)",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="sensor-min-spacing-m", type="number", value=200, min=0, max=2000, step=10,
                              style={"fontSize": "0.85rem", "marginBottom": "0.5rem"}),
                    html.Label("Cost Per Sensor (USD)",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="sensor-cost-per-sensor", type="number", value=10000, min=1, step=100,
                              style={"fontSize": "0.85rem", "marginBottom": "0.5rem"}),
                ]),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-database", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "Population Raster (Optional)",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    dbc.InputGroup([
                        dbc.Input(
                            id="sensor-pop-raster-path",
                            type="text",
                            placeholder="Optional for population strategy (.tif/.tiff)",
                            style={"fontSize": "0.85rem"},
                        ),
                        dbc.Button("Browse", id="sensor-browse-raster-btn", color="secondary", outline=True),
                    ], style={"marginBottom": "0.35rem"}),
                    html.Small(
                        "Used by population/hybrid strategy when available. "
                        "If not provided, optimizer falls back to non-population placement.",
                        style={"color": "#6c757d"},
                    ),
                ]),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-sliders-h", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "Sensor Placement Configuration Mode",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.5rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    dbc.RadioItems(
                        id="sensor-parameter-source-mode",
                        options=[
                            {"label": "Use Chemical Threat Zones Parameters", "value": "threat"},
                            {"label": "Use Sensor Placement-Specific Parameters", "value": "sensor"},
                        ],
                        value="threat",
                        style={"fontSize": "0.85rem", "marginBottom": "0.25rem"},
                    ),
                ]),
                html.Div(style={"marginBottom": "0.5rem"}),
            ] if is_sensor_analysis else []),

            # ----------------------------------------------------------------
            # Shelter-only block
            # ----------------------------------------------------------------
            *([
                html.Div([
                    html.I(className="fas fa-house-user", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                    "Shelter Status Settings",
                ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.5rem"}),
                html.Hr(style={"margin": "0.5rem 0"}),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-building-shield", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "Protective Action Parameters",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    html.Label("Building Type",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dcc.Dropdown(
                        id="shelter-building-type",
                        options=[
                            {"label": "Residential (Tight)",  "value": "residential_tight"},
                            {"label": "Residential (Leaky)", "value": "residential_leaky"},
                            {"label": "Commercial",          "value": "commercial"},
                            {"label": "Industrial",          "value": "industrial"},
                        ],
                        value="industrial",
                        clearable=False,
                        style={"fontSize": "0.85rem", "marginBottom": "0.5rem"},
                    ),
                    html.Label("Sheltering Time (min)",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="shelter-sheltering-time-min", type="number", value=60, min=1, max=240, step=1,
                              style={"fontSize": "0.85rem", "marginBottom": "0.5rem"}),
                    html.Label("Evacuation Time (min)",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="shelter-evacuation-time-min", type="number", value=15, min=1, max=180, step=1,
                              style={"fontSize": "0.85rem", "marginBottom": "0.5rem"}),
                    html.Label("Sample Grid Points",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="shelter-sample-grid-points", type="number", value=15, min=5, max=60, step=1,
                              style={"fontSize": "0.85rem", "marginBottom": "0.25rem"}),
                    html.Small("Higher sample points improve detail but increase compute time.", style={"color": "#6c757d"}),
                ]),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-sliders-h", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "Shelter Status Configuration Mode",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    dbc.RadioItems(
                        id="shelter-parameter-source-mode",
                        options=[
                            {"label": "Use Chemical Threat Zones Parameters", "value": "threat"},
                            {"label": "Use Shelter Status-Specific Parameters", "value": "shelter"},
                        ],
                        value="threat",
                        style={"fontSize": "0.85rem", "marginBottom": "0.25rem"},
                    ),
                ]),
                html.Div(style={"marginBottom": "0.5rem"}),
            ] if is_shelter_analysis else []),

            # ----------------------------------------------------------------
            # Health-impact-only block
            # ----------------------------------------------------------------
            *([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-heartbeat", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "Health Impact Assessment",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    html.Label("Threshold Sets to Display",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Checklist(
                        id="health-threshold-sets",
                        options=[
                            {"label": " Show AEGL (60 min)",       "value": "aegl"},
                            {"label": " Show ERPG (1 hour)",       "value": "erpg"},
                            {"label": " Show PAC",                 "value": "pac"},
                            {"label": " Show IDLH (30 min escape)", "value": "idlh"},
                        ],
                        value=["aegl", "erpg"],
                        style={"fontSize": "0.85rem", "marginBottom": "0.5rem"},
                    ),
                    html.Small("Select which health impact thresholds to compute and visualize.",
                               style={"color": "#6c757d"}),
                ]),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-sliders-h", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "Health Impact Configuration Mode",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    dbc.RadioItems(
                        id="health-parameter-source-mode",
                        options=[
                            {"label": "Use Chemical Threat Zones Parameters", "value": "threat"},
                            {"label": "Use Health Impact-Specific Parameters", "value": "health"},
                        ],
                        value="threat",
                        style={"fontSize": "0.85rem", "marginBottom": "0.25rem"},
                    ),
                ]),
                html.Div(style={"marginBottom": "0.5rem"}),
            ] if is_health_impact_analysis else []),

            # ----------------------------------------------------------------
            # Shared advanced parameters container (all tabs)
            # ----------------------------------------------------------------
            html.Div([

                # Chemical Properties
                html.Div([
                    html.I(className="fas fa-flask", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                    "Chemical Properties",
                ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.5rem"}),
                html.Hr(style={"margin": "0.5rem 0"}),
                html.Label("Chemical",
                           style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                dcc.Dropdown(
                    id="chemical-select",
                    options=[{"label": k, "value": k} for k in CHEMICAL_OPTIONS.keys()],
                    value=DEFAULT_CHEMICAL,
                    style={"fontSize": "0.85rem", "marginBottom": "0.75rem"},
                ),

                # Source Type
                html.Div([
                    html.I(className="fas fa-layer-group", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                    "Source Type",
                ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                html.Hr(style={"margin": "0.5rem 0"}),
                dbc.RadioItems(
                    id="release-type",
                    options=[
                        {"label": "Single Source", "value": "single"},
                        {"label": "Multi-Source",  "value": "multi"},
                    ],
                    value="single",
                    inline=True,
                    style={"marginBottom": "0.5rem", "fontSize": "0.85rem"},
                ),
                html.Div([
                    html.Label("Number of Sources",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(id="num-sources", type="number", value=2, min=2, max=10, step=1,
                              style={"fontSize": "0.85rem", "marginBottom": "0.75rem"}),
                ], id="num-sources-container", style={"display": "none"}),

                # Dynamic source parameters
                html.Div(id="source-parameters-container", children=[
                    html.Div([
                        # Location Settings
                        html.Div([
                            html.I(className="fas fa-map-marker-alt",
                                   style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                            "Location Settings",
                        ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                        html.Hr(style={"margin": "0.5rem 0"}),
                        dbc.RadioItems(
                            id="location-mode",
                            options=[
                                {"label": "Current Location", "value": "current"},
                                {"label": "Manual Location",  "value": "manual"},
                            ],
                            value="manual",
                            inline=True,
                            style={"marginBottom": "0.5rem", "fontSize": "0.85rem"},
                        ),
                        dcc.Geolocation(id="geolocation", high_accuracy=True),
                        html.Div(id="manual-location-inputs", children=[
                            html.Label("Latitude",
                                       style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                            dbc.Input(id="latitude", type="number", value=31.6911, step=0.0001,
                                      style={"marginBottom": "0.5rem", "fontSize": "0.85rem"}),
                            html.Label("Longitude",
                                       style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                            dbc.Input(id="longitude", type="number", value=74.0822, step=0.0001,
                                      style={"marginBottom": "0.75rem", "fontSize": "0.85rem"}),
                        ]),
                        html.Div(id="current-location-display", children=[
                            dbc.Alert([
                                html.I(className="fas fa-crosshairs", style={"marginRight": "0.5rem"}),
                                "Detecting your location...",
                            ], color="info", style={"fontSize": "0.85rem", "marginBottom": "0.75rem"}),
                        ], style={"display": "none"}),

                        # Release Parameters
                        html.Div([
                            html.I(className="fas fa-wind", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                            "Release Parameters",
                        ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                        html.Hr(style={"margin": "0.5rem 0"}),
                        create_slider_with_range_control(
                            "release-rate", "Release Rate (g/s)",
                            10, 2000, 800, 10,
                            {10: "10", 500: "500", 1000: "1000", 1500: "1500", 2000: "2000"},
                        ),
                        create_slider_with_range_control(
                            "tank-height", "Source Height (m)",
                            1, 20, 3.0, 0.5,
                            {1: "1", 5: "5", 10: "10", 15: "15", 20: "20"},
                        ),
                    ]),
                ]),

                # Receptor Height
                create_slider_with_range_control(
                    "receptor-height", "Receptor Height (m)",
                    0.01, 10, 1.5, 0.1,
                    {0.01: "0.01", 2: "2", 4: "4", 6: "6", 8: "8", 10: "10"},
                ),

                # Release Duration
                html.Div([
                    html.I(className="fas fa-clock", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                    "Release Duration",
                ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                html.Hr(style={"margin": "0.5rem 0"}),
                html.Div([
                    html.Label("Duration (minutes)",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dcc.Slider(
                        id="duration", min=1, max=120, step=1, value=30,
                        marks={1: "1", 30: "30", 60: "60", 90: "90", 120: "120"},
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                ], id="duration-container", style={"display": "block"}),
                html.Div([
                    html.Label("Mass Released (kg)",
                               style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d", "marginTop": "0.75rem"}),
                    dbc.Input(id="mass-released", type="number", value=500, min=1, step=1,
                              style={"marginBottom": "0.75rem", "fontSize": "0.85rem"}),
                    html.Div(id="mass-equivalence-note",
                             style={"fontSize": "0.75rem", "color": "#6c757d", "marginBottom": "0.25rem"}),
                ], id="mass-released-container", style={"display": "none"}),

                # Terrain Roughness
                html.Div([
                    html.I(className="fas fa-mountain", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                    "Terrain Roughness",
                ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                html.Hr(style={"margin": "0.5rem 0"}),
                html.Label("Surface Type",
                           style={"fontSize": "0.8rem", "fontWeight": "500", "marginBottom": "0.25rem", "color": "#6c757d"}),
                dcc.Dropdown(
                    id="terrain-roughness",
                    options=[
                        {"label": "Urban", "value": "URBAN"},
                        {"label": "Rural", "value": "RURAL"},
                    ],
                    value="URBAN",
                    clearable=False,
                    style={"fontSize": "0.85rem", "marginBottom": "0.75rem"},
                ),

                # Source Term Mode
                html.Div([
                    html.I(className="fas fa-industry", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                    "Source Term Mode",
                ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                html.Hr(style={"margin": "0.5rem 0"}),
                dbc.RadioItems(
                    id="source-term-mode",
                    options=[
                        {"label": "Continuous",           "value": "continuous"},
                        {"label": "Instantaneous/Puff",   "value": "instantaneous"},
                    ],
                    value="continuous",
                    inline=True,
                    style={"marginBottom": "0.5rem", "fontSize": "0.85rem"},
                ),
                html.Small(
                    "Continuous uses Release Rate + Duration; Instantaneous/Puff uses Mass Released.",
                    style={"color": "#6c757d"},
                ),

                # Weather Conditions
                html.Div([
                    html.I(className="fas fa-cloud-sun", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                    "Weather Conditions",
                ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                html.Hr(style={"margin": "0.5rem 0"}),
                dbc.RadioItems(
                    id="weather-mode",
                    options=[
                        {"label": "Auto (API)", "value": "auto"},
                        {"label": "Manual",     "value": "manual"},
                    ],
                    value="manual",
                    inline=True,
                    style={"marginBottom": "0.75rem", "fontSize": "0.85rem"},
                ),
                html.Div(id="weather-inputs", children=[create_weather_manual_inputs()]),

                # Auto-Refresh
                html.Div([
                    html.Div([
                        html.I(className="fas fa-sync-alt", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                        "Auto-Refresh Settings",
                    ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                    html.Hr(style={"margin": "0.5rem 0"}),
                    dbc.Row([
                        dbc.Col([
                            dbc.Checklist(
                                id="auto-refresh-enabled",
                                options=[{"label": " Enable Auto-Refresh", "value": "enabled"}],
                                value=[],
                                style={"fontSize": "0.85rem", "marginBottom": "0.5rem"},
                            ),
                        ], width=12),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Update Interval (seconds)",
                                       style={"fontSize": "0.8rem", "fontWeight": "500",
                                              "marginBottom": "0.25rem", "color": "#6c757d"}),
                            dbc.Input(
                                id="refresh-interval", type="number", value=60,
                                min=30, max=600, step=10,
                                style={"fontSize": "0.85rem", "marginBottom": "0.5rem"},
                            ),
                        ], width=12),
                    ]),
                    html.Div(id="auto-refresh-status",
                             style={"fontSize": "0.75rem", "color": "#6c757d", "marginTop": "0.25rem"}),
                ], id="auto-refresh-container", style={"display": "none"}),

                # Datetime Settings
                html.Div([
                    html.I(className="fas fa-calendar-alt", style={"marginRight": "0.4rem", "fontSize": "0.85rem"}),
                    "Datetime Settings",
                ], style={"fontSize": "0.85rem", "fontWeight": "600", "color": "#495057", "marginTop": "0.75rem"}),
                html.Hr(style={"margin": "0.5rem 0"}),
                dbc.RadioItems(
                    id="threat-datetime-mode",
                    options=[
                        {"label": "Datetime Now",        "value": "now"},
                        {"label": "Specific Datetime",   "value": "specific"},
                    ],
                    value="now",
                    inline=True,
                    style={"marginBottom": "0.5rem", "fontSize": "0.85rem"},
                ),
                html.Div([
                    html.Label("Select Datetime",
                               style={"fontSize": "0.8rem", "fontWeight": "500",
                                      "marginBottom": "0.25rem", "color": "#6c757d"}),
                    dbc.Input(
                        id="threat-specific-datetime",
                        type="datetime-local",
                        value=None,
                        style={"fontSize": "0.85rem", "marginBottom": "0.25rem"},
                    ),
                    html.Small("Used for stability class calculation in threat zone modeling.",
                               style={"color": "#6c757d"}),
                ], id="threat-datetime-input-container",
                   style={"display": "none", "marginBottom": "0.5rem"}),
                html.Label("Timezone Offset (hrs)",
                           style={"fontSize": "0.8rem", "fontWeight": "500",
                                  "marginBottom": "0.25rem", "color": "#6c757d"}),
                dbc.Input(
                    id="threat-timezone-offset-hrs", type="number",
                    value=5, min=-12, max=14, step=0.5,
                    style={"fontSize": "0.85rem", "marginBottom": "0.25rem"},
                ),
                html.Small(
                    "Applied to stability class for solar insolation calculations for threat zone simulation.",
                    style={"color": "#6c757d"},
                ),

                # Auto-refresh interval component
                dcc.Interval(
                    id="auto-refresh-interval",
                    interval=60 * 1000,
                    n_intervals=0,
                    disabled=True,
                ),

            ], id=advanced_container_id, style=advanced_container_style),

            # Calculate button
            dbc.Button(
                [html.I(className="fas fa-calculator", style={"marginRight": "0.5rem"}),
                 calc_button_label],
                id=calc_button_id,
                color=calc_button_color,
                className="w-100",
                style={
                    "fontSize": "0.9rem", "fontWeight": "600",
                    "padding": "0.6rem", "marginTop": "1.5rem", "marginBottom": "0.75rem",
                    "color": "white" if (is_route_analysis or is_sensor_analysis or is_health_impact_analysis) else None,
                    "backgroundColor": (
                        "#797300" if is_route_analysis else
                        "#0077a3" if is_sensor_analysis else
                        "#8B4513" if is_health_impact_analysis else None
                    ),
                    "borderColor": (
                        "#797300" if is_route_analysis else
                        "#0077a3" if is_sensor_analysis else
                        "#8B4513" if is_health_impact_analysis else None
                    ),
                },
            ),
            html.Div(id=calc_status_id, className="mt-2"),
        ]),
    ], style=SIDEBAR_STYLE)
