from pyeldqm.core.source_models.gas_pipeline.pipeline_leak import simulate_pipeline_leak
from pyeldqm.core.source_models.tank_release.tank_gas import simulate_tank_gas_leak

def test_pipeline_leak_outputs():
    res = simulate_pipeline_leak(duration_s=600, dt=60)
    assert 'Qt' in res and len(res['Qt']) == len(res['times'])


def test_tank_gas_leak_runs():
    res = simulate_tank_gas_leak(duration_s=60)
    assert len(res['Qt']) == len(res['times'])
