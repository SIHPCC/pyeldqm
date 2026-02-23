"""
Puddle Evaporation Model
========================
Comprehensive puddle evaporation model including all energy balance components:
- Solar insolation
- Longwave radiation (down and up)
- Sensible heat transfer
- Evaporative flux
- Substrate heat transfer
- Temperature evolution
"""

import numpy as np
from typing import Dict, Tuple, Optional, List
from datetime import datetime
from ...meteorology.solar_radiation import solar_insolation as calculate_solar_flux

# === Physical Constants ===
R_GAS = 8.314  # J/mol/K - Universal gas constant
VON_KARMAN = 0.4  # von Karman constant
SC_T = 0.85  # Turbulent Schmidt number
EULER_GAMMA = 0.5772  # Euler-Mascheroni constant
STEFAN_BOLTZMANN = 5.67e-8  # W/m²/K⁴
EMISSIVITY = 0.97  # Surface emissivity
CP_AIR = 1004  # J/kg/K - Specific heat of air
MW_WATER = 18.0  # g/mol - Molecular weight of water
DIFFUSIVITY_WATER = 2.39e-5  # m²/s - Diffusivity of water vapor in air
KINEMATIC_VISCOSITY_AIR = 1.5e-5  # m²/s

# === Substrate Properties ===
SUBSTRATE_PROPERTIES = {
    "default_soil": {"k": 8.64, "kappa": 4.13e-6},      # W/m/K, m²/s
    "dry_sandy_soil": {"k": 2.34, "kappa": 1.74e-6},
    "moist_sandy_soil": {"k": 5.31, "kappa": 3.74e-6},
    "concrete": {"k": 8.28, "kappa": 3.74e-6},
}

# === Stability Class Parameters ===
STABILITY_EXPONENTS = {
    'A': 0.108, 'B': 0.112, 'C': 0.120, 
    'D': 0.142, 'E': 0.203, 'F': 0.253
}


def vapor_pressure_antoine(T_K: float, A: float, B: float, C: float) -> float:
    """
    Calculate vapor pressure using Antoine equation.
    
    log10(P_mmHg) = A - B / (C + T_degC)
    
    Parameters:
    -----------
    T_K : float
        Temperature in Kelvin
    A, B, C : float
        Antoine equation coefficients
        Common chemicals:
        - Toluene: A=6.95464, B=1344.8, C=219.48
        - Benzene: A=6.89272, B=1203.531, C=219.888
        - Methanol: A=7.89750, B=1474.08, C=229.13
        - Ammonia: A=7.55466, B=1002.711, C=247.885
        - Chlorine: A=6.93790, B=861.34, C=246.33
    
    Returns:
    --------
    float : Vapor pressure in Pa
    """
    T_C = T_K - 273.15
    if T_C + C <= 0:
        return 0.0
    Pv_mmHg = 10 ** (A - B / (C + T_C))
    return Pv_mmHg * 133.322  # Convert mmHg to Pa


# Common chemical Antoine coefficients database
ANTOINE_COEFFICIENTS = {
    'toluene': (6.95464, 1344.8, 219.48),
    'benzene': (6.89272, 1203.531, 219.888),
    'methanol': (7.89750, 1474.08, 229.13),
    'ammonia': (7.55466, 1002.711, 247.885),
    'chlorine': (6.93790, 861.34, 246.33),
    'propane': (6.82973, 813.20, 248.00),
    'butane': (6.80896, 935.86, 238.73),
    'ethanol': (8.04494, 1554.3, 222.65),
    'acetone': (7.02447, 1161.0, 224.0),
    'water': (8.07131, 1730.63, 233.426),
}


def get_vapor_pressure(T_K: float, chemical: str = None, antoine_coeffs: Tuple[float, float, float] = None) -> float:
    """
    Calculate vapor pressure using Antoine equation.
    
    Can provide either a chemical name from the database OR custom Antoine coefficients.
    
    Parameters:
    -----------
    T_K : float
        Temperature in Kelvin
    chemical : str, optional
        Chemical name (e.g., 'toluene', 'benzene'). Case-insensitive.
        See ANTOINE_COEFFICIENTS for available chemicals.
    antoine_coeffs : tuple, optional
        Custom Antoine coefficients (A, B, C)
    
    Returns:
    --------
    float : Vapor pressure in Pa
    
    Raises:
    -------
    ValueError : If neither chemical nor antoine_coeffs is provided, or if chemical not found
    
    Examples:
    ---------
    >>> get_vapor_pressure(298.15, chemical='toluene')
    >>> get_vapor_pressure(298.15, antoine_coeffs=(6.95464, 1344.8, 219.48))
    """
    if antoine_coeffs is not None:
        A, B, C = antoine_coeffs
    elif chemical is not None:
        chem_lower = chemical.lower().strip()
        if chem_lower not in ANTOINE_COEFFICIENTS:
            available = ', '.join(sorted(ANTOINE_COEFFICIENTS.keys()))
            raise ValueError(f"Chemical '{chemical}' not found in database. Available: {available}")
        A, B, C = ANTOINE_COEFFICIENTS[chem_lower]
    else:
        raise ValueError("Must provide either 'chemical' name or 'antoine_coeffs' tuple")
    
    return vapor_pressure_antoine(T_K, A, B, C)


def air_density(T_K: float) -> float:
    """
    Calculate air density as function of temperature.
    
    Parameters:
    -----------
    T_K : float
        Air temperature in Kelvin
    
    Returns:
    --------
    float : Air density in kg/m³
    """
    return 2.42 - 0.0041 * T_K


def solar_insolation(
    datetime_obj: datetime,
    latitude_deg: float,
    longitude_deg: float,
    cloudiness_index: int,
    timezone_offset_hrs: float
) -> float:
    """
    Calculate solar insolation flux.
    
    Parameters:
    -----------
    datetime_obj : datetime
        Current datetime
    latitude_deg : float
        Latitude in degrees
    longitude_deg : float
        Longitude in degrees
    cloudiness_index : int
        Cloud cover index (0-10, 0=clear, 10=overcast)
    timezone_offset_hrs : float
        Timezone offset from UTC in hours
    
    Returns:
    --------
    float : Solar flux in W/m²
    """
    Fs, _ = calculate_solar_flux(datetime_obj, latitude_deg, longitude_deg, 
                                  cloudiness_index, timezone_offset_hrs)
    return Fs


def longwave_radiation_down(air_temp_K: float, humidity: float, cloudiness_index: int) -> float:
    """
    Calculate downward longwave radiation from atmosphere.
    
    Parameters:
    -----------
    air_temp_K : float
        Air temperature in Kelvin
    humidity : float
        Relative humidity (0-1)
    cloudiness_index : int
        Cloud cover index (0-10)
    
    Returns:
    --------
    float : Downward longwave radiation in W/m²
    """
    # Water vapor pressure
    e_w = 99.89 * humidity * np.exp(21.66 - 5431.3 / air_temp_K)
    
    # Cloud coefficients
    a_coeff = [0.740, 0.750, 0.760, 0.770, 0.783, 0.793, 0.800, 0.810, 0.820, 0.840, 0.870]
    b_coeff = [44.3e-6, 44.3e-6, 44.3e-6, 44.2e-6, 40.7e-6, 40.5e-6, 39.9e-6,
               38.4e-6, 35.4e-6, 31.0e-6, 26.6e-6]
    
    cloud_idx = min(max(cloudiness_index, 0), 10)
    a = a_coeff[cloud_idx]
    b = b_coeff[cloud_idx]
    B = a + b * e_w
    
    return (1 - 0.03) * STEFAN_BOLTZMANN * air_temp_K**4 * B


def longwave_radiation_up(T_puddle_K: float) -> float:
    """
    Calculate upward longwave radiation from puddle surface.
    
    Parameters:
    -----------
    T_puddle_K : float
        Puddle temperature in Kelvin
    
    Returns:
    --------
    float : Upward longwave radiation in W/m² (negative value)
    """
    return -EMISSIVITY * STEFAN_BOLTZMANN * T_puddle_K**4


def sensible_heat_flux(
    air_temp_K: float,
    T_puddle_K: float,
    wind_friction_speed: float,
    jc: float
) -> float:
    """
    Calculate sensible heat transfer between air and puddle.
    
    Parameters:
    -----------
    air_temp_K : float
        Air temperature in Kelvin
    T_puddle_K : float
        Puddle temperature in Kelvin
    wind_friction_speed : float
        Friction velocity (m/s)
    jc : float
        Mass transfer coefficient
    
    Returns:
    --------
    float : Sensible heat flux in W/m²
    """
    alpha = 2.12e-5  # Thermal diffusivity of air (m²/s)
    D = 2.1e-5  # Mass diffusivity (m²/s)
    
    rho_air = air_density(air_temp_K)
    
    return rho_air * CP_AIR * jc * (alpha / D)**(2/3) * wind_friction_speed * (air_temp_K - T_puddle_K)


def evaporative_flux(
    T_puddle_K: float,
    Pa: float,
    U: float,
    z: float,
    z0: float,
    Dp: float,
    Mc: float,
    Lv: float,
    stability_class: str = 'D',
    chemical: str = None,
    antoine_coeffs: Optional[Tuple[float, float, float]] = None
) -> Tuple[float, float, float, float, float]:
    """
    Calculate evaporative flux using mass transfer theory.
    
    Parameters:
    -----------
    T_puddle_K : float
        Puddle temperature (K)
    Pa : float
        Atmospheric pressure (Pa)
    U : float
        Wind speed at height z (m/s)
    z : float
        Measurement height (m)
    z0 : float
        Surface roughness length (m)
    Dp : float
        Puddle downwind length (m)
    Mc : float
        Molecular weight of chemical (g/mol)
    Lv : float
        Latent heat of vaporization (J/kg)
    stability_class : str
        Atmospheric stability class ('A' to 'F')
    chemical : str, optional
        Chemical name for vapor pressure calculation (e.g., 'toluene', 'benzene')
    antoine_coeffs : tuple, optional
        Custom Antoine coefficients (A, B, C). Overrides 'chemical' if provided.
    
    Returns:
    --------
    tuple : (F_evap, Cs, U_star, jc, evap_rate_kg_m2_s)
        - F_evap: Evaporative flux (W/m²)
        - Cs: Saturation concentration (kg/m³)
        - U_star: Friction velocity (m/s)
        - jc: Corrected mass transfer coefficient
        - evap_rate_kg_m2_s: Evaporation rate (kg/m²/s)
    """
    # Step 1: Friction velocity
    n = STABILITY_EXPONENTS.get(stability_class.upper(), 0.142)
    U_star = 0.03 * U * (10 / z) ** n
    
    # Step 2: Gas diffusivity
    Kc = DIFFUSIVITY_WATER * np.sqrt(MW_WATER / Mc)
    
    # Step 3: Schmidt and Reynolds numbers
    Sc = KINEMATIC_VISCOSITY_AIR / Kc
    Re0 = U_star * z0 / KINEMATIC_VISCOSITY_AIR
    
    # Step 4: Calculate f_sc
    if Re0 < 0.13:
        f_sc = (3.85 * Sc**(1/3) - 1.3)**2 + (SC_T / VON_KARMAN) * np.log(0.13 * Sc)
    elif Re0 > 2:
        f_sc = 7.3 * Re0**(0.25) * np.sqrt(Sc) - 5 * SC_T
    else:
        f_min = (3.85 * Sc**(1/3) - 1.3)**2 + (SC_T / VON_KARMAN) * np.log(0.13 * Sc)
        f_max = 7.3 * 2**(0.25) * np.sqrt(Sc) - 5 * SC_T
        f_sc = f_min + (f_max - f_min) * (Re0 - 0.13) / (2 - 0.13)
    
    # Step 5: Lambda and X1
    Lambda = (1 / n) + 1 + 2 * np.log(1 + n) - 2 * EULER_GAMMA + \
             (VON_KARMAN / SC_T) * (1 + n) * f_sc
    X1 = (n * VON_KARMAN**2 * Dp) / (SC_T * z0 * np.exp(1 / n))
    
    # Step 6: jbar (mean mass transfer coefficient)
    ln_term = np.log(np.exp(Lambda) * X1)
    denom = ln_term**2 + np.pi**2
    jbar = (VON_KARMAN / SC_T) * (1 + n) * (
        0.5
        - (1 / np.pi) * np.arctan(ln_term / np.pi)
        + (1 - EULER_GAMMA) / denom
        + (1 + (1 - EULER_GAMMA)**2 + (np.pi**2) / 6) * ln_term / denom**2
    )
    
    # Step 7: Vapor pressure and corrected jc
    Pv = get_vapor_pressure(T_puddle_K, chemical=chemical, antoine_coeffs=antoine_coeffs)
    
    jc = 0.0
    if Pv < Pa:
        jc = -jbar * (Pa / Pv) * np.log(1 - Pv / Pa)
    
    # Step 8: Saturation concentration
    Cs = (Mc * Pv) / (R_GAS * T_puddle_K) / 1000  # kg/m³
    
    # Step 9: Evaporative flux and rate
    evap_rate_kg_m2_s = Cs * U_star * jc  # kg/m²/s
    F_evap = -evap_rate_kg_m2_s * Lv  # W/m² (negative = heat loss)
    
    return F_evap, Cs, U_star, jc, evap_rate_kg_m2_s


def substrate_heat_flux(
    T_substrate_K: float,
    T_puddle_K: float,
    time_s: float,
    T_boiling_K: float,
    surface_type: str = "land",
    solid_type: str = "default_soil",
    puddle_radius_m: Optional[float] = None,
    ri_list: Optional[List[float]] = None,
    tau_list: Optional[List[float]] = None
) -> float:
    """
    Calculate heat flux from substrate to puddle.
    
    Parameters:
    -----------
    T_substrate_K : float
        Substrate temperature (K)
    T_puddle_K : float
        Puddle temperature (K)
    time_s : float
        Current time (seconds)
    T_boiling_K : float
        Boiling point (K)
    surface_type : str
        'land' or 'water'
    solid_type : str
        Type of soil/solid (for land surface)
    puddle_radius_m : float, optional
        Puddle radius (m), required for boiling case
    ri_list : list, optional
        List of ring radii (m), required for boiling case
    tau_list : list, optional
        List of ring formation times (s), required for boiling case
    
    Returns:
    --------
    float : Substrate heat flux in W/m²
    """
    if surface_type == "water":
        delta_T = T_substrate_K - T_puddle_K
        return 500 * delta_T if delta_T > 0 else 0
    
    elif surface_type == "land":
        if solid_type not in SUBSTRATE_PROPERTIES:
            raise ValueError(f"Invalid solid_type '{solid_type}'. Must be one of {list(SUBSTRATE_PROPERTIES.keys())}")
        
        props = SUBSTRATE_PROPERTIES[solid_type]
        k_ground = props["k"]  # W/m/K
        kappa_ground = props["kappa"]  # m²/s
        
        boiling_case = T_puddle_K >= T_boiling_K
        
        if not boiling_case:
            # Non-boiling case: standard conduction
            if time_s <= 1:
                return 0
            ramp = min(time_s / 600, 1.0)  # Ramp up over 10 minutes
            return ramp * k_ground * (T_substrate_K - T_puddle_K) / np.sqrt(np.pi * kappa_ground * time_s)
        
        else:
            # Boiling/cryogenic case: concentric ring approach
            if puddle_radius_m is None or ri_list is None or tau_list is None:
                raise ValueError("For boiling case, 'puddle_radius_m', 'ri_list', and 'tau_list' must be provided")
            
            N = len(ri_list)
            sum_terms = 0.0
            
            for i in range(N - 1):
                tau_i = tau_list[i]
                if tau_i >= time_s:
                    continue  # Ring hasn't formed yet
                
                r_i = ri_list[i]
                r_im1 = ri_list[i - 1] if i > 0 else 0
                r_avg = (r_i + r_im1) / 2
                delta_r = r_i - r_im1
                delta_t = time_s - tau_i
                
                if delta_t <= 0:
                    continue
                
                sum_terms += (2 * np.pi * r_avg * delta_r) / np.sqrt(delta_t)
            
            if time_s <= 1:
                return 0
            
            ramp = min(time_s / 600, 1.0)
            F_sub = ramp * k_ground * (T_substrate_K - T_puddle_K) * sum_terms / (np.pi * puddle_radius_m**2)
            return F_sub
    
    else:
        raise ValueError("surface_type must be 'land' or 'water'")


def net_energy_flux(
    Fs: float,
    F_long_down: float,
    F_long_up: float,
    F_sensible: float,
    F_evap: float,
    F_substrate: float
) -> float:
    """
    Calculate net energy flux to puddle.
    
    Returns:
    --------
    float : Net energy flux in W/m²
    """
    return Fs + F_long_down + F_long_up + F_sensible + F_evap + F_substrate


def calculate_all_fluxes(
    time_s: float,
    T_puddle_K: float,
    params: Dict,
    ignore_fluxes: Optional[List[str]] = None
) -> Dict:
    """
    Calculate all energy fluxes for puddle evaporation.
    
    Parameters:
    -----------
    time_s : float
        Current time (seconds)
    T_puddle_K : float
        Current puddle temperature (K)
    params : dict
        Dictionary containing all required parameters
    ignore_fluxes : list, optional
        List of flux names to ignore (set to zero)
    
    Returns:
    --------
    dict : Dictionary containing all flux values and auxiliary variables
    """
    if ignore_fluxes is None:
        ignore_fluxes = []
    
    results = {}
    
    # Solar insolation
    if 'Fs' not in ignore_fluxes:
        Fs = solar_insolation(
            params['datetime_obj'],
            params['latitude_deg'],
            params['longitude_deg'],
            params['cloudiness_index'],
            params['timezone_offset_hrs']
        )
    else:
        Fs = 0
    results['Fs'] = Fs
    
    # Longwave down
    if 'F_long_down' not in ignore_fluxes:
        F_long_down = longwave_radiation_down(
            params['air_temp_K'],
            params['humidity'],
            params['cloudiness_index']
        )
    else:
        F_long_down = 0
    results['F_long_down'] = F_long_down
    
    # Longwave up
    if 'F_long_up' not in ignore_fluxes:
        F_long_up = longwave_radiation_up(T_puddle_K)
    else:
        F_long_up = 0
    results['F_long_up'] = F_long_up
    
    # Evaporative flux
    if 'F_evap' not in ignore_fluxes:
        F_evap, Cs, U_star, jc, evap_rate = evaporative_flux(
            T_puddle_K,
            params['Pa'],
            params['U'],
            params['z'],
            params['z0'],
            params['Dp'],
            params['MW'],
            params['Lv'],
            params.get('stability_class', 'D'),
            params.get('chemical', None),
            params.get('antoine_coeffs', None)
        )
        results['evap_rate_kg_m2_s'] = evap_rate
        results['evap_rate_kg_m2_hr'] = evap_rate * 3600
        results['Cs'] = Cs
        results['U_star'] = U_star
        results['jc'] = jc
    else:
        F_evap = 0
        U_star = None
        jc = None
        results['evap_rate_kg_m2_s'] = 0
        results['evap_rate_kg_m2_hr'] = 0
    results['F_evap'] = F_evap
    
    # Sensible heat flux
    if 'F_sensible' not in ignore_fluxes:
        # If U_star or jc not calculated, estimate them
        if U_star is None or jc is None:
            n = STABILITY_EXPONENTS.get(params.get('stability_class', 'D').upper(), 0.142)
            U_star = 0.03 * params['U'] * (10 / params['z']) ** n
            jc = 1.0
        
        F_sensible = sensible_heat_flux(
            params['air_temp_K'],
            T_puddle_K,
            U_star,
            jc
        )
    else:
        F_sensible = 0
    results['F_sensible'] = F_sensible
    
    # Substrate heat flux
    if 'F_substrate' not in ignore_fluxes:
        F_substrate = substrate_heat_flux(
            params['T_substrate'],
            T_puddle_K,
            time_s,
            params['T_boiling'],
            params['surface_type'],
            params.get('solid_type', 'default_soil'),
            params.get('puddle_radius', None),
            params.get('ri_list', None),
            params.get('tau_list', None)
        )
    else:
        F_substrate = 0
    results['F_substrate'] = F_substrate
    
    # Net flux
    F_net = net_energy_flux(Fs, F_long_down, F_long_up, F_sensible, F_evap, F_substrate)
    results['F_net'] = F_net
    
    return results


def simulate_puddle_evaporation(
    params: Dict,
    simulation_duration_s: float,
    time_step_s: float,
    ignore_fluxes: Optional[List[str]] = None
) -> Dict:
    """
    Simulate puddle evaporation over time with full energy balance.
    
    Parameters:
    -----------
    params : dict
        Simulation parameters containing:
        - Chemical properties: MW, Lv, rho, Cp, T_boiling, antoine_coeffs
        - Meteorological: air_temp_K, humidity, U, z, z0, Pa, datetime_obj, etc.
        - Puddle: Initial_T_puddle, depth, Dp (or puddle_area)
        - Surface: surface_type, solid_type, T_substrate
    simulation_duration_s : float
        Total simulation time (seconds)
    time_step_s : float
        Time step (seconds)
    ignore_fluxes : list, optional
        List of flux names to ignore
    
    Returns:
    --------
    dict : Simulation results containing time series of all variables
    """
    from datetime import timedelta
    
    # Initialize storage
    time_array = np.arange(0, simulation_duration_s, time_step_s)
    n_steps = len(time_array)
    
    results = {
        'time': time_array,
        'T_puddle': np.zeros(n_steps),
        'Fs': np.zeros(n_steps),
        'F_long_down': np.zeros(n_steps),
        'F_long_up': np.zeros(n_steps),
        'F_sensible': np.zeros(n_steps),
        'F_evap': np.zeros(n_steps),
        'F_substrate': np.zeros(n_steps),
        'F_net': np.zeros(n_steps),
        'evap_rate_kg_m2_s': np.zeros(n_steps),
        'evap_rate_kg_m2_hr': np.zeros(n_steps),
    }
    
    # Initial conditions
    T_puddle = params['Initial_T_puddle']
    
    # Get puddle properties
    depth = params.get('depth', 0.01)  # m
    rho = params['rho']  # kg/m³
    Cp = params['Cp']  # J/kg/K
    T_boiling = params['T_boiling']  # K
    Lv = params['Lv']  # J/kg
    
    # Simulation loop
    for i, t in enumerate(time_array):
        # Update datetime if provided
        if 'datetime_obj' in params and 'base_datetime' in params:
            params['datetime_obj'] = params['base_datetime'] + timedelta(seconds=int(t))
        
        # Calculate fluxes
        fluxes = calculate_all_fluxes(t, T_puddle, params, ignore_fluxes)
        
        # Update temperature based on energy balance
        if T_puddle < T_boiling:
            # Non-boiling: heat changes temperature
            dT = (fluxes['F_net'] * time_step_s) / (rho * Cp * depth)
            T_puddle += dT
        else:
            # Boiling: temperature fixed, all net heat goes to evaporation
            T_puddle = T_boiling
            # Recalculate evaporation rate based on total heat flux
            if fluxes['F_net'] > 0:
                results['evap_rate_kg_m2_s'][i] = fluxes['F_net'] / Lv
                results['evap_rate_kg_m2_hr'][i] = results['evap_rate_kg_m2_s'][i] * 3600
        
        # Store results
        results['T_puddle'][i] = T_puddle
        results['Fs'][i] = fluxes['Fs']
        results['F_long_down'][i] = fluxes['F_long_down']
        results['F_long_up'][i] = fluxes['F_long_up']
        results['F_sensible'][i] = fluxes['F_sensible']
        results['F_evap'][i] = fluxes['F_evap']
        results['F_substrate'][i] = fluxes['F_substrate']
        results['F_net'][i] = fluxes['F_net']
        
        if not (T_puddle >= T_boiling):
            results['evap_rate_kg_m2_s'][i] = fluxes.get('evap_rate_kg_m2_s', 0)
            results['evap_rate_kg_m2_hr'][i] = fluxes.get('evap_rate_kg_m2_hr', 0)
    
    return results


# Legacy compatibility wrapper
def heat_fluxes(params: Dict, T_puddle: float, current_time_sec: float) -> Dict:
    """Legacy wrapper for backward compatibility."""
    return calculate_all_fluxes(current_time_sec, T_puddle, params)
