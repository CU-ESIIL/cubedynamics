"""Sentinel-2 data access helpers."""

from __future__ import annotations

from typing import Mapping, Sequence

import cubo
import xarray as xr

from ..config import BAND_DIM, DEFAULT_CHUNKS, TIME_DIM, X_DIM, Y_DIM


def load_s2_cube(
    lat: float,
    lon: float,
    start: str,
    end: str,
    edge_size: int = 1028,
    resolution: int = 10,
    cloud_lt: int = 40,
    bands: Sequence[str] | None = None,
    chunks: Mapping[str, int] | None = None,
) -> xr.Dataset:
    """Stream Sentinel-2 L2A data via cubo and return a dask-backed xarray Dataset."""

    selected_bands = list(bands) if bands is not None else ["B04", "B08"]
    cube = cubo.create(
        lat=lat,
        lon=lon,
        start=start,
        end=end,
        edge_size=edge_size,
        resolution=resolution,
        collection="sentinel-2-l2a",
        bands=selected_bands,
        query={"eo:cloud_cover": {"lt": cloud_lt}},
    )

    ds = cube.to_xarray()
    desired_order = tuple(dim for dim in (TIME_DIM, Y_DIM, X_DIM, BAND_DIM) if dim in ds.dims)
    ds = ds.transpose(*desired_order)
    ds = ds.chunk(chunks or DEFAULT_CHUNKS)
    return ds
