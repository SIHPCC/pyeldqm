# pyELDQM Validation Scripts

This directory contains comprehensive validation scripts for testing the pyELDQM package against known scenarios and industry-standard benchmarks.

## Overview

The validation suite includes seven independent scripts that test all major components of pyELDQM:

1. **Gaussian Dispersion Model** - Ammonia release scenario with AEGL threshold distances
2. **Heavy Gas Dispersion Model** - Chlorine release with industry-standard threat zones
3. **Pipeline Gas Leak** - Methane pipeline depressurization (Wilson model)
4. **Tank Gas Release** - Pressurized methane storage tank leak
5. **Tank Liquid Leak** - Toluene liquid discharge and puddle formation
6. **Tank Two-Phase Leak** - Flashing toluene release with vapor/aerosol separation
7. **Puddle Evaporation** - Multi-component energy balance model for pool evaporation

## Quick Start

### Run Individual Validation Tests

Each validation script is independent and can be run directly:

```bash
cd pyELDQM/validation/validation_scripts

# Gaussian dispersion
python validate_gaussian_dispersion.py

# Heavy gas dispersion
python validate_heavy_gas_dispersion.py

# Pipeline leak
python validate_pipeline_leak.py

# Tank gas release
python validate_tank_gas_release.py

# Tank liquid leak
python validate_tank_liquid_leak.py

# Tank two-phase leak
python validate_tank_twophase_leak.py

# Puddle evaporation
python validate_puddle_evaporation.py
```

All plots are automatically saved to `../../outputs/reports/` directory.

## Validation Scripts Details

### 1. Gaussian Dispersion (`validate_gaussian_dispersion.py`)

**Scenario:** Continuous ammonia release at ground level
- Chemical: Ammonia (NH3)
- Release rate: 1000 g/s
- Duration: 10 minutes
- Wind speed: 5 m/s
- Stability class: Automatically calculated

**Expected Results:**
- AEGL-1 (30 ppm): ~500-700 m
- AEGL-2 (160 ppm): ~200-300 m
- AEGL-3 (1100 ppm): ~50-100 m

**Outputs:**
- 2D concentration contour map
- Centerline concentration profile
- AEGL threshold distances

---

### 2. Heavy Gas Dispersion (`validate_heavy_gas_dispersion.py`)

**Scenario:** Dense chlorine gas release
- Chemical: Chlorine (Cl2)
- Release rate: 2.0 kg/s
- Source: Ground-level continuous
- Stability class: D (neutral)
- Wind speed: 5 m/s

**Expected Results:**
- AEGL-3 (20 ppm): ~2-3 km
- AEGL-2 (2 ppm): ~5-7 km  
- AEGL-1 (0.5 ppm): ~8-10 km
- Heavy gas behavior with gravitational slumping

**Outputs:**
- Threat zone footprint map
- Cloud evolution plots (width, height)
- Centerline concentration profile
- Comparison with passive plume model

---

### 3. Pipeline Gas Leak (`validate_pipeline_leak.py`)

**Scenario:** Pressurized methane pipeline rupture
- Chemical: Methane (CH4)
- Pipeline pressure: 5 MPa
- Pipeline: 200 m long, 0.1 m diameter
- Hole diameter: 6 mm

**Expected Results:**
- Exponential flow rate decay (Wilson model)
- Temperature drop due to Joule-Thomson effect
- Complete depressurization in ~30-60 minutes

**Outputs:**
- Flow rate evolution (Wilson and interface models)
- Temperature and pressure profiles
- Mass inventory tracking

---

### 4. Tank Gas Release (`validate_tank_gas_release.py`)

**Scenario:** Pressurized methane storage tank leak
- Chemical: Methane (CH4)
- Tank volume: 5 m³
- Initial mass: 50 kg
- Hole diameter: 2 cm

**Expected Results:**
- Choked/unchoked flow transitions
- Adiabatic temperature decrease
- Tank depressurization

**Outputs:**
- Flow rate vs time
- Pressure ratio evolution
- Temperature changes
- Flow regime identification

---

### 5. Tank Liquid Leak (`validate_tank_liquid_leak.py`)

**Scenario:** Toluene liquid discharge from storage tank
- Chemical: Toluene (C7H8)
- Initial volume: 7 m³
- Hole area: 0.01 m²
- Initial temperature: 37°C

**Expected Results:**
- Flow rate decreases as liquid level drops
- Puddle formation and growth
- Heat transfer effects

**Outputs:**
- Discharge and evaporation rates
- Liquid level evolution
- Puddle radius growth
- Temperature changes

---

### 6. Tank Two-Phase Leak (`validate_tank_twophase_leak.py`)

**Scenario:** Superheated toluene flashing release
- Chemical: Toluene (C7H8)
- Initial temperature: 127°C (above boiling point)
- Initial mass: ~8,670 kg
- Two-phase flow regime

**Expected Results:**
- Flash fraction > 0
- Vapor and aerosol generation
- Temperature decreases to boiling point

**Outputs:**
- Vapor/aerosol flow rates
- Flash fraction evolution
- Temperature profile
- Cumulative mass released

---

### 7. Puddle Evaporation (`validate_puddle_evaporation.py`)

**Scenario:** Toluene puddle evaporation with full energy balance
- Chemical: Toluene (C7H8) - configurable for 10+ chemicals
- Puddle area: 0.657 m²
- Depth: 2.3 cm
- Initial temperature: 21.3°C
- Location: 40°N, 75°W (September 17, 1984, 13:00)
- Weather: Clear sky, 3.9 m/s wind

**Expected Results:**
- Evaporation rate: 3-5 kg/(m²·hr)
- Temperature increase from solar heating
- Energy balance closure (all flux components)
- Daylight vs nighttime behavior differences

**Outputs:**
- Six energy flux components (solar, longwave up/down, sensible, evaporative, substrate)
- Net energy flux evolution
- Evaporation rate profiles
- Temperature evolution
- Nighttime scenario comparison

**Key Features:**
- Database of 10 common chemicals (toluene, benzene, ammonia, chlorine, etc.)
- Custom Antoine coefficients support
- Solar position calculation
- Atmospheric stability effects
- Multiple substrate types (soil, concrete, water)

---

## Understanding Validation Results

### Success Criteria

Each validation script verifies:
1. **Physical Realism** - Results follow expected physical trends
2. **Conservation Laws** - Mass and energy are conserved
3. **Benchmark Ranges** - Results align with industry-standard expectations
4. **Numerical Stability** - No discontinuities or unrealistic spikes
5. **Model Physics** - Correct implementation of governing equations

### Output Files

All validation results are saved to `../../outputs/reports/`:
- `validation_gaussian_ammonia.png`
- `validation_heavy_gas_chlorine.png`
- `validation_heavy_gas_cloud_evolution.png`
- `validation_pipeline_methane_leak.png`
- `validation_tank_gas_methane.png`
- `validation_tank_gas_analysis.png`
- `validation_tank_liquid_toluene.png`
- `validation_tank_twophase_toluene.png`
- `validation_puddle_evaporation.png`
- `validation_puddle_temperature.png`

### Interpreting Plots

- **Contour Maps**: Show spatial distribution of concentrations and threat zones
- **Time Series**: Track evolution of flow rates, temperatures, and pressures
- **Profiles**: Display centerline concentrations and downwind distances
- **Energy Balance**: Verify heat flux components sum to net flux
- **Comparison Plots**: Show model variations or scenario comparisons

## Troubleshooting

### Common Issues

**Import Errors:**
```
ModuleNotFoundError: No module named 'core'
```
→ Ensure you're running from the validation_scripts directory or pyELDQM root

**Missing Dependencies:**
```
No module named 'matplotlib'
```
→ Install required packages: `pip install -r requirements.txt`

**Encoding Errors (Windows):**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```
→ All scripts now use ASCII-safe output for Windows compatibility

**Plot Display:**
- Plots are displayed during execution and automatically saved
- Close plot windows to continue to next validation step

## Customizing Validations

Modify any validation script to test different scenarios:

1. Open the validation script (e.g., `validate_puddle_evaporation.py`)
2. Change parameters in the input section
3. Run the script to see updated results

Example modifications:
```python
# Change chemical (puddle evaporation)
params['chemical'] = 'benzene'  # or 'ammonia', 'chlorine', etc.

# Change wind speed (dispersion models)
wind_speed = 10.0  # m/s

# Change release rate (source models)
release_rate = 2000  # g/s

# Change atmospheric stability
stability_class = 'F'  # Very stable conditions
```

## Validation Script Features

### Common Features Across All Scripts:
- ✓ Comprehensive parameter documentation
- ✓ Physical validation checks
- ✓ Multiple visualization plots
- ✓ Console progress reporting
- ✓ Automatic file saving
- ✓ Summary statistics
- ✓ Unit conversions
- ✓ Error handling

### Model-Specific Validations:

**Source Models:**
- Mass conservation verification
- Energy balance closure
- Flow regime identification
- Temperature/pressure tracking

**Dispersion Models:**
- AEGL threshold distances
- Threat zone calculations
- Centerline concentration profiles
- Atmospheric stability effects

**Puddle Evaporation:**
- Six energy flux components
- Vapor pressure calculations
- Chemical database support
- Diurnal cycle effects

## Technical Notes

### Numerical Methods:
- Time integration: Explicit Euler method
- Spatial resolution: Adaptive gridding
- Convergence criteria: Relative tolerance 1e-6

### Physical Models:
- **Gaussian Model**: Pasquill-Gifford dispersion parameters
- **Heavy Gas**: Britter-McQuaid correlations
- **Pipeline**: Wilson depressurization model
- **Tank Gas**: Ideal gas with real gas corrections
- **Tank Liquid**: Bernoulli discharge equation
- **Two-Phase**: Flash fraction from energy balance
- **Evaporation**: Mass transfer theory with Antoine equation

## References

These validation scripts implement models based on:
- **EPA Guidelines**: Consequence modeling for chemical releases
- **CCPS Guidelines**: Center for Chemical Process Safety methodologies
- **AIChE Standards**: American Institute of Chemical Engineers
- **Academic Literature**: Peer-reviewed dispersion and source term papers
- **Industry Tools**: Validation against ALOHA, PHAST, SAFETI methodologies
