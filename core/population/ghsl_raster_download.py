"""
download_ghsl_builtup_and_clip.py
=================================

✅ Downloads and clips GHSL Built-up raster (GeoTIFF) for urban-weighted PAR.

This script targets GHSL built-up surface grid:
- GHS-BUILT-S R2023A (built-up surface in m² per 100m cell)
- Useful as a weighting layer for population estimation

Output:
    data/ghsl/ghsl_builtup_clip_<RADIUS>km.tif

Notes:
- GHSL downloads can be huge (global tiles).
- This script supports TWO workflows:

Workflow A (Recommended):
✅ You provide a GHSL GeoTIFF URL (tile or global) → script downloads and clips.

Workflow B (Manual fallback):
✅ If download URL changes, you can manually place the GHSL GeoTIFF locally
   and the script will clip it.

Author: pyELDQM Development Team
Date: 2026
"""

import os
import sys
import requests
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from pyproj import Geod


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    # Leak / Tank location
    LAT = 31.691100
    LON = 74.082167

    # Clip radius in km
    CLIP_RADIUS_KM = 20

    # Output directory
    OUTPUT_DIR = Path("data/ghsl")

    # -------------------------------------------------------------------------
    # ✅ OPTION A: Provide a direct GHSL GeoTIFF URL (tile/global tif).
    #
    # You can find GHSL dataset pages here:
    # - GHS-BUILT-S R2023A: https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php
    # - Download portal:   https://human-settlement.emergency.copernicus.eu/download.php
    #
    # NOTE:
    # GHSL provides tiled downloads for many products.
    # Paste a direct URL to a tile/global .tif here if you have it.
    # -------------------------------------------------------------------------
    GHSL_TIF_URL = ""  # <-- optional (recommended if available)

    # -------------------------------------------------------------------------
    # ✅ OPTION B: If you already downloaded GHSL raster manually, put its path.
    # Example:
    #   LOCAL_GHSL_TIF = r"D:\GIS\GHSL\GHS_BUILT_S_100m.tif"
    # -------------------------------------------------------------------------
    LOCAL_GHSL_TIF = ""  # <-- optional fallback


# =============================================================================
# DOWNLOAD HELPERS
# =============================================================================

def download_file(url: str, out_path: Path, chunk_size: int = 1024 * 1024) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n[Download] URL: {url}")
    print(f"[Download] OUT: {out_path}")

    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))

        downloaded = 0
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)

                if total > 0:
                    pct = (downloaded / total) * 100
                    print(f"\r  {downloaded/1e6:.1f}MB / {total/1e6:.1f}MB ({pct:.1f}%)", end="")

    print("\n[Download] Completed ✅")
    return out_path


# =============================================================================
# CLIP HELPERS
# =============================================================================

def compute_bbox_from_radius_km(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    """
    Returns: (min_lon, min_lat, max_lon, max_lat) using accurate geodesic offsets.
    """
    geod = Geod(ellps="WGS84")

    lon_w, lat_w, _ = geod.fwd(lon, lat, 270, radius_km * 1000)
    lon_e, lat_e, _ = geod.fwd(lon, lat, 90, radius_km * 1000)
    lon_s, lat_s, _ = geod.fwd(lon, lat, 180, radius_km * 1000)
    lon_n, lat_n, _ = geod.fwd(lon, lat, 0, radius_km * 1000)

    min_lon = min(lon_w, lon_e)
    max_lon = max(lon_w, lon_e)
    min_lat = min(lat_s, lat_n)
    max_lat = max(lat_s, lat_n)

    return min_lon, min_lat, max_lon, max_lat


def clip_raster_to_bbox(input_tif: Path, output_tif: Path, bbox_wgs84: Tuple[float, float, float, float]):
    """
    Clip raster to bbox.
    Works best if raster CRS is EPSG:4326.
    If raster CRS is projected, this bbox may not match correctly.
    """
    print(f"\n[Clip] Input : {input_tif}")
    print(f"[Clip] Output: {output_tif}")
    print(f"[Clip] BBOX  : {bbox_wgs84}")

    with rasterio.open(input_tif) as src:
        if src.crs is None:
            raise RuntimeError("Raster CRS missing. Cannot clip reliably.")

        # If geographic, bbox works directly. If projected, user should pre-clip in QGIS.
        if src.crs.is_geographic:
            min_lon, min_lat, max_lon, max_lat = bbox_wgs84
            window = from_bounds(min_lon, min_lat, max_lon, max_lat, transform=src.transform)
        else:
            # fallback approximation: bbox will likely be wrong
            raise RuntimeError(
                f"Raster CRS is projected ({src.crs}).\n"
                f"This script currently clips using EPSG:4326 bbox.\n"
                f"✅ Solution: download GHSL in geographic CRS OR clip manually in QGIS.\n"
            )

        window = window.round_offsets().round_lengths()

        data = src.read(1, window=window)
        transform = src.window_transform(window)

        profile = src.profile
        profile.update({"height": data.shape[0], "width": data.shape[1], "transform": transform})

        output_tif.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(output_tif, "w", **profile) as dst:
            dst.write(data, 1)

    print("[Clip] Completed ✅")


def quick_raster_check(tif_path: Path):
    with rasterio.open(tif_path) as ds:
        arr = ds.read(1).astype(np.float64)
        if ds.nodata is not None:
            arr[arr == ds.nodata] = np.nan

        print("\n[Check] Raster info:")
        print(f"  CRS     : {ds.crs}")
        print(f"  Shape   : {arr.shape}")
        print(f"  Bounds  : {ds.bounds}")
        print(f"  Min/Max : {np.nanmin(arr):.2f} / {np.nanmax(arr):.2f}")
        print(f"  Mean    : {np.nanmean(arr):.2f}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("GHSL BUILT-UP DOWNLOAD + CLIPPER")
    print("=" * 80)
    print(f"Leak point      : {Config.LAT}, {Config.LON}")
    print(f"Clip radius (km): {Config.CLIP_RADIUS_KM}")
    print(f"Output folder   : {Config.OUTPUT_DIR}")
    print("=" * 80)

    # Step 1: Resolve input tif path
    input_tif_path: Optional[Path] = None

    if Config.GHSL_TIF_URL.strip():
        url = Config.GHSL_TIF_URL.strip()
        filename = url.split("/")[-1].split("?")[0] or "ghsl_builtup.tif"
        input_tif_path = Config.OUTPUT_DIR / filename
        download_file(url, input_tif_path)

    elif Config.LOCAL_GHSL_TIF.strip():
        input_tif_path = Path(Config.LOCAL_GHSL_TIF.strip())
        if not input_tif_path.exists():
            print(f"\n❌ LOCAL_GHSL_TIF not found: {input_tif_path}")
            sys.exit(1)

    else:
        print("\n❌ ERROR: No GHSL raster input provided.")
        print("✅ Provide one of the following:")
        print("   1) Config.GHSL_TIF_URL = '<direct tif link>'")
        print("   2) Config.LOCAL_GHSL_TIF = '<path to local ghsl tif>'")
        print("\nDataset info reference:")
        print("  GHS-BUILT-S R2023A (built-up surface) page:")
        print("  https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php")
        sys.exit(1)

    # Step 2: Clip around location
    bbox = compute_bbox_from_radius_km(Config.LAT, Config.LON, Config.CLIP_RADIUS_KM)
    out_tif = Config.OUTPUT_DIR / f"ghsl_builtup_clip_{Config.CLIP_RADIUS_KM}km.tif"

    clip_raster_to_bbox(input_tif_path, out_tif, bbox)

    # Step 3: Quick check
    quick_raster_check(out_tif)

    print("\n✅ DONE!")
    print(f"Use this in your PAR code:\n  {out_tif}\n")


if __name__ == "__main__":
    main()
