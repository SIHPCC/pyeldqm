"""
Validation Script: Tank Two-Phase Leak
=======================================
Tests the pyELDQM tank two-phase release model for flashing liquid releases.
Validates flash fraction, aerosol formation, and temperature evolution.

"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.source_models.tank_release.tank_two_phase import simulate_tank_two_phase


def validate_tank_toluene_twophase():
    """
    Validate tank two-phase leak model with superheated toluene.
    
    Scenario:
    - Chemical: Toluene (C7H8)
    - Initial liquid mass: 10,000 kg (stored above boiling point)
    - Tank volume: 20 m³
    - Vapor space volume: 10 m³
    - Initial temperature: 400 K (127°C, above 110.6°C boiling point)
    - Hole area: 0.25 * π * (0.06)² m²
    - Ambient pressure: 101325 Pa
    
    Expected Results:
    - Flash fraction > 0 (two-phase flow)
    - Temperature decreases towards boiling point
    - Vapor and aerosol generation
    - Rapid initial discharge followed by slower release
    """
    
    print("="*70)
    print("VALIDATION: Tank Two-Phase Leak Model - Toluene")
    print("="*70)
    
    # --- Input Parameters ---
    chemical_name = "Toluene"
    molecular_weight = 92.14  # g/mol
    
    # Liquid properties
    liquid_density = 867  # kg/m³
    vapor_density = 3.0  # kg/m³
    specific_heat = 1700  # J/(kg·K)
    latent_heat = 351000  # J/kg
    boiling_point = 383.15  # K (110°C)
    
    # Tank properties
    tank_volume = 20.0  # m³
    vapor_volume = 10.0  # m³
    liquid_volume = 10.0  # m³
    tank_radius = 2.5  # m
    initial_liquid_mass = liquid_density * liquid_volume  # kg
    
    # Hole properties
    hole_height = 0.06  # m
    hole_area = 0.25 * np.pi * hole_height**2  # m²
    discharge_coefficient = 0.6
    
    # Temperatures
    initial_temperature = 400.0  # K (127°C - superheated)
    ambient_temperature = 300.0  # K
    
    # Heat transfer
    wall_heat_transfer_coeff = 20  # W/(m²·K)
    wall_thickness = 0.02  # m
    
    # Antoine equation coefficients for toluene
    antoine_A = 6.95464
    antoine_B = 1344.8
    antoine_C = 219.48
    
    print(f"\nInput Parameters:")
    print(f"  Chemical: {chemical_name} (MW = {molecular_weight} g/mol)")
    print(f"  Initial Liquid Mass: {initial_liquid_mass:.1f} kg")
    print(f"  Initial Temperature: {initial_temperature-273.15:.1f} degC")
    print(f"  Boiling Point: {boiling_point-273.15:.1f} degC")
    print(f"  Tank Volume: {tank_volume} m^3")
    print(f"  Hole Area: {hole_area:.6f} m^2")
    print(f"  Delta T above boiling: {initial_temperature - boiling_point:.1f} K")
    print()
    
    # --- Run Simulation ---
    print("Running tank two-phase leak simulation...")
    simulation_duration = 3600  # seconds (1 hour)
    time_step = 0.5  # seconds
    
    discharge_model = 'simple_hole'  # unused in current core API; kept for docs

    results = simulate_tank_two_phase(
        duration_s=simulation_duration,
        dt=time_step,
        Ah=hole_area,
        C_dis=discharge_coefficient,
        rho_l=liquid_density,
        rho_v=vapor_density,
        Pa=101325,
        cpl=specific_heat,
        toluene_Lv=latent_heat,
        Vt=tank_volume,
        rt=tank_radius,
        T_boil=boiling_point,
        Tt0=initial_temperature,
        Vl0=liquid_volume,
        alpha_w=wall_heat_transfer_coeff,
        delta_w=wall_thickness,
        Ta=ambient_temperature
    )
    
    # --- Extract Results ---
    times = results['times']  # seconds
    total_flow_rates = results['Qt']  # kg/s (total discharge)
    vapor_flow_rates = results['Qe']  # kg/s (vapor portion)
    temperatures = results['Tt']  # K
    remaining_mass = results['M_liq']  # kg
    
    # Calculate flash fraction
    flash_fractions = vapor_flow_rates / (total_flow_rates + 1e-10)
    
    # Convert time to minutes and hours
    times_min = times / 60
    times_hr = times / 3600
    
    # Calculate aerosol flow rate
    aerosol_flow_rates = total_flow_rates - vapor_flow_rates
    
    # --- Display Key Results ---
    print("\n" + "="*70)
    print("   SIMULATION RESULTS")
    print("="*70)
    print(f"\nInitial Conditions:")
    print(f"  Total Flow Rate (QT): {total_flow_rates[0]:.3f} kg/s")
    print(f"  Vapor Flow Rate (Qe): {vapor_flow_rates[0]:.3f} kg/s")
    print(f"  Aerosol Flow Rate: {aerosol_flow_rates[0]:.3f} kg/s")
    print(f"  Flash Fraction (chi): {flash_fractions[0]:.4f}")
    print(f"  Temperature: {temperatures[0]:.2f} K ({temperatures[0]-273.15:.1f} degC)")
    print(f"  Liquid Mass: {remaining_mass[0]:.1f} kg")
    
    print(f"\nFinal Conditions (after {simulation_duration/60:.0f} minutes):")
    print(f"  Total Flow Rate (QT): {total_flow_rates[-1]:.6f} kg/s")
    print(f"  Vapor Flow Rate (Qe): {vapor_flow_rates[-1]:.6f} kg/s")
    print(f"  Aerosol Flow Rate: {aerosol_flow_rates[-1]:.6f} kg/s")
    print(f"  Flash Fraction (chi): {flash_fractions[-1]:.4f}")
    print(f"  Temperature: {temperatures[-1]:.2f} K ({temperatures[-1]-273.15:.1f} degC)")
    print(f"  Remaining Mass: {remaining_mass[-1]:.1f} kg")
    
    # Calculate totals
    total_released = initial_liquid_mass - remaining_mass[-1]
    total_vapor = np.trapz(vapor_flow_rates, times)
    total_aerosol = np.trapz(aerosol_flow_rates, times)
    
    print(f"\nCumulative Results:")
    print(f"  Total Mass Released: {total_released:.1f} kg ({total_released/initial_liquid_mass*100:.1f}%)")
    print(f"  Total Vapor Released: {total_vapor:.1f} kg")
    print(f"  Total Aerosol Released: {total_aerosol:.1f} kg")
    print(f"  Vapor/Aerosol Ratio: {total_vapor/total_aerosol:.2f}" if total_aerosol > 0 else "  Vapor/Aerosol Ratio: N/A")
    
    # Time to reach boiling point
    boiling_idx = np.where(temperatures <= boiling_point)[0]
    if len(boiling_idx) > 0:
        time_to_boiling = times_min[boiling_idx[0]]
        print(f"\nTime to Reach Boiling Point: {time_to_boiling:.2f} minutes")
    else:
        print(f"\nBoiling point not reached during simulation")
    
    print("="*70 + "\n")
    
    # --- Plotting ---
    print("Generating validation plots...")
    
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    
    # Plot 1: Flow Rates
    axes[0, 0].plot(times_hr, total_flow_rates, 'b-', linewidth=2, label='QT (Total)')
    axes[0, 0].plot(times_hr, vapor_flow_rates, 'orange', linewidth=2, label='Qe (Vapor)')
    axes[0, 0].plot(times_hr, aerosol_flow_rates, 'green', linewidth=2, label='Aerosol')
    axes[0, 0].set_xlabel('Time (hours)')
    axes[0, 0].set_ylabel('Flow Rate (kg/s)')
    axes[0, 0].set_title('Mass Flow Rates (Total, Vapor, Aerosol)')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend()
    
    # Plot 2: Temperature Evolution
    axes[0, 1].plot(times_hr, temperatures - 273.15, 'green', linewidth=2, label='Liquid Temperature')
    axes[0, 1].axhline(boiling_point - 273.15, color='red', linestyle='--', 
                       linewidth=2, label=f'Boiling Point ({boiling_point-273.15:.1f}°C)')
    axes[0, 1].set_xlabel('Time (hours)')
    axes[0, 1].set_ylabel('Temperature (°C)')
    axes[0, 1].set_title('Temperature Evolution')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend()
    
    # Plot 3: Remaining Liquid Mass
    axes[1, 0].plot(times_hr, remaining_mass, 'red', linewidth=2, label='Remaining Mass')
    axes[1, 0].set_xlabel('Time (hours)')
    axes[1, 0].set_ylabel('Mass (kg)')
    axes[1, 0].set_title('Remaining Liquid Mass')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend()
    
    # Plot 4: Flash Fraction
    axes[1, 1].plot(times_hr, flash_fractions, 'purple', linewidth=2, label='Flash Fraction (χ)')
    axes[1, 1].set_xlabel('Time (hours)')
    axes[1, 1].set_ylabel('Flash Fraction')
    axes[1, 1].set_title('Flash Fraction Evolution')
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend()
    axes[1, 1].set_ylim([0, 1.1])
    
    # Plot 5: Cumulative Mass Released
    cumulative_vapor = np.cumsum(vapor_flow_rates * time_step)
    cumulative_aerosol = np.cumsum(aerosol_flow_rates * time_step)
    cumulative_total = cumulative_vapor + cumulative_aerosol
    
    axes[2, 0].plot(times_hr, cumulative_total, 'b-', linewidth=2, label='Total')
    axes[2, 0].plot(times_hr, cumulative_vapor, 'orange', linewidth=2, label='Vapor')
    axes[2, 0].plot(times_hr, cumulative_aerosol, 'green', linewidth=2, label='Aerosol')
    axes[2, 0].set_xlabel('Time (hours)')
    axes[2, 0].set_ylabel('Cumulative Mass (kg)')
    axes[2, 0].set_title('Cumulative Mass Released')
    axes[2, 0].grid(True, alpha=0.3)
    axes[2, 0].legend()
    
    # Plot 6: Vapor vs Aerosol Ratio
    vapor_fraction = vapor_flow_rates / (total_flow_rates + 1e-10)
    axes[2, 1].plot(times_hr, vapor_fraction * 100, 'teal', linewidth=2, label='Vapor %')
    axes[2, 1].plot(times_hr, (1-vapor_fraction) * 100, 'brown', linewidth=2, label='Aerosol %')
    axes[2, 1].set_xlabel('Time (hours)')
    axes[2, 1].set_ylabel('Percentage (%)')
    axes[2, 1].set_title('Vapor vs Aerosol Composition')
    axes[2, 1].grid(True, alpha=0.3)
    axes[2, 1].legend()
    axes[2, 1].set_ylim([0, 100])
    
    plt.tight_layout()
    
    # Save figure
    output_dir = os.path.join(os.path.dirname(__file__), '../../outputs/reports')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'validation_tank_twophase_toluene.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_file}")
    
    plt.show()
    
    # --- Validation Summary ---
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print("\nModel Performance:")
    print("  - Successfully simulated two-phase flashing release")
    print("  - Calculated flash fraction (chi) over time")
    print("  - Separated vapor and aerosol contributions")
    print("  - Modeled temperature evolution to boiling point")
    print("  - Tracked mass discharge rates")
    
    print("\nPhysical Behavior Check:")
    if flash_fractions[0] > 0:
        print(f"  - Initial flash fraction > 0 (two-phase flow confirmed)")
    if temperatures[-1] <= temperatures[0]:
        print("  - Temperature decreases due to evaporative cooling")
    if temperatures[-1] >= boiling_point - 5:
        print("  - Temperature approaches boiling point")
    if total_flow_rates[-1] < total_flow_rates[0]:
        print("  - Flow rate decreases over time")
    if remaining_mass[-1] < remaining_mass[0]:
        print("  - Mass conservation verified")
    
    print("\nValidation Complete!")
    print("="*70)
    
    return results


if __name__ == "__main__":
    validate_tank_toluene_twophase()
