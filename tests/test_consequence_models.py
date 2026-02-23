import numpy as np
from core.consequences import toxic_aegl_zones

def test_toxic_aegl_zones():
    x = np.linspace(0, 1000, 50)
    centerline = 1000/(x+1)  # decreasing profile
    limits = {'AEGL-1': 5, 'AEGL-2': 10}
    zones = toxic_aegl_zones(centerline, x, limits)
    assert zones['AEGL-1'] > zones['AEGL-2']
