"""
Dispersion Coefficient Utilities
=================================
Pasquill–Gifford–Turner dispersion sigma parameterisations (σ_x, σ_y, σ_z)
for rural and urban categories, plus Gaussian cross-wind and vertical
concentration kernel functions.
"""
from __future__ import annotations

import math
import numpy as np
from typing import Tuple

DISPERSION_COEFFICIENTS = {
    'A': {
        'BOTH': {"sx1": 0.02, "sx2": 1.22, "sy1": 0.22, "sy2": 0.0001},
        'RURAL': {"sz1": 0.2, "sz2": 0, "sz3": 0},
        'URBAN': {"sz1": 0.24, "sz2": 0.001, "sz3": 0.5}
    },
    'B': {
        'BOTH': {"sx1": 0.02, "sx2": 1.22, "sy1": 0.16, "sy2": 0.0001},
        'RURAL': {"sz1": 0.12, "sz2": 0, "sz3": 0},
        'URBAN': {"sz1": 0.24, "sz2": 0.001, "sz3": 0.5}
    },
    'C': {
        'BOTH': {"sx1": 0.02, "sx2": 1.22, "sy1": 0.11, "sy2": 0.0001},
        'RURAL': {"sz1": 0.08, "sz2": 0.0002, "sz3": -0.5},
        'URBAN': {"sz1": 0.2, "sz2": 0, "sz3": 0}
    },
    'D': {
        'BOTH': {"sx1": 0.04, "sx2": 1.14, "sy1": 0.08, "sy2": 0.0001},
        'RURAL': {"sz1": 0.06, "sz2": 0.0015, "sz3": -0.5},
        'URBAN': {"sz1": 0.14, "sz2": 0.0003, "sz3": -0.5}
    },
    'E': {
        'BOTH': {"sx1": 0.17, "sx2": 0.97, "sy1": 0.06, "sy2": 0.0001},
        'RURAL': {"sz1": 0.03, "sz2": 0.0003, "sz3": -1},
        'URBAN': {"sz1": 0.08, "sz2": 0.0015, "sz3": -0.5}
    },
    'F': {
        'BOTH': {"sx1": 0.17, "sx2": 0.97, "sy1": 0.04, "sy2": 0.0001},
        'RURAL': {"sz1": 0.016, "sz2": 0.0003, "sz3": -1},
        'URBAN': {"sz1": 0.08, "sz2": 0.0015, "sz3": -0.5}
    }
}


def sigma_x(x: float, sx1: float, sx2: float) -> float:
    return sx1 * (x ** sx2)

def sigma_y(x: float, sy1: float, sy2: float) -> float:
    # Use NumPy for vectorized sqrt to support array inputs
    return (sy1 * x) / np.sqrt(1 + sy2 * x)

def sigma_z(x: float, sz1: float, sz2: float, sz3: float) -> float:
    return sz1 * x * (1 + sz2 * x) ** sz3


def get_sigmas(x: float, stability_class: str, roughness: str) -> Tuple[float, float, float]:
    s = stability_class.upper()
    r = roughness.upper()
    both = DISPERSION_COEFFICIENTS[s]['BOTH']
    sz = DISPERSION_COEFFICIENTS[s][r]
    return (
        sigma_x(x, both['sx1'], both['sx2']),
        sigma_y(x, both['sy1'], both['sy2']),
        sigma_z(x, sz['sz1'], sz['sz2'], sz['sz3'])
    )


def gy(y: float, sigma_y: float) -> float:
    return (1 / (np.sqrt(2 * np.pi) * sigma_y)) * np.exp(-y**2 / (2 * sigma_y**2))


def gz(z: float, sigma_z: float, h_s: float) -> float:
    return (1 / (np.sqrt(2 * np.pi) * sigma_z)) * (
        np.exp(-((z - h_s)**2) / (2 * sigma_z**2)) + 
        np.exp(-((z + h_s)**2) / (2 * sigma_z**2))   
    )
