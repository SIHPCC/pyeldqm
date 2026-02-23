"""
Header component for Dash GUI
"""

from dash import html
from .styles import HEADER_STYLE

LOGO_SIZE = '100px'
LOGO_ZOOM = 2.75


def create_header():
    """Create the header section."""
    return html.Div([
        html.Div([
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
                html.I(
                    className='fas fa-radiation',
                    style={
                        'display': 'none',
                        'marginRight': '1rem',
                        'fontSize': '2rem',
                        'opacity': 0.85
                    }
                )
            ], style={'display': 'flex', 'alignItems': 'center'}),
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
                )
            ], style={'display': 'flex', 'flexDirection': 'column', 'textAlign': 'left'})
        ], style={
            'margin': 0,
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'left',
            'columnGap': '0.6rem',
            'flexWrap': 'wrap'
        })
    ], style=HEADER_STYLE)
