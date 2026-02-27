"""
app1/config.py
==============
Application-level configuration constants.

All Dash constructor arguments and runtime settings live here so that
``__init__.py`` (the factory) and ``server.py`` (the entry point) stay thin.
"""

import dash_bootstrap_components as dbc

# ---------------------------------------------------------------------------
# Dash constructor kwargs
# ---------------------------------------------------------------------------

DASH_KWARGS = dict(
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title=(
        "pyELDQM - Emergency Leakage & Dispersion "
        "Quantification Modelling Toolkit"
    ),
)

# ---------------------------------------------------------------------------
# Development-server settings  — override via environment variables
# ---------------------------------------------------------------------------
import os as _os

SERVER_HOST: str = _os.environ.get("HOST", "localhost")
SERVER_PORT: int = int(_os.environ.get("PORT", "8050"))
DEBUG: bool = _os.environ.get("DEBUG", "true").lower() not in ("false", "0", "no")
