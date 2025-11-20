"""Sentinel-2 helper utilities for CubeDynamics."""

from __future__ import annotations

import math
import warnings
from typing import Sequence

import cubo
import xarray as xr
from pyproj import CRS, Transformer

from . import verbs as v
from .piping import pipe


def load_sentinel2_cube(
    lat: float | None,
    lon: float | None,
    start: str,
    end: str,
    *,
    bbox: Sequence[float] | None = None,
    bands: Sequence[str] | None = None,
    edge_size: int = 512,
    resolution: int = 10,
    max_cloud: int = 40,
    show_progress: bool = True,
) -> xr.DataArray:
    """Stream a Sentinel-2 L2A cube via ``cubo``.

    Parameters
    ----------
    lat, lon
        Center point for the spatial subset. Provide both or supply ``bbox``.
    bbox
        Optional ``(xmin, ymin, xmax, ymax)`` bounding box in geographic
        coordinates. When provided, the center coordinate and pixel edge size
        are derived to fully cover the requested extent.
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

    lat, lon, edge_size = _resolve_lat_lon_and_edge_size(
        lat, lon, bbox, edge_size, resolution
    )

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
    lat: float | None,
    lon: float | None,
    start: str,
    end: str,
    *,
    bbox: Sequence[float] | None = None,
    bands: Sequence[str],
    edge_size: int = 512,
    resolution: int = 10,
    max_cloud: int = 40,
    show_progress: bool = True,
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
        bbox=bbox,
        bands=bands,
        edge_size=edge_size,
        resolution=resolution,
        max_cloud=max_cloud,
        show_progress=show_progress,
    )


def load_sentinel2_ndvi_cube(
    lat: float | None,
    lon: float | None,
    start: str,
    end: str,
    *,
    bbox: Sequence[float] | None = None,
    edge_size: int = 512,
    resolution: int = 10,
    max_cloud: int = 40,
    return_raw: bool = False,
    show_progress: bool = True,
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
        bbox=bbox,
        bands=["B04", "B08"],
        edge_size=edge_size,
        resolution=resolution,
        max_cloud=max_cloud,
        show_progress=show_progress,
    )

    ndvi = (pipe(s2) | v.ndvi_from_s2(nir_band="B08", red_band="B04")).unwrap()

    if return_raw:
        return s2, ndvi
    return ndvi


def load_sentinel2_ndvi_zscore_cube(
    lat: float | None,
    lon: float | None,
    start: str,
    end: str,
    *,
    bbox: Sequence[float] | None = None,
    edge_size: int = 512,
    resolution: int = 10,
    max_cloud: int = 40,
    keep_dim: bool = True,
    show_progress: bool = True,
) -> xr.DataArray:
    """Convenience wrapper that returns a z-scored Sentinel-2 NDVI cube.

    The helper simply calls :func:`load_sentinel2_ndvi_cube` and applies the
    standardized :func:`cubedynamics.verbs.zscore` verb so callers upgrading from
    older APIs retain a single-call experience.
    """

    warnings.warn(
        "load_sentinel2_ndvi_zscore_cube is deprecated; load raw NDVI and apply v.zscore(dim='time') instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    ndvi = load_sentinel2_ndvi_cube(
        lat=lat,
        lon=lon,
        start=start,
        end=end,
        bbox=bbox,
        edge_size=edge_size,
        resolution=resolution,
        max_cloud=max_cloud,
        show_progress=show_progress,
    )

    ndvi_z = (pipe(ndvi) | v.zscore(dim="time", keep_dim=keep_dim)).unwrap()
    return ndvi_z


__all__ = [
    "load_sentinel2_cube",
    "load_sentinel2_bands_cube",
    "load_sentinel2_ndvi_cube",
    "load_sentinel2_ndvi_zscore_cube",
]


def _resolve_lat_lon_and_edge_size(
    lat: float | None,
    lon: float | None,
    bbox: Sequence[float] | None,
    edge_size: int,
    resolution: int,
) -> tuple[float, float, int]:
    """Return a valid ``lat``, ``lon``, and ``edge_size`` for Sentinel-2 requests.

    ``cubo.create`` requires a center coordinate along with an edge size and
    spatial resolution. When callers provide a bounding box, we compute the
    center point and derive an edge size that fully covers the requested extent.
    The helper falls back to the user-provided latitude and longitude when a
    bounding box is not supplied.
    """

    if bbox is None:
        if lat is None or lon is None:
            raise ValueError(
                "load_sentinel2_cube requires either a bbox or both lat and lon."
            )
        return lat, lon, edge_size

    xmin, ymin, xmax, ymax = bbox
    center_lon = (xmin + xmax) / 2.0
    center_lat = (ymin + ymax) / 2.0

    zone = math.floor((center_lon + 180.0) / 6.0) + 1
    utm_crs = CRS.from_dict({"proj": "utm", "zone": zone, "south": center_lat < 0})
    transformer = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)

    x0, y0 = transformer.transform(xmin, ymin)
    x1, y1 = transformer.transform(xmax, ymax)

    span_m = max(abs(x1 - x0), abs(y1 - y0))
    required_edge = int(math.ceil(span_m / resolution))
    adjusted_edge = max(edge_size, required_edge)

    return center_lat, center_lon, adjusted_edge
