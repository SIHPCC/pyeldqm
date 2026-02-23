"""Sensor Placement Optimization tab — content area only."""

from dash import html, dcc
import dash_bootstrap_components as dbc
from ..styles import CARD_STYLE, CONTENT_STYLE


def create_sensor_placement_content():
    """Create Sensor Placement tab content."""
    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-satellite-dish", style={'marginRight': '0.5rem'}),
                             "Optimize Sensor Placement"],
                            id="calc-sensor-btn-top",
                            color="info",
                            size="lg",
                            className="w-100",
                            style={'fontSize': '0.95rem', 'fontWeight': '600', 'padding': '0.75rem',
                                   'backgroundColor': '#0077a3', 'borderColor': '#005f80', 'color': 'white'},
                        ),
                    ], width=5),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-undo", style={'marginRight': '0.4rem'}),
                             "Reset"],
                            id="reset-sensor-btn",
                            color="secondary",
                            size="lg",
                            className="w-100",
                            style={'fontSize': '0.95rem', 'fontWeight': '600', 'padding': '0.75rem'},
                        ),
                    ], width=5),
                ], justify="center", className="g-3", style={'alignItems': 'center'}),
                html.Div(id="sensor-status-top", className="mt-2"),
            ], style={'padding': '0.75rem'}),
        ], style={'marginBottom': '0.75rem', 'border': '2px solid #17a2b8',
                  'boxShadow': '0 2px 4px rgba(23,162,184,0.2)'}),

        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.I(className="fas fa-map",
                           style={'marginRight': '0.4rem', 'color': '#1f77b4', 'fontSize': '0.9rem'}),
                    "Sensor Placement Map",
                    dbc.Button(
                        html.I(className="fas fa-chevron-up", style={'fontSize': '0.8rem'}),
                        id="sensor-map-toggle", size="sm", color="secondary",
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
                        id="loading-sensor-map",
                        type="default",
                        children=html.Div(id="sensor-map-container", children=[
                            html.Div([
                                html.I(className="fas fa-info-circle fa-3x",
                                       style={'color': '#17a2b8', 'marginBottom': '1rem'}),
                                html.H5("Configure parameters and click 'Optimize Sensor Placement' to start"),
                            ], style={'textAlign': 'center', 'padding': '3rem', 'color': '#666'}),
                        ]),
                    ),
                ], style={'padding': '0.5rem', 'backgroundColor': '#f8f9fa'}),
                id="sensor-map-collapse",
                is_open=True,
            ),
        ], style=CARD_STYLE),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Sensors Deployed", className="text-muted"),
                        html.H4(id="sensor-deployed-count", children="---", style={'color': '#17a2b8'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#d1ecf1', 'border': '2px solid #17a2b8'}),
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Coverage Area", className="text-muted"),
                        html.H4(id="sensor-coverage-area", children="---", style={'color': '#28a745'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#d4edda', 'border': '2px solid #28a745'}),
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Estimated Cost", className="text-muted"),
                        html.H4(id="sensor-estimated-cost", children="---", style={'color': '#fd7e14'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#fff3cd', 'border': '2px solid #ffc107'}),
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Active Strategy", className="text-muted"),
                        html.H4(id="sensor-active-strategy", children="---", style={'color': '#6f42c1'}),
                    ], style={'textAlign': 'center'}),
                ], style={'background': '#e2d9f3', 'border': '2px solid #6f42c1'}),
            ], width=3),
        ], className="mt-3"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Priority Distribution", style={'fontWeight': '600'}),
                    dbc.CardBody([html.Div(id="sensor-priority-breakdown", children="---")]),
                ], style={'height': '100%'}),
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Network Summary", style={'fontWeight': '600'}),
                    dbc.CardBody([html.Div(id="sensor-network-summary", children="---")]),
                ], style={'height': '100%'}),
            ], width=6),
        ], className="mt-3"),

        html.Div(id="sensor-details", className="mt-3"),
    ], width=9, style=CONTENT_STYLE)
