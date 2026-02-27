"""
Reusable slider control with +/- range buttons.
Extracted from weather_inputs so it can be imported independently.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_slider_with_range_control(
    slider_id: str,
    label: str,
    default_min: float,
    default_max: float,
    default_value: float,
    default_step: float,
    default_marks: dict,
    unit: str = "",
) -> html.Div:
    """Create a slider with range increase/decrease buttons.

    Parameters
    ----------
    slider_id:
        Base ID used for the slider, the +/- buttons
        (``{slider_id}-increase`` / ``{slider_id}-decrease``), and the
        companion ``dcc.Store`` (``{slider_id}-range``).
    label:
        Human-readable label shown above the slider.
    default_min / default_max / default_value / default_step / default_marks:
        Standard ``dcc.Slider`` kwargs.
    unit:
        Optional unit string appended to the label (currently unused in
        layout but kept for future tooltips).
    """
    return html.Div([
        html.Div([
            html.Label(
                label,
                style={
                    'fontSize': '0.8rem', 'fontWeight': '500',
                    'marginBottom': '0.25rem', 'color': '#6c757d', 'flex': '1',
                },
            ),
            html.Div([
                dbc.Button(
                    "−",
                    id=f"{slider_id}-decrease",
                    size="sm",
                    color="light",
                    style={
                        'fontSize': '0.7rem', 'padding': '0.1rem 0.4rem',
                        'marginRight': '0.2rem', 'border': '1px solid #dee2e6',
                    },
                ),
                dbc.Button(
                    "+",
                    id=f"{slider_id}-increase",
                    size="sm",
                    color="light",
                    style={
                        'fontSize': '0.7rem', 'padding': '0.1rem 0.4rem',
                        'border': '1px solid #dee2e6',
                    },
                ),
            ], style={'display': 'flex'}),
        ], style={
            'display': 'flex', 'alignItems': 'center',
            'justifyContent': 'space-between',
        }),
        dcc.Slider(
            id=slider_id,
            min=default_min,
            max=default_max,
            step=default_step,
            value=default_value,
            marks=default_marks,
            tooltip={"placement": "bottom", "always_visible": False},
        ),
        dcc.Store(
            id=f"{slider_id}-range",
            data={'min': default_min, 'max': default_max, 'step': default_step},
        ),
    ], style={'marginTop': '0.5rem'})
