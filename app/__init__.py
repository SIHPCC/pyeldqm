"""
App factory for pyELDQM Dash application.

Usage
-----
from app import create_app
app = create_app()
app.run(debug=True)
"""

import dash

from .config import DASH_KWARGS
from .layout.main_layout import create_layout
from .callbacks import register_all_callbacks


def create_app() -> dash.Dash:
    """
    Instantiate and fully configure the Dash application.

    Returns
    -------
    dash.Dash
        A ready-to-run Dash application with layout and all callbacks registered.
    """
    app = dash.Dash(
        __name__,
        **DASH_KWARGS,
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        ],
    )

    app.layout = create_layout()
    register_all_callbacks(app)

    return app
