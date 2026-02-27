import numpy as np

__all__ = ['simulate_tank_two_phase']


def simulate_tank_two_phase(duration_s=3600, dt=0.5, Ah=0.25*np.pi*(0.06**2), C_dis=0.6,
                            rho_l=867, rho_v=3.0, Pa=101325, cpl=1700, toluene_Lv=351000,
                            Vt=20, rt=2.5, T_boil=383.15, Tt0=400.0, Vl0=10.0,
                            alpha_w=20, delta_w=0.02, Ta=300):
    """
    Simulate tank two-phase leak with proper energy balance.
    
    Parameters:
    -----------
    alpha_w : float
        Wall heat transfer coefficient (W/(m²·K))
    delta_w : float
        Wall thickness (m)
    Ta : float
        Ambient temperature (K)
    """
    g = 9.81
    Atank = np.pi * rt**2
    hl = Vl0 / Atank
    Atw = 2 * np.pi * rt * hl
    Tt = Tt0
    M_liq = rho_l * Vl0
    times = np.arange(0, duration_s, dt)
    QT_list, Qe_list, Tt_list, Mliq_list = [], [], [], []
    for t in times:
        ecs = Pa  # simple placeholder vapor pressure
        Ph = ecs + hl * rho_l * g if ecs > Pa else Pa + hl * rho_l * g
        chi_0 = max(min((cpl * (Tt - T_boil)) / toluene_Lv, 1.0), 0.0)
        v_g, v_l = 1/rho_v, 1/rho_l
        v_eff = chi_0 * (v_g - v_l) + v_l
        rho_eff = 1 / v_eff
        Vl = v_eff * M_liq
        Vl = max(Vl, 1e-3)
        hl = Vl / Atank
        QT = Ah * C_dis * np.sqrt(max(2 * (Ph - Pa) * rho_eff, 0))
        Qe = QT * chi_0
        
        # Energy balance: heat from walls - energy lost to evaporation
        FHw = (alpha_w * Vl * (Ta - Tt)) / (delta_w * Vt)
        dUldt = -Qe * toluene_Lv + FHw * (2 * np.pi * rt * hl)
        
        delta_T = (dUldt / (rho_l * cpl * Vl)) * dt
        Tt = max(Tt + delta_T, T_boil)
        vapor_mass = QT * dt * chi_0
        aerosol_mass = QT * dt * (1 - chi_0)
        M_liq -= (vapor_mass + aerosol_mass)
        M_liq = max(M_liq, 1e-3)
        QT_list.append(QT); Qe_list.append(Qe); Tt_list.append(Tt); Mliq_list.append(M_liq)
    return {'times': times, 'Qt': np.array(QT_list), 'Qe': np.array(Qe_list), 'Tt': np.array(Tt_list), 'M_liq': np.array(Mliq_list)}
