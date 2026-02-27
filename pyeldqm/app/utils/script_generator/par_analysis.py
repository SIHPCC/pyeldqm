"""
app/utils/script_generator/par_analysis.py
===========================================
Generates a standalone, runnable Python example script for the Population
At Risk (PAR) analysis tab.  The script replicates the full dispersion
calculation plus raster-based population counting and saves an interactive
Folium map.  Requires pyELDQM installed as a package (pip install pyeldqm).
"""

from __future__ import annotations

import textwrap
import re
from datetime import datetime

# Re-use dispersion-related building blocks from the threat_zones generator
from .threat_zones import (
    _slug,
    _source_color,
    _single_source_block,
    _multi_source_block,
)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_par_script(
    *,
    chemical: str,
    molecular_weight: float,
    release_type: str,
    source_term_mode: str,
    lat: float,
    lon: float,
    release_rate: float,
    tank_height: float,
    duration_minutes: float,
    mass_released_kg: float,
    terrain_roughness: str,
    receptor_height_m: float,
    weather_mode: str,
    wind_speed: float,
    wind_dir: float,
    temperature_c: float,
    humidity_pct: float,
    cloud_cover_pct: float,
    timezone_offset_hrs: float,
    datetime_mode: str,
    specific_datetime: str | None,
    aegl_thresholds: dict,
    x_max: int,
    y_max: int,
    raster_path: str,
    critical_threshold: float = 10000.0,
    high_threshold: float = 5000.0,
    multi_sources: list[dict] | None = None,
) -> str:
    """Return the full text of a standalone PAR analysis Python script.

    Parameters
    ----------
    All dispersion parameters mirror the sidebar inputs from the app.
    raster_path        : Absolute path to the population raster GeoTIFF.
    critical_threshold : PAR count above which risk is classified as Critical.
    high_threshold     : PAR count above which risk is classified as High.
    multi_sources      : List of source dicts; only used when release_type == 'multi'.
    """

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chem_slug = _slug(chemical)
    rel_type_label = "Multi-Source" if release_type == "multi" else "Single Source"

    # ── Weather block ───────────────────────────────────────────────────────
    if weather_mode == "auto":
        weather_block = textwrap.dedent(f"""\
            # Fetch live weather from Open-Meteo API
            weather = get_weather(
                latitude=SOURCE_LAT,
                longitude=SOURCE_LON,
                source="open_meteo",
            )
            print(f"  Wind speed : {{weather['wind_speed']:.2f}} m/s")
            print(f"  Wind dir   : {{weather['wind_dir']:.1f}} deg")
            print(f"  Temperature: {{weather['temperature_K'] - 273.15:.1f}} C")
        """)
    else:
        weather_block = textwrap.dedent(f"""\
            weather = {{
                "wind_speed"    : WIND_SPEED,
                "wind_dir"      : WIND_DIRECTION,
                "temperature_K" : TEMPERATURE_C + 273.15,
                "humidity"      : HUMIDITY / 100.0,
                "cloud_cover"   : CLOUD_COVER / 100.0,
                "source"        : "manual",
            }}
        """)

    # ── Datetime block ──────────────────────────────────────────────────────
    if datetime_mode == "specific" and specific_datetime:
        dt_block = f'simulation_datetime = datetime.fromisoformat("{specific_datetime}")'
    else:
        dt_block = "simulation_datetime = datetime.now()"

    # ── Dispersion block (single vs multi) ──────────────────────────────────
    if release_type == "single":
        dispersion_block = _single_source_block(source_term_mode)
    else:
        dispersion_block = _multi_source_block(source_term_mode, multi_sources or [])

    # ── Multi-source config ──────────────────────────────────────────────────
    if release_type == "multi" and multi_sources:
        lines = ["RELEASE_SOURCES = ["]
        for i, s in enumerate(multi_sources):
            lines.append(f"    {{  # Source {i + 1}")
            lines.append(f'        "lat"   : {s["lat"]},')
            lines.append(f'        "lon"   : {s["lon"]},')
            lines.append(f'        "name"  : "{s.get("name", f"Source {i + 1}")}",')
            lines.append(f'        "height": {s["height"]},')
            lines.append(f'        "rate"  : {s["rate"]},')
            lines.append(f'        "color" : "{_source_color(i)}",')
            lines.append("    },")
        lines.append("]")
        multi_source_cfg = "\n".join(lines)
    else:
        multi_source_cfg = "# No additional sources (single-source mode)"

    # ── Weather import ───────────────────────────────────────────────────────
    weather_import = (
        "from pyeldqm.core.meteorology.realtime_weather import get_weather"
        if weather_mode == "auto"
        else "# from pyeldqm.core.meteorology.realtime_weather import get_weather  # manual mode"
    )

    # safe repr for the raster path (Windows backslashes, spaces, etc.)
    raster_path_repr = repr(raster_path) if raster_path else repr("")

    def _d(s):
        return textwrap.dedent(s).lstrip("\n")

    # ── Script sections ──────────────────────────────────────────────────────
    s_docstring = _d(f"""\
        \"\"\"
        Population At Risk (PAR) Analysis — Auto-Generated Example
        ===========================================================
        Generated by pyELDQM Dash app on {now_str}

        Scenario   : {rel_type_label} Release
        Chemical   : {chemical}
        Location   : {lat}, {lon}
        Weather    : {"Real-time (Open-Meteo)" if weather_mode == "auto" else "Manual"}
        Raster     : {raster_path if raster_path else "(none — set RASTER_PATH)"}

        Complete reproduction of the PAR analysis from the pyELDQM Dash
        application: Gaussian dispersion → AEGL zone extraction →
        raster-based population counting → risk classification.

        Requirements
        ------------
            pip install pyeldqm rasterio

        Run from any directory:
            python {chem_slug}_par_analysis.py

        Outputs saved to ./outputs/par_analysis/
        -----------------------------------------
        - {chem_slug}_par_map_<ts>.html       — interactive Folium threat-zone map
        \"\"\"
    """)

    s_imports = _d(f"""\
        # ============================================================================
        # IMPORTS
        # ============================================================================

        import webbrowser
        from pathlib import Path
        from datetime import datetime

        import numpy as np

        # -- pyELDQM package imports (pip install pyeldqm) ---------------------------
        from pyeldqm.core.dispersion_models.gaussian_model import (
            calculate_gaussian_dispersion,
            multi_source_concentration,
        )
        from pyeldqm.core.meteorology.stability import get_stability_class
        from pyeldqm.core.meteorology.wind_profile import wind_speed as wind_profile
        {weather_import}
        from pyeldqm.core.visualization.folium_maps import (
            create_dispersion_map,
            meters_to_latlon,
            add_facility_markers,
            calculate_optimal_zoom_level,
        )
        from pyeldqm.core.utils.features import setup_computational_grid
        from pyeldqm.core.utils.zone_extraction import extract_zones
        from pyeldqm.app.utils.population import compute_par_counts_from_raster
    """)

    s_config = _d(f"""\
        # ============================================================================
        # CONFIGURATION
        # ============================================================================

        # -- Population raster -------------------------------------------------------
        RASTER_PATH        = {raster_path_repr}   # absolute path to GeoTIFF
        CRITICAL_THRESHOLD = {critical_threshold}    # PAR >= this → Critical risk
        HIGH_THRESHOLD     = {high_threshold}        # PAR >= this → High risk

        # -- Chemical ----------------------------------------------------------------
        CHEMICAL_NAME      = {chemical!r}
        MOLECULAR_WEIGHT   = {molecular_weight}      # g/mol

        # -- Release location --------------------------------------------------------
        SOURCE_LAT         = {lat}
        SOURCE_LON         = {lon}
        TIMEZONE_OFFSET_HRS = {timezone_offset_hrs}

        # -- Release parameters ------------------------------------------------------
        RELEASE_TYPE       = {release_type!r}        # "single" or "multi"
        SOURCE_TERM_MODE   = {source_term_mode!r}    # "continuous" or "instantaneous"
        RELEASE_RATE       = {release_rate}          # g/s  (continuous mode)
        TANK_HEIGHT        = {tank_height}           # m above ground
        DURATION_MINUTES   = {duration_minutes}      # release duration (min)
        MASS_RELEASED_KG   = {mass_released_kg}      # total mass (instantaneous mode)
        TERRAIN_ROUGHNESS  = {terrain_roughness!r}   # "URBAN" or "RURAL"
        RECEPTOR_HEIGHT_M  = {receptor_height_m}     # breathing-zone height (m)

        # -- Weather (used only when WEATHER_MODE == "manual") -----------------------
        WEATHER_MODE       = {weather_mode!r}
        WIND_SPEED         = {wind_speed}            # m/s
        WIND_DIRECTION     = {wind_dir}              # degrees (0=N, 90=E, 180=S, 270=W)
        TEMPERATURE_C      = {temperature_c}         # °C
        HUMIDITY           = {humidity_pct}          # %
        CLOUD_COVER        = {cloud_cover_pct}       # %

        # -- AEGL hazard thresholds (ppm) --------------------------------------------
        AEGL_THRESHOLDS = {{
            "AEGL-1": {aegl_thresholds.get("AEGL-1", 30)},
            "AEGL-2": {aegl_thresholds.get("AEGL-2", 160)},
            "AEGL-3": {aegl_thresholds.get("AEGL-3", 1100)},
        }}

        # -- Computational grid ------------------------------------------------------
        X_MAX = {x_max}    # m  (downwind extent)
        Y_MAX = {y_max}    # m  (crosswind extent)
        NX    = 500
        NY    = 500

    """)

    s_sources = "# -- Multi-source definitions (used only when RELEASE_TYPE == 'multi') --\n"
    s_sources += multi_source_cfg + "\n\n"

    s_datetime = _d(f"""\
        # ============================================================================
        # SIMULATION DATETIME
        # ============================================================================
        {dt_block}
        print(f"Simulation datetime : {{simulation_datetime}}")

    """)

    s_weather_header = _d("""\
        # ============================================================================
        # WEATHER CONDITIONS
        # ============================================================================
        print("\\nFetching / setting weather conditions ...")
    """)

    s_stability = _d("""\
        # ============================================================================
        # STABILITY CLASS
        # ============================================================================
        stability_class = get_stability_class(
            wind_speed=weather["wind_speed"],
            datetime_obj=simulation_datetime,
            latitude=SOURCE_LAT,
            longitude=SOURCE_LON,
            cloudiness_index=weather.get("cloud_cover", 0) * 10,
            timezone_offset_hrs=TIMEZONE_OFFSET_HRS,
        )
        print(f"  Stability class    : {stability_class}")

    """)

    s_grid = _d("""\
        # ============================================================================
        # COMPUTATIONAL GRID
        # ============================================================================
        print("\\nSetting up computational grid ...")
        X, Y, _, _ = setup_computational_grid(
            x_max=X_MAX, y_max=Y_MAX, nx=NX, ny=NY,
        )
        print(f"  Grid: {NX}x{NY} cells, downwind {X_MAX} m, crosswind {Y_MAX} m")

    """)

    s_dispersion_header = _d("""\
        # ============================================================================
        # DISPERSION CALCULATION
        # ============================================================================
        print("\\nRunning Gaussian dispersion model ...")

        RELEASE_DURATION_S = DURATION_MINUTES * 60.0
        TOTAL_MASS_G       = MASS_RELEASED_KG * 1000.0

    """)

    s_zones = _d("""\
        # ============================================================================
        # ZONE EXTRACTION
        # ============================================================================
        print("\\nExtracting AEGL threat zones ...")
        threat_zones = extract_zones(
            X, Y, concentration, AEGL_THRESHOLDS,
            SOURCE_LAT, SOURCE_LON,
            wind_dir=weather["wind_dir"],
        )

    """)

    s_par = _d(f"""\
        # ============================================================================
        # POPULATION AT RISK (PAR) CALCULATION
        # ============================================================================
        print("\\nCalculating Population at Risk ...")
        print(f"  Raster path : {{RASTER_PATH}}")

        par_counts, par_note = compute_par_counts_from_raster(RASTER_PATH, threat_zones)

        aegl3_pop = par_counts.get("AEGL-3", 0)
        aegl2_pop = par_counts.get("AEGL-2", 0)
        aegl1_pop = par_counts.get("AEGL-1", 0)
        total_par = aegl3_pop + aegl2_pop + aegl1_pop

        if total_par >= CRITICAL_THRESHOLD:
            risk_label, risk_symbol = "CRITICAL", "🔴"
        elif total_par >= HIGH_THRESHOLD:
            risk_label, risk_symbol = "HIGH", "🟠"
        else:
            risk_label, risk_symbol = "MODERATE / LOW", "🟢"

        print()
        print("=" * 60)
        print("POPULATION AT RISK RESULTS")
        print("=" * 60)
        print(f"  AEGL-3 zone (life-threatening): {{aegl3_pop:>10,}} people")
        print(f"  AEGL-2 zone (irreversible)    : {{aegl2_pop:>10,}} people")
        print(f"  AEGL-1 zone (mild effects)    : {{aegl1_pop:>10,}} people")
        print(f"  {{'-'*42}}")
        print(f"  Total PAR                     : {{total_par:>10,}} people")
        print(f"  Risk Level                    : {{risk_symbol}} {{risk_label}}")
        print(f"  Note: {{par_note}}")
        print()

        # ── Geographic statistics ──────────────────────────────────────────────
        try:
            from shapely.geometry import Point
            _src_pt = Point(SOURCE_LON, SOURCE_LAT)
            print("=" * 60)
            print("GEOGRAPHIC STATISTICS")
            print("=" * 60)
            for _zone_name in ["AEGL-3", "AEGL-2", "AEGL-1"]:
                _poly = threat_zones.get(_zone_name)
                if _poly is None or _poly.is_empty:
                    print(f"  {{_zone_name:<8}}: no zone formed")
                    continue
                _b = _poly.bounds
                _lat_span = _b[3] - _b[1]
                _lon_span = _b[2] - _b[0]
                _mid_lat = (_b[1] + _b[3]) / 2
                _area_km2 = max(
                    (_lat_span * 111) * (_lon_span * 111 * np.cos(np.radians(_mid_lat))),
                    0.0,
                )
                _max_d_km = max(
                    _src_pt.distance(Point(c)) * 111
                    for c in _poly.exterior.coords
                )
                _pop = par_counts.get(_zone_name, 0)
                _density = _pop / _area_km2 if _area_km2 > 0 else 0
                print(f"  {{_zone_name:<8}}: area={{_area_km2:.2f}} km²  "
                      f"max_dist={{_max_d_km:.2f}} km  "
                      f"pop={{_pop:,}}  density={{_density:,.0f}} p/km²")
            print()
        except Exception as _geo_exc:
            print(f"  [Geographic stats error: {{_geo_exc}}]")

    """)

    s_map = _d(f"""\
        # ============================================================================
        # INTERACTIVE PAR MAP
        # ============================================================================
        print("Creating PAR threat zone map ...")
        lat_grid, lon_grid = meters_to_latlon(
            X, Y, SOURCE_LAT, SOURCE_LON, weather["wind_dir"],
        )
        zoom_level, bounds = calculate_optimal_zoom_level(
            lat_grid, lon_grid, concentration,
            threshold=min(AEGL_THRESHOLDS.values()),
        )

        m = create_dispersion_map(
            source_lat=SOURCE_LAT,
            source_lon=SOURCE_LON,
            x_grid=X,
            y_grid=Y,
            concentration=concentration,
            thresholds=AEGL_THRESHOLDS,
            wind_direction=weather["wind_dir"],
            zoom_start=zoom_level,
            chemical_name=CHEMICAL_NAME,
            source_height=TANK_HEIGHT,
            wind_speed=weather["wind_speed"],
            stability_class=stability_class,
            include_heatmap=True,
            include_compass=True,
        )

        if resolved_sources:
            m = add_facility_markers(m, resolved_sources) or m

        if bounds[0] is not None:
            try:
                m.fit_bounds(
                    [[bounds[1], bounds[3]], [bounds[0], bounds[2]]],
                    padding=(0.1, 0.1), max_zoom=18,
                )
            except Exception:
                pass

        # ============================================================================
        # SAVE OUTPUT & OPEN IN BROWSER
        # ============================================================================
        _out_dir = Path.cwd() / "outputs" / "par_analysis"
        _out_dir.mkdir(parents=True, exist_ok=True)
        _ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        _map_path = _out_dir / f"{chem_slug}_par_map_{{_ts}}.html"
        m.save(str(_map_path))
        print(f"Map saved to: {{_map_path}}")

        webbrowser.open(_map_path.as_uri())
        print("\\nDone! PAR map opened in your browser.")
        print(f"Files are in: {{_out_dir}}")
    """)

    script = (
        s_docstring
        + "\n" + s_imports
        + "\n" + s_config
        + s_sources
        + s_datetime
        + s_weather_header + "\n"
        + weather_block + "\n\n"
        + s_stability
        + s_grid
        + s_dispersion_header
        + dispersion_block + "\n\n"
        + s_zones
        + s_par
        + s_map
    )

    return script
