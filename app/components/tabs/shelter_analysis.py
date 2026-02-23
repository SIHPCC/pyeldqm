"""Shelter-In-Place Analysis tab — content area only."""

from dash import html, dcc
import dash_bootstrap_components as dbc
from ..styles import CARD_STYLE, CONTENT_STYLE


def create_shelter_analysis_content():
    """Create Shelter-In-Place Analysis tab content."""
    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-house-user", style={'marginRight': '0.5rem'}),
                             "Calculate Shelter Status"],
                            id="calc-shelter-btn-top",
                            color="danger",
                            size="lg",
                            className="w-100",
                            style={'fontSize': '0.95rem', 'fontWeight': '600', 'padding': '0.75rem'},
                        ),
                    ], width=5),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-undo", style={'marginRight': '0.4rem'}),
                             "Reset"],
                            id="reset-shelter-btn",
                            color="secondary",
                            size="lg",
                            className="w-100",
                            style={'fontSize': '0.95rem', 'fontWeight': '600', 'padding': '0.75rem'},
                        ),
                    ], width=5),
                ], justify="center", className="g-3", style={'alignItems': 'center'}),
                html.Div(id="shelter-status-top", className="mt-2"),
            ], style={'padding': '0.75rem'}),
        ], style={'marginBottom': '0.75rem', 'border': '2px solid #6c757d',
                  'boxShadow': '0 2px 4px rgba(108,117,125,0.2)'}),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.I(className="fas fa-map",
                           style={'marginRight': '0.4rem', 'color': '#1f77b4', 'fontSize': '0.9rem'}),
                    "Shelter Status Map",
                    dbc.Button(
                        html.I(className="fas fa-chevron-up", style={'fontSize': '0.8rem'}),
                        id="shelter-map-toggle", size="sm", color="secondary",
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
                        id="loading-shelter-map",
                        type="default",
                        children=html.Div(id="shelter-map-container", children=[
                            html.Div([
                                html.I(className="fas fa-info-circle fa-3x",
                                       style={'color': '#6c757d', 'marginBottom': '1rem'}),
                                html.H5("Configure parameters and click 'Calculate Shelter Status' to start"),
                            ], style={'textAlign': 'center', 'padding': '3rem', 'color': '#666'}),
                        ]),
                    ),
                ], style={'padding': '0.5rem', 'backgroundColor': '#f8f9fa'}),
                id="shelter-map-collapse",
                is_open=True,
            ),
        ], style=CARD_STYLE),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Primary Recommendation", className="text-muted"),
                        html.H4(id="shelter-primary-recommendation", children="---", style={'color': '#6c757d'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#e9ecef', 'border': '2px solid #6c757d'}),
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Shelter Zones", className="text-muted"),
                        html.H4(id="shelter-shelter-zones-count", children="---", style={'color': '#28a745'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#d4edda', 'border': '2px solid #28a745'}),
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Evacuate Zones", className="text-muted"),
                        html.H4(id="shelter-evacuate-zones-count", children="---", style={'color': '#dc3545'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#f8d7da', 'border': '2px solid #dc3545'}),
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Sample Points", className="text-muted"),
                        html.H4(id="shelter-sampled-points", children="---", style={'color': '#17a2b8'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#d1ecf1', 'border': '2px solid #17a2b8'}),
            ], width=3),
        ], className="mt-3"),

        dbc.Card([
            dbc.CardHeader("Zone Breakdown", style={'fontWeight': '600'}),
            dbc.CardBody([html.Div(id="shelter-zone-breakdown", children="---")]),
        ], style={**CARD_STYLE, 'marginTop': '0.75rem'}),

        html.Div(id="shelter-details", className="mt-3"),

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
