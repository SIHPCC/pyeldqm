"""
WSGI / server entry-point for pyELDQM (app1).

Exposes ``app`` (Dash instance) and ``server`` (Flask WSGI application)
so that production servers (gunicorn, waitress, etc.) can import them directly.

Example — gunicorn
------------------
gunicorn "app1.server:server" --bind 0.0.0.0:8050

Example — waitress (Windows)
-----------------------------
waitress-serve --host 0.0.0.0 --port 8050 app1.server:server
"""

from . import create_app

app = create_app()
server = app.server  # underlying Flask WSGI app
