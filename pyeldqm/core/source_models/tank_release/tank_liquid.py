import numpy as np

__all__ = ['simulate_tank_liquid_leak']


def simulate_tank_liquid_leak(total_time_s=3600, dt=1.0, C_dis=0.6, Ah=0.01, zeta_h=0.3,
                              rho_l=867, rho_v=3.0, ecs=101325, Pa=101325, Lc=225000,
                              alpha_w=20, delta_w=0.01, Atw=4.0, Ta=294.15, Tt0=310.15,
                              cpl=1700, Vt=8.0, rp0=2.0, Vl0=7.0):
    g = 9.81
    pi = np.pi
    dt = dt
    times = np.arange(0, total_time_s + dt, dt)
    Ul = 0.0
    Tp = 300
    rp = rp0
    Mp = 5.0
    rho_p = rho_l
    cpl_p = cpl
    dp = 0.01
    Vl = Vl0
    rt = rp0
    Atank = (rp0**2)
    hl = Vl / Atank
    QT_list = []
    Qe_list = []
    delta_T_list = []
    rp_list = []
    delta_Tp_list = []
    Tt = Tt0
    for t in times:
        Af = Ah if hl >= zeta_h else Ah * (hl / zeta_h)
        Ph = ecs + hl * rho_l * g if ecs > Pa else Pa + hl * rho_l * g
        QT = C_dis * Af * np.sqrt(max(2 * (Ph - Pa) * rho_l, 0))
        Qe = QT * rho_v / max(rho_l - rho_v, 1e-6)
        FHw = (alpha_w * Vl * (Ta - Tt)) / (delta_w * Vt)
        dUldt = Qe * Lc + FHw * Atw
        Ul += dUldt * dt
        delta_T = (dUldt / (rho_l * cpl * max(Vl,1e-6))) * dt
        mass_loss = QT * dt
        Vl = max(Vl - mass_loss / rho_l, 0)
        hl = Vl / Atank
        delta_rp = (1 / max(rp,1e-6)) * np.sqrt((2 * g * Mp) / (pi * rho_l)) * dt
        rp += delta_rp
        fluxes_sum = FHw
        delta_Tp = ((1 / (rho_p * cpl_p * dp)) * (fluxes_sum + (QT * (Tt - Tp) / max(Mp,1e-6)))) * dt
        Tp += delta_Tp
        QT_list.append(QT); Qe_list.append(Qe); delta_T_list.append(delta_T); rp_list.append(rp); delta_Tp_list.append(delta_Tp)
    return {'times': times, 'Qt': np.array(QT_list), 'Qe': np.array(Qe_list), 'delta_T': np.array(delta_T_list), 'rp': np.array(rp_list), 'delta_Tp': np.array(delta_Tp_list)}
