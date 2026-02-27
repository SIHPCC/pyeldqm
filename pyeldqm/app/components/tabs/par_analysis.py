"""
Population At Risk (PAR) Analysis tab — content area only.

NOTE: The sidebar for this tab is rendered by
``layout.sidebar.create_threat_zones_sidebar(is_par_analysis=True)``
just as in the original app.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from ..styles import CONTENT_STYLE, CARD_STYLE


def create_par_content():
    """Create the main content area for the PAR Analysis tab."""
    return dbc.Col([
        # ── Top action bar ─────────────────────────────────────────────────
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-calculator", style={'marginRight': '0.5rem'}),
                             "Calculate PAR"],
                            id="calc-threat-btn-top",
                            color="success",
                            size="lg",
                            className="w-100",
                            style={'fontSize': '0.95rem', 'fontWeight': '600', 'padding': '0.75rem'},
                        ),
                    ], width=5),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-undo", style={'marginRight': '0.4rem'}),
                             "Reset"],
                            id="reset-par-btn",
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

        # ── PAR Map ────────────────────────────────────────────────────────
        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.I(className="fas fa-map",
                           style={'marginRight': '0.4rem', 'color': '#1f77b4', 'fontSize': '0.9rem'}),
                    "Population Risk Map",
                    dbc.Button(
                        html.I(className="fas fa-chevron-up", style={'fontSize': '0.8rem'}),
                        id="par-map-toggle", size="sm", color="secondary",
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
                    dcc.Loading(
                        id="loading-par-map",
                        type="default",
                        children=html.Div(id="par-map-container", children=[
                            html.Div([
                                html.I(className="fas fa-info-circle fa-3x",
                                       style={'color': '#28a745', 'marginBottom': '1rem'}),
                                html.H5("Population Raster Required", style={'marginBottom': '0.75rem'}),
                                html.P("Please select a population raster GeoTIFF file (.tif/.tiff) to calculate PAR.",
                                       style={'marginBottom': '0.35rem'}),
                                html.Small("Use the Browse button in the Population Data section to select a raster file.",
                                           style={'color': '#666'}),
                            ], style={'textAlign': 'center', 'padding': '3rem', 'color': '#666'}),
                        ]),
                    ),
                ], style={'padding': '0.5rem', 'backgroundColor': '#f8f9fa'}),
                id="par-map-collapse",
                is_open=True,
            ),
        ], style=CARD_STYLE),

        # ── AEGL count cards ────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5([html.I(className="fas fa-users", style={'marginRight': '0.5rem'}),
                                 "AEGL-3"], style={'color': '#dc3545'}),
                        html.H2(id="par-aegl3-count", children="---",
                                style={'color': '#dc3545', 'fontSize': '2.5rem'}),
                        html.P("People", className="text-muted"),
                        dbc.Badge("High Risk", color="danger", className="mt-2"),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#f8d7da', 'border': '2px solid #dc3545'}),
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5([html.I(className="fas fa-users", style={'marginRight': '0.5rem'}),
                                 "AEGL-2"], style={'color': '#fd7e14'}),
                        html.H2(id="par-aegl2-count", children="---",
                                style={'color': '#fd7e14', 'fontSize': '2.5rem'}),
                        html.P("People", className="text-muted"),
                        dbc.Badge("Moderate Risk", color="warning", className="mt-2"),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#fff3cd', 'border': '2px solid #ffc107'}),
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5([html.I(className="fas fa-users", style={'marginRight': '0.5rem'}),
                                 "AEGL-1"], style={'color': '#28a745'}),
                        html.H2(id="par-aegl1-count", children="---",
                                style={'color': '#28a745', 'fontSize': '2.5rem'}),
                        html.P("People", className="text-muted"),
                        dbc.Badge("Low Risk", color="success", className="mt-2"),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#d4edda', 'border': '2px solid #28a745'}),
            ], width=4),
        ], className="mt-3 mb-4"),

        # ── Geographic / Spatial Data ────────────────────────────────────────
        html.H5("Geographic & Spatial Data", className="mt-4 mb-3",
                style={'fontWeight': '600', 'color': '#495057'}),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Div([
                            html.I(className="fas fa-map",
                                   style={'marginRight': '0.4rem', 'color': '#17a2b8', 'fontSize': '0.9rem'}),
                            "Zone Extent (Area)",
                        ], style={'fontSize': '0.9rem', 'fontWeight': '700', 'display': 'flex',
                                  'alignItems': 'center', 'width': '100%', 'color': '#17a2b8',
                                  'letterSpacing': '0.5px'}),
                        style={'backgroundColor': 'transparent', 'borderBottom': '2px solid #17a2b8',
                               'padding': '0.5rem 0.75rem'},
                    ),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H6("AEGL-3", className="text-danger"),
                                html.H4(id="par-aegl3-area", children="---",
                                        style={'color': '#dc3545', 'fontSize': '1.5rem'}),
                            ], width=4, style={'textAlign': 'center', 'borderRight': '1px solid #dee2e6'}),
                            dbc.Col([
                                html.H6("AEGL-2", className="text-warning"),
                                html.H4(id="par-aegl2-area", children="---",
                                        style={'color': '#fd7e14', 'fontSize': '1.5rem'}),
                            ], width=4, style={'textAlign': 'center', 'borderRight': '1px solid #dee2e6'}),
                            dbc.Col([
                                html.H6("AEGL-1", className="text-success"),
                                html.H4(id="par-aegl1-area", children="---",
                                        style={'color': '#28a745', 'fontSize': '1.5rem'}),
                            ], width=4, style={'textAlign': 'center'}),
                        ]),
                        html.Hr(style={'margin': '0.75rem 0'}),
                        html.Small("Area in km²", className="text-muted d-block",
                                   style={'textAlign': 'center'}),
                    ], className="d-flex flex-column justify-content-center",
                       style={'minHeight': '200px'}),
                ], style={**CARD_STYLE, 'height': '100%'}),
            ], width=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Div([
                            html.I(className="fas fa-ruler-combined",
                                   style={'marginRight': '0.4rem', 'color': '#6c757d', 'fontSize': '0.9rem'}),
                            "Maximum Distance",
                        ], style={'fontSize': '0.9rem', 'fontWeight': '700', 'display': 'flex',
                                  'alignItems': 'center', 'width': '100%', 'color': '#6c757d',
                                  'letterSpacing': '0.5px'}),
                        style={'backgroundColor': 'transparent', 'borderBottom': '2px solid #6c757d',
                               'padding': '0.5rem 0.75rem'},
                    ),
                    dbc.CardBody([
                        html.P("Furthest affected area from source:", className="text-muted mb-2"),
                        html.H3(id="par-max-distance", children="---", style={'color': '#495057'}),
                        html.Small(id="par-max-distance-unit", children="km", className="text-muted"),
                    ], className="d-flex flex-column justify-content-center",
                       style={'textAlign': 'center', 'minHeight': '200px'}),
                ], style={**CARD_STYLE, 'height': '100%'}),
            ], width=6),
        ], className="mt-3 mb-3"),

        # ── Population density stats ─────────────────────────────────────────
        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.I(className="fas fa-chart-bar",
                           style={'marginRight': '0.4rem', 'color': '#6f42c1', 'fontSize': '0.9rem'}),
                    "Population Density Statistics",
                ], style={'fontSize': '0.9rem', 'fontWeight': '700', 'display': 'flex',
                          'alignItems': 'center', 'width': '100%', 'color': '#6f42c1',
                          'letterSpacing': '0.5px'}),
                style={'backgroundColor': 'transparent', 'borderBottom': '2px solid #6f42c1',
                       'padding': '0.5rem 0.75rem'},
            ),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("AEGL-3 Density", className="text-muted"),
                        html.H5(id="par-aegl3-density", children="---"),
                        html.Small("people/km²", className="text-muted"),
                    ], width=4, style={'textAlign': 'center', 'borderRight': '1px solid #dee2e6',
                                       'paddingRight': '1rem'}),
                    dbc.Col([
                        html.H6("AEGL-2 Density", className="text-muted"),
                        html.H5(id="par-aegl2-density", children="---"),
                        html.Small("people/km²", className="text-muted"),
                    ], width=4, style={'textAlign': 'center', 'borderRight': '1px solid #dee2e6',
                                       'paddingRight': '1rem', 'paddingLeft': '1rem'}),
                    dbc.Col([
                        html.H6("AEGL-1 Density", className="text-muted"),
                        html.H5(id="par-aegl1-density", children="---"),
                        html.Small("people/km²", className="text-muted"),
                    ], width=4, style={'textAlign': 'center', 'paddingLeft': '1rem'}),
                ]),
                html.Hr(style={'margin': '1rem 0'}),
                html.Div(id="par-density-assessment", className="text-muted",
                         style={'fontSize': '0.9rem'}),
            ]),
        ], style=CARD_STYLE, className="mt-3 mb-4"),

        html.Div(id="par-details", className="mt-3"),

        # ── Hidden placeholders required by shared Threat-Zones callbacks ───
        html.Div(id="threat-map-container", style={'display': 'none'}),
        html.Div(id="zone-statistics", style={'display': 'none'}),
        html.Div(id="chemical-properties-container", style={'display': 'none'}),
        html.Div(id="simulation-conditions-container", style={'display': 'none'}),
        html.Div(id="zone-distances-container", style={'display': 'none'}),
        dcc.Store(id='manual-calc-done', data=False),
        dcc.Store(
            id='concentration-data-store',
            data={'X': None, 'Y': None, 'concentration': None,
                  'thresholds': None, 'wind_dir': 0},
        ),
    ], width=9, style=CONTENT_STYLE)
