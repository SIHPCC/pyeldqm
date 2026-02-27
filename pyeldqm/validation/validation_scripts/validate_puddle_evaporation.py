"""
Validation Script: Puddle Evaporation Model
============================================
Tests the pyELDQM puddle evaporation model with full energy balance.
Validates all flux components, temperature evolution, and evaporation rates.

Scenario:
- Chemical: Toluene (C7H8)
- Puddle area: 0.657 m²
- Initial temperature: 21.3°C (ambient)
- Depth: 0.023 m
- Location: 40°N, 75°W
- Date/Time: September 17, 1984, 13:00
- Clear sky conditions
- Wind speed: 3.9 m/s at 3 m height

Expected Results:
- Solar flux varies with sun position
- Longwave radiation fluxes present
- Sensible heat transfer based on air-puddle temperature difference
- Evaporative cooling increases with temperature
- Puddle temperature changes based on net energy balance
- Transition to boiling if temperature reaches 110.6°C
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from datetime import datetime, timedelta

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pyeldqm.core.source_models.puddle_evaporation.evaporation import (
    simulate_puddle_evaporation,
    SUBSTRATE_PROPERTIES,
)


def validate_toluene_puddle_evaporation():
    """
    Validate puddle evaporation model with toluene under daylight conditions.
    
    This scenario matches the BaseCode energy_flux_v3.py test case.
    """
    
    print("="*70)
    print("VALIDATION: Puddle Evaporation Model - Toluene Daylight Scenario")
    print("="*70)
    
    # --- Input Parameters ---
    chemical_name = "Toluene"
    molecular_weight = 92.14  # g/mol
    latent_heat = 351000  # J/kg
    boiling_point = 110.6 + 273.15  # K
    liquid_density = 867  # kg/m³
    specific_heat = 1700  # J/(kg·K)
    
    # Puddle properties
    puddle_area = 0.657  # m²
    puddle_diameter = np.sqrt(puddle_area)  # m
    puddle_depth = 0.023  # m
    initial_temperature = 21.3 + 273.15  # K
    
    # Meteorological conditions
    air_temperature = 21.3 + 273.15  # K
    humidity = 0.5  # 50%
    wind_speed = 3.9  # m/s
    measurement_height = 3.0  # m
    surface_roughness = 0.0004  # m
    atmospheric_pressure = 101325  # Pa
    
    # Location and time
    latitude = 40.0  # degrees North
    longitude = -75.0  # degrees West
    timezone_offset = -5  # EST
    start_datetime = datetime(1984, 9, 17, 13, 0)  # Sept 17, 1984, 1:00 PM
    cloudiness_index = 0  # Clear sky
    
    # Surface properties
    surface_type = 'land'
    solid_type = 'default_soil'
    substrate_temperature = 21.3 + 273.15  # K
    
    # Simulation settings
    simulation_duration = 4800  # seconds (80 minutes)
    time_step = 100  # seconds
    
    print(f"\n{'Input Parameters':=^70}")
    print(f"\nChemical Properties:")
    print(f"  Name: {chemical_name}")
    print(f"  Molecular Weight: {molecular_weight} g/mol")
    print(f"  Density: {liquid_density} kg/m³")
    print(f"  Specific Heat: {specific_heat} J/(kg·K)")
    print(f"  Latent Heat: {latent_heat/1000:.0f} kJ/kg")
    print(f"  Boiling Point: {boiling_point-273.15:.1f} degC")
    
    print(f"\nPuddle Properties:")
    print(f"  Area: {puddle_area} m^2")
    print(f"  Diameter: {puddle_diameter:.3f} m")
    print(f"  Depth: {puddle_depth*100:.1f} cm")
    print(f"  Initial Temperature: {initial_temperature-273.15:.1f} degC")
    
    print(f"\nMeteorology:")
    print(f"  Air Temperature: {air_temperature-273.15:.1f} degC")
    print(f"  Humidity: {humidity*100:.0f}%")
    print(f"  Wind Speed: {wind_speed} m/s at {measurement_height} m")
    print(f"  Atmospheric Pressure: {atmospheric_pressure/1000:.1f} kPa")
    
    print(f"\nLocation & Time:")
    print(f"  Latitude: {latitude} deg N")
    print(f"  Longitude: {longitude} deg E")
    print(f"  Date/Time: {start_datetime.strftime('%B %d, %Y %H:%M')}")
    print(f"  Sky Condition: {'Clear' if cloudiness_index == 0 else f'Cloudy ({cloudiness_index}/10)'}")
    
    print(f"\nSurface:")
    print(f"  Type: {surface_type}")
    print(f"  Soil Type: {solid_type}")
    props = SUBSTRATE_PROPERTIES[solid_type]
    print(f"  Thermal Conductivity: {props['k']:.2f} W/(m·K)")
    print(f"  Thermal Diffusivity: {props['kappa']*1e6:.2f} x 10^-6 m^2/s")
    print(f"  Substrate Temperature: {substrate_temperature-273.15:.1f} degC")
    
    print(f"\nSimulation:")
    print(f"  Duration: {simulation_duration/60:.0f} minutes")
    print(f"  Time Step: {time_step} seconds")
    print()
    
    # --- Setup Parameters Dictionary ---
    params = {
        'datetime_obj': start_datetime,
        'base_datetime': start_datetime,
        'latitude_deg': latitude,
        'longitude_deg': longitude,
        'cloudiness_index': cloudiness_index,
        'timezone_offset_hrs': timezone_offset,
        'air_temp_K': air_temperature,
        'humidity': humidity,
        'U': wind_speed,
        'z': measurement_height,
        'z0': surface_roughness,
        'Dp': puddle_diameter,
        'MW': molecular_weight,
        'Lv': latent_heat,
        'Pa': atmospheric_pressure,
        'surface_type': surface_type,
        'solid_type': solid_type,
        'T_substrate': substrate_temperature,
        'T_boiling': boiling_point,
        'Initial_T_puddle': initial_temperature,
        'rho': liquid_density,
        'Cp': specific_heat,
        'depth': puddle_depth,
        'stability_class': 'D',  # Neutral stability
        'chemical': 'toluene',  # Use chemical name from database
        'puddle_radius': None,  # Not needed for non-boiling case
        'ri_list': None,
        'tau_list': None,
    }
    
    # --- Run Simulation ---
    print("Running puddle evaporation simulation...")
    
    # Ignore substrate flux (as in BaseCode example)
    results = simulate_puddle_evaporation(
        params,
        simulation_duration,
        time_step,
        ignore_fluxes=['F_substrate']
    )
    
    # --- Extract Results ---
    times = results['time']  # seconds
    times_min = times / 60  # minutes
    T_puddle = results['T_puddle']  # K
    Fs = results['Fs']  # W/m²
    F_long_down = results['F_long_down']
    F_long_up = results['F_long_up']
    F_sensible = results['F_sensible']
    F_evap = results['F_evap']
    F_substrate = results['F_substrate']
    F_net = results['F_net']
    evap_rate_kg_m2_hr = results['evap_rate_kg_m2_hr']
    
    # --- Display Key Results ---
    print("\n" + "="*70)
    print("   SIMULATION RESULTS")
    print("="*70)
    
    print(f"\nInitial Conditions (t=0):")
    print(f"  Puddle Temperature: {T_puddle[0]-273.15:.2f} degC")
    print(f"  Solar Flux: {Fs[0]:.1f} W/m²")
    print(f"  Longwave Down: {F_long_down[0]:.1f} W/m²")
    print(f"  Longwave Up: {F_long_up[0]:.1f} W/m²")
    print(f"  Sensible Heat: {F_sensible[0]:.1f} W/m²")
    print(f"  Evaporative Flux: {F_evap[0]:.1f} W/m²")
    print(f"  Net Flux: {F_net[0]:.1f} W/m²")
    print(f"  Evaporation Rate: {evap_rate_kg_m2_hr[0]:.3f} kg/(m²·hr)")
    
    print(f"\nFinal Conditions (t={times[-1]/60:.0f} min):")
    print(f"  Puddle Temperature: {T_puddle[-1]-273.15:.2f} degC")
    print(f"  Solar Flux: {Fs[-1]:.1f} W/m²")
    print(f"  Longwave Down: {F_long_down[-1]:.1f} W/m²")
    print(f"  Longwave Up: {F_long_up[-1]:.1f} W/m²")
    print(f"  Sensible Heat: {F_sensible[-1]:.1f} W/m²")
    print(f"  Evaporative Flux: {F_evap[-1]:.1f} W/m²")
    print(f"  Net Flux: {F_net[-1]:.1f} W/m²")
    print(f"  Evaporation Rate: {evap_rate_kg_m2_hr[-1]:.3f} kg/(m²·hr)")
    
    # Temperature statistics
    T_max = np.max(T_puddle)
    T_min = np.min(T_puddle)
    T_avg = np.mean(T_puddle)
    idx_max = np.argmax(T_puddle)
    
    print(f"\nTemperature Statistics:")
    print(f"  Maximum: {T_max-273.15:.2f} degC at t={times_min[idx_max]:.1f} min")
    print(f"  Minimum: {T_min-273.15:.2f} degC")
    print(f"  Average: {T_avg-273.15:.2f} degC")
    print(f"  Change: {T_puddle[-1]-T_puddle[0]:.2f} degC")
    
    # Evaporation statistics
    evap_avg = np.mean(evap_rate_kg_m2_hr)
    evap_max = np.max(evap_rate_kg_m2_hr)
    # Use scipy.integrate.trapezoid for newer numpy or np.trapz for older versions
    try:
        from scipy.integrate import trapezoid
        total_evap_mass = trapezoid(results['evap_rate_kg_m2_s'], times) * puddle_area  # kg
    except ImportError:
        total_evap_mass = np.trapz(results['evap_rate_kg_m2_s'], times) * puddle_area  # kg
    
    print(f"\nEvaporation Statistics:")
    print(f"  Average Rate: {evap_avg:.3f} kg/(m²·hr)")
    print(f"  Maximum Rate: {evap_max:.3f} kg/(m²·hr)")
    print(f"  Total Mass Evaporated: {total_evap_mass:.3f} kg")
    print(f"  Percentage of Puddle: {total_evap_mass/(puddle_area*puddle_depth*liquid_density)*100:.2f}%")
    
    # Energy flux statistics
    print(f"\nEnergy Flux Statistics (Average):")
    print(f"  Solar: {np.mean(Fs):.1f} W/m²")
    print(f"  Longwave Down: {np.mean(F_long_down):.1f} W/m²")
    print(f"  Longwave Up: {np.mean(F_long_up):.1f} W/m²")
    print(f"  Sensible: {np.mean(F_sensible):.1f} W/m²")
    print(f"  Evaporative: {np.mean(F_evap):.1f} W/m²")
    print(f"  Net: {np.mean(F_net):.1f} W/m²")
    
    print("="*70 + "\n")
    
    # --- Plotting ---
    print("Generating validation plots...")
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Energy Flux Components
    ax1 = axes[0]
    ax1.plot(times_min, Fs, label='Solar Flux (Fs)', linestyle='-', marker='o', 
             markersize=4, linewidth=1.5, color='gold')
    ax1.plot(times_min, F_long_down, label='Longwave Down (F↓)', linestyle='--', 
             marker='s', markersize=3, linewidth=1.2, color='red')
    ax1.plot(times_min, F_long_up, label='Longwave Up (F↑)', linestyle='--', 
             marker='^', markersize=3, linewidth=1.2, color='blue')
    ax1.plot(times_min, F_sensible, label='Sensible Heat', linestyle='-.', 
             marker='v', markersize=3, linewidth=1.2, color='green')
    ax1.plot(times_min, F_evap, label='Evaporative Loss (Fe)', linestyle=':', 
             marker='x', markersize=4, linewidth=1.2, color='purple')
    ax1.plot(times_min, F_substrate, label='Substrate Flux', linestyle='--', 
             marker='d', markersize=3, linewidth=1.2, color='brown')
    ax1.plot(times_min, F_net, label='Net Energy Flux', color='black', 
             linewidth=2.5, linestyle='-')
    
    ax1.axhline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)
    ax1.set_xlabel('Time (minutes)', fontsize=12)
    ax1.set_ylabel('Flux (W/m²)', fontsize=12)
    ax1.set_title('Energy Flux Components Over Time – Daylight Scenario', 
                  fontsize=14, fontweight='bold')
    ax1.legend(loc='best', fontsize=9, ncol=2)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # Plot 2: Evaporation Rate
    ax2 = axes[1]
    ax2.plot(times_min, evap_rate_kg_m2_hr, label='Evaporation Rate', 
             linestyle='-', marker='o', markersize=4, linewidth=2, color='darkblue')
    ax2.set_xlabel('Time (minutes)', fontsize=12)
    ax2.set_ylabel('Evaporation Rate (kg/m²/hr)', fontsize=12)
    ax2.set_title('Evaporation Rate Over Time – Daylight Scenario', 
                  fontsize=14, fontweight='bold')
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    # Save figure
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'outputs', 'reports')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'validation_puddle_evaporation.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {output_file}")
    
    plt.show()
    
    # --- Additional Plot: Temperature Evolution ---
    fig2, ax3 = plt.subplots(1, 1, figsize=(12, 6))
    
    ax3.plot(times_min, T_puddle - 273.15, label='Puddle Temperature', 
             linestyle='-', marker='o', markersize=4, linewidth=2, color='darkred')
    ax3.axhline(air_temperature - 273.15, color='blue', linestyle='--', 
                linewidth=1.5, label=f'Air Temperature ({air_temperature-273.15:.1f} degC)')
    ax3.axhline(boiling_point - 273.15, color='red', linestyle='--', 
                linewidth=1.5, label=f'Boiling Point ({boiling_point-273.15:.1f} degC)')
    
    ax3.set_xlabel('Time (minutes)', fontsize=12)
    ax3.set_ylabel('Temperature (degC)', fontsize=12)
    ax3.set_title('Puddle Temperature Evolution', fontsize=14, fontweight='bold')
    ax3.legend(loc='best', fontsize=10)
    ax3.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    output_file2 = os.path.join(output_dir, 'validation_puddle_temperature.png')
    plt.savefig(output_file2, dpi=150, bbox_inches='tight')
    print(f"Temperature plot saved to: {output_file2}")
    
    plt.show()
    
    print("\n" + "="*70)
    print("VALIDATION COMPLETE")
    print("="*70)
    
    return results


def validate_night_scenario():
    """
    Validate puddle evaporation during nighttime (no solar radiation).
    """
    
    print("\n" + "="*70)
    print("VALIDATION: Puddle Evaporation Model - Nighttime Scenario")
    print("="*70)
    
    # Similar setup but for nighttime
    params = {
        'datetime_obj': datetime(1984, 9, 17, 23, 0),  # 11 PM
        'base_datetime': datetime(1984, 9, 17, 23, 0),
        'latitude_deg': 40.0,
        'longitude_deg': -75.0,
        'cloudiness_index': 2,  # Some clouds
        'timezone_offset_hrs': -5,
        'air_temp_K': 15.0 + 273.15,  # Cooler at night
        'humidity': 0.7,  # Higher humidity
        'U': 2.5,  # Lower wind
        'z': 3.0,
        'z0': 0.0004,
        'Dp': np.sqrt(0.657),
        'MW': 92.14,
        'Lv': 351000,
        'Pa': 101325,
        'surface_type': 'land',
        'solid_type': 'default_soil',
        'T_substrate': 18.0 + 273.15,  # Ground retains some heat
        'T_boiling': 110.6 + 273.15,
        'Initial_T_puddle': 20.0 + 273.15,  # Puddle slightly warmer
        'rho': 867,
        'Cp': 1700,
        'depth': 0.023,
        'chemical': 'toluene',  # Use chemical name
        'stability_class': 'E',  # Stable conditions at night
    }
    
    print("\nRunning nighttime simulation...")
    
    results = simulate_puddle_evaporation(
        params,
        simulation_duration_s=3600,  # 1 hour
        time_step_s=100,
        ignore_fluxes=['F_substrate']
    )
    
    times_min = results['time'] / 60
    
    print(f"\nNighttime Results:")
    print(f"  Initial Temperature: {results['T_puddle'][0]-273.15:.2f} degC")
    print(f"  Final Temperature: {results['T_puddle'][-1]-273.15:.2f} degC")
    print(f"  Temperature Change: {results['T_puddle'][-1]-results['T_puddle'][0]:.2f} degC")
    print(f"  Average Solar Flux: {np.mean(results['Fs']):.1f} W/m² (should be ~0)")
    print(f"  Average Evap Rate: {np.mean(results['evap_rate_kg_m2_hr']):.3f} kg/(m²·hr)")
    
    # Quick plot
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    ax.plot(times_min, results['F_long_down'], label='Longwave Down', linewidth=2)
    ax.plot(times_min, results['F_long_up'], label='Longwave Up', linewidth=2)
    ax.plot(times_min, results['F_sensible'], label='Sensible Heat', linewidth=2)
    ax.plot(times_min, results['F_evap'], label='Evaporative Loss', linewidth=2)
    ax.plot(times_min, results['F_net'], label='Net Flux', linewidth=2.5, color='black')
    ax.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax.set_xlabel('Time (minutes)', fontsize=12)
    ax.set_ylabel('Flux (W/m²)', fontsize=12)
    ax.set_title('Energy Fluxes - Nighttime Scenario', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    print("="*70)
    
    return results


if __name__ == "__main__":
    # Run daylight validation
    results_day = validate_toluene_puddle_evaporation()
    
    # Optional: Run nighttime validation
    print("\n\nWould you like to run the nighttime scenario? (Running it now...)\n")
    results_night = validate_night_scenario()
    
    print("\n" + "="*70)
    print("ALL VALIDATIONS COMPLETED SUCCESSFULLY")
    print("="*70)
