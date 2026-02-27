"""
layout/main_layout.py
=====================
Root Dash layout wired to all tab content components.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from ..components.header import create_header
from ..components.styles import SIDEBAR_STYLE
from ..components.tabs.threat_zones import create_threat_zones_content
from ..components.tabs.par_analysis import create_par_content
from ..components.tabs.route_optimization import create_route_optimization_content
from ..components.tabs.sensor_placement import create_sensor_placement_content
from ..components.tabs.shelter_analysis import create_shelter_analysis_content
from ..components.tabs.health_impact import create_health_impact_content
from .sidebar import create_threat_zones_sidebar


def create_layout():
    """Return the root ``dbc.Container`` that becomes ``app.layout``."""
    return dbc.Container([
        # ── Header ──────────────────────────────────────────────────────────
        create_header(),

        # ── Tab navigation ──────────────────────────────────────────────────
        html.Div(
            dbc.Tabs([
                dbc.Tab(label="🗺️ Chemical Threat Zones",      tab_id="tab-threat-zones"),
                dbc.Tab(label="👥 Population At Risk",       tab_id="tab-par-analysis"),
                dbc.Tab(label="🚗 Emergency Routes",   tab_id="tab-route-optimization"),
                dbc.Tab(label="📡 Sensor Placement",   tab_id="tab-sensor-placement"),
                dbc.Tab(label="💊 Health Impact",      tab_id="tab-health-impact"),
                dbc.Tab(label="🏠 Shelter Status",     tab_id="tab-shelter-analysis"),
                dbc.Tab(label="ℹ️ About",               tab_id="tab-about"),
            ],
                id="main-tabs",
                active_tab="tab-threat-zones",
                className="mb-0 flex-nowrap",
                style={
                    "position": "relative",
                    "zIndex": 1100,
                    "backgroundColor": "#E6E6E6",
                    "fontFamily": SIDEBAR_STYLE.get("fontFamily"),
                    "fontWeight": "700",
                    "flexWrap": "nowrap",
                    "minWidth": "max-content",
                },
            ),
            className="mb-3",
            style={
                "overflowX": "auto",
                "overflowY": "hidden",
                "backgroundColor": "#E6E6E6",
                "WebkitOverflowScrolling": "touch",
            },
        ),

        # ── Cross-tab shared state ───────────────────────────────────────────
        dcc.Store(id="threat-params-store", data=None),
        dcc.Store(id="generated-script-store", data=None),
        dcc.Download(id="script-download"),
        dcc.Store(id="par-generated-script-store", data=None),
        dcc.Download(id="par-script-download"),
        dcc.Store(id="route-generated-script-store", data=None),
        dcc.Download(id="route-script-download"),
        dcc.Store(id="sensor-generated-script-store", data=None),
        dcc.Download(id="sensor-script-download"),
        dcc.Store(id="health-generated-script-store", data=None),
        dcc.Download(id="health-script-download"),
        dcc.Store(id="shelter-generated-script-store", data=None),
        dcc.Download(id="shelter-script-download"),

        # ── Tab content (rendered by routing callback) ───────────────────────
        html.Div(id="tab-content", style={"position": "relative", "zIndex": 1}),

    ], fluid=True, style={"maxWidth": "100%", "padding": 0})
