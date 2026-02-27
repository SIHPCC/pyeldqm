import numpy as np
from pyeldqm.core.dispersion_models.gaussian_model import single_source_concentration
from pyeldqm.core.dispersion_models.dispersion_utils import get_sigmas

def test_gaussian_concentration_positive():
    x, y, z = 100.0, 0.0, 1.5
    t, t_r = 60.0, 60.0
    Q, U = 1000.0, 5.0
    h_s = 3.0
    sig_x, sig_y, sig_z = get_sigmas(x, 'D', 'RURAL')
    c = single_source_concentration(x, y, z, t, t_r, Q, U, sig_x, sig_y, sig_z, h_s, mode='continuous')
    assert c > 0
