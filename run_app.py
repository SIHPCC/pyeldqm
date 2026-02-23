"""
Development entry-point for pyELDQM.

Run from the project root:
    python run_app.py

The app will be available at http://localhost:8050 by default.
Set the PORT environment variable to use a different port.
"""

import os
import sys

# Ensure the project root is on sys.path so `app` is importable.
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.server import app  # noqa: E402 — intentional late import after path setup


def main() -> None:
    """Console-script entry point (``pyeldqm-app``)."""  # noqa: D401
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DEBUG", "true").lower() not in ("false", "0", "no")

    import logging
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger(__name__).info(
        "Starting pyELDQM Dash app on http://localhost:%d  (debug=%s)", port, debug
    )
    app.run(host="localhost", port=port, debug=debug)


if __name__ == "__main__":
    main()
