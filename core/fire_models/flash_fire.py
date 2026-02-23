import math

__all__ = ['flash_fire_radius']


def flash_fire_radius(mass_kg: float, LFL_vol_frac: float = 0.05, mixing_height_m: float = 2.0) -> float:
    """Very simple hazard radius estimate: volume to reach LFL in a mixing layer.
    Assumes instantaneous mixing in a cylinder of height h; r such that
    mass / (rho_air * volume) >= LFL. Uses rho_air ~ 1.2 kg/m3.
    """
    rho_air = 1.2
    target_conc = LFL_vol_frac * rho_air
    volume_m3 = mass_kg / max(target_conc, 1e-6)
    r = math.sqrt(volume_m3 / (math.pi * mixing_height_m))
    return r
