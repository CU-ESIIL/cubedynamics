"""Read one catalog-discovered 3DEP tile window, never a complete DEM.

Discovery: https://tnmaccess.nationalmap.gov/api/v1/docs
The Current catalog tag selects current products even when the asset URL
contains /historical/. Filename freshness is not a discovery strategy.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
import rasterio
from rasterio.windows import Window, from_bounds
from rasterio.warp import transform_bounds
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.data.qa import evaluate_qa_profile
from cubedynamics.data.lifecycle import UpstreamIdentity
from cubedynamics.data.schema import normalize_xarray_schema, schema_fingerprint
from examples.source_projects._evidence import AccessBlocked, fetch, json_get, save_report

CATALOG = "https://tnmaccess.nationalmap.gov/api/v1/products"
BBOX = (-105.300, 39.985, -105.291, 39.994)
MAX_SIDE = 256


def pixel_window(bbox, crs, transform, width, height):
    """WGS84 bounds -> native CRS -> outward-rounded full pixel cells.

    Preserve native north-up row orientation. Reject non-overlap, rotated grids
    and requests beyond 256 pixels per side *before* accessing raster values.
    """
    west, south, east, north = bbox
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("Invalid geographic bounds")
    if transform.b or transform.d or transform.a <= 0 or transform.e >= 0 or crs is None:
        raise ValueError("Only explicit north-up CRS rasters are supported")
    native = transform_bounds("EPSG:4326", crs, *bbox, densify_pts=21)
    raw = from_bounds(*native, transform=transform)
    # Tolerance prevents a floating-point hair beyond an exact grid edge from
    # adding a whole extra cell; genuinely fractional edges expand outwards.
    left, top = math.floor(raw.col_off + 1e-7), math.floor(raw.row_off + 1e-7)
    right = math.ceil(raw.col_off + raw.width - 1e-7)
    bottom = math.ceil(raw.row_off + raw.height - 1e-7)
    if right - left > MAX_SIDE or bottom - top > MAX_SIDE:
        raise ValueError("Requested window exceeds 256 pixels per side")
    left, top, right, bottom = max(0, left), max(0, top), min(width, right), min(height, bottom)
    if left >= right or top >= bottom:
        raise ValueError("AOI does not overlap tile")
    return Window(left, top, right - left, bottom - top), native


def elevation(tile, bbox=BBOX):
    """Project-owned noun: bounded eager 2-D elevation, no invented time axis.

    Native cells/CRS/nodata are preserved; no resampling or vertical conversion.
    GDAL makes remote HTTP Range requests. Caller captures its HTTP diagnostics.
    """
    url = tile["downloadURL"]
    if not (-106 <= bbox[0] < bbox[2] <= -105 and 39 <= bbox[1] < bbox[3] <= 40):
        raise ValueError("This proof is limited to the Boulder n40w106 CONUS tile")
    if not url.startswith("https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/") or not url.endswith(".tif"):
        raise ValueError("Expected catalog-owned 1/3 arc-second GeoTIFF")
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif", CPL_CURL_VERBOSE=True,
            GDAL_HTTP_NETRC="NO", GDAL_HTTP_MAX_RETRY="0", GDAL_HTTP_TIMEOUT="40"):
        with rasterio.open(url) as raster:
            window, native_bounds = pixel_window(bbox, raster.crs, raster.transform,
                                                 raster.width, raster.height)
            if raster.count != 1 or max(raster.block_shapes[0]) > 1024:
                raise ValueError("Unexpected band count/block size; refusing raster read")
            values = raster.read(1, window=window, masked=True).astype("float64").filled(np.nan)
            transform = raster.window_transform(window)
            cube = xr.DataArray(values, dims=("y", "x"), name="elevation",
                coords={"x": transform.c + (np.arange(window.width) + .5) * transform.a,
                        "y": transform.f + (np.arange(window.height) + .5) * transform.e},
                attrs={"units": "m", "crs": raster.crs.to_string(), "source": "USGS 3DEP",
                       "scientific_noun": "elevation", "source_flavor": "usgs_3dep",
                       "source_mode": "snapshot", "is_synthetic": False,
                       "vertical_datum": "NAVD88 (catalog CONUS product description)",
                       "requested_bbox_wgs84": list(bbox), "native_bbox": list(native_bounds),
                       "transform": list(transform), "source_nodata": raster.nodata,
                       "pixel_window": [window.col_off, window.row_off, window.width, window.height],
                       "tile": json.dumps(tile, sort_keys=True), "source_url": url,
                       "source_shape": [raster.height, raster.width],
                       "block_shapes": list(raster.block_shapes), "resampling": "none"})
            return cube


def range_evidence(log):
    """Count actual GDAL requested byte intervals, conservatively including repeats."""
    ranges = [(int(a), int(b)) for a, b in re.findall(r"Range: bytes=(\d+)-(\d+)", log)]
    statuses = re.findall(r"< HTTP/[\d.]+ (\d+)", log)
    return {"ranges": ranges, "requested_bytes_upper_bound": sum(b-a+1 for a,b in ranges),
            "statuses": statuses, "range_response_count": statuses.count("206")}


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    trace, evidence = [], {"bbox": BBOX, "source_mode": "snapshot"}
    gates = {k: "NOT_TESTED" for k in ("retrieval", "bounded_access", "identity", "schema", "numerical_qa", "visual_qa")}
    try:
        catalog = json_get(CATALOG, params={"datasets": "National Elevation Dataset (NED) 1/3 arc-second Current",
            "bbox": ",".join(map(str, BBOX)), "max": 10, "prodFormats": "GeoTIFF"}, evidence=trace)
        if catalog.get("errors") or catalog["total"] != 1 or len(catalog["items"]) != 1:
            raise ValueError("Expected exactly one current tile; no arbitrary first-result selection")
        tile = catalog["items"][0]
        (output / "catalog.json").write_text(json.dumps(catalog, indent=2))
        header = fetch(tile["downloadURL"], headers={"Range": "bytes=0-16383"},
                       max_bytes=16384, evidence=trace)
        if trace[-1]["status"] != 206 or len(header) != 16384:
            raise ValueError("Server did not honor bounded Range probe")
        # Isolate GDAL's process-global curl log. Nothing from the full tile is
        # written; worker persists only the bounded 2-D scientific sample.
        with (output / "gdal-http.log").open("w") as log:
            result = subprocess.run([sys.executable, "-m", "examples.source_projects.three_dep.proof", "--worker", str(output)],
                                    stderr=log, capture_output=False, timeout=100)
        if result.returncode:
            error_path=output/"worker-error.json"
            error=json.loads(error_path.read_text()) if error_path.exists() else {}
            if error.get("kind")=="schema_or_adapter":
                raise ValueError(error["message"])
            raise AccessBlocked("GDAL worker failed; inspect gdal-http.log and worker-error.json")
        cube = xr.load_dataarray(output / "sample.nc", engine="h5netcdf")
        network = range_evidence((output / "gdal-http.log").read_text())
        bounded = bool(network["ranges"]) and network["range_response_count"] == len(network["ranges"])
        bounded &= network["requested_bytes_upper_bound"] < min(tile["sizeInBytes"] / 10, 8_000_000)
        gates.update(retrieval="PASS", identity="PASS", bounded_access="PASS" if bounded else "FAIL")
        profile = evaluate_qa_profile("continuous_raster_static", cube)
        finite = np.isfinite(cube.values)
        stats = {"shape": list(cube.shape), "finite_fraction": float(finite.mean()),
                 "min_m": float(cube.min()), "max_m": float(cube.max()),
                 "mean_m": float((pipe(cube) | v.mean(dim=("y", "x"))).unwrap())}
        numerical = profile.passed and finite.mean() > .95 and stats["min_m"] < stats["max_m"]
        gates.update(schema="PASS" if profile.passed else "FAIL", numerical_qa="PASS" if numerical else "FAIL")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 5), layout="constrained")
        cube.plot(ax=ax, cmap="terrain", cbar_kwargs={"label": "Elevation (m, NAVD88)"})
        ax.set(title="Real USGS 3DEP · Boulder foothills", xlabel="Longitude (NAD83)", ylabel="Latitude (NAD83)")
        ax.ticklabel_format(useOffset=False, style="plain")
        fig.savefig(output / "terrain.png", dpi=150)
        plt.close(fig)
        evidence.update(tile=tile, network=network, numerical=stats, qa_profile=profile.as_dict(),
                        schema=normalize_xarray_schema(cube), schema_fingerprint=schema_fingerprint(cube),
                        figure="terrain.png", pixel_metadata={k: v.tolist() if isinstance(v, np.ndarray) else
                            v.item() if isinstance(v, np.generic) else v for k,v in cube.attrs.items()})
        evidence["upstream_identity"]=UpstreamIdentity(provider="USGS",product="3DEP 1/3 arc-second DEM",
            endpoint=CATALOG,strategy={"kind":"catalog_current_tile_version"},
            observed={"source_id":tile["sourceId"],"asset":tile["downloadURL"],"publication_date":tile["publicationDate"],
                      "etag":trace[-1]["headers"]["ETag"],"last_modified":trace[-1]["headers"]["Last-Modified"]},
            retrieved_at=trace[0]["retrieved_at"]).as_dict()
    except (AccessBlocked, subprocess.TimeoutExpired) as exc:
        gates["retrieval"] = "BLOCKED"
        evidence["blocker"] = str(exc)
    except (ValueError, KeyError) as exc:
        gates["retrieval"] = "FAIL"
        evidence["failure"] = str(exc)
    evidence["http"] = trace
    return save_report(output / "report.json", gates=gates, evidence=evidence,
        caveats=("One tile/window only; not a continent-wide or vertical-accuracy certification.",
                 "Visual review is separate; static raster is not a time cube."))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/source_qa/three_dep"))
    parser.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker:
        try:
            tile = json.loads((args.worker / "catalog.json").read_text())["items"][0]
            cube = elevation(tile)
            cube.attrs["is_synthetic"] = 0  # NetCDF attrs do not encode booleans.
            cube.to_netcdf(args.worker / "sample.nc", engine="h5netcdf")
        except Exception as exc:
            kind="access" if isinstance(exc,rasterio.errors.RasterioIOError) else "schema_or_adapter"
            (args.worker/"worker-error.json").write_text(json.dumps({"kind":kind,"message":str(exc)}))
            raise
    else:
        result = run(args.output)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["certification"]["outcome"].startswith("PASS") else 2)
