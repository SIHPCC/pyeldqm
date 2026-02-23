"""
Chemical phase/state utilities.

Provides a conservative gas-phase check based on temperature and available
boiling/freezing point data from the chemical database.
"""

from __future__ import annotations

from typing import Optional, Dict, Any

from ..chemical_database import ChemicalDatabase


def _f_to_c(temp_f: Optional[float]) -> Optional[float]:
    if temp_f is None:
        return None
    try:
        return (float(temp_f) - 32.0) * 5.0 / 9.0
    except (TypeError, ValueError):
        return None


def determine_phase(chemical_name: str, temperature_c: float, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Determine the phase of a chemical at the given temperature (C).

    Returns a dict with keys: phase, is_gas, reason, boiling_c, freezing_c.
    """
    with ChemicalDatabase(db_path) as db:
        chem = db.get_chemical_by_name(chemical_name)

    if not chem:
        return {
            "phase": "unknown",
            "is_gas": None,
            "reason": "chemical_not_found",
            "boiling_c": None,
            "freezing_c": None,
        }

    boiling_f = chem.get("ambient_boiling_point_f") or chem.get("normal_boiling_point_f")
    freezing_f = chem.get("freezing_point_f")

    boiling_c = _f_to_c(boiling_f)
    freezing_c = _f_to_c(freezing_f)

    if boiling_c is None:
        return {
            "phase": "unknown",
            "is_gas": None,
            "reason": "boiling_point_missing",
            "boiling_c": None,
            "freezing_c": freezing_c,
        }

    try:
        temp_c = float(temperature_c)
    except (TypeError, ValueError):
        return {
            "phase": "unknown",
            "is_gas": None,
            "reason": "invalid_temperature",
            "boiling_c": boiling_c,
            "freezing_c": freezing_c,
        }

    if temp_c >= boiling_c:
        return {
            "phase": "gas",
            "is_gas": True,
            "reason": "temp_at_or_above_boiling",
            "boiling_c": boiling_c,
            "freezing_c": freezing_c,
        }

    if freezing_c is not None and temp_c <= freezing_c:
        phase = "solid"
    else:
        phase = "liquid"

    return {
        "phase": phase,
        "is_gas": False,
        "reason": "temp_below_boiling",
        "boiling_c": boiling_c,
        "freezing_c": freezing_c,
    }
