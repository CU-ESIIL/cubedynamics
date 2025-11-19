"""Virtual cube streaming helpers.

These utilities let callers represent large cubes as tiled loaders rather than
immediately materializing the full data into memory. A :class:`VirtualCube`
contains just enough metadata and the tiling strategy to load small tiles on
demand.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Mapping, Tuple

import numpy as np
import pandas as pd
import xarray as xr


@dataclass
class VirtualCube:
    """Representation of a lazily tiled cube.

    Parameters
    ----------
    dims:
        The expected dimension order of the cube (e.g., ("time", "y", "x")).
    coords_metadata:
        Minimal metadata needed to reconstruct coordinates if necessary. This
        is intentionally lightweight; tiles returned by ``loader`` carry the
        authoritative coordinate values.
    loader:
        Callable that loads a concrete ``xarray.DataArray`` tile when invoked
        with ``loader_kwargs`` merged with the kwargs yielded by the tilers.
    loader_kwargs:
        Base keyword arguments forwarded to ``loader`` for every tile request.
    time_tiler, spatial_tiler:
        Callables that accept ``loader_kwargs`` and yield dictionaries of extra
        keyword arguments describing each tile along the time or spatial axes.
    """

    dims: Tuple[str, ...]
    coords_metadata: Dict[str, Any]
    loader: Callable[..., xr.DataArray]
    loader_kwargs: Dict[str, Any]
    time_tiler: Callable[[Dict[str, Any]], Iterable[Dict[str, Any]]]
    spatial_tiler: Callable[[Dict[str, Any]], Iterable[Dict[str, Any]]]

    def iter_time_tiles(self) -> Iterable[xr.DataArray]:
        """Iterate over time-tiled cubes (full spatial AOI per tile)."""

        for t_kwargs in self.time_tiler(self.loader_kwargs):
            kwargs = {**self.loader_kwargs, **t_kwargs}
            yield self.loader(**kwargs)

    def iter_spatial_tiles(self) -> Iterable[xr.DataArray]:
        """Iterate over cubes tiled in space (full time range per tile)."""

        for s_kwargs in self.spatial_tiler(self.loader_kwargs):
            kwargs = {**self.loader_kwargs, **s_kwargs}
            yield self.loader(**kwargs)

    def iter_tiles(self) -> Iterable[xr.DataArray]:
        """Iterate over time × space tiles produced by both tilers."""

        time_specs = list(self.time_tiler(self.loader_kwargs))
        space_specs = list(self.spatial_tiler(self.loader_kwargs))

        if not time_specs:
            time_specs = [{}]
        if not space_specs:
            space_specs = [{}]

        for t_kwargs in time_specs:
            for s_kwargs in space_specs:
                kwargs = {**self.loader_kwargs, **t_kwargs, **s_kwargs}
                yield self.loader(**kwargs)

    def materialize(self) -> xr.DataArray:
        """Materialize the virtual cube as a single :class:`xarray.DataArray`."""

        tiles = list(self.iter_tiles())
        if not tiles:
            raise ValueError("VirtualCube has no tiles to materialize")

        combined = xr.combine_by_coords(tiles)
        if isinstance(combined, xr.Dataset) and len(combined.data_vars) == 1:
            only_var = next(iter(combined.data_vars))
            return combined[only_var]
        if isinstance(combined, xr.Dataset):
            raise ValueError("VirtualCube materialization produced a multi-variable dataset")
        return combined


def make_time_tiler(start: Any, end: Any, freq: str = "A") -> Callable[[Dict[str, Any]], Iterable[Dict[str, Any]]]:
    """Create a deterministic time tiler.

    The tiler yields ``{"start": chunk_start, "end": chunk_end}`` dictionaries
    splitting the interval ``[start, end]`` into regular ``freq`` increments.
    The final chunk always ends exactly at ``end``.
    """

    def tiler(kwargs: Mapping[str, Any]) -> Iterable[Dict[str, Any]]:
        t0 = pd.to_datetime(start if start is not None else kwargs.get("start"))
        t1 = pd.to_datetime(end if end is not None else kwargs.get("end"))
        if t0 is None or t1 is None:
            yield {}
            return

        edges = pd.date_range(t0, t1, freq=freq)
        if len(edges) == 0 or edges[0] != t0:
            edges = pd.DatetimeIndex([t0]).append(edges)
        if edges[-1] < t1:
            edges = edges.append(pd.DatetimeIndex([t1]))
        if len(edges) == 1:
            edges = edges.append(pd.DatetimeIndex([t1]))

        for s, e in zip(edges[:-1], edges[1:]):
            yield {"start": s, "end": e}

    return tiler


def make_spatial_tiler(
    bbox: Any,
    dlon: float = 2.0,
    dlat: float = 2.0,
) -> Callable[[Dict[str, Any]], Iterable[Dict[str, Any]]]:
    """Create a deterministic spatial tiler for a bounding box."""

    def tiler(kwargs: Mapping[str, Any]) -> Iterable[Dict[str, Any]]:
        bb = bbox if bbox is not None else kwargs.get("bbox")
        if bb is None:
            yield {}
            return

        xmin, ymin, xmax, ymax = bb
        xs = np.arange(xmin, xmax, dlon)
        ys = np.arange(ymin, ymax, dlat)

        for y0 in ys:
            for x0 in xs:
                yield {
                    "bbox": (
                        x0,
                        y0,
                        min(x0 + dlon, xmax),
                        min(y0 + dlat, ymax),
                    )
                }

    return tiler


__all__ = [
    "VirtualCube",
    "make_spatial_tiler",
    "make_time_tiler",
]
