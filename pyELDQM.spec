# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules


PROJECT_ROOT = Path(globals().get("SPECPATH", ".")).resolve()
APP_ASSETS = PROJECT_ROOT / "pyeldqm" / "app" / "assets"
RUNTIME_HOOK = PROJECT_ROOT / "pyeldqm" / "runtime_hooks" / "pyinstaller_runtime.py"


def _exclude_tests(module_name: str) -> bool:
    return ".tests" not in module_name


def _safe_collect_all(package_name: str):
    """Collect datas/binaries/hiddenimports when package is available."""
    try:
        return collect_all(package_name, filter_submodules=_exclude_tests)
    except Exception:
        return [], [], []


def _dedupe(items):
    seen = set()
    out = []
    for item in items:
        key = repr(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


datas = [
    (str(PROJECT_ROOT / "pyeldqm" / "data"), "pyeldqm/data"),
    (str(PROJECT_ROOT / "pyeldqm" / "configs"), "pyeldqm/configs"),
    (str(APP_ASSETS), "pyeldqm/app/assets"),
]
binaries = []
hiddenimports = []

# Core packages that are dynamically imported by callbacks and can be missed.
for pkg in [
    "osmnx",
    "networkx",
    "rasterio",
    "pyproj",
    "geopandas",
    "pyogrio",
    "shapely",
    "fiona",
]:
    d, b, h = _safe_collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Extra guard to include lazily-imported submodules.
for pkg in ["osmnx", "networkx", "rasterio", "pyproj", "geopandas"]:
    try:
        hiddenimports += collect_submodules(pkg, filter=_exclude_tests)
    except Exception:
        pass

datas = _dedupe(datas)
binaries = _dedupe(binaries)
hiddenimports = _dedupe(hiddenimports)


a = Analysis(
    ["run_app.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(RUNTIME_HOOK)],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="pyELDQM",
    icon=str(APP_ASSETS / "favicon.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
