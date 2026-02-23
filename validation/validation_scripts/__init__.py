"""
pyELDQM Validation Scripts Package
===================================

This package contains comprehensive validation scripts for testing pyELDQM
consequence modeling capabilities against industry-standard scenarios.

Available validation modules:
- validate_gaussian_dispersion: Gaussian plume model validation
- validate_heavy_gas_dispersion: Heavy gas dispersion model validation
- validate_pipeline_leak: Pipeline gas leak model validation
- validate_tank_gas_release: Tank gas release model validation
- validate_tank_liquid_leak: Tank liquid leak model validation
- validate_tank_twophase_leak: Tank two-phase leak model validation
- validate_puddle_evaporation: Puddle evaporation model validation

Usage:
    # Run individual validation script
    python validate_gaussian_dispersion.py
    
    # Or import and run programmatically
    from validation_scripts import validate_gaussian_dispersion
    validate_gaussian_dispersion.validate_gaussian_ammonia_release()
    
Each validation script is independent and can be run standalone.
"""

__version__ = "1.0.0"
__author__ = "pyELDQM Development Team"

# Import validation functions for easier access
try:
    from . import validate_gaussian_dispersion
    from . import validate_heavy_gas_dispersion
    from . import validate_pipeline_leak
    from . import validate_tank_gas_release
    from . import validate_tank_liquid_leak
    from . import validate_tank_twophase_leak
    from . import validate_puddle_evaporation
    
    __all__ = [
        'validate_gaussian_dispersion',
        'validate_heavy_gas_dispersion',
        'validate_pipeline_leak',
        'validate_tank_gas_release',
        'validate_tank_liquid_leak',
        'validate_tank_twophase_leak',
        'validate_puddle_evaporation',
    ]
except ImportError:
    # Allow running scripts directly without package structure
    pass
