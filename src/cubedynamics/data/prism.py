"""PRISM data access helpers with a streaming-first contract."""

from __future__ import annotations

from typing import Hashable, Mapping, Sequence

import numpy as np
import pandas as pd
import xarray as xr

from ..config import DEFAULT_CHUNKS, TIME_DIM, X_DIM, Y_DIM


def load_prism_cube(
    variables: Sequence[str],
    start: str,
    end: str,
    aoi: Mapping[str, float],
    time_res: str = "M",
    chunks: Mapping[Hashable, int] | None = None,
    prefer_streaming: bool = True,
) -> xr.Dataset:
    """Load a PRISM-like cube with a streaming-first policy."""

    chunk_map = _resolve_chunks(chunks)

    if prefer_streaming:
        try:
            ds = _open_prism_streaming(variables, start, end, aoi, time_res)
        except Exception as exc:  # pragma: no cover - used in tests
            import warnings

            warnings.warn(
                "PRISM streaming backend unavailable; falling back to local download.",
                RuntimeWarning,
            )
            ds = _open_prism_download(variables, start, end, aoi, time_res, error=exc)
    else:
        ds = _open_prism_download(variables, start, end, aoi, time_res)

    ds = _crop_to_aoi(ds, aoi)
    ds = ds.chunk(chunk_map)
    return ds


def _open_prism_streaming(
    variables: Sequence[str],
    start: str,
    end: str,
    aoi: Mapping[str, float],
    time_res: str = "M",
) -> xr.Dataset:
    try:
        import dask.array as da
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("dask is required for PRISM streaming") from exc

    freq = time_res or "M"
    times = pd.date_range(start, end, freq=freq)
    if not len(times):
        raise ValueError("No time steps available for the requested range")

    y_coords, x_coords = _build_coords_for_aoi(aoi)
    chunks = (len(times), min(len(y_coords), 128), min(len(x_coords), 128))
    rng = da.random.RandomState(111)
    data_vars = {}
    for name in variables:
        data = rng.gamma(shape=2.0, scale=1.0, size=(len(times), len(y_coords), len(x_coords)), chunks=chunks)
        da_var = xr.DataArray(
            data,
            coords={TIME_DIM: times, Y_DIM: y_coords, X_DIM: x_coords},
            dims=(TIME_DIM, Y_DIM, X_DIM),
            name=name,
            attrs={"units": "synthetic"},
        )
        data_vars[name] = da_var

    return xr.Dataset(data_vars)


def _open_prism_download(
    variables: Sequence[str],
    start: str,
    end: str,
    aoi: Mapping[str, float],
    time_res: str = "M",
    *,
    error: Exception | None = None,
) -> xr.Dataset:
    freq = time_res or "M"
    times = pd.date_range(start, end, freq=freq)
    y_coords, x_coords = _build_coords_for_aoi(aoi)
    rng = np.random.default_rng(19)

    data_vars = {}
    for name in variables:
        data = rng.uniform(low=0.0, high=5.0, size=(len(times), len(y_coords), len(x_coords)))
        da_var = xr.DataArray(
            data,
            coords={TIME_DIM: times, Y_DIM: y_coords, X_DIM: x_coords},
            dims=(TIME_DIM, Y_DIM, X_DIM),
            name=name,
            attrs={"source": "synthetic-prism", "fallback_error": str(error) if error else ""},
        )
        data_vars[name] = da_var

    return xr.Dataset(data_vars)


def _build_coords_for_aoi(aoi: Mapping[str, float]) -> tuple[np.ndarray, np.ndarray]:
    min_lat, max_lat = float(aoi["min_lat"]), float(aoi["max_lat"])
    min_lon, max_lon = float(aoi["min_lon"]), float(aoi["max_lon"])
    n_y = max(2, int(round((max_lat - min_lat) / 0.1)))
    n_x = max(2, int(round((max_lon - min_lon) / 0.1)))
    y_coords = np.linspace(min_lat, max_lat, n_y)
    x_coords = np.linspace(min_lon, max_lon, n_x)
    return y_coords, x_coords


def _crop_to_aoi(ds: xr.Dataset, aoi: Mapping[str, float]) -> xr.Dataset:
    y_vals = ds.coords[Y_DIM]
    x_vals = ds.coords[X_DIM]
    y_mask = (y_vals >= aoi["min_lat"]) & (y_vals <= aoi["max_lat"])
    x_mask = (x_vals >= aoi["min_lon"]) & (x_vals <= aoi["max_lon"])
    return ds.sel({Y_DIM: y_vals[y_mask], X_DIM: x_vals[x_mask]})


def _resolve_chunks(chunks: Mapping[Hashable, int] | None) -> Mapping[Hashable, int]:
    if chunks is None:
        return DEFAULT_CHUNKS
    return chunks


__all__ = ["load_prism_cube"]
