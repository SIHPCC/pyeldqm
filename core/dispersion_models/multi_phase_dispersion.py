"""
Minimal multi-phase dispersion: split source into vapor and aerosol fractions
and superpose Gaussian centerline concentrations for both.
"""
import numpy as np
from .gaussian_model import single_source_concentration as gaussian_conc
from .dispersion_utils import get_sigmas

def combined_concentration(x, y, z, t, t_r, Q_total, U, h_s, stability_class, roughness, vapor_frac=0.7, mode='continuous'):
    Q_v = Q_total * vapor_frac
    Q_a = Q_total * (1 - vapor_frac)
    sig_x, sig_y, sig_z = get_sigmas(x, stability_class, roughness)
    Cv = gaussian_conc(x, y, z, t, t_r, Q_v, U, sig_x, sig_y, sig_z, h_s, mode=mode)
    Ca = gaussian_conc(x, y, z, t, t_r, Q_a, U, sig_x, sig_y*1.2, sig_z*1.2, h_s, mode=mode)
    return Cv + Ca
