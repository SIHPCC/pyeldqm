import numpy as np
from scipy.optimize import fsolve

__all__ = ['simulate_pipeline_leak']


def friction_factor(epsilon, d_p):
    return 0.25 / (0.75 - np.log10(epsilon / d_p))**2


def compute_beta(Kf, Kh, tau_p, Gamma):
    term = (1 + (Kh**2) / (Kf * Gamma))**1.5 - 1
    beta = (2 / 3) * tau_p * Kf * Gamma**1.5 * Kh**-3 * term
    return beta


def v_ir_residual(v_ir, Kf, c, gamma, v_ia):
    term1 = (c**2 - gamma * v_ir**2) / (gamma * v_ir**2)
    term2 = (c**2 - gamma * v_ia**2) / (gamma * v_ia**2)
    term3 = 2 * np.log(v_ir / v_ia)
    return 1 / Kf - (term1 - term2 + term3)


def simulate_pipeline_leak(duration_s=3600, dt=60, MW=16.04, gamma=1.31, Tg=320.0, Po=5e6,
                           r_p=0.05, Lp=200.0, r_h=0.003, epsilon=0.0001):
    R = 8314.5
    Rj = R / MW
    Pa = 1.013e5
    rho_r = Po / (Rj * Tg)
    P_r = Po
    d_p = 2*r_p
    A_p = np.pi * r_p**2
    A_h = np.pi * r_h**2
    mu = friction_factor(epsilon, d_p)
    Gamma = ((gamma + 1) / 2) ** ((gamma + 1) / (gamma - 1))
    Q0 = Po * A_h * np.sqrt((gamma * MW) / (Gamma * R * Tg))
    M0 = (Po * A_p * Lp) / (Rj * Tg)
    mass_leaked = 0.0
    Mt = M0
    v_ir_guess = 1.0
    times = np.arange(0, duration_s, dt)
    Q_T, q_t, T_g, Pia, vi, M_remaining = [], [], [], [], [], []
    for t in times:
        c = np.sqrt(gamma * Rj * Tg)
        Kf = d_p / (gamma * mu * Lp)
        Kh = A_h / A_p
        tau_p = Lp / c
        beta = compute_beta(Kf, Kh, tau_p, Gamma)
        alpha = Mt / (beta * Q0)
        Qt = (Q0 / (1 + alpha)) * (np.exp(-t / (alpha**2 * beta)) + alpha * np.exp(-t / beta))
        mass_leaked += Qt * dt
        v_ia = c / gamma
        v_ir = fsolve(v_ir_residual, v_ir_guess, args=(Kf, c, gamma, v_ia))[0]
        P_ia = (v_ir / v_ia) * (P_r - 0.5 * rho_r * v_ir**2)
        Tf = Tg * (Pa / P_ia) ** ((gamma - 1) / gamma)
        rho_ia = rho_r * (P_ia / P_r)
        Q_t_val = A_p * rho_ia * v_ia
        Mt = M0 - mass_leaked
        Po = Mt * Rj * Tf / (A_p * Lp)
        P_r = Po
        rho_r = P_r / (Rj * Tf)
        Tg = Tf
        v_ir_guess = v_ir
        M_remaining.append(Mt); Q_T.append(Qt); T_g.append(Tg); q_t.append(Q_t_val); Pia.append(P_ia); vi.append(v_ir)
    return {
        'times': times,
        'Qt': np.array(Q_T),
        'Q_interface': np.array(q_t),
        'T_exit': np.array(T_g),
        'P_interface': np.array(Pia),
        'v_interface': np.array(vi),
        'M_remaining': np.array(M_remaining)
    }
