# pyELDQM

**Python-Based Real-Time Emergency Leakage and Dispersion Quantification Model**

[![CI](https://github.com/SIHPCC/pyeldqm/actions/workflows/ci.yml/badge.svg)](https://github.com/SIHPCC/pyeldqm/actions/workflows/ci.yml)
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
conda create -n pyeldqm python=3.10
conda activate pyeldqm

# 2. Install pyELDQM with pip inside the conda environment
pip install pyeldqm
```

> **Geospatial extras** (osmnx, geopandas, rasterio) require GDAL and are optional.
> Install them with `pip install "pyeldqm[geo]"` if you need evacuation routing or
> population raster support.

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
import pyeldqm as eldqm

from pyeldqm.core.dispersion_models.gaussian_model import calculate_gaussian_dispersion

config = {
    "source": {"lat": 14.60, "lon": 121.03, "Q_gs": 1.5},
    "chemical": {"name": "chlorine", "MW": 70.91},
    "meteorology": {"wind_speed_ms": 3.0, "wind_direction_deg": 270,
                    "stability_class": "D", "roughness": "RURAL"},
    "grid": {"x_max_m": 3000, "y_max_m": 1500, "nx": 200, "ny": 100},
}
result = calculate_gaussian_dispersion(config)
```

```python
import pyeldqm as eldqm

from pyeldqm.core.source_models.gas_pipeline.pipeline_leak import simulate_pipeline_leak

result = simulate_pipeline_leak(duration_s=600, dt=60)
print(result["Qt"])   # mass-flow rate time-series [kg/s]
```

```python
import pyeldqm as eldqm

from pyeldqm.core.health_thresholds import get_all_thresholds

thresholds = get_all_thresholds("ammonia")
print(thresholds["AEGL"])   # {'AEGL-1': 30.0, 'AEGL-2': 160.0, 'AEGL-3': 1100.0}
```

---

## Scenario configuration (YAML)

Pre-built scenarios live in `configs/`:

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
├── core/                        # Pure-Python scientific library
│   ├── dispersion_models/       # Gaussian + dense-gas models
│   ├── fire_models/             # Pool fire, jet fire, flash fire
│   ├── meteorology/             # Stability, wind profile, solar radiation
│   ├── source_models/           # Pipeline, tank, puddle source terms
│   ├── evacuation/              # Route optimisation (osmnx)
│   ├── population/              # Population raster I/O
│   ├── utils/                   # geo_constants, sensor optimisation, …
│   └── visualization/           # Folium map builders
├── app/                         # Dash web-application layer
│   ├── callbacks/               # Dash callback modules
│   ├── components/              # Reusable UI components
│   └── layout/                  # Page layout (tabs, sidebar, header)
├── configs/                     # Example YAML scenarios
├── data/                        # Reference data (not in wheel)
├── tests/                       # pytest test suite
├── examples/                    # Standalone usage scripts
├── pyproject.toml               # Packaging & tool configuration
├── CHANGELOG.md
└── CONTRIBUTING.md
```

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