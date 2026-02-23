"""
download_worldpop_and_clip.py (Fixed Version with Better Error Handling)
========================================================================

✅ Downloads WorldPop data with fallback methods
"""

import sys
import requests
from pathlib import Path
from typing import Tuple

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from pyproj import Geod


class Config:
    ISO3 = "PAK"  # Pakistan
    LAT = 31.691100
    LON = 74.082167
    CLIP_RADIUS_KM = 20
    OUTPUT_DIR = Path("data/population")
    
    # Direct WorldPop FTP URL (alternative to STAC)
    # Format: https://data.worldpop.org/GIS/Population/Global_2000_2020/<YEAR>/<ISO3>/<ISO3>_ppp_<YEAR>_UNadj.tif
    WORLDPOP_FTP_BASE = "https://data.worldpop.org/GIS/Population/Global_2000_2020"
    YEAR = "2020"  # Latest available year


def http_get_json_safe(url: str):
    """HTTP GET with detailed error reporting"""
    try:
        r = requests.get(url, timeout=60)
        print(f"[HTTP] Status: {r.status_code}")
        print(f"[HTTP] Content-Type: {r.headers.get('Content-Type', 'unknown')}")
        
        if r.status_code != 200:
            print(f"[ERROR] HTTP {r.status_code}: {r.text[:500]}")
            return None
            
        # Try to parse JSON
        try:
            return r.json()
        except Exception as e:
            print(f"[ERROR] JSON parse failed: {e}")
            print(f"[ERROR] Response text: {r.text[:500]}")
            return None
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return None


def download_file(url: str, out_path: Path, chunk_size: int = 1024 * 1024) -> Path:
    """Download file with progress"""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n[Download] {url}")
    print(f"[Save]     {out_path}")

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


def compute_bbox_from_radius_km(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    """Compute bounding box around (lat, lon) using geodesic distance"""
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
    """Clip raster using bbox in EPSG:4326 space"""
    print(f"\n[Clip] Input : {input_tif}")
    print(f"[Clip] Output: {output_tif}")
    print(f"[Clip] BBOX  : {bbox_wgs84}")

    with rasterio.open(input_tif) as src:
        if src.crs is None:
            raise RuntimeError("Raster CRS is missing. Cannot reliably clip.")
        if str(src.crs).upper() not in ["EPSG:4326", "OGC:CRS84"]:
            print(f"[WARN] Raster CRS = {src.crs} (expected EPSG:4326). Clipping still attempted...")

        min_lon, min_lat, max_lon, max_lat = bbox_wgs84

        window = from_bounds(min_lon, min_lat, max_lon, max_lat, transform=src.transform)
        window = window.round_offsets().round_lengths()

        data = src.read(1, window=window)
        transform = src.window_transform(window)

        profile = src.profile
        profile.update({
            "height": data.shape[0],
            "width": data.shape[1],
            "transform": transform
        })

        output_tif.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(output_tif, "w", **profile) as dst:
            dst.write(data, 1)

    print("[Clip] Completed ✅")


def quick_check(tif_path: Path):
    """Quick stats on raster"""
    with rasterio.open(tif_path) as ds:
        arr = ds.read(1).astype(np.float64)

        if ds.nodata is not None:
            arr[arr == ds.nodata] = np.nan

        print("\n[Check] Raster summary:")
        print(f"  CRS     : {ds.crs}")
        print(f"  Shape   : {arr.shape}")
        print(f"  Bounds  : {ds.bounds}")
        print(f"  Min/Max : {np.nanmin(arr):.2f} / {np.nanmax(arr):.2f}")
        print(f"  Mean    : {np.nanmean(arr):.2f}")
        print(f"  Total Pop: {np.nansum(arr):.0f}")


def try_stac_download() -> str:
    """Try STAC API (may fail)"""
    print("\n[Method 1] Trying STAC API...")
    stac_url = f"https://stac.worldpop.org/collections/{Config.ISO3}"
    
    result = http_get_json_safe(stac_url)
    if result and "assets" in result:
        # Find best TIF asset
        assets = result["assets"]
        for key, meta in assets.items():
            href = meta.get("href", "")
            if href.lower().endswith(".tif") or href.lower().endswith(".tiff"):
                print(f"[STAC] Found asset: {key} -> {href}")
                return href
    
    print("[STAC] Failed or no assets found")
    return None


def try_direct_ftp_download() -> str:
    """Fallback: Direct FTP URL"""
    print("\n[Method 2] Trying direct FTP URL...")
    
    # WorldPop naming: <ISO3>_ppp_<YEAR>_UNadj.tif
    filename = f"{Config.ISO3.lower()}_ppp_{Config.YEAR}_UNadj.tif"
    url = f"{Config.WORLDPOP_FTP_BASE}/{Config.YEAR}/{Config.ISO3.upper()}/{filename}"
    
    print(f"[FTP] Trying: {url}")
    
    # Check if URL exists
    try:
        r = requests.head(url, timeout=30)
        if r.status_code == 200:
            print(f"[FTP] Found! File size: {int(r.headers.get('Content-Length', 0))/1e6:.1f} MB")
            return url
        else:
            print(f"[FTP] Not found (status {r.status_code})")
    except Exception as e:
        print(f"[FTP] Failed: {e}")
    
    return None


def main():
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("WORLDPOP AUTO DOWNLOADER + CLIPPER (FIXED VERSION)")
    print("=" * 80)
    print(f"ISO3        : {Config.ISO3}")
    print(f"Leak point  : {Config.LAT}, {Config.LON}")
    print(f"Radius (km) : {Config.CLIP_RADIUS_KM}")
    print(f"Year        : {Config.YEAR}")
    print("=" * 80)

    try:
        # Try STAC first, fallback to FTP
        tif_url = try_stac_download()
        if not tif_url:
            tif_url = try_direct_ftp_download()
        
        if not tif_url:
            raise RuntimeError(
                "All download methods failed. Please:\n"
                "1. Check internet connection\n"
                "2. Verify ISO3 code is correct\n"
                "3. Try manual download from: https://hub.worldpop.org/geodata/listing?id=29"
            )

        # Download
        raw_tif_path = Config.OUTPUT_DIR / f"worldpop_{Config.ISO3}_raw.tif"
        download_file(tif_url, raw_tif_path)

        # Clip
        bbox = compute_bbox_from_radius_km(Config.LAT, Config.LON, Config.CLIP_RADIUS_KM)
        out_tif = Config.OUTPUT_DIR / f"worldpop_{Config.ISO3}_clip_{Config.CLIP_RADIUS_KM}km.tif"
        clip_raster_to_bbox(raw_tif_path, out_tif, bbox)

        # Check
        quick_check(out_tif)

        print("\n✅ DONE!")
        print(f"Output: {out_tif.absolute()}\n")
        
        return str(out_tif.absolute())

    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
