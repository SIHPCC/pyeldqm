"""
core/logging_config.py
======================
Centralised logging configuration for pyELDQM.

Call ``configure_logging()`` once at application start-up (e.g. in
``run_app.py``).  Every other module should acquire its own logger via::

    import logging
    logger = logging.getLogger(__name__)

and call ``logger.info()``, ``logger.debug()``, ``logger.warning()``, etc.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


def configure_logging(
    level: int = logging.INFO,
    log_file: Optional[str | Path] = None,
    fmt: str = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
) -> None:
    """Configure the root logger for the whole application.

    Parameters
    ----------
    level:
        Minimum log level (e.g. ``logging.DEBUG``, ``logging.INFO``).
        Defaults to ``logging.INFO``.
    log_file:
        Optional path to a log file.  If provided, a ``FileHandler`` is added
        in addition to the ``StreamHandler`` (stdout).
    fmt:
        Log-record format string.
    datefmt:
        Date/time format string for the formatter.
    """
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]
    if log_file is not None:
        file_handler = logging.FileHandler(Path(log_file), encoding="utf-8")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    root = logging.getLogger()
    # Avoid adding duplicate handlers on repeated calls
    if not root.handlers:
        for h in handlers:
            h.setFormatter(formatter)
            root.addHandler(h)
    root.setLevel(level)

    # Silence noisy third-party loggers
    for noisy in ("urllib3", "requests", "werkzeug", "osmnx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
