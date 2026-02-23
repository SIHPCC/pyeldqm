"""
Chemical Threat Zones tab — content area + chemical properties display.

Exports
-------
create_threat_zones_content()
create_chemical_properties_display(chemical_name)
CHEMICAL_OPTIONS
DEFAULT_CHEMICAL
"""

import sys
import os

from dash import html, dcc
import dash_bootstrap_components as dbc
from ..styles import CONTENT_STYLE

# ---------------------------------------------------------------------------
# Resolve project root so ChemicalDatabase can always be imported
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))
_app1_dir = os.path.dirname(os.path.dirname(_here))   # …/app1
_root = os.path.dirname(_app1_dir)                     # project root
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.chemical_database import ChemicalDatabase  # noqa: E402


# ---------------------------------------------------------------------------
# Chemical options helpers
# ---------------------------------------------------------------------------

def _get_fallback_chemicals() -> dict:
    return {
        "Ammonia (NH3)": {"name": "Ammonia (NH3)", "molecular_weight": 17.03},
        "Chlorine (Cl2)": {"name": "Chlorine (Cl2)", "molecular_weight": 70.90},
        "Hydrogen Sulfide (H2S)": {"name": "Hydrogen Sulfide (H2S)", "molecular_weight": 34.08},
        "Sulfur Dioxide (SO2)": {"name": "Sulfur Dioxide (SO2)", "molecular_weight": 64.07},
    }


def _get_chemicals_from_database() -> dict:
    try:
        db = ChemicalDatabase()
        chemicals = db.get_all_chemicals()
        options = {c.get('name', 'Unknown'): c for c in chemicals}
        if db._conn:
            db._conn.close()
            db._conn = None
        return options if options else _get_fallback_chemicals()
    except Exception as exc:
        print(f"[threat_zones tab] Error loading chemicals: {exc}")
        return _get_fallback_chemicals()


CHEMICAL_OPTIONS = _get_chemicals_from_database()


def _get_default_chemical() -> str:
    for name in CHEMICAL_OPTIONS:
        if name.upper() == "AMMONIA":
            return name
    for name in CHEMICAL_OPTIONS:
        if "AMMONIA" in name.upper():
            return name
    return next(iter(CHEMICAL_OPTIONS), "Ammonia")


DEFAULT_CHEMICAL = _get_default_chemical()


# ---------------------------------------------------------------------------
# Tab content
# ---------------------------------------------------------------------------

def create_threat_zones_content():
    """Create the main content area for the Chemical Threat Zones tab."""
    return dbc.Col([
        dcc.Location(id="app-location", refresh=True),

        # ── Top action bar ──────────────────────────────────────────────────
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-calculator", style={'marginRight': '0.5rem'}),
                             "Calculate Threat Zones"],
                            id="calc-threat-btn-top",
                            color="primary",
                            size="lg",
                            className="w-100",
                            style={'fontSize': '0.95rem', 'fontWeight': '600', 'padding': '0.75rem'},
                        ),
                    ], width=5),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-undo", style={'marginRight': '0.4rem'}),
                             "Reset"],
                            id="reset-app-btn",
                            color="secondary",
                            size="lg",
                            className="w-100",
                            style={'fontSize': '0.95rem', 'fontWeight': '600', 'padding': '0.75rem'},
                        ),
                    ], width=5),
                ], justify="center", className="g-3", style={'alignItems': 'center'}),
                html.Div(id="calc-status-top", className="mt-2"),
            ], style={'padding': '0.75rem'}),
        ], style={'marginBottom': '0.75rem', 'border': '2px solid #1f77b4',
                  'boxShadow': '0 2px 4px rgba(31,119,180,0.2)'}),

        # ── Threat Zone Map ─────────────────────────────────────────────────
        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.I(className="fas fa-map",
                           style={'marginRight': '0.4rem', 'color': '#1f77b4', 'fontSize': '0.9rem'}),
                    "Threat Zone Map",
                    dbc.Button(
                        html.I(className="fas fa-chevron-up", style={'fontSize': '0.8rem'}),
                        id="threat-zone-map-toggle", size="sm", color="secondary",
                        className="float-end",
                        style={'marginLeft': 'auto', 'padding': '0.25rem 0.5rem'},
                    ),
                ], style={'fontSize': '0.9rem', 'fontWeight': '700', 'display': 'flex',
                          'alignItems': 'center', 'width': '100%', 'color': '#1f77b4',
                          'letterSpacing': '0.5px'}),
                style={'backgroundColor': 'transparent', 'borderBottom': '2px solid #1f77b4',
                       'padding': '0.5rem 0.75rem'},
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.Div(id="loading-output", children=[
                        dcc.Loading(
                            id="loading-map",
                            type="default",
                            children=html.Div(
                                id="threat-map-container",
                                children=[
                                    html.Div([
                                        html.I(className="fas fa-info-circle fa-2x",
                                               style={'color': '#6c757d', 'marginBottom': '1rem'}),
                                        html.P("Configure parameters and click 'Calculate Threat Zones' to start"),
                                    ], style={'textAlign': 'center', 'padding': '2rem', 'color': '#6c757d'}),
                                ],
                                style={'height': 'auto'},
                            ),
                        ),
                    ]),
                ], style={'padding': '0.5rem', 'backgroundColor': '#f8f9fa'}),
                id="threat-zone-map-collapse",
                is_open=True,
            ),
        ], style={'marginBottom': '0.75rem', 'border': '1px solid #dee2e6',
                  'boxShadow': '0 1px 2px rgba(0,0,0,0.04)'}),

        # ── Chemical Properties ─────────────────────────────────────────────
        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.I(className="fas fa-flask-vial",
                           style={'marginRight': '0.4rem', 'color': '#2ca02c', 'fontSize': '0.9rem'}),
                    "Chemical Properties",
                    dbc.Button(
                        html.I(className="fas fa-chevron-up", style={'fontSize': '0.8rem'}),
                        id="chem-properties-toggle", size="sm", color="secondary",
                        className="float-end",
                        style={'marginLeft': 'auto', 'padding': '0.25rem 0.5rem'},
                    ),
                ], style={'fontSize': '0.9rem', 'fontWeight': '700', 'display': 'flex',
                          'alignItems': 'center', 'width': '100%', 'color': '#2ca02c',
                          'letterSpacing': '0.5px'}),
                style={'backgroundColor': 'transparent', 'borderBottom': '2px solid #2ca02c',
                       'padding': '0.5rem 0.75rem'},
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.Div(id="chemical-properties-container", children=[
                        html.Div([
                            html.I(className="fas fa-info-circle fa-2x",
                                   style={'color': '#6c757d', 'marginBottom': '1rem'}),
                            html.P("Configure parameters and click 'Calculate Threat Zones' to start"),
                        ], style={'textAlign': 'center', 'padding': '2rem', 'color': '#6c757d'}),
                    ]),
                ], style={'padding': '0.6rem', 'backgroundColor': '#f8f9fa'}),
                id="chem-properties-collapse",
                is_open=True,
            ),
        ], style={'marginBottom': '0.75rem', 'border': '1px solid #dee2e6',
                  'boxShadow': '0 1px 2px rgba(0,0,0,0.04)'}, className="mt-3"),

        # ── Simulation Conditions ───────────────────────────────────────────
        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.I(className="fas fa-sliders-h",
                           style={'marginRight': '0.4rem', 'color': '#9467bd', 'fontSize': '0.9rem'}),
                    "Simulation Conditions",
                    dbc.Button(
                        html.I(className="fas fa-chevron-up", style={'fontSize': '0.8rem'}),
                        id="sim-conditions-toggle", size="sm", color="secondary",
                        className="float-end",
                        style={'marginLeft': 'auto', 'padding': '0.25rem 0.5rem'},
                    ),
                ], style={'fontSize': '0.9rem', 'fontWeight': '700', 'display': 'flex',
                          'alignItems': 'center', 'width': '100%', 'color': '#9467bd',
                          'letterSpacing': '0.5px'}),
                style={'backgroundColor': 'transparent', 'borderBottom': '2px solid #9467bd',
                       'padding': '0.5rem 0.75rem'},
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.Div(id="simulation-conditions-container", children=[
                        html.Div([
                            html.I(className="fas fa-info-circle fa-2x",
                                   style={'color': '#6c757d', 'marginBottom': '1rem'}),
                            html.P("Configure parameters and click 'Calculate Threat Zones' to start"),
                        ], style={'textAlign': 'center', 'padding': '2rem', 'color': '#6c757d'}),
                    ]),
                ], style={'padding': '0.6rem', 'backgroundColor': '#f8f9fa'}),
                id="sim-conditions-collapse",
                is_open=True,
            ),
        ], style={'marginBottom': '0.75rem', 'border': '1px solid #dee2e6',
                  'boxShadow': '0 1px 2px rgba(0,0,0,0.04)'}, className="mt-3"),

        # ── Threat Zone Distances ───────────────────────────────────────────
        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.I(className="fas fa-ruler",
                           style={'marginRight': '0.4rem', 'color': '#d62728', 'fontSize': '0.9rem'}),
                    "Threat Zone Distances",
                    dbc.Button(
                        html.I(className="fas fa-chevron-up", style={'fontSize': '0.8rem'}),
                        id="zone-distances-toggle", size="sm", color="secondary",
                        className="float-end",
                        style={'marginLeft': 'auto', 'padding': '0.25rem 0.5rem'},
                    ),
                ], style={'fontSize': '0.9rem', 'fontWeight': '700', 'display': 'flex',
                          'alignItems': 'center', 'width': '100%', 'color': '#d62728',
                          'letterSpacing': '0.5px'}),
                style={'backgroundColor': 'transparent', 'borderBottom': '2px solid #d62728',
                       'padding': '0.5rem 0.75rem'},
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.Div(id="zone-distances-container", children=[
                        html.Div([
                            html.I(className="fas fa-info-circle fa-2x",
                                   style={'color': '#6c757d', 'marginBottom': '1rem'}),
                            html.P("Configure parameters and click 'Calculate Threat Zones' to start"),
                        ], style={'textAlign': 'center', 'padding': '2rem', 'color': '#6c757d'}),
                    ]),
                ], style={'padding': '0.6rem', 'backgroundColor': '#f8f9fa'}),
                id="zone-distances-collapse",
                is_open=True,
            ),
        ], style={'marginBottom': '0.75rem', 'border': '1px solid #dee2e6',
                  'boxShadow': '0 1px 2px rgba(0,0,0,0.04)'}, className="mt-3"),

        # ── Concentration Analytics ─────────────────────────────────────────
        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.I(className="fas fa-chart-line",
                           style={'marginRight': '0.4rem', 'color': '#ff7f0e', 'fontSize': '0.9rem'}),
                    "Concentration Data Analytics",
                    dbc.Button(
                        html.I(className="fas fa-chevron-down", style={'fontSize': '0.8rem'}),
                        id="analytics-toggle", size="sm", color="secondary",
                        className="float-end",
                        style={'marginLeft': 'auto', 'padding': '0.25rem 0.5rem'},
                    ),
                ], style={'fontSize': '0.9rem', 'fontWeight': '700', 'display': 'flex',
                          'alignItems': 'center', 'width': '100%', 'color': '#ff7f0e',
                          'letterSpacing': '0.5px'}),
                style={'backgroundColor': 'transparent', 'borderBottom': '2px solid #ff7f0e',
                       'padding': '0.5rem 0.75rem'},
            ),
            dbc.Collapse(
                dbc.CardBody([
                    html.Div(id="concentration-plots-container", children=[
                        html.Div([
                            html.I(className="fas fa-info-circle fa-2x",
                                   style={'color': '#6c757d', 'marginBottom': '1rem'}),
                            html.P("Configure parameters and click 'Calculate Threat Zones' to view analytics"),
                        ], style={'textAlign': 'center', 'padding': '2rem', 'color': '#6c757d'}),
                    ]),
                ], style={'padding': '0.6rem', 'backgroundColor': '#f8f9fa'}),
                id="analytics-collapse",
                is_open=True,
            ),
        ], style={'marginBottom': '0.75rem', 'border': '1px solid #dee2e6',
                  'boxShadow': '0 1px 2px rgba(0,0,0,0.04)'}, className="mt-3"),

        # ── Stats + stores ──────────────────────────────────────────────────
        html.Div(id="zone-statistics", className="mt-3"),
        dcc.Store(id='manual-calc-done', data=False),
        dcc.Store(
            id='concentration-data-store',
            data={'X': None, 'Y': None, 'concentration': None,
                  'thresholds': None, 'wind_dir': 0},
        ),

        # ── Hidden placeholders required by PAR-Analysis callbacks ──────────
        html.Div(id="par-map-container",         style={'display': 'none'}),
        html.Div(id="par-aegl3-count",           style={'display': 'none'}),
        html.Div(id="par-aegl2-count",           style={'display': 'none'}),
        html.Div(id="par-aegl1-count",           style={'display': 'none'}),
        html.Div(id="par-details",               style={'display': 'none'}),
        html.Div(id="par-aegl3-area",            style={'display': 'none'}),
        html.Div(id="par-aegl2-area",            style={'display': 'none'}),
        html.Div(id="par-aegl1-area",            style={'display': 'none'}),
        html.Div(id="par-max-distance",          style={'display': 'none'}),
        html.Div(id="par-aegl3-density",         style={'display': 'none'}),
        html.Div(id="par-aegl2-density",         style={'display': 'none'}),
        html.Div(id="par-aegl1-density",         style={'display': 'none'}),
        html.Div(id="par-density-assessment",    style={'display': 'none'}),
        dcc.Input(id="par-population-raster-path",  style={'display': 'none'}, value=""),
        dcc.Input(id="critical-threshold",          style={'display': 'none'}, value=10000),
        dcc.Input(id="high-threshold",              style={'display': 'none'}, value=5000),
        dcc.Input(id="par-parameter-source-mode",   style={'display': 'none'}, value="threat"),
        html.Button(id="reset-par-btn",             style={'display': 'none'}),
        html.Button(id="btn-download-par-script",   style={'display': 'none'}),
    ], width=9, style=CONTENT_STYLE)


# ---------------------------------------------------------------------------
# Chemical properties display helper
# ---------------------------------------------------------------------------

def create_chemical_properties_display(chemical_name: str) -> html.Div:
    """Build a professionally formatted chemical properties panel."""
    try:
        db = ChemicalDatabase()
        chemical = db.get_chemical_by_name(chemical_name)
        if db._conn:
            db._conn.close()
            db._conn = None

        if not chemical:
            return html.Div([
                dbc.Alert(f"Chemical '{chemical_name}' not found in database", color="warning"),
            ])

        property_groups = {
            'Basic Information': [
                ('name', 'Chemical Name'),
                ('cas_number', 'CAS Number'),
                ('molecular_weight', 'Molecular Weight (g/mol)'),
            ],
            'Toxicity Thresholds (ppm)': [
                ('idlh', 'IDLH (Immediately Dangerous to Life or Health)'),
                ('aegl1_60min', 'AEGL-1 (60 min)'),
                ('aegl2_60min', 'AEGL-2 (60 min)'),
                ('aegl3_60min', 'AEGL-3 (60 min)'),
            ],
            'Emergency Response Guidelines': [
                ('erpg1', 'ERPG-1'),
                ('erpg2', 'ERPG-2'),
                ('erpg3', 'ERPG-3'),
                ('pac1', 'PAC-1'),
                ('pac2', 'PAC-2'),
                ('pac3', 'PAC-3'),
            ],
            'Explosive Characteristics': [
                ('lel', 'LEL (Lower Explosive Limit)'),
                ('uel', 'UEL (Upper Explosive Limit)'),
            ],
            'Physical Properties': [
                ('ambient_boiling_point_f', 'Ambient Boiling Point (°F)'),
                ('freezing_point_f', 'Freezing Point (°F)'),
            ],
        }

        colors = {
            'Basic Information': '#2c3e50',
            'Toxicity Thresholds (ppm)': '#c0392b',
            'Emergency Response Guidelines': '#d68910',
            'Explosive Characteristics': '#f39c12',
            'Physical Properties': '#1f77b4',
        }

        sections = []
        for section_title, properties in property_groups.items():
            section_props = []
            for prop_key, display_key in properties:
                value = chemical.get(prop_key)
                if value is not None:
                    display_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                    section_props.append({'label': display_key, 'value': display_value})

            if not section_props:
                continue

            col_size = (len(section_props) + 3) // 4
            cols = []
            for col_idx in range(4):
                col_props = section_props[col_idx * col_size:(col_idx + 1) * col_size]
                if col_props:
                    col_content = [
                        html.Div([
                            html.Div(p['label'], style={
                                'fontSize': '0.75rem', 'fontWeight': '500', 'color': '#34495e',
                                'marginBottom': '0.08rem', 'letterSpacing': '0.3px',
                            }),
                            html.Div(p['value'], style={
                                'fontSize': '0.85rem', 'fontWeight': '600', 'color': '#2c3e50',
                                'marginBottom': '0.5rem', 'paddingBottom': '0.3rem',
                                'borderBottom': '1px solid #ecf0f1',
                            }),
                        ], style={'marginBottom': '0.3rem'})
                        for p in col_props
                    ]
                    cols.append(dbc.Col(col_content, width=3, style={'paddingRight': '0.5rem'}))

            color = colors[section_title]
            sections.append(dbc.Card([
                dbc.CardHeader(
                    html.Div([
                        html.I(className="fas fa-layer-group",
                               style={'marginRight': '0.4rem', 'color': color, 'fontSize': '0.85rem'}),
                        section_title,
                    ], style={'fontSize': '0.9rem', 'fontWeight': '700', 'color': color,
                               'letterSpacing': '0.5px'}),
                    style={'backgroundColor': 'transparent', 'borderBottom': f'2px solid {color}',
                           'padding': '0.5rem 0.75rem'},
                ),
                dbc.CardBody([
                    dbc.Row(cols, style={'margin': '0px', 'rowGap': '0px'}),
                ], style={'padding': '0.6rem', 'backgroundColor': '#f8f9fa'}),
            ], style={'marginBottom': '0.75rem', 'border': '1px solid #dee2e6',
                      'boxShadow': '0 1px 2px rgba(0,0,0,0.04)'}))

        if not sections:
            return html.Div([dbc.Alert(f"No properties available for '{chemical_name}'", color="info")])

        return html.Div(sections, style={'backgroundColor': '#ffffff', 'borderRadius': '4px', 'padding': '0px'})

    except Exception as exc:
        return html.Div([dbc.Alert(f"Error loading chemical properties: {exc}", color="danger")])
