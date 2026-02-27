
<p align="center"><img src="docs/images/pyELDQM_logo_v0.1.png" alt="pyELDQM logo" width="100%" style="max-width: 1200px; height: auto;" /></p>

[![CI](https://github.com/SIHPCC/pyeldqm/actions/workflows/ci.yml/badge.svg)](https://github.com/SIHPCC/pyeldqm/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pyeldqm.svg)](https://pypi.org/project/pyeldqm/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

pyELDQM is an open-source, modular toolkit for real-time chemical emergency modelling.
It provides Gaussian plume / puff dispersion, dense-gas (Britter-McQuaid), fire & explosion
consequence models, PAR (Protective Action Recommendation) analysis, evacuation route
optimisation, and an interactive Dash web application — all in pure Python.

**Author:** Dr. Zohaib Atiq Khan

**Other Contributors:**
- Dr. Muhammad Imran Rashid
- Mr. Muhammad Ahmad
- Ms. Aroosa Dilbar
- Mr. Muhammad Saleem Akhtar
- Ms. Fatima

---

## Features

| Module | Description |
|---|---|
| **Dispersion** | Gaussian plume/puff (single & multi-source), dense-gas Britter-McQuaid ODE |
| **Source models** | Gas pipeline leaks, pressurised tank gas/liquid/two-phase releases, puddle evaporation |
| **Fire & explosion** | Pool fire, jet fire thermal flux; flash-fire radius; BLEVE |
| **Meteorology** | Pasquill-Gifford stability classification, Monin-Obukhov / power-law wind profiles, solar insolation |
| **Health thresholds** | AEGL, ERPG, IDLH, PAC look-up from SQLite chemical database |
| **Consequences** | AEGL/ERPG hazard-zone footprints from dispersion output |
| **PAR analysis** | Shelter-in-place vs. evacuation decision support with population raster integration |
| **Sensor placement** | Coverage-optimised sensor network design |
| **Evacuation routing** | OpenStreetMap-based route optimisation (osmnx / networkx) |
| **Web app** | Interactive Dash 2 dashboard with real-time threat maps (Folium/Leaflet) |

---

## Installation

> **Recommended:** Install pyELDQM inside a dedicated virtual environment to avoid
> package conflicts with other projects on your system.

```bash
# 1. Create and activate a virtual environment
python -m venv pyeldqm-env

# Windows
pyeldqm-env\Scripts\activate
# macOS / Linux
source pyeldqm-env/bin/activate

# 2. Install pyELDQM
pip install pyeldqm
```

### Conda installation (local build)

```bash
# 1. Create and activate a conda environment
conda create -n pyeldqm python=3.14
conda activate pyeldqm

# 2a. Install published release from PyPI
pip install pyeldqm

# 2b. OR install from local source (development / editable)
pip install -e .
```

> **Important:** Always use `pip install -e .` (note the `-e` flag) when
> installing from a cloned source tree. Omitting `-e` will cause a
> *"unable to open database file"* error and missing-module errors.

### Development install

```bash
git clone https://github.com/SIHPCC/pyeldqm.git
cd pyeldqm
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .
```

---

## Quick start

### Launch the web application

```bash
pyeldqm-app
# → http://localhost:8050
```

Environment variables (all optional):

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8050` | Listening port |
| `HOST` | `localhost` | Bind address |
| `DEBUG` | `true` | Dash debug mode |

### Python API

```python
from pyeldqm.core.chemical_database import ChemicalDatabase

with ChemicalDatabase() as db:
    ammonia = db.get_chemical_by_name("AMMONIA")
    print(ammonia["cas_number"], ammonia["molecular_weight"])
```

```python
from pyeldqm.core.meteorology.realtime_weather import get_weather

# Real-time weather (Open-Meteo)
weather = get_weather(source="open_meteo", latitude=24.9, longitude=67.1)
print(weather["wind_speed"], weather["wind_dir"], weather["temperature_K"])
```

```python
import numpy as np
from pyeldqm.core.dispersion_models.gaussian_model import multi_source_concentration

# 2D local grid (meters)
x_vals = np.linspace(10, 2000, 200)
y_vals = np.linspace(-800, 800, 160)
X, Y = np.meshgrid(x_vals, y_vals)

# Multiple continuous release sources (g/s)
sources = [
    {"name": "A", "Q": 800, "x0": 0, "y0": 0, "h_s": 3.0, "wind_dir": 45.0},
    {"name": "B", "Q": 600, "x0": 250, "y0": -120, "h_s": 2.5, "wind_dir": 45.0},
]

C_total = multi_source_concentration(
    sources=sources,
    x_grid=X,
    y_grid=Y,
    z=1.5,
    t=600,
    t_r=600,
    U=5.0,
    stability_class="D",
    roughness="URBAN",
    mode="continuous",
    grid_wind_direction=45.0,
)
print(float(np.max(C_total)))
```

---

## Scenario configuration (YAML)

Pre-built scenarios live in `pyeldqm/configs/`:

| File | Scenario |
|---|---|
| `base_config.yaml` | Generic Gaussian dispersion |
| `chlorine_pipeline_leak.yaml` | Chlorine pipeline rupture |
| `ammonia_tank_release.yaml` | Pressurised ammonia tank release |
| `lpg_bleve.yaml` | LPG pool fire / BLEVE |
| `realtime_monitoring.yaml` | Live weather + multi-source |

---

## Project structure

```
pyELDQM/
|-- pyeldqm/                       # Python package root
|   |-- app/                       # Dash web application
|   |   |-- assets/
|   |   |-- callbacks/
|   |   |-- components/
|   |   |   `-- tabs/
|   |   |-- layout/
|   |   `-- utils/
|   |       `-- script_generator/
|   |-- core/                      # Scientific and modelling engine
|   |   |-- dispersion_models/
|   |   |-- evacuation/
|   |   |-- fire_models/
|   |   |-- geography/
|   |   |-- meteorology/
|   |   |-- population/
|   |   |-- protective_actions/
|   |   |-- source_models/
|   |   |   |-- gas_pipeline/
|   |   |   |-- puddle_evaporation/
|   |   |   `-- tank_release/
|   |   |-- utils/
|   |   `-- visualization/
|   |-- data/                      # Runtime/reference data
|   |   |-- chemicals_database/
|   |   |-- geographic_data/
|   |   |-- population/
|   |   |-- thermodynamics_data/
|   |   `-- weather_samples/
|   |-- configs/                   # Scenario YAML files
|   `-- validation/
|       `-- validation_scripts/
|-- examples/
|   |-- notebooks/
|   `-- scripts/
|-- docs/
|   `-- images/
|-- tests/
|-- cache/
|-- outputs/
|-- .github/
|   `-- workflows/
|-- run_app.py
|-- pyproject.toml
|-- MANIFEST.in
|-- requirements.txt
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- README.md
`-- LICENSE
```

---

## Gallery

| Screenshot | Description |
|---|---|
| ![Threat Zones](docs/images/threat_zones.png) | Chemical Threat Zones|
| ![PAR Analysis](docs/images/par_analysis.png) | Population At Risk analysis |
| ![Emergency Routes](docs/images/emergency_routes.png) | Emergency route optimization |
| ![Sensor Placement](docs/images/sensor_placement.png) | Sensor network optimization |
| ![Health Impact](docs/images/health_impact.png) | Health impact threshold zones |
| ![Shelter Status](docs/images/shelter_status.png) | Shelter-in-place vs evacuation guidance |

---

## Running tests

```bash
pytest tests/ --cov=core --cov-report=term-missing
```

The test suite covers dispersion utilities, meteorology, health thresholds, geographic
constants, source models, fire models, and consequence models (~65 tests).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, coding standards, and the
pull-request workflow.

---

## License

MIT — see [LICENSE](LICENSE).

