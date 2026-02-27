# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.1] — 2026-02-27

### Added
- About tab (`ℹ️ About`) as the seventh main tab — professional & industrial-grade
  information panel covering capabilities, dispersion models, standards compliance,
  technology stack, and contributor profiles.
- Principal Investigator profile for Dr. Zohaib Atiq Khan (Assistant Professor,
  Dept. of Chemical, Polymer & Composite Materials Engineering, UET Lahore)
  including HPC Centre and SIHPCC details.
- Version, licence, Python compatibility, and open-source badges in both the
  main application header and the About tab hero banner.
- "View on GitHub" button added to the main header (links to SIHPCC/pyeldqm).
- PNG/image assets (`*.png`, `*.jpg`, `*.svg`, `*.ico`) included in
  `pyproject.toml` package-data and `MANIFEST.in` so the pyELDQM logo is
  correctly bundled on `pip install`.
- Scrollable tab bar with `overflow-x: auto` wrapper and `flex-wrap: nowrap`
  CSS so all seven tabs remain accessible at any viewport width.

### Changed
- Main header background updated to a dark-to-blue gradient
  (`#1a2a3a → #1f3a5f → #1f77b4`) matching the About hero banner.
- `requires-python` updated to `>=3.9,<3.15`; Python 3.13 and 3.14
  classifiers added.
- Tab labels shortened for better fit in the navigation bar.

### Fixed
- Logo (`pyELDQM_logo_v0.1.png`) not appearing after `pip install -e .` because
  image files were excluded from package-data.

---

## [0.1.0] — 2026-02-01

### Added
- Full `pyproject.toml` with build metadata, optional extras (`app`, `geo`, `full`), and a
  single console-script entry point `pyeldqm-app`.
- `LICENSE` (MIT).
- `MANIFEST.in` to include YAML configs and CSS assets in source distributions.
- `core/logging_config.py`: centralised `configure_logging()` helper; silences noisy
  third-party loggers (werkzeug, osmnx, requests).
- `core/utils/geo_constants.py`: `METERS_PER_DEGREE_LAT` constant and degree ↔ metre
  conversion helpers — single source of truth across the codebase.
- Module-level `__init__.py` files for all sub-packages (`core/dispersion_models`,
  `core/fire_models`, `core/meteorology`, `core/source_models`, and three
  `source_models` sub-packages) with explicit `__all__` exports.
- Type annotations (PEP 484) across `heavy_gas_model.py`, `dispersion_utils.py`,
  `wind_profile.py`, `consequences.py`, and `health_thresholds.py`.
- Module docstrings for `gaussian_model.py`, `dispersion_utils.py`, `wind_profile.py`,
  `consequences.py`, and `chemical_database.py`.
- `__del__` guard on `ChemicalDatabase` to prevent SQLite connection leaks.
- Test suite expanded: `test_dispersion_utils`, `test_meteorology`,
  `test_health_thresholds`, `test_geo_constants`.
- GitHub Actions CI workflow (`.github/workflows/ci.yml`): lint → test → build on
  Python 3.9, 3.10, 3.11.

### Changed
- **Critical bug fix**: `MW_AIR` in `heavy_gas_model.py` corrected from `70.91` (Cl₂)
  to `28.97` (dry air). This affected buoyancy calculations throughout the Britter-McQuaid
  dense-gas ODE.
- `H_GND_TRANSFER` renamed to `H_GND_W_M2K` with a units comment
  (`W m⁻² K⁻¹`) for clarity.
- `R = 0.08206` inline literal in `gaussian_model.py` promoted to a named module
  constant `R_LATM` with a units docstring.
- All `print()` debug calls replaced with structured `logging` calls
  (`gaussian_model`, `folium_maps`, `zone_extraction`, `app/utils/population`).
- `app/config.py` reads `HOST`, `PORT`, and `DEBUG` from environment variables
  (non-breaking defaults preserved).
- `run_app.py` wrapped in `def main()` for use as a proper `console_scripts` entry
  point; `main.py` gutted to a deprecation-notice docstring.
- Sidebar population-raster placeholder changed from a Windows `D:/` path to a
  platform-neutral `/data/...` example.
- `Dict[str, any]` → `Dict[str, Any]` in `health_thresholds.py` (lowercase `any`
  is not the typing `Any`).

### Removed
- Binary `core/fire_models/fire_models.rar` — tracked by mistake.
- `sys.path.insert` hack in `tests/conftest.py` (replaced by `pyproject.toml`
  `pythonpath` setting).

### Fixed
- `coverage = n / max_sensors` placeholder in `sensor_optimization.py` replaced
  with a proper coverage fraction based on placed sensor count.

[Unreleased]: https://github.com/SIHPCC/pyeldqm/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/SIHPCC/pyeldqm/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/SIHPCC/pyeldqm/releases/tag/v0.1.0
