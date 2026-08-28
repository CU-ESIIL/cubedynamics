"""Single-tile native 3DEP candidate with enforced bounded HTTP range reads."""
from __future__ import annotations

import json
import math
import re
from pathlib import PurePosixPath
from urllib.parse import urlsplit

import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import Window, from_bounds
import xarray as xr

from ._ranges import RangeFile
from ._transport import SourceClient, ReadLimits, SourceSchemaError, SourceBudgetError

CATALOG = "https://tnmaccess.nationalmap.gov/api/v1/products"
CONTRACT = "3dep-native-single-tile-v1"


def _bbox(bbox):
    west, south, east, north = map(float, bbox)
    if not (-125 <= west < east <= -66 and 24 <= south < north <= 50
            and east - west <= .02 and north - south <= .02):
        raise ValueError("Candidate supports CONUS bounds <=0.02 degrees per side, without antimeridian wrap")
    return west, south, east, north


def pixel_window(bbox, crs, transform, width, height):
    """Outward native cells; reject partial coverage, never silently clip."""
    _bbox(bbox)
    if crs is None or transform.b or transform.d or transform.a <= 0 or transform.e >= 0:
        raise SourceSchemaError("Only explicit north-up raster CRS is supported")
    native = transform_bounds("EPSG:4326", crs, *bbox, densify_pts=21)
    raw = from_bounds(*native, transform=transform)
    left, top = math.floor(raw.col_off + 1e-7), math.floor(raw.row_off + 1e-7)
    right, bottom = math.ceil(raw.col_off + raw.width - 1e-7), math.ceil(raw.row_off + raw.height - 1e-7)
    if left < 0 or top < 0 or right > width or bottom > height:
        raise SourceSchemaError("AOI crosses tile coverage; candidate does not mosaic or return partial coverage")
    if not 0 < right - left <= 256 or not 0 < bottom - top <= 256:
        raise SourceBudgetError("Requested window exceeds 256 native pixels per side")
    return Window(left, top, right-left, bottom-top), native


def elevation(*, bbox, source="usgs_3dep", tile_id=None, snapshot_dir=None, offline=False):
    """Read one fully covering 1/3 arc-second tile, preserving native cells.

    Candidate API: CONUS, <=0.02° each side and <=256 native pixels each side,
    one unambiguous tile, 8 MB body / 80 request / 180 s budget. No mosaicking,
    resampling, vertical conversion or synthetic time dimension. Requires
    Rasterio >=1.4 for its Python opener; older versions fail before network.
    Explicit snapshots can be replayed offline on the same decoder stack.
    Without ``tile_id``, require exactly one catalog-tagged Current tile. An
    explicit ScienceBase ``tile_id`` selects a version from the broader product
    catalog; it is NOT asserted current. Missing current coverage never falls
    back to an arbitrary historical record.
    """
    if source != "usgs_3dep":
        raise ValueError("Only source='usgs_3dep' is implemented")
    bbox = _bbox(bbox)
    if tile_id is not None and (not isinstance(tile_id, str) or not re.fullmatch(r"[a-fA-F0-9]{24}", tile_id)):
        raise ValueError("tile_id must be an exact 24-character ScienceBase ID")
    if tuple(map(int, rasterio.__version__.split(".")[:2])) < (1, 4):
        raise ImportError("Bounded 3DEP requires rasterio>=1.4; no uncapped GDAL fallback")
    with SourceClient(origins={"https://tnmaccess.nationalmap.gov", "https://prd-tnm.s3.amazonaws.com"},
                      limits=ReadLimits(requests=80, bytes=8_000_000),
                      snapshot_dir=snapshot_dir, offline=offline) as client:
        dataset = "National Elevation Dataset (NED) 1/3 arc-second" + (" Current" if tile_id is None else "")
        catalog = client.json(CATALOG, params={"datasets": dataset,
            "bbox": ",".join(map(str, bbox)), "max": 10, "prodFormats": "GeoTIFF"})
        items = catalog.get("items", [])
        if catalog.get("errors") or catalog.get("total") != len(items):
            raise SourceSchemaError("Incomplete/error catalog response; no implicit pagination")
        if tile_id is not None:
            items = [item for item in items if item.get("sourceId") == tile_id]
        if len(items) != 1:
            raise SourceSchemaError("Expected one unambiguous current tile; no arbitrary first-result selection")
        tile = items[0]
        url = tile["downloadURL"]
        if not url.startswith("https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/") or not url.endswith(".tif"):
            raise SourceSchemaError("Unexpected 3DEP catalog asset")
        # GDAL accesses Python range files only. Sidecars are disabled; there is
        # no native /vsicurl path that could bypass the query-wide byte budget.
        filename = PurePosixPath(urlsplit(url).path).name
        def opener(path, mode="rb"):
            if path != filename or mode not in ("r", "rb"):
                raise FileNotFoundError(path)
            return RangeFile(url, client)
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_PAM_ENABLED="NO"):
            with rasterio.open(filename, opener=opener, driver="GTiff") as raster:
                window, native = pixel_window(bbox, raster.crs, raster.transform, raster.width, raster.height)
                if raster.count != 1 or max(raster.block_shapes[0]) > 1024 or raster.nodata is None:
                    raise SourceSchemaError("Unexpected bands, blocks, or missing nodata metadata")
                values = raster.read(1, window=window, masked=True).astype("float64").filled(np.nan)
                transform = raster.window_transform(window)
                cube = xr.DataArray(values, name="elevation", dims=("y", "x"),
                    coords={"x": transform.c + (np.arange(int(window.width)) + .5) * transform.a,
                            "y": transform.f + (np.arange(int(window.height)) + .5) * transform.e},
                    attrs={"units": "m", "crs": raster.crs.to_string(), "source": "USGS 3DEP",
                           "scientific_noun": "elevation", "source_flavor": "usgs_3dep", "source_mode": "snapshot",
                           "is_synthetic": 0, "release_status": "candidate_not_certified",
                           "interpretation_contract": CONTRACT, "requested_bbox_wgs84": list(bbox),
                           "native_bbox": list(native), "source_nodata": raster.nodata,
                           "transform": list(transform), "source_url": url,
                           "catalog_selection": "current" if tile_id is None else "explicit_version_not_asserted_current",
                           "vertical_datum": "NAVD88 per CONUS product description; tile-specific accuracy not certified",
                           "tile": json.dumps(tile, sort_keys=True), "resampling": "none"})
        cube.attrs["provenance"] = json.dumps(client.trace, sort_keys=True)
        cube.attrs["body_bytes"] = client.bytes
        return cube


__all__ = ["elevation"]
