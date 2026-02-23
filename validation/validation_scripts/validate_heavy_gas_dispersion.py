"""
Validation Script: Heavy Gas Dispersion Model
==============================================
Tests the pyELDQM heavy gas dispersion model with chlorine release scenario.
Compares AEGL threat zone distances with ALOHA-style predictions.

"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.dispersion_models.heavy_gas_model import (
    run_heavy_gas_model,
    calc_Sy_passive,
    HEAVY_GAS_PARAMS,
    MW_AIR,
    MW_GAS
)


def validate_heavy_gas_chlorine_release():
    """
    Validate heavy gas dispersion model with chlorine release.
    
    Scenario:
    - Chemical: Chlorine (Cl2)
    - Release rate: 2.0 kg/s
    - Source type: Continuous ground-level release
    - Wind speed: 5.0 m/s at 3m height
    - Stability class: D (neutral)
    - Surface roughness: 0.03 m (rural)
    
    Expected Results (ALOHA-style):
    - AEGL-3 (20 ppm): ~2-3 miles
    - AEGL-2 (2 ppm): ~5-7 miles
    - AEGL-1 (0.5 ppm): ~8-10 miles
    """
    
    print("="*70)
    print("VALIDATION: Heavy Gas Dispersion Model - Chlorine Release")
    print("="*70)
    
    # --- Input Parameters ---
    chemical_name = "Chlorine"
    MW_gas = 70.91  # g/mol
    MW_air = 28.97  # g/mol
    release_rate = 2.0  # kg/s
    initial_temperature = 239.15  # K (cold release)
    
    # Meteorological conditions
    wind_speed = 5.0  # m/s
    wind_height = 3.0  # m
    stability_class = 'D'
    surface_roughness = 0.03  # m
    ambient_temperature = 298.15  # K
    
    # Source configuration
    source_config = {
        'type': 'continuous',
        'dims': {'diameter': 0.1}
    }
    
    print(f"\nInput Parameters:")
    print(f"  Chemical: {chemical_name} (MW = {MW_gas} g/mol)")
    print(f"  Release Rate: {release_rate} kg/s")
    print(f"  Initial Temperature: {initial_temperature} K")
    print(f"  Wind Speed: {wind_speed} m/s at {wind_height} m")
    print(f"  Stability Class: {stability_class}")
    print(f"  Ambient Temperature: {ambient_temperature} K")
    print()
    
    # --- Run Dispersion Model ---
    print("Running heavy gas dispersion calculations...")
    sol, n, gamma_val, U_ref, z_ref = run_heavy_gas_model(
        stability_class, release_rate, wind_speed, wind_height, surface_roughness, source_config
    )
    
    # --- Extract Results ---
    x_dist = sol.t  # meters
    cloud_width = sol.y[1]  # Beff (cloud half-width)
    cloud_height = sol.y[0]  # Sz (cloud height)
    
    # Calculate centerline concentration
    params = HEAVY_GAS_PARAMS[stability_class]
    centerline_ppm = []
    
    for i, x in enumerate(x_dist):
        Sz = sol.y[0][i]
        Beff = sol.y[1][i]
        Tc = sol.y[2][i]
        Flux = sol.y[3][i]
        
        Heff = (Sz / (1.0 + n)) * gamma_val
        U_eff = (U_ref / gamma_val) * ((Sz / z_ref)**n)
        
        w_c = release_rate / Flux
        if w_c > 1.0: w_c = 1.0
        inv_MW_mix = (w_c / MW_GAS) + ((1 - w_c) / MW_AIR)
        MW_mix = 1.0 / inv_MW_mix
        
        from core.dispersion_models.heavy_gas_model import calc_rho
        rho_mix = calc_rho(Tc, MW_mix)
        
        conc_kgm3 = release_rate / (2 * Beff * Heff * U_eff)
        ppm = (conc_kgm3 / rho_mix) * (MW_AIR / MW_GAS) * 1e6
        centerline_ppm.append(ppm)
    
    centerline_ppm = np.array(centerline_ppm)
    
    # --- AEGL Limits for Chlorine ---
    METERS_TO_MILES = 0.000621371
    AEGL_LIMITS = {
        'AEGL-3': 20,   # ppm
        'AEGL-2': 2,    # ppm
        'AEGL-1': 0.5   # ppm
    }
    
    # --- Calculate Threat Zone Distances ---
    print("\n" + "="*70)
    print("   THREAT ZONE DISTANCES (ALOHA-Style)")
    print("="*70)
    print(f"Chemical: {chemical_name} (MW: {MW_gas})")
    print(f"Wind: {wind_speed} m/s | Stability: {stability_class}")
    print("-" * 70)
    
    zone_distances = {}
    for name, limit in AEGL_LIMITS.items():
        indices = np.where(centerline_ppm > limit)[0]
        if len(indices) > 0:
            max_idx = indices[-1]
            dist_meters = x_dist[max_idx]
            dist_miles = dist_meters * METERS_TO_MILES
            zone_distances[name] = dist_meters
            print(f"{name} ({limit:>4} ppm) : {dist_miles:.2f} miles ({dist_meters:.0f} m)")
        else:
            zone_distances[name] = 0
            print(f"{name} ({limit:>4} ppm) : < 10 meters")
    
    print("="*70 + "\n")
    
    # --- Create 2D Footprint Plot ---
    print("Generating 2D footprint plot...")
    
    # Create grid for plotting
    y_max_plot = 3000  # meters
    y_line = np.linspace(-y_max_plot, y_max_plot, 500)
    X_grid, Y_grid = np.meshgrid(x_dist, y_line)
    Z_grid = np.zeros_like(X_grid)
    
    # Populate concentration grid
    for i, x in enumerate(x_dist):
        ppm_center = centerline_ppm[i]
        width = cloud_width[i]
        
        for j, y in enumerate(y_line):
            abs_y = abs(y)
            if width > 0:
                # Gaussian lateral profile
                Z_grid[j, i] = ppm_center * np.exp(-0.5 * (abs_y / width)**2)
            else:
                Z_grid[j, i] = ppm_center if abs_y == 0 else 0
    
    # --- Convert to miles for plotting ---
    X_grid_miles = X_grid * METERS_TO_MILES
    Y_grid_miles = Y_grid * METERS_TO_MILES
    
    # --- Create Figure ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: 2D Contour Map (ALOHA-style)
    levels = [0.5, 2, 20, 1000000]
    colors = ['yellow', 'orange', 'red']
    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(levels, cmap.N)
    
    contour = ax1.contourf(X_grid_miles, Y_grid_miles, Z_grid, 
                           levels=levels, cmap=cmap, norm=norm, extend='max')
    
    # Legend patches
    red_patch = mpatches.Patch(color='red', label='AEGL-3 (≥ 20 ppm)')
    org_patch = mpatches.Patch(color='orange', label='AEGL-2 (≥ 2 ppm)')
    yel_patch = mpatches.Patch(color='yellow', label='AEGL-1 (≥ 0.5 ppm)')
    
    # Format axes
    def abs_formatter(x, pos):
        return f"{abs(x):.1f}"
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(abs_formatter))
    
    ax1.axhline(0, color='black', linestyle='--', alpha=0.3)
    ax1.set_title(f"ALOHA Threat Zone Estimate\n{release_rate} kg/s {chemical_name} | Wind: {wind_speed} m/s | Class: {stability_class}")
    ax1.set_xlabel("miles")
    ax1.set_ylabel("miles")
    ax1.set_ylim(-3.0, 3.0)
    ax1.set_xlim(0, 10.0)
    ax1.legend(handles=[red_patch, org_patch, yel_patch], loc='upper right')
    ax1.grid(True, linestyle='-', alpha=0.5, color='black')
    
    # Plot 2: Centerline Concentration Profile
    ax2.semilogy(x_dist * METERS_TO_MILES, centerline_ppm, 'b-', linewidth=2, label='Centerline Concentration')
    
    # Add AEGL threshold lines
    for label, threshold in AEGL_LIMITS.items():
        ax2.axhline(threshold, linestyle='--', linewidth=1.5, label=f'{label} ({threshold} ppm)')
    
    ax2.set_xlabel("Downwind Distance (miles)", fontsize=11)
    ax2.set_ylabel("Concentration (ppm)", fontsize=11)
    ax2.set_title("Centerline Concentration vs Distance", fontsize=12)
    ax2.grid(True, alpha=0.3, which='both')
    ax2.legend()
    ax2.set_xlim(0, 10)
    
    plt.tight_layout()
    
    # Save figure
    output_dir = os.path.join(os.path.dirname(__file__), '../../outputs/reports')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'validation_heavy_gas_chlorine.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_file}")
    
    plt.show()
    
    # --- Create Cloud Evolution Plots ---
    print("\nGenerating cloud evolution plots...")
    
    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Cloud width evolution
    ax3.plot(x_dist * METERS_TO_MILES, cloud_width, 'g-', linewidth=2)
    ax3.set_xlabel("Downwind Distance (miles)")
    ax3.set_ylabel("Cloud Half-Width (m)")
    ax3.set_title("Cloud Lateral Spreading")
    ax3.grid(True, alpha=0.3)
    
    # Cloud height evolution
    ax4.plot(x_dist * METERS_TO_MILES, cloud_height, 'r-', linewidth=2)
    ax4.set_xlabel("Downwind Distance (miles)")
    ax4.set_ylabel("Cloud Height (m)")
    ax4.set_title("Cloud Vertical Growth")
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_file2 = os.path.join(output_dir, 'validation_heavy_gas_cloud_evolution.png')
    plt.savefig(output_file2, dpi=150, bbox_inches='tight')
    print(f"Cloud evolution plot saved to: {output_file2}")
    
    plt.show()
    
    # --- Validation Summary ---
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print("\nModel Performance:")
    print("  ✓ Successfully simulated heavy gas dispersion")
    print("  ✓ Generated AEGL threat zones")
    print("  ✓ Produced ALOHA-style visualizations")
    print("  ✓ Calculated cloud evolution parameters")
    
    print("\nExpected vs Actual AEGL Distances:")
    print("  AEGL-1 (0.5 ppm):  Expected ~8-10 miles,  Actual:", 
          f"{zone_distances['AEGL-1']*METERS_TO_MILES:.2f} miles" if zone_distances['AEGL-1'] > 0 else "Not exceeded")
    print("  AEGL-2 (2 ppm):    Expected ~5-7 miles,   Actual:", 
          f"{zone_distances['AEGL-2']*METERS_TO_MILES:.2f} miles" if zone_distances['AEGL-2'] > 0 else "Not exceeded")
    print("  AEGL-3 (20 ppm):   Expected ~2-3 miles,   Actual:", 
          f"{zone_distances['AEGL-3']*METERS_TO_MILES:.2f} miles" if zone_distances['AEGL-3'] > 0 else "Not exceeded")
    
    print("\n✓ Validation Complete!")
    print("="*70)
    
    return zone_distances


if __name__ == "__main__":
    validate_heavy_gas_chlorine_release()
