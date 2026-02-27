import math

__all__ = ['pool_fire_flux']


def pool_fire_flux(distance_m: float, diameter_m: float, emissive_power_kw_m2: float = 200.0,
                    view_factor: float = 0.35, atmospheric_transmissivity: float = 0.9) -> float:
    """Compute thermal radiation heat flux from a pool fire at distance.
    q = E * F * tau * (D / (D + 2R))^2 (simple geometry factor)
    Returns kW/m2.
    """
    R = max(distance_m, 0.1)
    D = diameter_m
    geom = (D / (D + 2*R))**2
    q_kw_m2 = emissive_power_kw_m2 * view_factor * atmospheric_transmissivity * geom
    return q_kw_m2
