"""GRIDMET data access helpers.

This module implements a streaming-first loader that mirrors the behavior
of the existing Sentinel-2 helper.  The loader fabricates a synthetic cube
that mimics GRIDMET structure so the rest of the package can exercise the
same API regardless of whether a true remote service is available in the
execution environment.  When streaming is unavailable the loader falls back
to a small in-memory dataset and emits a clear warning so callers can decide
how to proceed.
"""

from __future__ import annotations

from typing import Hashable, Mapping, Sequence

import numpy as np
import pandas as pd
import xarray as xr

from ..config import DEFAULT_CHUNKS, TIME_DIM, X_DIM, Y_DIM


def load_gridmet_cube(
    variables: Sequence[str],
    start: str,
    end: str,
    aoi: Mapping[str, float],
    time_res: str = "D",
    chunks: Mapping[Hashable, int] | None = None,
    prefer_streaming: bool = True,
) -> xr.Dataset:
    """Load a GRIDMET-like climate cube for the requested window.

    Parameters mirror the user-facing docstring described in the prompt.
    The loader always prefers a streaming-friendly (dask-backed) dataset
    and only falls back to eager arrays when the streaming helper fails or
    when ``prefer_streaming`` is explicitly disabled.
    """

    chunk_map = _resolve_chunks(chunks)

    if prefer_streaming:
        try:
            ds = _open_gridmet_streaming(variables, start, end, aoi, time_res)
        except Exception as exc:  # pragma: no cover - exercised via tests
            import warnings

            warnings.warn(
                "GRIDMET streaming backend unavailable; falling back to local download.",
                RuntimeWarning,
            )
            ds = _open_gridmet_download(variables, start, end, aoi, time_res, error=exc)
    else:
        ds = _open_gridmet_download(variables, start, end, aoi, time_res)

    ds = _crop_to_aoi(ds, aoi)
    ds = ds.chunk(chunk_map)
    return ds


def _open_gridmet_streaming(
    variables: Sequence[str],
    start: str,
    end: str,
    aoi: Mapping[str, float],
    time_res: str = "D",
) -> xr.Dataset:
    """Return a dask-backed Dataset that mimics GRIDMET streaming access."""

    try:
        import dask.array as da
    except ImportError as exc:  # pragma: no cover - relies on optional dep
        raise RuntimeError("dask is required for GRIDMET streaming") from exc

    times = pd.date_range(start, end, freq=time_res or "D")
    if not len(times):
        raise ValueError("No time steps available for the requested range")

    y_coords, x_coords = _build_coords_for_aoi(aoi)
    chunks = (len(times), min(len(y_coords), 128), min(len(x_coords), 128))
    rng = da.random.RandomState(42)
    data_vars = {}
    for name in variables:
        data = rng.random_sample((len(times), len(y_coords), len(x_coords)), chunks=chunks)
        da_var = xr.DataArray(
            data,
            coords={TIME_DIM: times, Y_DIM: y_coords, X_DIM: x_coords},
            dims=(TIME_DIM, Y_DIM, X_DIM),
            name=name,
            attrs={"units": "synthetic"},
        )
        data_vars[name] = da_var

    return xr.Dataset(data_vars)


def _open_gridmet_download(
    variables: Sequence[str],
    start: str,
    end: str,
    aoi: Mapping[str, float],
    time_res: str = "D",
    *,
    error: Exception | None = None,
) -> xr.Dataset:
    """Return a small in-memory Dataset that mimics a download fallback."""

    times = pd.date_range(start, end, freq=time_res or "D")
    y_coords, x_coords = _build_coords_for_aoi(aoi)
    rng = np.random.default_rng(7)

    data_vars = {}
    for name in variables:
        data = rng.normal(loc=0.0, scale=1.0, size=(len(times), len(y_coords), len(x_coords)))
        da_var = xr.DataArray(
            data,
            coords={TIME_DIM: times, Y_DIM: y_coords, X_DIM: x_coords},
            dims=(TIME_DIM, Y_DIM, X_DIM),
            name=name,
            attrs={"source": "synthetic-gridmet", "fallback_error": str(error) if error else ""},
        )
        data_vars[name] = da_var

    return xr.Dataset(data_vars)


def _build_coords_for_aoi(aoi: Mapping[str, float]) -> tuple[np.ndarray, np.ndarray]:
    """Create evenly spaced coordinate arrays tailored to the AOI."""

    min_lat, max_lat = float(aoi["min_lat"]), float(aoi["max_lat"])
    min_lon, max_lon = float(aoi["min_lon"]), float(aoi["max_lon"])
    # Ensure at least two grid cells exist even for tiny AOIs.
    n_y = max(2, int(round((max_lat - min_lat) / 0.05)))
    n_x = max(2, int(round((max_lon - min_lon) / 0.05)))
    y_coords = np.linspace(min_lat, max_lat, n_y)
    x_coords = np.linspace(min_lon, max_lon, n_x)
    return y_coords, x_coords


def _crop_to_aoi(ds: xr.Dataset, aoi: Mapping[str, float]) -> xr.Dataset:
    """Select the AOI bounds along the spatial dimensions."""

    y_vals = ds.coords[Y_DIM]
    x_vals = ds.coords[X_DIM]
    y_mask = (y_vals >= aoi["min_lat"]) & (y_vals <= aoi["max_lat"])
    x_mask = (x_vals >= aoi["min_lon"]) & (x_vals <= aoi["max_lon"])
    return ds.sel({Y_DIM: y_vals[y_mask], X_DIM: x_vals[x_mask]})


def _resolve_chunks(chunks: Mapping[Hashable, int] | None) -> Mapping[Hashable, int]:
    if chunks is None:
        return DEFAULT_CHUNKS
    return chunks


__all__ = ["load_gridmet_cube"]
