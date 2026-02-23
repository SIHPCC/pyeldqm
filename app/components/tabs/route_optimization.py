"""Emergency Route Optimization tab — content area only."""

from dash import html, dcc
import dash_bootstrap_components as dbc
from ..styles import CARD_STYLE, CONTENT_STYLE


def create_route_optimization_content():
    """Create Emergency Route Optimization tab content."""
    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-route", style={'marginRight': '0.5rem'}),
                             "Calculate Emergency Routes"],
                            id="calc-route-btn-top",
                            color="warning",
                            size="lg",
                            className="w-100",
                            style={'fontSize': '0.95rem', 'fontWeight': '600', 'padding': '0.75rem',
                                   'backgroundColor': "#797300", 'borderColor': "#797300", 'color': 'white'},
                        ),
                    ], width=5),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-undo", style={'marginRight': '0.4rem'}),
                             "Reset"],
                            id="reset-route-btn",
                            color="secondary",
                            size="lg",
                            className="w-100",
                            style={'fontSize': '0.95rem', 'fontWeight': '600', 'padding': '0.75rem'},
                        ),
                    ], width=5),
                ], justify="center", className="g-3", style={'alignItems': 'center'}),
                html.Div(id="route-status-top", className="mt-2"),
            ], style={'padding': '0.75rem'}),
        ], style={'marginBottom': '0.75rem', 'border': '2px solid #f0ad4e',
                  'boxShadow': '0 2px 4px rgba(240,173,78,0.2)'}),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.I(className="fas fa-map",
                           style={'marginRight': '0.4rem', 'color': '#1f77b4', 'fontSize': '0.9rem'}),
                    "Route Optimization Map",
                    dbc.Button(
                        html.I(className="fas fa-chevron-up", style={'fontSize': '0.8rem'}),
                        id="route-map-toggle", size="sm", color="secondary",
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
                        id="loading-route-map",
                        type="default",
                        children=html.Div(id="route-map-container", children=[
                            html.Div([
                                html.I(className="fas fa-info-circle fa-3x",
                                       style={'color': '#17a2b8', 'marginBottom': '1rem'}),
                                html.H5("Configure parameters and click 'Calculate Emergency Routes' to start"),
                            ], style={'textAlign': 'center', 'padding': '3rem', 'color': '#666'}),
                        ]),
                    ),
                ], style={'padding': '0.5rem', 'backgroundColor': '#f8f9fa'}),
                id="route-map-collapse",
                is_open=True,
            ),
        ], style=CARD_STYLE),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Best Shelter", className="text-muted"),
                        html.H4(id="route-best-shelter", children="---", style={'color': '#28a745'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#d4edda', 'border': '2px solid #28a745'}),
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Route Distance", className="text-muted"),
                        html.H4(id="route-distance", children="---", style={'color': '#1f77b4'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#d1ecf1', 'border': '2px solid #17a2b8'}),
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Risk-Weighted Cost", className="text-muted"),
                        html.H4(id="route-cost", children="---", style={'color': '#fd7e14'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#fff3cd', 'border': '2px solid #ffc107'}),
            ], width=4),
        ], className="mt-3"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Safe Segments", className="text-muted"),
                        html.H4(id="route-safe-segments", children="---", style={'color': '#28a745'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#eafaf1', 'border': '1px solid #b7e4c7'}),
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Unsafe Segments", className="text-muted"),
                        html.H4(id="route-unsafe-segments", children="---", style={'color': '#dc3545'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#fdeaea', 'border': '1px solid #f5c2c7'}),
            ], width=6),
        ], className="mt-3"),

        dbc.Card([
            dbc.CardHeader("Shelter Ranking", style={'fontWeight': '600'}),
            dbc.CardBody([html.Div(id="route-ranking", children="---")]),
        ], style={**CARD_STYLE, 'marginTop': '0.75rem'}),

        html.Div(id="route-details", className="mt-2"),
    ], width=9, style=CONTENT_STYLE)
