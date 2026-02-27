"""
Health Impact Threshold Helper

Provides unified access to AEGL, ERPG, IDLH, and PAC thresholds for chemicals.
Automatically retrieves threshold values from the chemical database.
"""
from typing import Dict, Optional, Any
import warnings
from .chemical_database import ChemicalDatabase


def _parse_ppm(value) -> Optional[float]:
    """
    Parse a threshold value that may be stored as a bare number or a string
    with a units suffix such as '30 ppm', '300 PPM', etc.

    Returns a float, or None if the value is None / unparseable.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    # Strip common unit suffixes and whitespace then try conversion
    cleaned = str(value).strip().lower()
    for suffix in (' ppm', 'ppm', ' mg/m3', 'mg/m3', ' mg/l', 'mg/l'):
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)].strip()
            break
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def get_aegl_thresholds(
    chemical_name: str,
    duration_min: int = 60
) -> Dict[str, Optional[float]]:
    """
    Get AEGL thresholds for a chemical.
    
    AEGL (Acute Exposure Guideline Levels):
    - AEGL-1: Discomfort, not disabling
    - AEGL-2: Irreversible or serious, long-lasting effects
    - AEGL-3: Life-threatening health effects or death
    
    Parameters:
    -----------
    chemical_name : str
        Name of chemical
    duration_min : int
        Exposure duration in minutes (default 60)
    
    Returns:
    --------
    dict : {'AEGL-1': value, 'AEGL-2': value, 'AEGL-3': value} in ppm
    """
    with ChemicalDatabase() as db:
        chem = db.get_chemical_by_name(chemical_name)
        
        if not chem:
            warnings.warn(f"Chemical '{chemical_name}' not found in database")
            return {"AEGL-1": None, "AEGL-2": None, "AEGL-3": None}
        
        # Currently database has 60-min values; could extend for other durations
        return {
            "AEGL-1": _parse_ppm(chem.get('aegl1_60min')),
            "AEGL-2": _parse_ppm(chem.get('aegl2_60min')),
            "AEGL-3": _parse_ppm(chem.get('aegl3_60min'))
        }


def get_erpg_thresholds(chemical_name: str) -> Dict[str, Optional[float]]:
    """
    Get ERPG thresholds for a chemical.
    
    ERPG (Emergency Response Planning Guidelines):
    - ERPG-1: Maximum airborne concentration below which nearly all individuals
              could be exposed for up to 1 hour without experiencing other than
              mild transient adverse health effects or perceiving a clearly defined
              objectionable odor.
    - ERPG-2: Maximum airborne concentration below which nearly all individuals
              could be exposed for up to 1 hour without experiencing or developing
              irreversible or other serious health effects that could impair their
              abilities to take protective action.
    - ERPG-3: Maximum airborne concentration below which nearly all individuals
              could be exposed for up to 1 hour without experiencing or developing
              life-threatening health effects.
    
    Parameters:
    -----------
    chemical_name : str
        Name of chemical
    
    Returns:
    --------
    dict : {'ERPG-1': value, 'ERPG-2': value, 'ERPG-3': value} in ppm
    """
    with ChemicalDatabase() as db:
        chem = db.get_chemical_by_name(chemical_name)
        
        if not chem:
            warnings.warn(f"Chemical '{chemical_name}' not found in database")
            return {"ERPG-1": None, "ERPG-2": None, "ERPG-3": None}
        
        return {
            "ERPG-1": _parse_ppm(chem.get('erpg1')),
            "ERPG-2": _parse_ppm(chem.get('erpg2')),
            "ERPG-3": _parse_ppm(chem.get('erpg3'))
        }


def get_idlh_threshold(chemical_name: str) -> Optional[float]:
    """
    Get IDLH threshold for a chemical.
    
    IDLH (Immediately Dangerous to Life or Health):
    Maximum concentration from which one could escape within 30 minutes
    without any escape-impairing symptoms or irreversible health effects.
    
    Used by NIOSH for respirator selection.
    
    Parameters:
    -----------
    chemical_name : str
        Name of chemical
    
    Returns:
    --------
    float or None : IDLH value in ppm
    """
    with ChemicalDatabase() as db:
        chem = db.get_chemical_by_name(chemical_name)
        
        if not chem:
            warnings.warn(f"Chemical '{chemical_name}' not found in database")
            return None
        
        return _parse_ppm(chem.get('idlh'))


def get_pac_thresholds(chemical_name: str) -> Dict[str, Optional[float]]:
    """
    Get PAC thresholds for a chemical.
    
    PAC (Protective Action Criteria):
    Developed by DOE for emergency planning.
    - PAC-1: Mild, transient health effects
    - PAC-2: Irreversible or serious health effects
    - PAC-3: Life-threatening health effects
    
    Parameters:
    -----------
    chemical_name : str
        Name of chemical
    
    Returns:
    --------
    dict : {'PAC-1': value, 'PAC-2': value, 'PAC-3': value} in ppm
    """
    with ChemicalDatabase() as db:
        chem = db.get_chemical_by_name(chemical_name)
        
        if not chem:
            warnings.warn(f"Chemical '{chemical_name}' not found in database")
            return {"PAC-1": None, "PAC-2": None, "PAC-3": None}
        
        return {
            "PAC-1": _parse_ppm(chem.get('pac1')),
            "PAC-2": _parse_ppm(chem.get('pac2')),
            "PAC-3": _parse_ppm(chem.get('pac3'))
        }


def get_all_thresholds(chemical_name: str) -> Dict[str, Any]:
    """
    Get all available health thresholds for a chemical.
    
    Parameters:
    -----------
    chemical_name : str
        Name of chemical
    
    Returns:
    --------
    dict : All threshold values organized by type
    """
    aegl = get_aegl_thresholds(chemical_name)
    erpg = get_erpg_thresholds(chemical_name)
    pac = get_pac_thresholds(chemical_name)
    idlh = get_idlh_threshold(chemical_name)
    
    return {
        "chemical": chemical_name,
        "AEGL": aegl,
        "ERPG": erpg,
        "PAC": pac,
        "IDLH": idlh
    }


def recommend_threshold_type(
    chemical_name: str,
    preference_order: list = None
) -> Dict[str, Optional[float]]:
    """
    Recommend best available threshold type for a chemical.
    
    Tries to find thresholds in order of preference.
    Default order: AEGL > ERPG > PAC
    
    Parameters:
    -----------
    chemical_name : str
        Name of chemical
    preference_order : list, optional
        Order of preference ['AEGL', 'ERPG', 'PAC']
    
    Returns:
    --------
    dict : Best available thresholds with metadata
    """
    if preference_order is None:
        preference_order = ['AEGL', 'ERPG', 'PAC']
    
    all_thresh = get_all_thresholds(chemical_name)
    
    for threshold_type in preference_order:
        if threshold_type in all_thresh:
            thresholds = all_thresh[threshold_type]
            # Check if at least one level has data
            if any(v is not None for v in thresholds.values()):
                return {
                    "type": threshold_type,
                    "thresholds": thresholds,
                    "chemical": chemical_name
                }
    
    # No thresholds found
    warnings.warn(f"No thresholds found for '{chemical_name}'")
    return {
        "type": None,
        "thresholds": {},
        "chemical": chemical_name
    }


def display_thresholds(chemical_name: str):
    """Print formatted table of all thresholds for a chemical."""
    all_thresh = get_all_thresholds(chemical_name)
    
    print(f"\n{'='*80}")
    print(f"Health Impact Thresholds: {chemical_name.upper()}")
    print(f"{'='*80}\n")
    
    # AEGL
    print("📊 AEGL (Acute Exposure Guideline Levels) - 60 min:")
    aegl = all_thresh['AEGL']
    print(f"  Level 1 (Discomfort):           {aegl['AEGL-1'] or 'N/A'} ppm")
    print(f"  Level 2 (Irreversible effects): {aegl['AEGL-2'] or 'N/A'} ppm")
    print(f"  Level 3 (Life-threatening):     {aegl['AEGL-3'] or 'N/A'} ppm\n")
    
    # ERPG
    print("📊 ERPG (Emergency Response Planning Guidelines) - 1 hour:")
    erpg = all_thresh['ERPG']
    print(f"  Level 1 (Mild effects):         {erpg['ERPG-1'] or 'N/A'} ppm")
    print(f"  Level 2 (Serious effects):      {erpg['ERPG-2'] or 'N/A'} ppm")
    print(f"  Level 3 (Life-threatening):     {erpg['ERPG-3'] or 'N/A'} ppm\n")
    
    # PAC
    print("📊 PAC (Protective Action Criteria):")
    pac = all_thresh['PAC']
    print(f"  Level 1 (Mild effects):         {pac['PAC-1'] or 'N/A'} ppm")
    print(f"  Level 2 (Irreversible effects): {pac['PAC-2'] or 'N/A'} ppm")
    print(f"  Level 3 (Life-threatening):     {pac['PAC-3'] or 'N/A'} ppm\n")
    
    # IDLH
    print("📊 IDLH (Immediately Dangerous to Life or Health) - 30 min escape:")
    print(f"  IDLH:                           {all_thresh['IDLH'] or 'N/A'} ppm\n")
    
    print(f"{'='*80}\n")


# Example usage
if __name__ == "__main__":
    # Display thresholds for common chemicals
    for chemical in ["AMMONIA", "CHLORINE", "HYDROGEN SULFIDE"]:
        display_thresholds(chemical)
    
    # Get specific threshold types
    print("\n" + "="*80)
    print("Recommended Threshold Selection")
    print("="*80)
    
    rec = recommend_threshold_type("AMMONIA")
    print(f"\nAMMONIA - Using {rec['type']} thresholds:")
    for level, value in rec['thresholds'].items():
        print(f"  {level}: {value} ppm")
