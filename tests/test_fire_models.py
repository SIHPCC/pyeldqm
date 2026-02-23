from core.fire_models.pool_fire import pool_fire_flux

def test_pool_fire_flux_decay():
    q1 = pool_fire_flux(50.0, 10.0)
    q2 = pool_fire_flux(200.0, 10.0)
    assert q1 > q2
