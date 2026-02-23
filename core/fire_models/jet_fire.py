import math

__all__ = ['jet_fire_flux']


def jet_fire_flux(centerline_distance_m: float, release_rate_kg_s: float,
                   flame_emissive_power_kw_m2: float = 250.0,
                   spreading_angle_deg: float = 5.0,
                   transmissivity: float = 0.9) -> float:
    """Simple jet fire centerline heat flux model.
    Flux decays ~ 1/x^2 beyond flame length proportional to release rate.
    """
    x = max(centerline_distance_m, 0.1)
    flame_length_m = 3.0 * release_rate_kg_s  # crude proportionality
    if x <= flame_length_m:
        geom = 1.0
    else:
        geom = (flame_length_m / x)**2
    return flame_emissive_power_kw_m2 * transmissivity * geom
