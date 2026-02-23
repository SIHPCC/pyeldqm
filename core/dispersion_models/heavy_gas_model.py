"""
Heavy Gas Dispersion Model (Britter-McQuaid / HEGADAS-style)
=============================================================
ODE-based model for dense/heavy gas dispersion accounting for gravity
slumping, turbulent entrainment, cloud heating, and passive dispersion
transition.

References
----------
- Britter, R.E. & McQuaid, J. (1988). *Workbook on the Dispersion of Dense
  Gases*.  HSE Contract Research Report No. 17/1988.
- NOAA CAMEO Chemicals simplified parameterisation.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Tuple

import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import gamma

# ---------------------------------------------------------------------------
# Physical / model constants
# ---------------------------------------------------------------------------
VON_KARMAN: float = 0.41          # von Kármán constant (dimensionless)
G: float = 9.81                   # gravitational acceleration (m s⁻²)
R_GAS_CONST: float = 8.314        # universal gas constant (J mol⁻¹ K⁻¹)
TAMB: float = 298.15              # ambient / reference temperature (K)
MW_AIR: float = 28.97            # molecular weight of dry air (g mol⁻¹)
MW_GAS: float = 64.06             # default dense gas molecular weight – SO₂ (g mol⁻¹)
CE_CONST: float = 1.15            # gravity-spreading entrainment coefficient
DELTA_L: float = 1.0              # integration step scale (m)
H_GND_W_M2K: float = 20.0        # ground–cloud heat transfer coefficient (W m⁻² K⁻¹)
CP_GAS: float = 480               # heat capacity of dense gas mixture (J kg⁻¹ K⁻¹)

HEAVY_GAS_PARAMS = {
    'A': {'n': 0.108, 'sy1': 0.22, 'sy2': 0.0001, 'sz1': 0.20, 'sz2': 0.0, 'sz3': 0.0},
    'B': {'n': 0.112, 'sy1': 0.16, 'sy2': 0.0001, 'sz1': 0.12, 'sz2': 0.0, 'sz3': 0.0},
    'C': {'n': 0.120, 'sy1': 0.11, 'sy2': 0.0001, 'sz1': 0.08, 'sz2': 0.0002, 'sz3': -0.5},
    'D': {'n': 0.142, 'sy1': 0.08, 'sy2': 0.0001, 'sz1': 0.06, 'sz2': 0.0015, 'sz3': -0.5},
    'E': {'n': 0.203, 'sy1': 0.06, 'sy2': 0.0001, 'sz1': 0.03, 'sz2': 0.0003, 'sz3': -1.0},
    'F': {'n': 0.253, 'sy1': 0.04, 'sy2': 0.0001, 'sz1': 0.016, 'sz2': 0.0003, 'sz3': -1.0}
}


def calc_rho(temp: float, mw: float) -> float:
    """Return gas density (kg m⁻³) via ideal gas law at 101 325 Pa."""
    pressure = 101_325.0  # Pa
    return (pressure * mw * 1e-3) / (R_GAS_CONST * temp)


def calc_phi(Ri_prime: float) -> float:
    """Return stability function phi for entrainment suppression."""
    if Ri_prime < 0:
        return 1.0
    return 0.88 + 0.099 * (Ri_prime**1.04) + 1.4e-25 * (Ri_prime**5.7)


def get_ustar(u_ref: float, z_ref: float, z0: float) -> float:
    """Return friction velocity u* (m s⁻¹) via log-law."""
    return (VON_KARMAN * u_ref) / math.log(z_ref / z0)


def calc_sigma_w(u_star: float, Ri_T: float) -> float:
    """Return vertical velocity standard deviation σ_w (m s⁻¹)."""
    ratio = math.sqrt(1 + Ri_T ** (2 / 3))
    return u_star * ratio


def calc_Sy_passive(x: float, params: Dict[str, float]) -> float:
    """Return passive crosswind spread σ_y (m) at downwind distance x (m)."""
    denom = math.sqrt(1 + params['sy2'] * x)
    return (params['sy1'] * x) / denom


def calc_secondary_source(
    Q_source: float,
    u_star: float,
    U_ref: float,
    z_ref: float,
    n_exp: float,
    source_type: str,
    source_dims: Dict[str, float],
) -> Tuple[float, float]:
    """Calculate secondary source initial radius and height (Rb, Hb) in metres."""
    rho_source = calc_rho(239.15, MW_GAS)
    rho_a = calc_rho(TAMB, MW_AIR)
    g_prime = G * (rho_source - rho_a) / rho_a
    U_10 = U_ref * (10.0 / z_ref)**n_exp
    if source_type == 'instantaneous':
        V0 = source_dims.get('volume', 1.0)
        A0 = source_dims.get('area', 1.0)
        Hb = V0 / A0
        Rb = math.sqrt(A0 / math.pi)
    elif source_type == 'puddle':
        D = source_dims.get('diameter', 10.0)
        Hb = Q_source / (rho_source * U_10 * D)
        Rb = D / 2.0
    else:
        Hb = math.sqrt((Q_source * math.pi) / (4 * rho_source * U_10))
        Rb = 0.0
    Hb = max(Hb, 0.1)
    Ri_star = (g_prime * Hb) / (u_star**2)
    term_temp = (TAMB - 239.15) / 239.15
    Ri_T = G * term_temp * (Hb / (u_star * U_ref)) * ((z_ref / Hb)**n_exp)
    sigma_w = calc_sigma_w(u_star, Ri_T)
    ratio_sq = (u_star / sigma_w)**2 if sigma_w > 0 else 1.0
    Ri_prime = Ri_star * ratio_sq
    phi = calc_phi(Ri_prime)
    Erosion_Flux = (rho_a * VON_KARMAN * sigma_w * (1 + n_exp)) / phi
    if source_type == 'continuous':
        if Erosion_Flux <= 1e-6:
            Rb = 50.0
        else:
            Area = Q_source / Erosion_Flux
            Rb = math.sqrt(Area / math.pi)
    elif source_type == 'puddle':
        calc_Area = Q_source / Erosion_Flux if Erosion_Flux > 1e-6 else 99999
        phys_Area = math.pi * (Rb**2)
        if calc_Area > phys_Area:
             Rb = math.sqrt(calc_Area / math.pi)
    return Rb, Hb


def run_heavy_gas_model(
    stab_class: str,
    Q_kg_s: float,
    U_ref: float,
    z_ref: float,
    z0: float,
    source_cfg: Dict[str, Any],
) -> Tuple[Any, float, float, float, float]:
    """Run the heavy-gas ODE model and return (sol, n_exp, gamma_term, U_ref, z_ref)."""
    params = HEAVY_GAS_PARAMS[stab_class]
    n_exp = params['n']
    gamma_term = gamma(1.0 / (1.0 + n_exp))
    rho_a = calc_rho(TAMB, MW_AIR)
    u_star = get_ustar(U_ref, z_ref, z0)
    Rb, Hb = calc_secondary_source(Q_kg_s, u_star, U_ref, z_ref, n_exp, source_cfg['type'], source_cfg['dims'])
    def derivatives(x, state):
        Sz, Beff, Tc, Flux = state
        Sz = max(Sz, 0.1)
        Beff = max(Beff, 0.1)
        Tc = min(Tc, TAMB)
        Flux = max(Flux, 1e-6)
        w_c = Q_kg_s / Flux
        if w_c > 1.0: w_c = 1.0
        inv_MW_mix = (w_c / MW_GAS) + ((1 - w_c) / MW_AIR)
        MW_mix = 1.0 / inv_MW_mix
        rho_c = calc_rho(Tc, MW_mix)
        Heff = (Sz / (1.0 + n_exp)) * gamma_term
        g_prime = G * (rho_c - rho_a) / rho_a
        U_eff = (U_ref / gamma_term) * ((Sz / z_ref)**n_exp)
        Ri_star = (g_prime * Heff) / (u_star**2)
        term_temp = max(0, (TAMB - Tc) / Tc)
        Ri_T = G * term_temp * (Heff / (u_star * U_ref)) * ((z_ref / Heff)**n_exp)
        sigma_w = calc_sigma_w(u_star, Ri_T)
        Ri_prime = Ri_star * (u_star / sigma_w)**2
        phi = calc_phi(max(0.0, Ri_prime))
        scaling_factor = (1.0 + n_exp) / gamma_term
        dSz_dx = (scaling_factor * VON_KARMAN * u_star) / (U_eff * phi)
        term_gravity = 0.0
        if g_prime > 0 and Ri_prime > 1.0:
            part_a = CE_CONST * gamma_term * ((z_ref / Sz)**n_exp)
            part_b = math.sqrt(g_prime * Heff) / U_ref
            term_gravity = part_a * part_b
        denom = math.sqrt(1 + params['sy2'] * x)
        dSy_dx = (params['sy1'] / denom) - (params['sy1'] * x * params['sy2']) / (2 * denom**3)
        term_passive = (math.sqrt(math.pi) / 2.0) * dSy_dx
        dBeff_dx = term_gravity + term_passive
        entrainment_rate = (rho_a * VON_KARMAN * sigma_w * (1 + n_exp)) / phi
        dMassFlux_dx = entrainment_rate * (2 * Beff)
        F_H = H_GND_W_M2K * (TAMB - Tc)
        dT_dilution = (dMassFlux_dx / Flux) * (TAMB - Tc)
        dT_heating = ((F_H * (2 * Beff)) / DELTA_L) / (Flux * CP_GAS)
        dTc_dx = dT_dilution + dT_heating
        return [dSz_dx, dBeff_dx, dTc_dx, dMassFlux_dx]
    Sz_init = Hb * (1.0 + n_exp) / gamma_term
    y0 = [Sz_init, Rb, 239.15, Q_kg_s]
    sol = solve_ivp(fun=derivatives, t_span=(Rb, 12000), y0=y0, method='RK45', max_step=10.0)
    return sol, n_exp, gamma_term, U_ref, z_ref
