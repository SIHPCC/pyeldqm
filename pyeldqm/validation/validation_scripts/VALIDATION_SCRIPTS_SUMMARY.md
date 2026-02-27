# Validation Scripts Summary

## Overview
The pyELDQM package includes 7 comprehensive validation scripts that test all major components of the consequence modeling system. Each script provides ready-to-run validation tests with detailed outputs and visualizations.

## Validation Scripts

### 1. Gaussian Dispersion Model (`validate_gaussian_dispersion.py`)
**Purpose:** Validates passive plume dispersion for neutrally buoyant releases

**Test Scenario:**
- Chemical: Ammonia (NH3)
- Release: Continuous ground-level source
- Release rate: 1000 g/s
- Duration: 10 minutes
- Wind speed: 5 m/s at 10 m height
- Atmospheric stability: Automatically calculated from meteorological conditions

**Validation Checks:**
- AEGL threshold distance calculations
- Concentration decay with distance
- Plume spread with atmospheric stability
- Conservation of mass

**Outputs:**
- 2D concentration contour map
- Centerline concentration profile
- AEGL threshold distances (30, 160, 1100 ppm)
- Crosswind integrated concentration

---

### 2. Heavy Gas Dispersion Model (`validate_heavy_gas_dispersion.py`)
**Purpose:** Validates dense gas dispersion with gravity slumping

**Test Scenario:**
- Chemical: Chlorine (Cl2)
- Release: Ground-level continuous source
- Release rate: 2.0 kg/s
- Molecular weight: 70.9 g/mol (2.45× heavier than air)
- Stability class: D (neutral)
- Wind speed: 5 m/s

**Validation Checks:**
- Heavy gas behavior vs passive plume
- Cloud width and height evolution
- AEGL threat zone distances
- Gravitational slumping effects

**Outputs:**
- Threat zone footprint map
- Cloud evolution (width, height vs distance)
- Centerline concentration profile
- Heavy gas vs Gaussian comparison

---

### 3. Pipeline Gas Leak Model (`validate_pipeline_leak.py`)
**Purpose:** Validates pipeline depressurization and leak rates

**Test Scenario:**
- Chemical: Methane (CH4)
- Pipeline length: 10 km
- Initial pressure: 80 bar
- Initial temperature: 25°C
- Hole diameter: 10 cm
- Ambient pressure: 1.013 bar

**Validation Checks:**
- Wilson model implementation
- Joule-Thomson cooling
- Mass conservation
- Exponential pressure decay

**Outputs:**
- Flow rate evolution (Wilson and interface models)
- Pressure and temperature profiles
- Mass inventory tracking
- Depressurization time prediction

---

### 4. Tank Gas Release Model (`validate_tank_gas_release.py`)
**Purpose:** Validates pressurized gas tank discharge

**Test Scenario:**
- Chemical: Methane (CH4)
- Tank volume: 5 m³
- Initial mass: 50 kg
- Initial pressure: ~20 bar
- Hole diameter: 2 cm
- Discharge coefficient: 0.62

**Validation Checks:**
- Choked/unchoked flow transitions
- Adiabatic expansion cooling
- Pressure ratio evolution
- Critical flow conditions

**Outputs:**
- Flow rate vs time
- Pressure ratio and Mach number
- Temperature evolution
- Flow regime identification
- Mass remaining tracking

---

### 5. Tank Liquid Leak Model (`validate_tank_liquid_leak.py`)
**Purpose:** Validates liquid discharge and puddle formation

**Test Scenario:**
- Chemical: Toluene (C7H8)
- Tank volume: 10 m³
- Initial liquid volume: 7 m³
- Initial temperature: 37°C
- Hole area: 0.01 m²
- Tank geometry: Cylindrical

**Validation Checks:**
- Bernoulli discharge equation
- Liquid level decrease
- Puddle growth dynamics
- Heat transfer effects

**Outputs:**
- Discharge and evaporation rates
- Liquid level evolution
- Puddle radius and depth
- Temperature changes
- Mass distribution (tank, puddle, vapor)

---

### 6. Tank Two-Phase Leak Model (`validate_tank_twophase_leak.py`)
**Purpose:** Validates flashing releases and vapor/aerosol separation

**Test Scenario:**
- Chemical: Toluene (C7H8)
- Initial liquid mass: ~8,670 kg
- Tank volume: 20 m³
- Initial temperature: 400 K (127°C, above 110.6°C boiling point)
- Hole area: 0.00028 m²
- Two-phase flow regime

**Validation Checks:**
- Flash fraction calculation
- Energy balance (cooling from evaporation vs heat from tank walls)
- Vapor/aerosol mass flow rates
- Temperature evolution toward boiling point

**Outputs:**
- Total, vapor, and aerosol flow rates
- Flash fraction evolution
- Temperature profile (decreasing trend)
- Remaining liquid mass
- Cumulative vapor and aerosol release

---

### 7. Puddle Evaporation Model (`validate_puddle_evaporation.py`)
**Purpose:** Validates comprehensive energy balance for pool evaporation

**Test Scenario:**
- Chemical: Toluene (C7H8) - with database support for 10+ chemicals
- Puddle area: 0.657 m²
- Depth: 2.3 cm
- Initial temperature: 21.3°C
- Location: 40°N, 75°W
- Date/Time: September 17, 1984, 13:00 (daylight scenario)
- Weather: Clear sky, 50% humidity, 3.9 m/s wind

**Validation Checks:**
- Six energy flux components
- Net energy balance closure
- Solar position calculation
- Evaporation rate trends
- Temperature evolution
- Day/night cycle effects

**Outputs:**
- Solar insolation flux
- Longwave radiation (up and down)
- Sensible heat flux
- Evaporative flux
- Substrate heat flux
- Net energy flux
- Evaporation rate profiles
- Puddle temperature evolution
- Nighttime scenario comparison

**Key Features:**
- Chemical database: toluene, benzene, ammonia, chlorine, water, methanol, ethanol, acetone, propane, butane
- Custom Antoine coefficients support
- Multiple substrate types: default soil, dry sandy soil, moist sandy soil, concrete
- Atmospheric stability effects
- Mass transfer theory implementation

---

## Common Validation Structure

All validation scripts follow a consistent structure:

```python
def validate_[model]_[scenario]():
    # 1. Parameter Setup
    #    - Document all input parameters
    #    - Define scenario conditions
    
    # 2. Display Configuration
    #    - Print comprehensive input summary
    #    - Show all assumptions
    
    # 3. Run Simulation
    #    - Call pyELDQM model functions
    #    - Track execution progress
    
    # 4. Extract Results
    #    - Parse simulation outputs
    #    - Calculate derived quantities
    
    # 5. Validation Analysis
    #    - Check physical realism
    #    - Verify conservation laws
    #    - Compare with expected ranges
    
    # 6. Generate Plots
    #    - Create multiple visualizations
    #    - Save to outputs/reports/
    #    - Display to user
    
    # 7. Summary Report
    #    - Print validation statistics
    #    - Display key results
    #    - Report pass/fail status
    
    return results
```

## Output Files

All validation scripts save results to `pyELDQM/outputs/reports/`:

- `validation_gaussian_ammonia.png` - Gaussian dispersion results
- `validation_heavy_gas_chlorine.png` - Heavy gas footprint
- `validation_heavy_gas_cloud_evolution.png` - Cloud geometry evolution
- `validation_pipeline_methane_leak.png` - Pipeline leak analysis
- `validation_tank_gas_methane.png` - Tank gas release
- `validation_tank_gas_analysis.png` - Flow regime analysis
- `validation_tank_liquid_toluene.png` - Liquid discharge
- `validation_tank_twophase_toluene.png` - Two-phase release
- `validation_puddle_evaporation.png` - Energy flux components
- `validation_puddle_temperature.png` - Temperature evolution

## Validation Coverage

### Source Term Models
✓ Tank pressurized gas release (choked/unchoked flow)  
✓ Tank liquid discharge (Bernoulli equation)  
✓ Tank two-phase flashing release (flash fraction)  
✓ Pipeline gas leak (Wilson depressurization)  
✓ Puddle evaporation (energy balance)

### Dispersion Models
✓ Gaussian plume model (Pasquill-Gifford)  
✓ Heavy gas dispersion (Britter-McQuaid)

### Physical Processes
✓ Choked and unchoked flow transitions  
✓ Joule-Thomson cooling  
✓ Adiabatic expansion  
✓ Flash fraction calculation  
✓ Six-component energy balance  
✓ Heat transfer (convection, radiation, conduction)  
✓ Mass conservation  
✓ Wind profile effects  
✓ Atmospheric stability  
✓ Solar position calculation  
✓ Vapor pressure (Antoine equation)

### Consequence Metrics
✓ AEGL threshold distances (1, 2, 3)  
✓ Threat zone footprints  
✓ Time-to-depressurization  
✓ Evaporation rates  
✓ Temperature evolution  
✓ Mass release rates

## Usage

### Running Individual Tests

```bash
cd pyELDQM/validation/validation_scripts

# Run any validation script
python validate_gaussian_dispersion.py
python validate_heavy_gas_dispersion.py
python validate_pipeline_leak.py
python validate_tank_gas_release.py
python validate_tank_liquid_leak.py
python validate_tank_twophase_leak.py
python validate_puddle_evaporation.py
```

### Customizing Scenarios

Modify parameters directly in scripts:

```python
# Example: Change chemical in puddle evaporation
params['chemical'] = 'benzene'  # Instead of 'toluene'

# Example: Change wind speed in dispersion
wind_speed = 10.0  # m/s instead of 5.0

# Example: Change release rate
release_rate = 2000  # g/s instead of 1000
```

## Expected Results

When validation tests run successfully, you should see:

- Detailed input parameter summary
- Simulation progress indicators
- Physical validation checks passing
- Multiple plots generated and displayed
- Summary statistics and key results
- Output files saved to outputs/reports/

### Typical Console Output:
```
======================================================================
VALIDATION: [Model Name] - [Scenario]
======================================================================

Input Parameters:
  [Detailed parameter listing]

Running simulation...

======================================================================
   SIMULATION RESULTS
======================================================================

[Key validation metrics]
[Physical checks]
[Statistics]

Generating plots...
Plot saved to: outputs/reports/validation_*.png

======================================================================
VALIDATION COMPLETE
======================================================================
```

## Technical Details

### Numerical Methods
- **Time integration:** Explicit Euler method with adaptive time stepping
- **Spatial discretization:** Uniform or adaptive gridding
- **Convergence criteria:** Relative tolerance 1e-6

### Model Implementations
- **Gaussian:** Pasquill-Gifford dispersion coefficients
- **Heavy Gas:** Britter-McQuaid correlations with passive plume comparison
- **Wilson:** Isothermal depressurization with Joule-Thomson correction
- **Tank Gas:** Ideal gas law with real gas corrections
- **Tank Liquid:** Bernoulli discharge with level tracking
- **Two-Phase:** Energy balance flash fraction
- **Evaporation:** Mass transfer theory with vapor pressure

### Chemical Properties Database
Built-in support for:
- Toluene, Benzene (aromatics)
- Ammonia, Chlorine (hazardous gases)
- Methanol, Ethanol (alcohols)
- Propane, Butane (hydrocarbons)
- Acetone (ketones)
- Water (reference)

## Notes

### Script Features
Each validation script includes:
- Comprehensive input parameter documentation
- Physical validation and sanity checks
- Conservation law verification
- Multiple publication-quality plots
- Detailed console output with progress tracking
- Automatic file saving to outputs directory
- Summary statistics and key metrics
- Windows-compatible ASCII output (no encoding issues)

### Extensibility
The validation framework is designed for easy extension:
- Add new chemicals to the puddle evaporation database
- Modify scenarios by changing input parameters
- Create new validation scripts following the established template
- Compare results with other consequence modeling tools

### Quality Assurance
All scripts have been validated for:
- Numerical stability
- Physical realism
- Mass and energy conservation
- Agreement with industry-standard models
- Proper unit handling and conversions

## Future Enhancements

Potential additions to the validation suite:
- **Fire Models**: Pool fire, jet fire, flash fire validations
- **Explosion Models**: VCE, BLEVE, confined explosions
- **Multi-Phase Flow**: LNG, cryogenic releases
- **Complex Terrain**: Effects of buildings and topography
- **Time-Varying Conditions**: Changing meteorology and release rates
- **Uncertainty Analysis**: Monte Carlo and sensitivity studies

## Getting Help

For issues or questions:
1. Check the README.md in validation_scripts/
2. Review the docstrings in individual validation scripts
3. Examine console output for diagnostic messages
4. Verify input parameters are within valid ranges
5. Ensure all dependencies are installed (matplotlib, numpy, scipy)

## References

The validation scripts implement models documented in:
- **EPA**: Risk Management Program Guidance
- **CCPS**: Guidelines for Consequence Analysis
- **AIChE**: Emergency Relief System Design
- **TNO**: Methods for the Calculation of Possible Damage (Yellow Book)
- **HSE UK**: Failure Rate and Event Data (Purple Book)
- Academic journals on dispersion modeling and consequence analysis

1. **Independence**: Each script can run independently without dependencies on other scripts

2. **Extensibility**: Easy to add new validation tests by following the established template

3. **Documentation**: Each script includes:
   - Comprehensive docstrings
   - Inline explanatory comments
   - Detailed console output
   - Expected results and benchmarks

4. **Error Handling**: Robust error checking with meaningful diagnostic messages

5. **Flexibility**: Parameters can be easily modified to test different scenarios

6. **Professional Output**: 
   - Multi-panel plots with proper labels and legends
   - Industry-standard visualizations
   - Comprehensive statistical summaries
   - Automatic file saving

## Installation and Usage

### Install Dependencies
```bash
cd pyELDQM
pip install -r requirements.txt
```

### Run Individual Validations
```bash
cd pyELDQM/validation/validation_scripts

# Run any validation script
python validate_gaussian_dispersion.py
python validate_puddle_evaporation.py
# etc.
```

### Review Results
- Console output shows detailed validation results
- Plots are displayed and saved to `../../outputs/reports/`
- All tests include pass/fail indicators based on physical checks

### Customize Scenarios
- Open any validation script
- Modify parameters in the input section
- Re-run to see updated results
- Compare with baseline scenarios

## Development Notes

The validation scripts are designed following software engineering best practices:
- **Modular Design**: Each test is self-contained
- **Clear Structure**: Consistent organization across all scripts
- **Documentation**: Extensive comments and docstrings
- **Reproducibility**: Fixed random seeds where applicable
- **Maintainability**: Easy to update and extend
- **Cross-Platform**: Compatible with Windows, Linux, macOS
