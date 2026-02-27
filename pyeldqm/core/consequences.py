"""
Consequence Modelling Utilities
================================
High-level consequence functions that map dispersion model output to
hazard-zone footprints (e.g., AEGL-1 / AEGL-2 / AEGL-3 threat distances).
"""
import numpy as np
from typing import Dict

__all__ = ['toxic_aegl_zones']


def toxic_aegl_zones(centerline_ppm: np.ndarray, x_dist_m: np.ndarray, limits: Dict[str, float]) -> Dict[str, float]:
    """Return farthest downwind distances where AEGL thresholds are exceeded.
    """
    out = {}
    for name, limit in limits.items():
        idx = np.where(centerline_ppm >= limit)[0]
        out[name] = float(x_dist_m[idx[-1]]) if len(idx) > 0 else 0.0
    return out
