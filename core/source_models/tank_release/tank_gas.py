import numpy as np

__all__ = ['simulate_tank_gas_leak']


def compute_Z(Tt, V_m, A_prime, B_prime, R):
    term1 = 1 / (1 - (B_prime / V_m))
    term2 = A_prime / (R * Tt**1.5 * V_m * (1 + (B_prime / V_m)))
    return term1 - term2


def simulate_tank_gas_leak(duration_s=300, dt=1.0, R=8.314, Tc=190.6, Pc=4599000, Tt0=300.0,
                           M_gas=16.04, V_tank=5.0, m_gas0=50.0, Pa=101325, gamma=1.31,
                           C_dis=0.6, r_h=0.01, r_t=1.0):
    A_h = np.pi * r_h**2
    A_prime = 0.4278 * (R**2 * Tc**2.5 / Pc)
    B_prime = 0.0867 * R * Tc / Pc
    L_h = 2 * r_h
    L_t = 2 * r_t
    beta_c = L_h / L_t
    if beta_c > 0.2:
        Rc = (2 / (gamma + 1)) ** (gamma / (gamma - 1))
    else:
        from scipy.optimize import fsolve
        def Rc_small(Rc):
            lhs = Rc ** ((1 - gamma) / gamma) + (gamma - 1) / 2 * beta_c**4 * Rc**(2 / gamma)
            rhs = (gamma + 1) / 2
            return lhs - rhs
        Rc = fsolve(Rc_small, 0.5)[0]
    m_gas = m_gas0
    Tt = Tt0
    time_steps = int(duration_s / dt)
    flowrate_list, mass_list, temp_list, pressure_list, time_list = [], [], [], [], []
    for i in range(time_steps):
        n_mol = (m_gas * 1000) / M_gas
        V_m = V_tank / n_mol
        Z = compute_Z(Tt, V_m, A_prime, B_prime, R)
        Pt = (Z * R * Tt) / V_m
        Rp = Pa / Pt
        rho_g = Pt * M_gas / (Z * R * Tt * 1000)
        if Rp < Rc:
            QT = C_dis * A_h * np.sqrt(rho_g * Pt * gamma * (2 / (gamma + 1)) ** ((gamma + 1) / (gamma - 1)))
        else:
            argument = 2 * rho_g * Pt * gamma / (gamma - 1) * ((Rp) ** (2 / gamma) - (Rp) ** ((gamma + 1) / gamma))
            QT = C_dis * A_h * np.sqrt(max(argument, 0))
        m_gas = max(m_gas - QT * dt, 1e-3)
        n_mol_next = (m_gas * 1000) / M_gas
        V_m_next = V_tank / n_mol_next
        Z_next = compute_Z(Tt, V_m_next, A_prime, B_prime, R)
        Pt_next = (Z_next * R * Tt) / V_m_next
        Tt = Tt * (Pt / Pt_next) ** ((1 - gamma) / gamma)
        flowrate_list.append(QT); mass_list.append(m_gas); temp_list.append(Tt); pressure_list.append(Pt); time_list.append(i*dt)
    return {
        'times': np.array(time_list),
        'Qt': np.array(flowrate_list),
        'mass': np.array(mass_list),
        'temperature': np.array(temp_list),
        'pressure': np.array(pressure_list)
    }
