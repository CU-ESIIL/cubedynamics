"""Sentinel-2 helper utilities for CubeDynamics."""

from __future__ import annotations

import warnings
from typing import Sequence

import cubo
import xarray as xr

from . import verbs as v
from .piping import pipe


def load_sentinel2_cube(
    lat: float,
    lon: float,
    start: str,
    end: str,
    *,
    bands: Sequence[str] | None = None,
    edge_size: int = 512,
    resolution: int = 10,
    max_cloud: int = 40,
) -> xr.DataArray:
    """Stream a Sentinel-2 L2A cube via ``cubo``.

    Parameters
    ----------
    lat, lon
        Center point for the spatial subset.
    start, end
        Date range (``YYYY-MM-DD``).
    bands
        Optional Sentinel-2 band names (e.g., ``["B02", "B03", "B04", "B08"]``).
        If ``None``, ``cubo``'s default "all bands" behavior is used.
    edge_size
        Spatial window size in pixels (default ``512``).
    resolution
        Spatial resolution in meters (default ``10``).
    max_cloud
        Maximum allowed cloud cover percentage (default ``40``).

    Returns
    -------
    xarray.DataArray
        Sentinel-2 stack with dims ``(time, y, x, band)``.
    """

    create_kwargs = dict(
        lat=lat,
        lon=lon,
        collection="sentinel-2-l2a",
        start_date=start,
        end_date=end,
        edge_size=edge_size,
        resolution=resolution,
        query={"eo:cloud_cover": {"lt": max_cloud}},
    )

    if bands is not None:
        create_kwargs["bands"] = list(bands)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        s2 = cubo.create(**create_kwargs)

    if "band" in s2.dims:
        s2 = s2.transpose("time", "y", "x", "band")

    return s2


def load_sentinel2_bands_cube(
    lat: float,
    lon: float,
    start: str,
    end: str,
    *,
    bands: Sequence[str],
    edge_size: int = 512,
    resolution: int = 10,
    max_cloud: int = 40,
) -> xr.DataArray:
    """Stream a Sentinel-2 L2A cube for a user-selected list of bands.

    This is a convenience wrapper over :func:`load_sentinel2_cube` that requires
    an explicit band list. Parameters mirror the generic loader except that
    ``bands`` is required.
    """

    if not bands:
        raise ValueError(
            "load_sentinel2_bands_cube requires a non-empty 'bands' list."
        )

    return load_sentinel2_cube(
        lat=lat,
        lon=lon,
        start=start,
        end=end,
        bands=bands,
        edge_size=edge_size,
        resolution=resolution,
        max_cloud=max_cloud,
    )


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
) -> xr.DataArray | tuple[xr.DataArray, xr.DataArray]:
    """Stream Sentinel-2 L2A data and compute a raw NDVI cube.

    The helper loads the red (B04) and near-infrared (B08) bands via
    :func:`load_sentinel2_bands_cube` and derives NDVI using the
    :mod:`cubedynamics.verbs` implementation.  NDVI values are returned in their
    raw physical range ``[-1, 1]`` so downstream verbs control any
    standardization.

    Parameters mirror :func:`load_sentinel2_bands_cube`.  When ``return_raw`` is
    ``True`` both the reflectance stack and NDVI cube are returned so callers can
    cache the original bands.
    """

    s2 = load_sentinel2_bands_cube(
        lat=lat,
        lon=lon,
        start=start,
        end=end,
        bands=["B04", "B08"],
        edge_size=edge_size,
        resolution=resolution,
        max_cloud=max_cloud,
    )

    ndvi = (pipe(s2) | v.ndvi_from_s2(nir_band="B08", red_band="B04")).unwrap()

    if return_raw:
        return s2, ndvi
    return ndvi


def load_sentinel2_ndvi_zscore_cube(
    lat: float,
    lon: float,
    start: str,
    end: str,
    *,
    edge_size: int = 512,
    resolution: int = 10,
    max_cloud: int = 40,
    keep_dim: bool = True,
) -> xr.DataArray:
    """Convenience wrapper that returns a z-scored Sentinel-2 NDVI cube.

    The helper simply calls :func:`load_sentinel2_ndvi_cube` and applies the
    standardized :func:`cubedynamics.verbs.zscore` verb so callers upgrading from
    older APIs retain a single-call experience.
    """

    ndvi = load_sentinel2_ndvi_cube(
        lat=lat,
        lon=lon,
        start=start,
        end=end,
        edge_size=edge_size,
        resolution=resolution,
        max_cloud=max_cloud,
    )

    ndvi_z = (pipe(ndvi) | v.zscore(dim="time", keep_dim=keep_dim)).unwrap()
    return ndvi_z


__all__ = [
    "load_sentinel2_cube",
    "load_sentinel2_bands_cube",
    "load_sentinel2_ndvi_cube",
    "load_sentinel2_ndvi_zscore_cube",
]
