from pyeldqm.core.dispersion_models.multi_phase_dispersion import combined_concentration

def test_combined_concentration_basic():
    c = combined_concentration(100.0, 0.0, 1.5, 60.0, 60.0, 1000.0, 5.0, 3.0, 'D', 'RURAL', vapor_frac=0.7)
    assert c > 0
