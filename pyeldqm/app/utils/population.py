"""
utils/population.py
===================
Rasterio-based PAR population count helper.  Zero Dash / callback imports.
"""

import logging
import os
import numpy as np

logger = logging.getLogger(__name__)


def compute_par_counts_from_raster(raster_path: str, threat_zones: dict) -> tuple[dict, str]:
    """Sum raster population values within AEGL threat zone polygons.

    Parameters
    ----------
    raster_path  : Absolute path to a WorldPop-compatible GeoTIFF.
    threat_zones : Dict mapping zone names ('AEGL-1', 'AEGL-2', 'AEGL-3')
                   to Shapely polygons.

    Returns
    -------
    counts : dict  {zone_name: int}
    message: str   human-readable status / error message
    """
    counts: dict[str, int] = {"AEGL-3": 0, "AEGL-2": 0, "AEGL-1": 0}

    if not raster_path:
        msg = "Select a population raster (.tif/.tiff) to compute PAR."
        logger.warning(msg)
        return counts, msg

    if not os.path.exists(raster_path):
        msg = f"Population raster not found: {raster_path}"
        logger.warning(msg)
        return counts, msg

    if not raster_path.lower().endswith((".tif", ".tiff")):
        msg = "Invalid raster format. Please select a GeoTIFF file (.tif/.tiff)."
        logger.warning(msg)
        return counts, msg

    non_empty_zones = {
        k: v for k, v in threat_zones.items()
        if v is not None and not v.is_empty
    }
    if not non_empty_zones:
        msg = "No threat zones generated. Please calculate threat zones first."
        logger.warning(msg)
        return counts, msg

    logger.debug("Non-empty zones: %s", list(non_empty_zones.keys()))

    try:
        import rasterio
        from rasterio.mask import mask
        from rasterio.warp import transform_geom
        from shapely.geometry import mapping

        with rasterio.open(raster_path) as dataset:
            nodata = dataset.nodata
            raster_crs = dataset.crs
            logger.debug(
                "Raster bounds: %s, CRS: %s, NoData: %s",
                dataset.bounds, raster_crs, nodata,
            )

            for zone_name in ["AEGL-3", "AEGL-2", "AEGL-1"]:
                zone_poly = threat_zones.get(zone_name)
                if zone_poly is None or zone_poly.is_empty:
                    counts[zone_name] = 0
                    logger.debug("%s: empty or None", zone_name)
                    continue

                try:
                    zone_geom = mapping(zone_poly)
                    logger.debug("%s bounds: %s", zone_name, zone_poly.bounds)

                    crs_str = str(raster_crs).upper() if raster_crs else ""
                    if raster_crs and crs_str not in ("EPSG:4326", "OGC:CRS84", "WGS 84"):
                        try:
                            zone_geom = transform_geom("EPSG:4326", raster_crs, zone_geom)
                            logger.debug("%s: transformed EPSG:4326 → %s", zone_name, raster_crs)
                        except Exception as crs_err:
                            logger.warning(
                                "%s: CRS transform failed (using as-is): %s",
                                zone_name, crs_err,
                            )

                    clipped, _ = mask(dataset, [zone_geom], crop=True, all_touched=True)
                    pop = clipped[0].astype(np.float64)
                    logger.debug(
                        "%s clipped shape: %s, non-zero pixels: %d",
                        zone_name, pop.shape, int(np.count_nonzero(pop)),
                    )

                    if nodata is not None:
                        pop[pop == nodata] = np.nan
                    pop = np.nan_to_num(pop, nan=0.0, posinf=0.0, neginf=0.0)
                    count = int(max(np.sum(pop), 0))
                    counts[zone_name] = count
                    logger.debug("%s population sum: %d", zone_name, count)

                except Exception as exc:
                    counts[zone_name] = 0
                    logger.exception("Error processing %s: %s", zone_name, exc)

        return counts, "PAR calculated from selected population raster."

    except Exception as exc:
        msg = f"Unable to process raster for PAR: {exc}"
        logger.exception(msg)
        return counts, msg
