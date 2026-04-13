"""
app1/config.py
==============
Application-level configuration constants.

All Dash constructor arguments and runtime settings live here so that
``__init__.py`` (the factory) and ``server.py`` (the entry point) stay thin.
"""

import sys
from pathlib import Path

import dash_bootstrap_components as dbc


def _resolve_assets_folder() -> str:
    """Return a robust assets path for source and frozen builds."""
    pkg_assets = Path(__file__).resolve().parent / "assets"

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        candidates = []
        if meipass:
            base = Path(meipass)
            candidates.extend([
                base / "pyeldqm" / "app" / "assets",
                base / "assets",
            ])

        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend([
            exe_dir / "_internal" / "pyeldqm" / "app" / "assets",
            exe_dir / "pyeldqm" / "app" / "assets",
            exe_dir / "assets",
        ])

        for path in candidates:
            if path.exists():
                return str(path)

    return str(pkg_assets)

# ---------------------------------------------------------------------------
# Dash constructor kwargs
# ---------------------------------------------------------------------------

DASH_KWARGS = dict(
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    assets_folder=_resolve_assets_folder(),
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
