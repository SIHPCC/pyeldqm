"""
Header component for Dash GUI
"""

from dash import html
import dash_bootstrap_components as dbc
from .styles import HEADER_STYLE

LOGO_SIZE = '100px'
LOGO_ZOOM = 2.75


def create_header():
    """Create the header section."""
    return html.Div([
        html.Div([
            # ── Logo ─────────────────────────────────────────────────────────
            html.Div([
                html.Img(
                    src='/assets/pyELDQM_logo_v0.1.png',
                    alt='pyELDQM logo',
                    style={
                        'width': LOGO_SIZE,
                        'height': LOGO_SIZE,
                        'objectFit': 'contain',
                        'transform': f'scale({LOGO_ZOOM})',
                        'transformOrigin': 'center',
                        'marginRight': '1.5rem',
                        'display': 'block'
                    }
                ),
            ], style={'display': 'flex', 'alignItems': 'center'}),

            # ── Title block ──────────────────────────────────────────────────
            html.Div([
                html.Div(
                    'pyELDQM',
                    style={
                        'fontSize': '2rem',
                        'fontWeight': '800',
                        'letterSpacing': '0.9px',
                        'lineHeight': '1.1'
                    }
                ),
                html.Div(
                    'EMERGENCY LEAKAGE & DISPERSION QUANTIFICATION MODELLING TOOLKIT',
                    style={
                        'fontSize': '1.5rem',
                        'fontWeight': '600',
                        'opacity': 0.95,
                        'letterSpacing': '0.45px',
                        'marginTop': '0.28rem'
                    }
                ),
                html.Div(
                    'Toxic Release Analysis | Consequence Forecasting | Response Support',
                    style={
                        'fontSize': '1rem',
                        'fontWeight': '400',
                        'opacity': 0.86,
                        'letterSpacing': '0.3px',
                        'marginTop': '0.36rem'
                    }
                ),
                html.Div([
                    dbc.Badge('v 0.1.1',     color='light',   text_color='dark', className='me-2'),
                    dbc.Badge('MIT License', color='success',                    className='me-2'),
                    dbc.Badge('Python ≥ 3.10', color='info',  text_color='dark', className='me-2'),
                    dbc.Badge('Open Source', color='warning',  text_color='dark'),
                ], style={'marginTop': '0.55rem'}),
            ], style={'display': 'flex', 'flexDirection': 'column', 'textAlign': 'left',
                      'flex': '1'}),

            # ── GitHub button ────────────────────────────────────────────────
            html.Div([
                dbc.Button([
                    html.I(className='fab fa-github', style={'marginRight': '0.5rem'}),
                    'View on GitHub',
                ],
                href='https://github.com/SIHPCC/pyeldqm',
                target='_blank',
                color='light',
                outline=True,
                size='sm',
                style={
                    'fontWeight': '600',
                    'borderRadius': '8px',
                    'fontSize': '0.85rem',
                    'whiteSpace': 'nowrap',
                    'color': 'white',
                    'borderColor': 'rgba(255,255,255,0.6)',
                }),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginLeft': 'auto',
                      'flexShrink': '0'}),

        ], style={
            'margin': 0,
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'space-between',
            'columnGap': '0.6rem',
            'flexWrap': 'wrap',
            'width': '100%',
        })
    ], style={
        **HEADER_STYLE,
        'background': 'linear-gradient(135deg, #1a2a3a 0%, #1f3a5f 60%, #1f77b4 100%)',
        'boxShadow': '0 4px 18px rgba(31,119,180,0.3)',
    })
