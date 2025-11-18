"""Sentinel-2 helper utilities for CubeDynamics."""

from __future__ import annotations

import warnings

import cubo
import xarray as xr

from . import verbs as v
from .piping import pipe


def load_sentinel2_ndvi_cube(
    lat: float,
    lon: float,
    start: str,
    end: str,
    *,
    edge_size: int = 512,
    resolution: int = 10,
    max_cloud: int = 40,
    return_raw: bool = False,
) -> xr.DataArray | tuple[xr.DataArray, xr.DataArray, xr.DataArray]:
    """Stream Sentinel-2 L2A data and compute NDVI and NDVI z-score cubes.

    Parameters
    ----------
    lat, lon:
        Center point for the Sentinel-2 spatial subset.
    start, end:
        Date range (``YYYY-MM-DD``) to request.
    edge_size:
        Spatial window size in pixels (default ``512``).
    resolution:
        Spatial resolution in meters (default ``10``).
    max_cloud:
        Maximum allowed cloud cover percentage (default ``40``).
    return_raw:
        If ``True`` return ``(s2, ndvi, ndvi_z)``; otherwise only the NDVI
        z-score cube is returned.

    Returns
    -------
    xarray.DataArray or tuple of DataArray
        NDVI z-score cube or ``(s2, ndvi, ndvi_z)`` if ``return_raw`` is true.
    """

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        s2 = cubo.create(
            lat=lat,
            lon=lon,
            collection="sentinel-2-l2a",
            bands=["B04", "B08"],
            start_date=start,
            end_date=end,
            edge_size=edge_size,
            resolution=resolution,
            query={"eo:cloud_cover": {"lt": max_cloud}},
        )

    if "band" in s2.dims:
        s2 = s2.transpose("time", "y", "x", "band")

    ndvi = (pipe(s2) | v.ndvi_from_s2(nir_band="B08", red_band="B04")).unwrap()
    ndvi_z = (pipe(ndvi) | v.zscore(dim="time")).unwrap()

    if return_raw:
        return s2, ndvi, ndvi_z
    return ndvi_z


__all__ = ["load_sentinel2_ndvi_cube"]
