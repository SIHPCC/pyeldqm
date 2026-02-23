"""
Wind Profile Module
====================
Vertical wind-speed profiles using Monin-Obukhov similarity theory and
the power-law approximation, based on Pasquill–Gifford stability classes.

References
----------
- Seinfeld & Pandis, *Atmospheric Chemistry and Physics*, 3rd ed.
- US EPA, *Workbook of Atmospheric Dispersion Estimates* (AP-26).
"""
from __future__ import annotations

import numpy as np

k: float = 0.4


def obukhov_length(z0: float, stability_class: str) -> float:
    s = stability_class.upper()
    if s == 'A':
        return -11.4 * z0**0.10
    elif s == 'B':
        return -26.0 * z0**0.17
    elif s == 'C':
        return -123.0 * z0**0.30
    elif s == 'D':
        return float('inf')
    elif s == 'E':
        return 123.0 * z0**0.30
    elif s == 'F':
        return 26.0 * z0**0.17
    raise ValueError(f"Invalid stability class: {stability_class}")

def psi_zeta(zeta: float) -> float:
    if zeta < 0:
        a = (1 - 15 * zeta) ** 0.25
        return 2 * np.log((1 + a) / 2) + np.log((1 + a**2) / 2) - 2 * np.arctan(a) + (np.pi / a)
    elif zeta == 0:
        return 0
    else:
        return -4.7 * zeta

def stability_exponent(stability_class: str) -> float:
    n_values = {'A':0.108,'B':0.112,'C':0.120,'D':0.142,'E':0.203,'F':0.253}
    s = stability_class.upper()
    if s not in n_values:
        raise ValueError(f"Invalid stability class: {stability_class}")
    return n_values[s]

def friction_velocity(U_user: float, z_user: float, stability_class: str) -> float:
    n = stability_exponent(stability_class)
    return 0.03 * U_user * (10 / z_user)**n

def wind_speed(z_user: float, z0: float, U_user: float, stability_class: str, gas_type: str = "neutrally_buoyant", method: str = "power_law") -> float:
    """
    Calculate wind speed at a given height using specified method.
    
    Parameters:
    -----------
    z_user : float
        Height at which to calculate wind speed (m)
    z0 : float
        Roughness height (m)
    U_user : float
        Reference wind speed (m/s)
    stability_class : str
        Pasquill stability class (A-F)
    gas_type : str, default="neutrally_buoyant"
        Type of gas: "neutrally_buoyant" or "dense"
        (Only used with method="monin_obukhov")
    method : str, default="monin_obukhov"
        Wind profile method:
        - "monin_obukhov": Monin-Obukhov similarity theory (physically detailed)
        - "power_law": Simple power-law exponent (Pasquill-Gifford, faster, less detailed)
    
    Returns:
    --------
    float : Wind speed at z_user (m/s)
    """
    s = stability_class.upper()
    method = method.lower()
    
    if method == "monin_obukhov":
        if gas_type.lower() == "neutrally_buoyant":
            L = obukhov_length(z0, s)
            u_star = friction_velocity(U_user, z_user, s)
            z = z_user
            zeta = z / L if not np.isinf(L) else 0
            psi = psi_zeta(zeta)
            return (u_star / k) * (np.log((z + z0) / z0) + psi)
        elif gas_type.lower() == "dense":
            n = stability_exponent(s)
            return U_user * (z_user / z0) ** n
        else:
            raise ValueError("gas_type must be 'neutrally_buoyant' or 'dense'")
    
    elif method == "power_law":
        # Simple power-law exponent (Pasquill-Gifford)
        # Formula: U = U_ref * (z / z_ref) ^ n
        # This assumes z0 is the reference height where U_user is measured
        n = stability_exponent(s)
        return U_user * (z_user / z0) ** n
    
    else:
        raise ValueError("method must be 'monin_obukhov' or 'power_law'")