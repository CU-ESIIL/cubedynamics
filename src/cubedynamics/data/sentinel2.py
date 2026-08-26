"""Sentinel-2 data access helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Sequence

import cubo
import xarray as xr

from ..config import BAND_DIM, DEFAULT_CHUNKS, TIME_DIM, X_DIM, Y_DIM
from ..indices.vegetation import compute_ndvi_from_s2


def _to_dataarray(cube: xr.Dataset | xr.DataArray) -> xr.DataArray:
    if isinstance(cube, xr.DataArray):
        return cube
    if BAND_DIM in cube.dims:
        return cube.to_array().squeeze("variable", drop=True)
    if len(cube.data_vars) == 1:
        return cube[list(cube.data_vars)[0]]
    raise ValueError("Unable to determine data variable containing Sentinel-2 bands.")


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
) -> xr.DataArray:
    """Stream Sentinel-2 L2A data via cubo and return a dask-backed xarray object."""

    selected_bands = list(bands) if bands is not None else ["B04", "B08"]
    cube = cubo.create(
        lat=lat,
        lon=lon,
        start_date=start,
        end_date=end,
        edge_size=edge_size,
        resolution=resolution,
        collection="sentinel-2-l2a",
        bands=selected_bands,
        query={"eo:cloud_cover": {"lt": cloud_lt}},
    )

    data = _to_dataarray(cube)
    desired_order = tuple(
        dim for dim in (TIME_DIM, BAND_DIM, Y_DIM, X_DIM) if dim in data.dims
    )
    data = data.transpose(*desired_order)
    data = data.chunk(chunks or DEFAULT_CHUNKS)
    data = data.copy(deep=False)
    data.attrs.update(
        {
            "source": "sentinel2",
            "source_provider": "European Union Copernicus Programme / ESA",
            "source_product": "Sentinel-2 Level-2A surface reflectance",
            "source_variables": ",".join(selected_bands),
            "requested_start": str(start),
            "requested_end": str(end),
            "spatial_query": f"lat={lat},lon={lon},edge_size={edge_size}",
            "spatial_resolution": f"{resolution} m requested output",
            "streaming_protocol": "cubo STAC and cloud-optimized assets",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "is_synthetic": False,
        }
    )
    return data


def load_s2_ndvi_cube(
    lat: float,
    lon: float,
    start: str,
    end: str,
    edge_size: int = 1028,
    resolution: int = 10,
    cloud_lt: int = 40,
    bands: Sequence[str] | None = None,
    chunks: Mapping[str, int] | None = None,
) -> xr.DataArray:
    """Stream Sentinel-2 and return an NDVI cube ready for downstream ops."""

    required_bands = {"B04", "B08"}
    if bands is None:
        selected_bands = ["B04", "B08"]
    else:
        selected_bands = list(bands)
        missing = sorted(required_bands.difference(selected_bands))
        selected_bands.extend(missing)

    s2 = load_s2_cube(
        lat=lat,
        lon=lon,
        start=start,
        end=end,
        edge_size=edge_size,
        resolution=resolution,
        cloud_lt=cloud_lt,
        bands=selected_bands,
        chunks=chunks,
    )
    ndvi = compute_ndvi_from_s2(s2)
    ndvi.attrs.update(
        {
            key: value
            for key, value in s2.attrs.items()
            if key not in {"long_name", "formula", "bands"}
        }
    )
    ndvi.attrs.update(
        {
            "source_product": "NDVI derived from Sentinel-2 Level-2A B08 and B04",
            "source_variables": "B08,B04",
            "data_state": "derived",
            "units": "1",
        }
    )
    return ndvi
