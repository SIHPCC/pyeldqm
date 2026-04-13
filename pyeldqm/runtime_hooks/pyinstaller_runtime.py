"""Runtime environment setup for frozen pyELDQM executables.

This hook runs before user code in PyInstaller builds.
It stabilizes geospatial runtime paths (GDAL/PROJ) required by rasterio/pyproj.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _existing(paths: list[Path]) -> list[Path]:
    return [p for p in paths if p.exists()]


def _prepend_path_env(paths: list[Path]) -> None:
    if not paths:
        return
    current = os.environ.get("PATH", "")
    prefix = os.pathsep.join(str(p) for p in paths)
    os.environ["PATH"] = f"{prefix}{os.pathsep}{current}" if current else prefix


def _set_geo_env() -> None:
    base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))

    path_dirs = _existing([
        base,
        base / "Library" / "bin",
        base / "bin",
        base / "lib",
    ])
    _prepend_path_env(path_dirs)

    gdal_candidates = _existing([
        base / "Library" / "share" / "gdal",
        base / "share" / "gdal",
        base / "gdal-data",
        base / "data" / "gdal",
    ])
    proj_candidates = _existing([
        base / "Library" / "share" / "proj",
        base / "share" / "proj",
        base / "proj-data",
        base / "data" / "proj",
    ])

    if gdal_candidates and not os.environ.get("GDAL_DATA"):
        os.environ["GDAL_DATA"] = str(gdal_candidates[0])

    if proj_candidates:
        if not os.environ.get("PROJ_LIB"):
            os.environ["PROJ_LIB"] = str(proj_candidates[0])
        if not os.environ.get("PROJ_DATA"):
            os.environ["PROJ_DATA"] = str(proj_candidates[0])

    # Let pyproj know explicitly where projection grids are in frozen mode.
    try:
        from pyproj import datadir as _pyproj_datadir

        if proj_candidates:
            _pyproj_datadir.set_data_dir(str(proj_candidates[0]))
    except Exception:
        pass


_set_geo_env()
