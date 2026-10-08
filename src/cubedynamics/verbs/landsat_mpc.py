"""Lazy Landsat Collection 2 Level-2 streaming from Planetary Computer.

STAC raster metadata is the sole scaling authority. Scene cloud-cover filtering
is not pixel masking. Source stages do metadata IO; Dask tasks read remote COG
windows only when the caller computes the array.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from functools import wraps
from typing import Iterable

import numpy as np
import xarray as xr

from ..piping import Verb

MPC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
# Retained unchanged for legacy imports; the STAC loader does not use it.
BAND_MAP = {"red": "SR_B4", "nir": "SR_B5"}


def pipeable(func):
    """Support both factory stages and immediate calls with a positional value."""
    @wraps(func)
    def _wrapper(*args, **kwargs):
        if args or "value" in kwargs:
            return func(*args, **kwargs)
        stage = Verb(lambda value: func(value, **kwargs))
        stage._cd_semantic_name = func.__name__
        return stage
    return _wrapper


def _common_epsg(items, bands):
    """Infer only a complete, unanimous item/asset EPSG; never guess a UTM zone."""
    codes = set()
    for item in items:
        for band in bands:
            asset_fields = item.assets[band].extra_fields
            fields = (asset_fields if any(k in asset_fields for k in ("proj:epsg", "proj:code"))
                      else item.properties)
            code = fields.get("proj:epsg")
            if code is None:
                text = fields.get("proj:code", "")
                code = text[5:] if isinstance(text, str) and text.startswith("EPSG:") else None
            try:
                codes.add(int(code))
            except (TypeError, ValueError):
                return None
    return codes.pop() if len(codes) == 1 else None


def landsat_mpc_stream(
    bbox: Sequence[float], start: str, end: str,
    bands: Iterable[str] = ("red", "nir08"), max_cloud_cover: float = 50,
    epsg: int | None = None, resolution: float = 30, chunksize=1024,
    platforms: Iterable[str] | None = None, stac_url: str = MPC_STAC_URL,
) -> xr.DataArray:
    """Discover signed STAC assets and build a lazy, scaled rectangular cube.

    ``bands`` are MPC asset keys. Optical bands use physical reflectance; QA
    assets retain their encoded values. No pixel mask is applied. Resolution
    is in output CRS units. Missing assets fail explicitly rather than dropping
    observations or manufacturing all-NaN bands.
    """
    import planetary_computer as pc
    import stackstac
    from pystac_client import Client

    bbox = tuple(bbox)
    if (len(bbox) != 4 or not all(math.isfinite(v) for v in bbox)
            or not -180 <= bbox[0] < bbox[2] <= 180
            or not -90 <= bbox[1] < bbox[3] <= 90):
        raise ValueError("bbox must be [west, south, east, north] in lon/lat, without antimeridian crossing.")
    if isinstance(bands, str):
        raise ValueError("bands must be a sequence of MPC asset names, not a string.")
    bands = tuple(bands)
    if not bands or len(set(bands)) != len(bands):
        raise ValueError("bands must be nonempty and unique.")
    if not math.isfinite(max_cloud_cover) or not 0 <= max_cloud_cover <= 100:
        raise ValueError("max_cloud_cover must be between 0 and 100.")
    if not math.isfinite(resolution) or resolution <= 0:
        raise ValueError("resolution must be positive in output CRS units.")
    query = {"eo:cloud_cover": {"lt": max_cloud_cover}}
    if platforms is not None:
        platforms = (platforms,) if isinstance(platforms, str) else tuple(platforms)
        if not platforms:
            raise ValueError("platforms must be nonempty or None.")
        query["platform"] = {"in": list(platforms)}
    search = Client.open(stac_url).search(
        collections=["landsat-c2-l2"], bbox=bbox,
        datetime=f"{start}/{end}", query=query,
    )
    items = list(search.items())
    if not items:
        raise RuntimeError("No Landsat items found for this query.")
    for item in items:
        missing = set(bands).difference(item.assets)
        if missing:
            raise ValueError(f"Landsat item {item.id} lacks requested assets: {sorted(missing)}.")
        for band in set(bands).intersection(
            {"coastal", "blue", "green", "red", "nir08", "swir16", "swir22"}
        ):
            raster_bands = item.assets[band].extra_fields.get("raster:bands", [])
            if (len(raster_bands) != 1 or "scale" not in raster_bands[0]
                    or "offset" not in raster_bands[0]):
                raise ValueError(
                    f"Landsat item {item.id} asset {band} lacks STAC scale/offset metadata; "
                    "cannot safely return physical reflectance."
                )
    if epsg is None:
        epsg = _common_epsg(items, bands)
        if epsg is None:
            raise ValueError("Cannot infer a common Landsat CRS from STAC metadata. Specify epsg= with an appropriate output CRS (e.g. 32613 for Boulder).")
    signed_items = [pc.sign(item) for item in items]
    cube = stackstac.stack(
        signed_items, assets=list(bands), bounds_latlon=bbox, epsg=epsg,
        resolution=resolution, chunksize=chunksize, rescale=True,
        dtype=np.dtype("float64"), errors_as_nodata=(),
    ).sel(band=list(bands)).transpose("time", "band", "y", "x")
    cube.attrs.update(
        source="Microsoft Planetary Computer", collection="landsat-c2-l2", epsg=epsg,
        query_bbox=bbox, query_datetime=f"{start}/{end}",
        scene_cloud_cover_lt=max_cloud_cover,
        scaling="STAC raster:bands scale/offset applied once by stackstac",
        pixel_cloud_mask_applied=False,
    )
    return cube


@pipeable
def landsat_mpc(
    value, *, bbox, start, end, bands=("red", "nir08"),
    max_cloud_cover=50, epsg=None, resolution=30, chunksize=1024,
    platforms=None, stac_url=MPC_STAC_URL,
):
    """Load Landsat Collection 2 Level-2 bands as a lazy source stage.

    Call ``landsat_mpc(**options)`` to create a pipe stage, or
    ``landsat_mpc(None, **options)`` for an immediate DataArray. Input is unused.

    Parameters
    ----------
    value : Any
        Pipe input, unused.
    bbox : sequence of float
        WGS84 [west, south, east, north].
    start, end : str
        ISO dates for STAC discovery.
    bands : sequence of str
        MPC asset names, defaults to red and nir08. Optical values are physical
        surface reflectance: do not apply Collection 2 scaling again.
    max_cloud_cover : float
        Strict upper bound on scene cloud percentage, not a pixel cloud mask.
    epsg : int or None
        Output EPSG. Inferred only from complete, common STAC EPSG metadata;
        otherwise supply explicitly. No geographic UTM guessing.
    resolution : float
        Output pixel size in CRS units (30 meters for a meter-based CRS).
    chunksize : int or tuple
        Dask chunk size accepted by stackstac, defaults to 1024.
    platforms : sequence of str or None
        Optional STAC platform filter, e.g. ("landsat-8", "landsat-9").
    stac_url : str
        STAC API endpoint.

    Returns
    -------
    xarray.DataArray
        Dask-backed (time, band, y, x) cube. Compute triggers remote COG reads.
    """
    return landsat_mpc_stream(
        bbox, start, end, bands, max_cloud_cover, epsg, resolution, chunksize,
        platforms, stac_url,
    )


def landsat8_mpc_stream(
    bbox, start, end, band_aliases=("red", "nir"), max_cloud_cover=50,
    chunks_xy=None, stac_url=MPC_STAC_URL, *, epsg=None, resolution=30,
) -> xr.DataArray:
    """Compatibility loader restricted to Landsat 8; preserves legacy nir label.

    Values now correctly use physical reflectance rather than raw digital
    numbers. Supply epsg when STAC projection metadata is insufficient.
    """
    aliases = tuple(band_aliases)
    chunks = {"x": 1024, "y": 1024} if chunks_xy is None else chunks_xy
    cube = landsat_mpc_stream(
        bbox, start, end, tuple("nir08" if b == "nir" else b for b in aliases),
        max_cloud_cover, epsg, resolution,
        (1, 1, chunks["y"], chunks["x"]), ("landsat-8",), stac_url,
    )
    return cube.astype("float32").assign_coords(band=list(aliases))


@pipeable
def landsat8_mpc(
    value, *, bbox, start, end, band_aliases=("red", "nir"),
    max_cloud_cover=50, chunks_xy=None, stac_url=MPC_STAC_URL,
    epsg=None, resolution=30,
):
    """Compatibility Landsat 8 stage; prefer landsat_mpc for new workflows."""
    return landsat8_mpc_stream(
        bbox, start, end, band_aliases, max_cloud_cover, chunks_xy, stac_url,
        epsg=epsg, resolution=resolution,
    )


def _compute_ndvi_from_stack(
    stack: xr.DataArray, *, red_alias: str = "red", nir_alias: str = "nir"
) -> xr.DataArray:
    """Compute NDVI from a Landsat stack with a ``band`` dimension."""

    if "band" not in stack.dims:
        raise ValueError("Landsat stack must include a 'band' dimension to compute NDVI.")

    bands = stack.coords.get("band")
    if bands is not None and red_alias in bands.values and nir_alias in bands.values:
        red = stack.sel(band=red_alias)
        nir = stack.sel(band=nir_alias)
    else:
        # Fallback to positional selection if aliases are missing
        red = stack.isel(band=0)
        nir = stack.isel(band=1)

    ndvi = (nir - red) / (nir + red)
    ndvi = ndvi.rename("ndvi")
    ndvi.attrs.setdefault("long_name", "Normalized Difference Vegetation Index")
    ndvi.attrs.setdefault("units", "1")
    return ndvi


def _bounding_box_from_mask(mask: xr.DataArray) -> tuple[slice, slice]:
    """Return slices that crop to the non-NaN footprint of ``mask``.

    Raises
    ------
    ValueError
        If the mask contains no finite pixels.
    """

    mask_values = np.asarray(mask.values)
    finite = np.isfinite(mask_values)
    if not finite.any():
        raise ValueError("No finite pixels available to crop Landsat NDVI.")

    y_idx, x_idx = np.nonzero(finite)
    y_min, y_max = int(y_idx.min()), int(y_idx.max())
    x_min, x_max = int(x_idx.min()), int(x_idx.max())
    return slice(y_min, y_max + 1), slice(x_min, x_max + 1)


def _coarsen_if_needed(da: xr.DataArray, *, max_y: int, max_x: int) -> xr.DataArray:
    """Coarsen ``da`` along y/x so sizes do not exceed ``max_*``."""

    factors: dict[str, int] = {}
    if da.sizes.get("y", 0) > max_y:
        factors["y"] = int(math.ceil(da.sizes["y"] / max_y))
    if da.sizes.get("x", 0) > max_x:
        factors["x"] = int(math.ceil(da.sizes["x"] / max_x))

    if not factors:
        return da

    return da.coarsen(**factors, boundary="trim").mean()


def landsat_vis_ndvi(
    bbox,
    start,
    end,
    *,
    collection: str = "landsat-c2-l2",
    max_y: int = 256,
    max_x: int = 256,
    max_time: int = 16,
    auto_crop_valid: bool = True,
    band_aliases: Iterable[str] = ("red", "nir"),
    max_cloud_cover: float = 50,
    chunks_xy: Mapping[str, int] | None = None,
    stac_url: str = MPC_STAC_URL,
    stack_da: xr.DataArray | None = None,
    epsg: int | None = None,
    resolution: float = 30,
) -> xr.DataArray:
    """Return a visualization-friendly Landsat NDVI cube.

    The helper keeps in-memory footprints small by cropping out empty borders and
    coarsening spatial/time axes when needed. It mirrors ``v.landsat8_mpc`` for
    sourcing data but materializes the reduced cube for plotting.
    """

    if collection not in {"landsat-c2-l2", "landsat-8-c2-l2"}:
        raise ValueError("Only the 'landsat-c2-l2' collection is supported.")

    stack = stack_da
    if stack is None:
        stack = landsat8_mpc_stream(
            bbox=bbox,
            start=start,
            end=end,
            band_aliases=band_aliases,
            max_cloud_cover=max_cloud_cover,
            chunks_xy=chunks_xy,
            stac_url=stac_url,
            epsg=epsg,
            resolution=resolution,
        )

    ndvi = _compute_ndvi_from_stack(stack)

    if auto_crop_valid:
        finite_mask = np.isfinite(ndvi)
        valid_mask = finite_mask.any(dim="time") if "time" in ndvi.dims else finite_mask
        y_slice, x_slice = _bounding_box_from_mask(valid_mask)
        ndvi = ndvi.isel(y=y_slice, x=x_slice)

    if ndvi.sizes.get("time", 0) > max_time:
        step = int(math.ceil(ndvi.sizes["time"] / max_time))
        ndvi = ndvi.isel(time=slice(0, None, step))

    ndvi = _coarsen_if_needed(ndvi, max_y=max_y, max_x=max_x)

    return ndvi.transpose("time", "y", "x").compute()


def landsat_ndvi_plot(
    bbox,
    start,
    end,
    *,
    max_y: int = 256,
    max_x: int = 256,
    max_time: int = 16,
    epsg: int | None = None,
    **plot_kwargs,
):
    """Load Landsat NDVI, downsample for visualization, and render the cube viewer."""

    ndvi_vis = landsat_vis_ndvi(
        bbox=bbox,
        start=start,
        end=end,
        max_y=max_y,
        max_x=max_x,
        max_time=max_time,
        epsg=epsg,
    )

    from cubedynamics import pipe, verbs as v

    return pipe(ndvi_vis) | v.plot(time_dim="time", **plot_kwargs)


__all__ = ["landsat_mpc", "landsat_mpc_stream", "landsat8_mpc", "landsat8_mpc_stream", "BAND_MAP", "MPC_STAC_URL"]
