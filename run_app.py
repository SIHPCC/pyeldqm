"""
Development entry-point for pyELDQM.

Run from the project root:
    python run_app.py

The app will be available at http://localhost:8050 by default.
Set the PORT environment variable to use a different port.
"""

import os
import sys
import threading
import webbrowser

# Ensure the project root is on sys.path so `app` is importable.
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pyeldqm.app.server import app  # noqa: E402 — intentional late import after path setup


def main() -> None:
    """Console-script entry point (``pyeldqm-app``)."""  # noqa: D401
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DEBUG", "false").lower() not in ("false", "0", "no")
    host = os.environ.get("HOST", "localhost")
    auto_open = os.environ.get("AUTO_OPEN_BROWSER", "true").lower() not in (
        "false",
        "0",
        "no",
    )
    url = f"http://{host}:{port}"

    should_open_browser = auto_open and (
        not debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    )
    if should_open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    import logging
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger(__name__).info(
        "Starting pyELDQM Dash app on %s  (debug=%s, auto_open=%s)",
        url,
        debug,
        auto_open,
    )
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
