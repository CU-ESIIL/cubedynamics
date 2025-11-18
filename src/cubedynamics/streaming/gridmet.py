from __future__ import annotations

import io
from typing import Any, Dict, Optional

import requests
import xarray as xr
from xarray.backends.plugins import list_engines

GRIDMET_BASE_URL = "https://www.northwestknowledge.net/metdata/data"
_ENGINE_PREFERENCE = ("h5netcdf", "netcdf4", "scipy")
_AVAILABLE_ENGINES = list_engines()


def _select_stream_engine() -> Optional[str]:
    """Pick the best available xarray engine for streaming gridMET files."""

    for engine in _ENGINE_PREFERENCE:
        if engine in _AVAILABLE_ENGINES:
            return engine
    return None


_STREAM_ENGINE = _select_stream_engine()


def _prepare_stream_target(buf: io.BytesIO, engine: Optional[str]) -> Any:
    """Return an object suitable for xr.open_dataset for the chosen engine."""

    if engine == "netcdf4":
        # The netCDF4 backend cannot consume BytesIO objects directly, but it can
        # read from a ``bytes`` or ``memoryview`` buffer. ``getbuffer`` avoids an
        # extra copy while keeping the in-memory constraint intact.
        return memoryview(buf.getbuffer())

    if engine == "scipy":
        # SciPy prefers plain bytes. ``getvalue`` makes a copy, but we only fall
        # back here when h5netcdf/netCDF4 are unavailable.
        return buf.getvalue()

    # Default to BytesIO for h5netcdf (the validated path) and for any other
    # engines that support file-like objects.
    buf.seek(0)
    return buf


def _bbox_from_geojson(aoi_geojson: Dict) -> Dict[str, float]:
    """
    Compute a simple lat/lon bounding box from a GeoJSON polygon (EPSG:4326).
    Assumes geometry["type"] == "Polygon" and uses the outer ring.
    """
    geom = aoi_geojson.get("geometry", aoi_geojson)
    coords = geom["coordinates"][0]
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return {
        "south": float(min(lats)),
        "north": float(max(lats)),
        "west": float(min(lons)),
        "east": float(max(lons)),
    }


def _open_gridmet_year(
    variable: str,
    year: int,
    chunks: Optional[Dict[str, int]] = None,
) -> xr.Dataset:
    """
    Download a single gridMET year fully in memory and open it with the best
    available xarray backend (preferring the validated h5netcdf path).
    """
    url = f"{GRIDMET_BASE_URL}/{variable}_{year}.nc"

    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()

    buf = io.BytesIO()
    for chunk in resp.iter_content(chunk_size=1024 * 1024):  # 1 MB chunks
        if not chunk:
            break
        buf.write(chunk)
    buf.seek(0)

    open_kwargs = {
        "decode_times": True,
        "chunks": chunks,
    }
    if _STREAM_ENGINE is None:
        raise RuntimeError(
            "No suitable xarray IO engine is available. Install 'h5netcdf' or "
            "'netCDF4' to stream gridMET data."
        )

    open_kwargs["engine"] = _STREAM_ENGINE

    stream_target = _prepare_stream_target(buf, _STREAM_ENGINE)
    ds = xr.open_dataset(stream_target, **open_kwargs)

    # gridMET uses "day" as the time dimension; normalize to "time"
    if "day" in ds.dims:
        ds = ds.rename({"day": "time"})
    if "day" in ds.coords:
        ds = ds.rename({"day": "time"})

    return ds


def stream_gridmet_to_cube(
    aoi_geojson: Dict,
    variable: str,
    start: str,
    end: str,
    freq: str = "D",
    chunks: Optional[Dict[str, int]] = None,
) -> xr.DataArray:
    """
    Stream a gridMET subset as an xarray.DataArray "cube" for a given AOI.

    Parameters
    ----------
    aoi_geojson
        GeoJSON Feature or geometry in EPSG:4326.
    variable
        gridMET variable name, e.g. "pr", "tmmx", "tmmn", "vs", "erc", etc.
    start, end
        Time range in ISO format, e.g. "2000-01-01".
    freq
        Output time frequency. "D" for daily; "MS" for monthly start, etc.
    chunks
        Optional dask-style chunk mapping, e.g. {"time": 365}.

    Returns
    -------
    xr.DataArray
        A cube with dims (time, lat, lon), already cropped to the AOI and
        resampled to the requested frequency.
    """
    # Parse years from the date strings
    start_year = int(start[:4])
    end_year = int(end[:4])

    # 1) Load all needed years into a list of Datasets
    year_chunks = chunks or {"time": 366}
    ds_list = []
    for year in range(start_year, end_year + 1):
        ds_y = _open_gridmet_year(variable, year, chunks=year_chunks)
        ds_list.append(ds_y)

    # 2) Concatenate along the normalized time axis and clip to [start, end]
    ds = xr.concat(ds_list, dim="time")
    ds = ds.sel(time=slice(start, end))

    # 3) Spatial subset using the AOI bbox
    bbox = _bbox_from_geojson(aoi_geojson)
    da = ds[variable].sel(
        lat=slice(bbox["south"], bbox["north"]),
        lon=slice(bbox["west"], bbox["east"]),
    )

    # 4) Optional resampling in time (e.g., to monthly)
    if freq != "D":
        da = da.resample(time=freq).mean()

    da.name = variable
    return da


__all__ = ["stream_gridmet_to_cube"]
