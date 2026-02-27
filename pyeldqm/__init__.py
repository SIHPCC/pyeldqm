"""pyELDQM - Python-based real-time Emergency Leakage & Dispersion Quantification Model."""

from __future__ import annotations

import sys

__version__ = "0.1.2"
__author__ = "pyELDQM Development Team"

# Re-export subpackages under the pyeldqm namespace.
from . import app, core, data, validation  # noqa: E402

sys.modules.setdefault("pyeldqm.core", core)
sys.modules.setdefault("pyeldqm.app", app)
sys.modules.setdefault("pyeldqm.data", data)
sys.modules.setdefault("pyeldqm.validation", validation)
sys.modules.setdefault("core", core)
sys.modules.setdefault("app", app)
sys.modules.setdefault("data", data)
sys.modules.setdefault("validation", validation)

__all__ = ["core", "app", "data", "validation"]
