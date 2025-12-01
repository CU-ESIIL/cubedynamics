"""Landsat-8 streaming via Microsoft Planetary Computer (MPC).

The :func:`landsat8_mpc` verb streams Landsat 8 Collection 2 Level-2 surface
reflectance from the Microsoft Planetary Computer STAC catalog. It returns a
lazy, dask-backed :class:`xarray.DataArray` with dimensions ``(time, band, y,
x)`` so downstream computations can be composed without loading the full
dataset into memory.

Example
-------
>>> from cubedynamics import pipe, verbs as v
>>> bbox = [-105.35, 39.9, -105.15, 40.1]
>>> cube = pipe(None) | v.landsat8_mpc(
...     bbox=bbox,
...     start="2019-07-01",
...     end="2019-08-01",
... )
>>> da = cube.unwrap()
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import wraps
from typing import Iterable

import numpy as np
import planetary_computer as pc
import rioxarray as rxr
import xarray as xr
from pystac_client import Client

from ..piping import Verb

MPC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

BAND_MAP: Mapping[str, str] = {
    "red": "SR_B4",
    "nir": "SR_B5",
}


def pipeable(func):
    """Decorator that makes a verb callable or pipe-friendly.

    When called without the first positional argument, a :class:`Verb` is
    returned so the function can be used in ``pipe(...) | v.some_verb(...)``
    chains. When called with a ``value`` argument, the function executes
    immediately.
    """

    @wraps(func)
    def _wrapper(*args, **kwargs):
        if args:
            return func(*args, **kwargs)
        return Verb(lambda value: func(value, **kwargs))

    return _wrapper


def landsat8_mpc_stream(
    bbox: Sequence[float],
    start: str,
    end: str,
    band_aliases: Iterable[str] = ("red", "nir"),
    max_cloud_cover: float = 50,
    chunks_xy: Mapping[str, int] | None = None,
    stac_url: str = MPC_STAC_URL,
) -> xr.DataArray:
    """Stream Landsat-8 Collection 2 Level-2 scenes from Microsoft Planetary Computer.

    The stream lazily opens surface reflectance COGs (SR_B4 for red and SR_B5 for
    near-infrared by default) and stacks them into a cube with dimensions
    ``(time, band, y, x)``. Data are returned as ``float32`` and remain dask-backed
    so downstream computations trigger IO as needed.

    Parameters
    ----------
    bbox
        Bounding box ``[minx, miny, maxx, maxy]`` in lon/lat for the STAC search.
    start, end
        ISO date strings delimiting the search interval.
    band_aliases
        Sequence of band aliases to load. Must be keys in :data:`BAND_MAP`.
    max_cloud_cover
        Maximum allowable ``eo:cloud_cover`` percentage for candidate scenes.
    chunks_xy
        Optional mapping for dask chunk sizes along x/y passed to
        :func:`rioxarray.open_rasterio`. Defaults to ``{"x": 1024, "y": 1024}``.
    stac_url
        STAC API endpoint. Defaults to the MPC STAC service.

    Returns
    -------
    xarray.DataArray
        DataArray with dimensions ``(time, band, y, x)`` containing the stacked
        scenes.
    """

    if chunks_xy is None:
        chunks_xy = {"x": 1024, "y": 1024}

    catalog = Client.open(stac_url)

    search = catalog.search(
        collections=["landsat-8-c2-l2"],
        bbox=bbox,
        datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": max_cloud_cover}},
    )

    items = list(search.get_items())
    if not items:
        raise RuntimeError("No Landsat-8 items found for this query.")

    signed_items = [pc.sign(item) for item in items]
    scene_das: list[xr.DataArray] = []

    for item in signed_items:
        band_das: list[xr.DataArray] = []
        skip_item = False

        for alias in band_aliases:
            asset_id = BAND_MAP[alias]
            asset = item.assets.get(asset_id)
            if asset is None:
                skip_item = True
                break

            href = asset.href
            da = rxr.open_rasterio(href, masked=True, chunks=chunks_xy)
            if "band" in da.dims and da.sizes.get("band", 1) == 1:
                da = da.squeeze("band", drop=True)
            da = da.expand_dims(band=[alias])
            band_das.append(da)

        if skip_item or not band_das:
            continue

        scene = xr.concat(band_das, dim="band")
        dt = np.datetime64(item.properties["datetime"])
        scene = scene.expand_dims(time=[dt])
        scene_das.append(scene)

    if not scene_das:
        raise RuntimeError("No scenes could be stacked (missing assets?).")

    cube = xr.concat(scene_das, dim="time", join="outer").sortby("time")
    cube = cube.astype("float32")
    return cube


@pipeable
def landsat8_mpc(
    value,
    *,
    bbox,
    start,
    end,
    band_aliases=("red", "nir"),
    max_cloud_cover=50,
    chunks_xy=None,
    stac_url="https://planetarycomputer.microsoft.com/api/stac/v1",
):
    """
    Landsat 8 (MPC) streaming verb for cubedynamics.

    Parameters
    ----------
    value : Any
        Required for pipeable verbs but unused here.
    bbox : list[float]
        [min_lon, min_lat, max_lon, max_lat]
    start : str
        ISO start date (YYYY-MM-DD)
    end : str
        ISO end date (YYYY-MM-DD)
    band_aliases : tuple[str]
        Bands to extract (e.g., ("red","nir"))
    max_cloud_cover : int
        Maximum cloud cover percentage
    chunks_xy : dict or None
        Dask spatial chunking, e.g. {"x": 1024, "y": 1024}
    stac_url : str
        STAC endpoint, defaults to the Microsoft Planetary Computer.

    Returns
    -------
    xarray.DataArray
        DataArray with dims (time, band, y, x).
    """
    return landsat8_mpc_stream(
        bbox=bbox,
        start=start,
        end=end,
        band_aliases=band_aliases,
        max_cloud_cover=max_cloud_cover,
        chunks_xy=chunks_xy,
        stac_url=stac_url,
    )


__all__ = ["landsat8_mpc", "landsat8_mpc_stream", "BAND_MAP", "MPC_STAC_URL"]
