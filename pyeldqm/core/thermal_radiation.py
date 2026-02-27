from typing import List, Tuple
from .fire_models.pool_fire import pool_fire_flux
from .fire_models.jet_fire import jet_fire_flux

__all__ = ['iso_flux_radius']


def iso_flux_radius(target_kw_m2: float, distances_m: List[float], diameter_m: float) -> Tuple[float, float]:
    """Return nearest and farthest radii where pool fire flux >= target.
    """
    fluxes = [pool_fire_flux(d, diameter_m) for d in distances_m]
    hits = [d for d, q in zip(distances_m, fluxes) if q >= target_kw_m2]
    if not hits:
        return (0.0, 0.0)
    return (min(hits), max(hits))
