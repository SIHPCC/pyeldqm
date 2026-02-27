from pyeldqm.core.dispersion_models.heavy_gas_model import run_heavy_gas_model

def test_heavy_gas_runs():
    sol, n, gamma_val, U_ref, z_ref = run_heavy_gas_model('D', 2.0, 5.0, 3.0, 0.03, {'type':'continuous','dims': {'diameter': 0.1}})
    assert len(sol.t) > 10
