"""
Validation Script: Gaussian Dispersion Model
=============================================
Tests the pyELDQM Gaussian dispersion model against a standard ammonia release scenario.
Compares concentration contours and AEGL threshold distances.

"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pyeldqm.core.dispersion_models.gaussian_model import single_source_concentration
from pyeldqm.core.dispersion_models.dispersion_utils import get_sigmas
from pyeldqm.core.meteorology.stability import get_stability_class
from pyeldqm.core.meteorology.wind_profile import wind_speed as calc_wind_profile


def validate_gaussian_ammonia_release():
    """
    Validate Gaussian model with a continuous ammonia release.
    
    Scenario:
    - Chemical: Ammonia (NH3)
    - Release rate: 1000 g/s
    - Duration: 10 minutes
    - Wind speed: 5 m/s at 3m height
    - Source height: 3 m
    - Temperature: 35°C
    - Location: Pakistan (28°N, 70.1°E)
    
    Expected Results:
    - AEGL-1 (30 ppm): ~500-700 m
    - AEGL-2 (160 ppm): ~200-300 m
    - AEGL-3 (1100 ppm): ~50-100 m
    """
    
    print("="*70)
    print("VALIDATION: Gaussian Dispersion Model - Ammonia Release")
    print("="*70)
    
    # --- Input Parameters ---
    chemical_name = "Ammonia"
    MW = 17.03  # g/mol
    release_rate = 1000  # g/s
    release_duration = 600  # seconds (10 minutes)
    
    # Environmental conditions (match BaseCode)
    U = 5  # Wind speed (m/s)
    z0 = 1.5  # Reference height for wind profile (m)
    z_ref = 3  # Source height reference (m)
    h_s = 3  # Source height (m)
    n = 1  # Release duration multiplier
    temperature = 35 + 273.15  # K
    
    # Location and time
    datetime_obj = datetime(2025, 6, 25, 15, 0)
    latitude = 28.0
    longitude = 70.1
    cloudiness_index = 0
    timezone_offset_hrs = 5
    
    # --- Stability Class Calculation ---
    stability_class = get_stability_class(
        wind_speed=U,
        datetime_obj=datetime_obj,
        latitude=latitude,
        longitude=longitude,
        cloudiness_index=cloudiness_index,
        timezone_offset_hrs=timezone_offset_hrs
    )
    
    # Calculate t and t_r (match BaseCode)
    t_r = 60 * n  # Release duration (s)
    t = 60 * n  # Time after release (s)
    
    print(f"\nInput Parameters:")
    print(f"  Chemical: {chemical_name} (MW = {MW} g/mol)")
    print(f"  Release Rate: {release_rate} g/s")
    print(f"  Duration: {release_duration/60:.1f} minutes")
    print(f"  Wind Speed: {U} m/s at {z_ref} m")
    print(f"  Source Height: {h_s} m")
    print(f"  Temperature: {temperature-273.15:.1f} degC")
    print(f"  Stability Class: {stability_class}")
    print()
    
    # --- Calculate adjusted wind speed at source height ---
    U_local = calc_wind_profile(
        z_user=h_s,
        z0=z_ref,
        U_user=U,
        stability_class=stability_class
    )
    
    print(f"  Effective wind speed at {h_s}m: {U_local:.2f} m/s")
    
    # --- Create Grid ---
    x_max = 2000  # m
    y_max = 400  # m
    nx, ny = 200, 200
    
    x_vals = np.linspace(10, x_max, nx)
    y_vals = np.linspace(-y_max, y_max, ny)
    X, Y = np.meshgrid(x_vals, y_vals)
    
    # --- Calculate Concentrations ---
    print("Calculating concentration field...")
    C_grid = np.zeros_like(X)
    
    # Molar volume calculation (match BaseCode)
    R = 0.08206  # L·atm/(mol·K)
    Vm = R * temperature / 1.0  # L/mol at 1 atm
    
    for i in range(ny):
        for j in range(nx):
            x = X[i, j]
            y = Y[i, j]
            sig_x, sig_y, sig_z = get_sigmas(x, stability_class, 'RURAL')
            C_grid[i, j] = max([
                single_source_concentration(
                    x=x,
                    y=y,
                    z=z0,  # Use z0 as reference (roughness height, match BaseCode)
                    t=t,
                    t_r=t_r,
                    Q=release_rate,  # Use g/s (same as BaseCode)
                    U=U_local,
                    sigma_x=sig_x,
                    sigma_y=sig_y,
                    sigma_z=sig_z,
                    h_s=h_s,
                    mode='continuous'
                )
            ])
    
    # Convert to ppm (same method as BaseCode)
    C_ppm = C_grid * (Vm / MW) * 1000
    
    # --- Find AEGL Distances ---
    AEGL_THRESHOLDS = {
        "AEGL-1": 30,    # ppm
        "AEGL-2": 160,   # ppm
        "AEGL-3": 1100   # ppm
    }
    
    print("\n" + "-"*70)
    print("AEGL Threshold Distances (Centerline):")
    print("-"*70)
    
    centerline_ppm = C_ppm[ny // 2, :]  # centerline (y = 0)
    aegl_distances = {}
    
    for label, threshold in AEGL_THRESHOLDS.items():
        indices = np.where(centerline_ppm >= threshold)[0]
        if len(indices) > 0:
            distance = x_vals[indices[-1]]
            aegl_distances[label] = round(distance, 2)
            print(f"  {label} ({threshold:>4} ppm): {distance:>7.1f} meters")
        else:
            aegl_distances[label] = None
            print(f"  {label} ({threshold:>4} ppm): Not exceeded")
    
    print("-"*70)
    
    # --- Plotting ---
    print("\nGenerating plots...")
    
    # Plot 1: 2D Concentration Contours
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Contour plot with AEGL zones
    levels = [30, 160, 1100, 10000]
    colors = ['yellow', 'orange', 'red']
    
    cp = ax1.contourf(X, Y, C_ppm, levels=levels, colors=colors, extend='max')
    ax1.contour(X, Y, C_ppm, levels=[30], colors='black', linewidths=1.5)
    
    ax1.set_xlabel("Downwind Distance (m)", fontsize=11)
    ax1.set_ylabel("Crosswind Distance (m)", fontsize=11)
    ax1.set_title(f"Ammonia Dispersion - Stability Class {stability_class}", fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, x_max)
    ax1.set_ylim(-750, 750)
    
    cbar = plt.colorbar(cp, ax=ax1, label='Concentration (ppm)')
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', label='AEGL-3 (≥1100 ppm)'),
        Patch(facecolor='orange', label='AEGL-2 (≥160 ppm)'),
        Patch(facecolor='yellow', label='AEGL-1 (≥30 ppm)')
    ]
    ax1.legend(handles=legend_elements, loc='upper right')
    
    # Plot 2: Centerline Concentration Profile
    ax2.semilogy(x_vals, centerline_ppm, 'b-', linewidth=2, label='Centerline Concentration')
    
    # Add AEGL threshold lines
    for label, threshold in AEGL_THRESHOLDS.items():
        ax2.axhline(threshold, linestyle='--', linewidth=1.5, label=f'{label} ({threshold} ppm)')
    
    ax2.set_xlabel("Downwind Distance (m)", fontsize=11)
    ax2.set_ylabel("Concentration (ppm)", fontsize=11)
    ax2.set_title("Centerline Concentration Profile", fontsize=12)
    ax2.grid(True, alpha=0.3, which='both')
    ax2.legend()
    ax2.set_xlim(0, x_max)
    
    plt.tight_layout()
    
    # Save figure
    output_dir = os.path.join(os.path.dirname(__file__), '../../outputs/reports')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'validation_gaussian_ammonia.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_file}")
    
    plt.show()
    
    # --- Validation Summary ---
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print("\nModel Performance:")
    print("  - Successfully calculated concentration field")
    print("  - Generated AEGL threat zones")
    print("  - Produced visualization plots")
    print("\nExpected vs Actual AEGL Distances:")
    print("  AEGL-1 (30 ppm):   Expected ~500-700m,   Actual:", 
          f"{aegl_distances['AEGL-1']}m" if aegl_distances['AEGL-1'] else "Not exceeded")
    print("  AEGL-2 (160 ppm):  Expected ~200-300m,   Actual:", 
          f"{aegl_distances['AEGL-2']}m" if aegl_distances['AEGL-2'] else "Not exceeded")
    print("  AEGL-3 (1100 ppm): Expected ~50-100m,    Actual:", 
          f"{aegl_distances['AEGL-3']}m" if aegl_distances['AEGL-3'] else "Not exceeded")
    
    print("\nValidation Complete!")
    print("="*70)
    
    return aegl_distances


if __name__ == "__main__":
    validate_gaussian_ammonia_release()
